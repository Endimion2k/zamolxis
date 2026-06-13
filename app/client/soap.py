"""Client SOAP minimal pentru portal.just.ro.

De ce client „de mână" și nu `zeep`:
  - Serviciul e HTTP simplu și avem nevoie de control fin (throttle/retry).
  - Evităm dependențe grele (lxml) care nu au mereu wheels pe Python nou.
  - Cererea CautareDosare e suficient de simplă încât un template + ElementTree
    din standard library acoperă tot.

Parsarea răspunsului e *namespace-agnostic*: comparăm doar local-name-ul tag-ului,
ca să nu depindem de prefixe/namespace-uri exacte.
"""

from __future__ import annotations

import time
from datetime import datetime
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape

import requests

from .models import Dosar, Parte, Sedinta

ENDPOINT = "http://portalquery.just.ro/query.asmx"
NS = "portalquery.just.ro"  # targetNamespace din WSDL (fără schemă, intenționat)
SOAP_ENV = "http://schemas.xmlsoap.org/soap/envelope/"
XSI = "http://www.w3.org/2001/XMLSchema-instance"


class PortalError(Exception):
    """Eroare la comunicarea cu web service-ul instanțelor."""


def _local(tag: str) -> str:
    """Întoarce local-name-ul unui tag (fără {namespace})."""
    return tag.rsplit("}", 1)[-1]


def _find(el: ET.Element, name: str) -> ET.Element | None:
    for child in el:
        if _local(child.tag) == name:
            return child
    return None


def _findall(el: ET.Element, name: str) -> list[ET.Element]:
    return [c for c in el if _local(c.tag) == name]


def _text(el: ET.Element | None, name: str, default: str = "") -> str:
    if el is None:
        return default
    child = _find(el, name)
    if child is None or child.text is None:
        return default
    return child.text.strip()


def _deep_find(el: ET.Element, name: str) -> ET.Element | None:
    """Caută recursiv primul element cu local-name dat (pentru a sări peste
    wrapper-ele SOAP Body/Response fără a depinde de namespace-uri)."""
    for child in el.iter():
        if _local(child.tag) == name:
            return child
    return None


class PortalClient:
    """Client pentru metodele CautareDosare / CautareSedinte.

    Parametri de politețe față de serviciul public:
      throttle  — secunde de pauză minimă între cereri
      retries   — reîncercări la erori tranzitorii (timeout / 5xx)
      timeout   — timeout per cerere
    """

    def __init__(
        self,
        *,
        timeout: float = 30.0,
        throttle: float = 1.0,
        retries: int = 3,
        session: requests.Session | None = None,
        user_agent: str = "PortalActiuniColective/0.1 (proiect informativ public)",
    ) -> None:
        self.timeout = timeout
        self.throttle = throttle
        self.retries = retries
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": user_agent})
        self._last_call: float = 0.0

    # ---- API public -----------------------------------------------------

    def cautare_dosare(
        self,
        *,
        numar: str | None = None,
        obiect: str | None = None,
        parte: str | None = None,
        institutie: str | None = None,
        data_start: datetime | None = None,
        data_stop: datetime | None = None,
    ) -> list[Dosar]:
        """Caută dosare. Cel puțin unul dintre numar/obiect/parte e obligatoriu.

        institutie/data_start/data_stop sunt nillable: lipsa lor = fără filtru.
        Atenție: serviciul întoarce maximum 1000 de dosare per cerere.
        """
        if not any((numar, obiect, parte)):
            raise PortalError(
                "CautareDosare cere cel puțin unul dintre: numar, obiect, parte."
            )
        body = self._build_cautare_dosare_body(
            numar, obiect, parte, institutie, data_start, data_stop
        )
        root = self._post("CautareDosare", body)
        result = _deep_find(root, "CautareDosareResult")
        if result is None:
            return []
        return [self._parse_dosar(d) for d in _findall(result, "Dosar")]

    # ---- intern ---------------------------------------------------------

    def _build_cautare_dosare_body(
        self,
        numar: str | None,
        obiect: str | None,
        parte: str | None,
        institutie: str | None,
        data_start: datetime | None,
        data_stop: datetime | None,
    ) -> str:
        def opt(tag: str, value: str | None) -> str:
            if value is None:
                return ""  # element optional: îl omitem complet
            return f"<{tag}>{escape(value)}</{tag}>"

        def nillable(tag: str, value: str | None) -> str:
            if value is None:
                return f'<{tag} xsi:nil="true" />'
            return f"<{tag}>{escape(value)}</{tag}>"

        def dt(tag: str, value: datetime | None) -> str:
            if value is None:
                return f'<{tag} xsi:nil="true" />'
            return f"<{tag}>{value.strftime('%Y-%m-%dT%H:%M:%S')}</{tag}>"

        return (
            f'<CautareDosare xmlns="{NS}">'
            f"{opt('numarDosar', numar)}"
            f"{opt('obiectDosar', obiect)}"
            f"{opt('numeParte', parte)}"
            f"{nillable('institutie', institutie)}"
            f"{dt('dataStart', data_start)}"
            f"{dt('dataStop', data_stop)}"
            f"</CautareDosare>"
        )

    def _post(self, action: str, body: str) -> ET.Element:
        envelope = (
            '<?xml version="1.0" encoding="utf-8"?>'
            f'<soap:Envelope xmlns:xsi="{XSI}" '
            'xmlns:xsd="http://www.w3.org/2001/XMLSchema" '
            f'xmlns:soap="{SOAP_ENV}">'
            f"<soap:Body>{body}</soap:Body>"
            "</soap:Envelope>"
        ).encode("utf-8")

        headers = {
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": f'"{NS}/{action}"',
        }

        last_exc: Exception | None = None
        for attempt in range(1, self.retries + 1):
            self._respect_throttle()
            try:
                resp = self.session.post(
                    ENDPOINT, data=envelope, headers=headers, timeout=self.timeout
                )
            except requests.RequestException as exc:
                last_exc = exc
                self._backoff(attempt)
                continue

            if resp.status_code >= 500:
                last_exc = PortalError(f"HTTP {resp.status_code} de la serviciu")
                self._backoff(attempt)
                continue
            if resp.status_code != 200:
                raise PortalError(
                    f"HTTP {resp.status_code}: {resp.text[:300]}"
                )

            try:
                root = ET.fromstring(resp.content)
            except ET.ParseError as exc:
                raise PortalError(f"Răspuns XML invalid: {exc}") from exc

            fault = _deep_find(root, "Fault")
            if fault is not None:
                raise PortalError(f"SOAP Fault: {_text(fault, 'faultstring')}")
            return root

        raise PortalError(
            f"Cererea {action} a eșuat după {self.retries} încercări"
        ) from last_exc

    def _respect_throttle(self) -> None:
        if self.throttle <= 0:
            return
        # time.monotonic e disponibil; evităm ceasul de perete pentru pauze.
        elapsed = time.monotonic() - self._last_call
        if elapsed < self.throttle:
            time.sleep(self.throttle - elapsed)
        self._last_call = time.monotonic()

    def _backoff(self, attempt: int) -> None:
        time.sleep(min(2 ** attempt, 30))

    # ---- parsare --------------------------------------------------------

    def _parse_dosar(self, el: ET.Element) -> Dosar:
        parti_el = _find(el, "parti")
        sedinte_el = _find(el, "sedinte")
        parti = (
            [self._parse_parte(p) for p in _findall(parti_el, "DosarParte")]
            if parti_el is not None
            else []
        )
        sedinte = (
            [self._parse_sedinta(s) for s in _findall(sedinte_el, "DosarSedinta")]
            if sedinte_el is not None
            else []
        )
        return Dosar(
            numar=_text(el, "numar"),
            numar_vechi=_text(el, "numarVechi"),
            data=_text(el, "data"),
            institutie=_text(el, "institutie"),
            departament=_text(el, "departament"),
            categorie=_text(el, "categorieCazNume"),
            stadiu=_text(el, "stadiuProcesualNume"),
            obiect=_text(el, "obiect"),
            data_modificare=_text(el, "dataModificare"),
            parti=parti,
            sedinte=sedinte,
        )

    @staticmethod
    def _parse_parte(el: ET.Element) -> Parte:
        return Parte(nume=_text(el, "nume"), calitate=_text(el, "calitateParte"))

    @staticmethod
    def _parse_sedinta(el: ET.Element) -> Sedinta:
        return Sedinta(
            data=_text(el, "data"),
            ora=_text(el, "ora"),
            solutie=_text(el, "solutie"),
            solutie_sumar=_text(el, "solutieSumar"),
            complet=_text(el, "complet"),
            numar_document=_text(el, "numarDocument"),
        )

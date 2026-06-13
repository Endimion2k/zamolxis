"""Orchestratorul scanării.

Strategia de interogare (ocolește limitele API-ului — vezi PLAN.md §7):
  • Motorul principal = iterarea ACTORILOR COLECTIVI pe `numeParte` (asociație/sindicat/
    autoritate ca parte = semnalul de acțiune colectivă).
  • Secundar = markeri expliciți de obiect („în reprezentare" etc.), pentru acțiuni
    L.414/2023 care nu sunt legate de un actor din registru.
  • ÎMPĂRȚIRE ADAPTIVĂ PE DATE pentru ORICE interogare: dacă atinge plafonul de 1000
    (trunchiere), o spargem recursiv la jumătate de interval până coboară sub plafon.
    Necesar pentru sindicate foarte active (mii de dosare).
  • Dedup global pe `numar`; upsert idempotent → re-rulările nu duplică.

Tot ce ține de rețea trece prin `PortalClient` (throttle + retry).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from app import registry
from app.classifier import clasifica
from app.client import Dosar, PortalClient, PortalError
from app.storage import init_db, log_scan, upsert_caz

PLAFON_API = 1000
MIN_FEREASTRA = timedelta(days=3)       # sub asta nu mai împărțim (evită recursie infinită)
DEFAULT_START = datetime(2005, 1, 1)    # ECRIS online ~ ultimii ~20 ani
# plafon de sub-interogări per actor/marker — protejează împotriva părților
# hiper-active (ex. sindicate, autorități) care ar exploda împărțirea adaptivă.
MAX_SUBINTEROGARI = 40


@dataclass
class ScanReport:
    interogari: int = 0
    aduse: int = 0          # total dosare returnate (cu duplicate)
    unice: int = 0          # dosare distincte (după numar)
    noi: int = 0
    actualizate: int = 0
    sarite: int = 0         # respinse (când doar_colective=True)
    trunchieri: list[str] = field(default_factory=list)
    erori: list[str] = field(default_factory=list)
    pe_domeniu: Counter = field(default_factory=Counter)

    def rezumat(self) -> str:
        linii = [
            f"interogări: {self.interogari}",
            f"aduse: {self.aduse} → unice: {self.unice}",
            f"stocate: {self.noi} noi, {self.actualizate} actualizate, "
            f"{self.sarite} sărite (respinse)",
            f"pe domeniu: {dict(self.pe_domeniu)}",
        ]
        if self.trunchieri:
            linii.append(f"⚠ trunchieri (1000): {len(self.trunchieri)} → {self.trunchieri[:5]}")
        if self.erori:
            linii.append(f"⚠ erori: {len(self.erori)} → {self.erori[:5]}")
        return "\n".join(linii)


def scaneaza(
    conn,
    client: PortalClient | None = None,
    *,
    doar_colective: bool = True,
    include_obiecte: bool = True,
    data_start: datetime | None = None,
    data_stop: datetime | None = None,
    on_progress=None,
    asociatii: list | None = None,
    obiecte_query: tuple | list | None = None,
    domenii: tuple | list | None = None,
) -> ScanReport:
    """Scanează registrul, clasifică rezultatele și le scrie în `conn`.

    data_start/data_stop: fereastra de căutare (delta). Implicit [2005 .. acum].
    domenii: ce domenii din registru să scaneze (implicit cele agreate, în scop).
    asociatii/obiecte_query: injectabile (pentru teste); altfel din registru.
    """
    init_db(conn)
    client = client or PortalClient()
    if asociatii is None:
        scop = tuple(domenii) if domenii is not None else registry.DOMENII_IN_SCOP
        asociatii = [a for a in registry.ASOCIATII if a["domeniu"] in scop]
    obiecte_query = registry.OBIECTE_QUERY if obiecte_query is None else obiecte_query
    start = data_start or DEFAULT_START
    stop = data_stop or datetime.now()

    raport = ScanReport()
    seen: set[str] = set()

    def progres(msg: str) -> None:
        if on_progress:
            on_progress(msg)

    def proceseaza(dosare: list[Dosar]) -> None:
        for d in dosare:
            raport.aduse += 1
            if not d.numar or d.numar in seen:
                continue
            seen.add(d.numar)
            raport.unice += 1
            clas = clasifica(d)
            if doar_colective and not clas.este_colectiv:
                raport.sarite += 1
                continue
            if upsert_caz(conn, d, clas):
                raport.noi += 1
            else:
                raport.actualizate += 1
            if clas.domeniu:
                raport.pe_domeniu[clas.domeniu] += 1

    # 1) Actori colectivi (numeParte) — motorul principal
    for a in asociatii:
        progres(f"parte: {a['query']}")
        _scan_adaptiv(client, "parte", a["query"], start, stop, conn, raport,
                      proceseaza, {"ramas": MAX_SUBINTEROGARI}, obiect=a.get("obiect"))

    # 2) Markeri expliciți de obiect — pentru acțiuni fără actor din registru
    if include_obiecte:
        for q in obiecte_query:
            progres(f"obiect: {q}")
            _scan_adaptiv(client, "obiect", q, start, stop, conn, raport,
                          proceseaza, {"ramas": MAX_SUBINTEROGARI})

    return raport


def _scan_adaptiv(
    client: PortalClient,
    kind: str,                # 'parte' | 'obiect'
    value: str,
    start: datetime,
    stop: datetime,
    conn,
    raport: ScanReport,
    proceseaza,
    buget: dict,              # {"ramas": N} — plafon de sub-interogări (mutabil)
    obiect: str | None = None,  # filtru opțional de obiect, când kind == 'parte'
) -> None:
    """O interogare într-o fereastră; dacă atinge plafonul, o sparge la jumătate.

    `buget` limitează numărul total de sub-interogări pentru un actor/marker, ca o
    parte hiper-activă să nu declanșeze sute de cereri.
    """
    eticheta_baza = f"{kind}={value}" + (f"+obiect={obiect}" if obiect else "")
    if buget["ramas"] <= 0:
        raport.trunchieri.append(f"{eticheta_baza} [buget epuizat la {start:%Y-%m-%d}]")
        return
    buget["ramas"] -= 1
    raport.interogari += 1

    kwargs: dict = {"data_start": start, "data_stop": stop}
    if kind == "parte":
        kwargs["parte"] = value
        if obiect:
            kwargs["obiect"] = obiect
    else:
        kwargs["obiect"] = value
    eticheta = f"{eticheta_baza} [{start:%Y-%m-%d}..{stop:%Y-%m-%d}]"

    try:
        dosare = client.cautare_dosare(**kwargs)
    except PortalError as exc:
        raport.erori.append(f"{eticheta}: {exc}")
        return

    if len(dosare) >= PLAFON_API and (stop - start) > MIN_FEREASTRA:
        mid = start + (stop - start) / 2
        _scan_adaptiv(client, kind, value, start, mid, conn, raport, proceseaza, buget, obiect)
        _scan_adaptiv(client, kind, value, mid, stop, conn, raport, proceseaza, buget, obiect)
        return

    trunchiat = len(dosare) >= PLAFON_API
    if trunchiat:
        raport.trunchieri.append(eticheta)
    log_scan(conn, kind, eticheta, len(dosare), trunchiat)
    proceseaza(dosare)

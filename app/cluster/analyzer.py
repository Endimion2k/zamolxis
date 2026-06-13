"""Analiza valurilor de litigii.

Pentru fiecare pârât de masă din registru: aduce dosarele (împărțire adaptivă pe date),
le grupează după (pârâtul specific + bucket-ul de obiect) și salvează grupurile care
depășesc pragul ca „valuri" de litigii identice.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime

from app import registry
from app.classifier import taxonomy as tx
from app.client import PortalClient, PortalError
from app.scanner.orchestrator import (
    DEFAULT_START,
    MAX_SUBINTEROGARI,
    MIN_FEREASTRA,
    PLAFON_API,
)
from app.storage import init_db, upsert_grup

from .bucket import bucket_obiect, domeniu_bucket

PRAG_GRUP = 25  # nr. minim de dosare distincte ca să considerăm un „val"

_LATURA_PARAT = ("parat", "intimat")


@dataclass
class GroupReport:
    parati_scanati: int = 0
    dosare_vazute: int = 0
    grupuri: int = 0
    grupuri_noi: int = 0
    trunchieri: list[str] = field(default_factory=list)
    erori: list[str] = field(default_factory=list)

    def rezumat(self) -> str:
        linii = [
            f"pârâți scanați: {self.parati_scanati}",
            f"dosare văzute: {self.dosare_vazute}",
            f"valuri (≥{PRAG_GRUP}): {self.grupuri} ({self.grupuri_noi} noi)",
        ]
        if self.trunchieri:
            linii.append(f"⚠ trunchieri: {len(self.trunchieri)} → {self.trunchieri[:5]}")
        if self.erori:
            linii.append(f"⚠ erori: {len(self.erori)} → {self.erori[:5]}")
        return "\n".join(linii)


def _colecteaza_adaptiv(client, filtru: dict, start, stop, buget):
    """Adună toate dosarele pentru un filtru ({'parte':..} sau {'obiect':..}),
    împărțind pe intervale de date la plafon. Întoarce (listă, trunchiat)."""
    if buget["ramas"] <= 0:
        return [], True
    buget["ramas"] -= 1
    try:
        dosare = client.cautare_dosare(**filtru, data_start=start, data_stop=stop)
    except PortalError:
        return [], False
    if len(dosare) >= PLAFON_API and (stop - start) > MIN_FEREASTRA:
        mid = start + (stop - start) / 2
        a, ta = _colecteaza_adaptiv(client, filtru, start, mid, buget)
        b, tb = _colecteaza_adaptiv(client, filtru, mid, stop, buget)
        return a + b, (ta or tb)
    return dosare, len(dosare) >= PLAFON_API


_RE_ADMIN = re.compile(
    r"administrator\s+(?:judiciar|special)\s+(?:al\s+)?(?:debitoa?rei\s+)?(.+)$", re.I
)


def _canon_parat(nume: str) -> str:
    """Reduce numele pârâtului la firma de bază, eliminând învelișul de insolvență.
    Consolidează variantele aceluiași debitor într-un singur val:
      „X prin administrator judiciar CITR..."          → X
      „CITR ... administrator judiciar al debitoarei X" → X
      „CITR ... administrator judiciar al X"            → X
    """
    n = nume.strip()
    # 1) „X prin administrator ..." → păstrăm doar X (debitorul e înainte)
    n = re.split(r"\bprin\s+administrator", n, flags=re.I)[0].strip(" -–")
    # 2) „<administrator> administrator judiciar/special [al] [debitoarei] X" → X
    m = _RE_ADMIN.search(n)
    if m and len(m.group(1).strip()) > 5:
        n = m.group(1)
    return n.strip(" -–") or nume.strip()


_RE_FORMA = re.compile(r"\b(s\s?c|s\s?r\s?l|s\s?a|sca|snc|ifn|s\s?r\s?l\s?d)\b")


def _canon_firma(nume: str) -> str:
    """Cheie de grupare pentru o firmă, robustă la forme juridice/insolvență:
    'SC NORDIS MANAGEMENT S.R.L.' și 'NORDIS MANAGEMENT SRL' → 'nordis management'."""
    n = tx.normalizeaza(_canon_parat(nume))
    n = _RE_FORMA.sub(" ", n)
    return re.sub(r"\s+", " ", n).strip()


def _entitati_parat(dosar) -> list[str]:
    """Părțile-pârât care sunt PERSOANE JURIDICE (firme/instituții), pe latura pârâtă.
    Persoanele fizice sunt ignorate (nu „descoperim" oameni dați în judecată)."""
    out = []
    for p in dosar.parti:
        calitate = tx.normalizeaza(p.calitate)
        if not any(l in calitate for l in _LATURA_PARAT):
            continue
        if p.nume and tx.este_entitate_nepersonala(p.nume):
            out.append(p.nume)
    return out


def descopera_valuri(
    conn,
    client: PortalClient | None = None,
    *,
    obiecte: list,
    prag: int = PRAG_GRUP,
    data_start: datetime | None = None,
    data_stop: datetime | None = None,
    on_progress=None,
) -> GroupReport:
    """DESCOPERIRE AUTOMATĂ: caută pe TIP DE OBIECT (problemă) și descoperă ce
    persoane juridice sunt acționate în masă — fără listă prealabilă de pârâți.

    `obiecte`: listă de {query, label, domeniu}. Pentru fiecare, grupăm dosarele
    după pârâtul-firmă canonicalizat și salvăm firmele peste prag.
    """
    init_db(conn)
    client = client or PortalClient()
    start = data_start or DEFAULT_START
    stop = data_stop or datetime.now()
    raport = GroupReport()

    def progres(msg):
        if on_progress:
            on_progress(msg)

    for ob in obiecte:
        progres(f"obiect: {ob['query']}")
        raport.parati_scanati += 1
        buget = {"ramas": MAX_SUBINTEROGARI}
        dosare, trunchiat = _colecteaza_adaptiv(client, {"obiect": ob["query"]}, start, stop, buget)
        if trunchiat:
            raport.trunchieri.append(ob["query"])

        # grupează după firma-pârât descoperită
        grupuri: dict[str, dict] = defaultdict(
            lambda: {"numere": set(), "display": Counter(), "instante": Counter(),
                     "exemple": {}, "data_min": None, "data_max": None}
        )
        for d in dosare:
            raport.dosare_vazute += 1
            if not d.numar:
                continue
            for parat in _entitati_parat(d):
                key = _canon_firma(parat)
                if len(key) < 4:
                    continue
                g = grupuri[key]
                if d.numar in g["numere"]:
                    continue
                g["numere"].add(d.numar)
                g["display"][_canon_parat(parat)] += 1
                g["instante"][d.institutie] += 1
                g["exemple"][d.numar] = {"numar": d.numar, "instanta": d.institutie, "data": d.data}
                zi = (d.data or "")[:10]
                if zi:
                    g["data_min"] = min(g["data_min"] or zi, zi)
                    g["data_max"] = max(g["data_max"] or zi, zi)

        for key, g in grupuri.items():
            n = len(g["numere"])
            if n < prag:
                continue
            display = g["display"].most_common(1)[0][0]
            exemple = sorted(g["exemple"].values(), key=lambda e: e["data"], reverse=True)[:5]
            raport.grupuri += 1
            if upsert_grup(
                conn, parat=display, parat_key=key, obiect_tip=ob["label"],
                domeniu=ob["domeniu"], nr_dosare=n, aprox=trunchiat,
                instante=dict(g["instante"]), exemple=exemple,
                prima_data=g["data_min"] or "", ultima_data=g["data_max"] or "",
            ):
                raport.grupuri_noi += 1

    return raport


def _gaseste_parat(dosar, query_n: str, variante_n: list[str]) -> str | None:
    """Numele specific al părții-pârât care corespunde interogării (sau None)."""
    for p in dosar.parti:
        calitate = tx.normalizeaza(p.calitate)
        if not any(l in calitate for l in _LATURA_PARAT):
            continue
        nume_n = tx.normalizeaza(p.nume)
        if query_n in nume_n or any(v in nume_n for v in variante_n):
            return p.nume
    return None


def scaneaza_grupuri(
    conn,
    client: PortalClient | None = None,
    *,
    parati: list | None = None,
    prag: int = PRAG_GRUP,
    data_start: datetime | None = None,
    data_stop: datetime | None = None,
    bucketuri: list | None = None,
    domenii: tuple | list | None = None,
    on_progress=None,
) -> GroupReport:
    init_db(conn)
    client = client or PortalClient()
    if parati is None:
        parati = registry.PARATI_MASA
        if domenii is not None:
            parati = [p for p in parati if p["domeniu"] in domenii]
    start = data_start or DEFAULT_START
    stop = data_stop or datetime.now()
    raport = GroupReport()

    def progres(msg):
        if on_progress:
            on_progress(msg)

    for pm in parati:
        progres(f"pârât: {pm['query']}")
        raport.parati_scanati += 1
        query_n = tx.normalizeaza(pm["query"])
        variante_n = [tx.normalizeaza(v) for v in pm.get("variante", [])]
        buget = {"ramas": MAX_SUBINTEROGARI}
        dosare, trunchiat = _colecteaza_adaptiv(client, {"parte": pm["query"]}, start, stop, buget)
        if trunchiat:
            raport.trunchieri.append(pm["query"])

        # grupează: (parat specific, bucket) → date agregate
        grupuri: dict[tuple[str, str], dict] = defaultdict(
            lambda: {"numere": set(), "instante": Counter(), "exemple": {},
                     "data_min": None, "data_max": None}
        )
        for d in dosare:
            raport.dosare_vazute += 1
            parat = _gaseste_parat(d, query_n, variante_n)
            if not parat or not d.numar:
                continue
            parat = _canon_parat(parat)
            bucket = bucket_obiect(d.obiect, bucketuri)
            g = grupuri[(parat, bucket)]
            if d.numar in g["numere"]:
                continue
            g["numere"].add(d.numar)
            g["instante"][d.institutie] += 1
            g["exemple"][d.numar] = {"numar": d.numar, "instanta": d.institutie, "data": d.data}
            zi = (d.data or "")[:10]
            if zi:
                g["data_min"] = min(g["data_min"] or zi, zi)
                g["data_max"] = max(g["data_max"] or zi, zi)

        # salvează valurile peste prag
        for (parat, bucket), g in grupuri.items():
            n = len(g["numere"])
            if n < prag:
                continue
            dom = domeniu_bucket(bucket, bucketuri) or pm["domeniu"]
            exemple = sorted(g["exemple"].values(), key=lambda e: e["data"], reverse=True)[:5]
            raport.grupuri += 1
            nou = upsert_grup(
                conn, parat=parat, parat_key=tx.normalizeaza(parat), obiect_tip=bucket,
                domeniu=dom, nr_dosare=n, aprox=trunchiat, instante=dict(g["instante"]),
                exemple=exemple, prima_data=g["data_min"] or "", ultima_data=g["data_max"] or "",
            )
            if nou:
                raport.grupuri_noi += 1

    return raport

"""Clasificator determinist „e acțiune colectivă relevantă?".

Filozofie (din constatarea Fazei 1): obiectul singur NU separă colectivul de individual.
Semnalul tare e în PĂRȚI — o asociație ca parte sau mulți reclamanți. Obiectul dă
domeniul și, uneori, un marker explicit; markerii de excludere resping direct.

Scor 0–100 → nivel:
  >= 70  confirmat   (afișabil cu încredere)
  40–69  revizuire   (candidat, necesită validare umană)
  <  40  respins     (probabil individual / irelevant)
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.client.models import Dosar, Parte

from . import taxonomy as tx

PRAG_CONFIRMAT = 70
PRAG_REVIZUIRE = 40


@dataclass(slots=True)
class Clasificare:
    scor: int
    nivel: str  # 'confirmat' | 'revizuire' | 'respins'
    domeniu: str | None  # 'bancar' | 'consumatori' | 'mediu' | None
    motive: list[str] = field(default_factory=list)
    rezumat: str = ""

    @property
    def este_colectiv(self) -> bool:
        return self.nivel != "respins"


# --- helpers pe părți --------------------------------------------------------

def _reclamanti_distincti(dosar: Dosar) -> list[Parte]:
    """Părți din latura reclamantă, deduplicate după nume normalizat."""
    vazute: set[str] = set()
    rezultat: list[Parte] = []
    for p in dosar.parti:
        calitate = tx.normalizeaza(p.calitate)
        if not any(c in calitate for c in tx.CALITATI_RECLAMANT):
            continue
        cheie = tx.normalizeaza(p.nume)
        if cheie and cheie not in vazute:
            vazute.add(cheie)
            rezultat.append(p)
    return rezultat


@dataclass(slots=True)
class _AnalizaAsociatii:
    reclamant_cunoscuta: list[Parte] = field(default_factory=list)
    reclamant_generica: list[Parte] = field(default_factory=list)
    alta_latura: list[Parte] = field(default_factory=list)  # asociație, dar nu reclamant


def _analiza_asociatii(dosar: Dosar) -> _AnalizaAsociatii:
    """Clasifică asociațiile-parte după latură: o asociație pe latura RECLAMANTĂ e
    semnalul de acțiune în reprezentare; o asociație PÂRÂTĂ înseamnă că ea e dată în
    judecată (nu reprezintă pe nimeni) — semnal slab."""
    a = _AnalizaAsociatii()
    for p in dosar.parti:
        nume_n = tx.normalizeaza(p.nume)
        if not nume_n:
            continue
        cunoscuta = any(k in nume_n for k in tx.ASOCIATII_CUNOSCUTE)
        generica = any(i in nume_n for i in tx.INDICII_ASOCIATIE) and not any(
            e in nume_n for e in tx.EXCEPTII_ASOCIATIE
        )
        if not (cunoscuta or generica):
            continue
        calitate = tx.normalizeaza(p.calitate)
        pe_reclamant = any(s in calitate for s in tx.CALITATI_LATURA_RECLAMANTA)
        if pe_reclamant and cunoscuta:
            a.reclamant_cunoscuta.append(p)
        elif pe_reclamant:
            a.reclamant_generica.append(p)
        else:
            a.alta_latura.append(p)
    return a


def _are_parat_persoana_juridica(dosar: Dosar) -> bool:
    for p in dosar.parti:
        if tx.RE_PERSOANA_JURIDICA.search(tx.normalizeaza(p.nume)):
            return True
    return False


# --- rezumat-șablon (fără LLM) ----------------------------------------------

_FRAZA_DOMENIU = {
    "bancar": "clauze considerate abuzive în contracte bancare",
    "consumatori": "protecția intereselor colective ale consumatorilor",
    "mediu": "protecția mediului",
    "munca": "drepturile colective ale salariaților",
    "sanatate": "drepturile pacienților",
    "alt": "interese colective",
}


def _construieste_rezumat(
    dosar: Dosar,
    domeniu: str | None,
    actor: Parte | None,
    nr_reclamanti: int,
) -> str:
    miza = _FRAZA_DOMENIU.get(domeniu or "", "interese colective")
    actor_nume = tx.normalizeaza(actor.nume) if actor is not None else ""
    parati = [
        p.nume
        for p in dosar.parti
        if ("parat" in tx.normalizeaza(p.calitate) or "intimat" in tx.normalizeaza(p.calitate))
        and tx.normalizeaza(p.nume) != actor_nume  # nu pârâm actorul însuși
    ]
    # anonimizăm pârâtul în rezumat dacă e persoană fizică (GDPR)
    tinta = tx.nume_public(parati[0]) if parati else "un comerciant"
    if actor is not None:
        return f"{actor.nume} a acționat în instanță {tinta}, vizând {miza}."
    if nr_reclamanti >= 2:
        return (
            f"{nr_reclamanti} reclamanți contestă împreună, în fața instanței, "
            f"chestiuni privind {miza} (pârât: {tinta})."
        )
    return f"Dosar privind {miza}."


# --- clasificare -------------------------------------------------------------

def clasifica(dosar: Dosar) -> Clasificare:
    obiect_n = tx.normalizeaza(dosar.obiect)
    text = f"{obiect_n} {tx.normalizeaza(dosar.categorie)}"

    # 1. excludere directă (familial / personal / administrativ)
    for kw in tx.MARKERI_EXCLUDERE:
        if kw in obiect_n:
            return Clasificare(
                scor=0,
                nivel="respins",
                domeniu=None,
                motive=[f"obiect individual/administrativ: „{kw}”"],
                rezumat="",
            )

    domeniu = tx.detecteaza_domeniu(text)
    asoc = _analiza_asociatii(dosar)
    reclamanti = _reclamanti_distincti(dosar)
    n = len(reclamanti)
    actor: Parte | None = None

    scor = 0
    motive: list[str] = []

    # 2. marker explicit de acțiune în reprezentare / colectivă (semnal tare)
    if any(m in obiect_n for m in tx.MARKERI_COLECTIV):
        scor += 45
        motive.append("obiectul indică explicit o acțiune în reprezentare/colectivă")

    # 3. asociație ca parte — contează LATURA (reclamant = semnal tare)
    if asoc.reclamant_cunoscuta:
        actor = asoc.reclamant_cunoscuta[0]
        scor += 50
        motive.append(f"reclamant = asociație din lista albă ({actor.nume})")
    elif asoc.reclamant_generica:
        actor = asoc.reclamant_generica[0]
        scor += 35
        motive.append(f"reclamant pare organizație colectivă ({actor.nume})")
    elif asoc.alta_latura:
        scor += 5
        motive.append(
            f"asociație implicată, dar nu ca reclamant ({asoc.alta_latura[0].nume})"
        )

    # 4. număr de reclamanți (acțiune de masă)
    if n >= 20:
        scor += 55
        motive.append(f"{n} reclamanți — acțiune de masă")
    elif n >= 10:
        scor += 40
        motive.append(f"{n} reclamanți")
    elif n >= 5:
        scor += 25
        motive.append(f"{n} reclamanți")
    elif n >= 3:
        scor += 10
        motive.append(f"{n} reclamanți")

    # 5. domeniu relevant (slab — doar candidat)
    if domeniu:
        scor += 15
        motive.append(f"domeniu relevant: {domeniu}")

    # 6. pârât persoană juridică (suport)
    if _are_parat_persoana_juridica(dosar):
        scor += 5
        motive.append("pârât persoană juridică (comerciant)")

    # domeniu de etichetare: dacă obiectul nu l-a dat, îl deducem din asociația
    # reclamantă (doar pentru filtrare/afișare, NU afectează scorul)
    if domeniu is None and actor is not None:
        dedus = tx.domeniu_din_asociatie(actor.nume)
        if dedus:
            domeniu = dedus
            motive.append(f"domeniu dedus din asociație: {dedus}")

    scor = max(0, min(100, scor))
    if scor >= PRAG_CONFIRMAT:
        nivel = "confirmat"
    elif scor >= PRAG_REVIZUIRE:
        nivel = "revizuire"
    else:
        nivel = "respins"

    rezumat = (
        _construieste_rezumat(dosar, domeniu, actor, n)
        if nivel != "respins"
        else ""
    )

    return Clasificare(
        scor=scor, nivel=nivel, domeniu=domeniu, motive=motive, rezumat=rezumat
    )

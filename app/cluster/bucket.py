"""Normalizarea obiectului unui dosar într-un „bucket" (tip canonic).

Scop: să grupăm mii de variante de formulare („contestaţie decizie de pensionare",
„CONTESTATIE DECIZIE PENSIONARE - recalculare") sub aceeași etichetă, ca să putem
număra valuri de dosare identice.
"""

from __future__ import annotations

import re

from app import registry
from app.classifier.taxonomy import normalizeaza

# zgomot tipic de la coada obiectului (numere de dosar, contracte, date, disjungeri)
_NOISE = re.compile(
    r"\b(disjuns din|contract.*|nr\s*\d.*|din dosar.*|\d{1,2}\s\d{1,2}\s\d{2,4}.*)"
)


def bucket_obiect(obiect: str, bucketuri: list | None = None) -> str:
    """Întoarce eticheta canonică a obiectului, sau un fallback din primele cuvinte."""
    bucketuri = registry.BUCKETE_OBIECT if bucketuri is None else bucketuri
    n = normalizeaza(obiect)
    if not n:
        return "(neprecizat)"
    for b in bucketuri:
        if any(cheie in n for cheie in b["chei"]):
            return b["label"]
    # fallback: curățăm zgomotul și păstrăm primele ~5 cuvinte semnificative
    curat = _NOISE.sub("", n).strip()
    cuvinte = [w for w in curat.split() if len(w) > 2][:5]
    return " ".join(cuvinte).capitalize() if cuvinte else "(neprecizat)"


def domeniu_bucket(label: str, bucketuri: list | None = None) -> str | None:
    bucketuri = registry.BUCKETE_OBIECT if bucketuri is None else bucketuri
    for b in bucketuri:
        if b["label"] == label:
            return b["domeniu"]
    return None

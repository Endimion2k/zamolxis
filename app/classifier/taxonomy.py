"""Taxonomie și liste de referință pentru clasificator.

Toate comparațiile se fac pe text NORMALIZAT (vezi `normalizeaza`): minuscule, fără
diacritice, spații colapsate. ECRIS folosește diacritice cu sedilă (ş=\\u015f, ţ=\\u0163)
și uneori cu virgulă (ș=\\u0219); normalizarea le tratează la fel.
"""

from __future__ import annotations

import re
import unicodedata

from app import registry as _reg


def normalizeaza(text: str | None) -> str:
    """minuscule + fără diacritice + spații/punctuație colapsate la spațiu."""
    if not text:
        return ""
    # NFKD descompune ş/ș/ţ/ț/ă/â/î în literă de bază + semn → eliminăm semnele
    desc = unicodedata.normalize("NFKD", text)
    fara_diac = "".join(c for c in desc if not unicodedata.combining(c))
    fara_diac = fara_diac.lower()
    # orice nu e literă/cifră devine spațiu, ca să facem match pe cuvinte întregi ușor
    return re.sub(r"[^a-z0-9]+", " ", fara_diac).strip()


# --- Taxonomia de obiecte (derivată din registru, NORMALIZATĂ la încărcare) --
# Normalizăm cheile cu aceeași funcție ca textul comparat → match consistent,
# imun la diacritice/punctuație din registru.
DOMENII: dict[str, tuple[str, ...]] = {
    dom: tuple(normalizeaza(k) for k in chei)
    for dom, chei in _reg.DOMENII_OBIECTE.items()
}

# Markeri EXPLICIȚI de acțiune colectivă/în reprezentare (semnal tare)
MARKERI_COLECTIV: tuple[str, ...] = tuple(normalizeaza(m) for m in _reg.MARKERI_COLECTIV)

# Markeri de EXCLUDERE (litigiu pur individual/familial/administrativ → respins direct)
MARKERI_EXCLUDERE: tuple[str, ...] = tuple(normalizeaza(m) for m in _reg.MARKERI_EXCLUDERE)

# --- Calități de parte: latura reclamantă -----------------------------------
# Stricte (pentru numărarea reclamanților la fond):
CALITATI_RECLAMANT: tuple[str, ...] = (
    "reclamant",
    "petent",
    "contestator",
    "petenta",
)
# Lărgite (pentru a stabili dacă o asociație e pe latura care acuză, inclusiv în căi
# de atac — apelant/recurent sunt de regulă tot inițiatorul acțiunii):
CALITATI_LATURA_RECLAMANTA: tuple[str, ...] = CALITATI_RECLAMANT + (
    "apelant",
    "recurent",
    "revizuent",
    "reclamanta",
)

# --- Listă albă de asociații (derivată din registru) -------------------------
# match prin substring pe numele normalizat al părții. Sursa: app.registry.ASOCIATII.
ASOCIATII_CUNOSCUTE: tuple[str, ...] = tuple(
    sorted(
        {
            n
            for a in _reg.ASOCIATII
            for v in (*a["variante"], a["query"])
            if (n := normalizeaza(v))
        }
    )
)

# Domeniul tipic al unei asociații cunoscute — etichetă când obiectul nu conține
# cuvinte-cheie de domeniu (ex. ONG-uri de mediu care atacă acte administrative).
ASOCIATII_DOMENIU: dict[str, str] = {
    n: a["domeniu"]
    for a in _reg.ASOCIATII
    for v in (*a["variante"], a["query"])
    if (n := normalizeaza(v))
}


def domeniu_din_asociatie(nume: str) -> str | None:
    n = normalizeaza(nume)
    for cheie, dom in ASOCIATII_DOMENIU.items():
        if cheie in n:
            return dom
    return None


# Indicii generice că o parte e o organizație colectivă (chiar dacă nu e în listă)
INDICII_ASOCIATIE: tuple[str, ...] = (
    "asociatia",
    "asociatie",
    "federatia",
    "confederatia",
    "uniunea",
    "sindicatul",
    "sindicatele",
    "coalitia",
    "liga ",
    "fundatia",
    "organizatia",
)

# Excepție: „asociația de proprietari" generică NU e actor colectiv în sensul nostru
# (generează mii de dosare de recuperare cote întreținere — vezi notele cercetării).
# Federația (FAPR) rămâne relevantă, fiind prinsă de lista albă.
EXCEPTII_ASOCIATIE: tuple[str, ...] = ("proprietar",)

# Indicii că pârâtul e persoană juridică (comerciant) — suport pentru ipoteza colectivă
RE_PERSOANA_JURIDICA = re.compile(r"\b(sa|srl|sca|snc|ifn|bank|banca|srl d)\b")

# Detecție lărgită de persoană juridică / entitate publică — pentru AFIȘARE.
# Persoanele juridice se arată integral; persoanele fizice se anonimizează (GDPR).
# Formele de societate sunt tolerante la puncte/spații, fiindcă normalizarea
# transformă „S.R.L." → „s r l" (separat). Altfel ratam firmele scrise cu puncte.
RE_ENTITATE_NEPERSONALA = re.compile(
    r"\b(s\s?c|s\s?a|s\s?r\s?l|s\s?c\s?a|s\s?n\s?c|ifn|bank|banca|institut|primaria|"
    r"primarie|guvern|guvernul|minister|ministerul|agentia|autoritatea|patronat|"
    r"patronatul|federatia|uniunea|fundatia|asociatia|asociatie|consiliul|directia|"
    r"inspectoratul|spitalul|universitatea|comuna|orasul|municipiul|judetul|"
    r"prefectura|regia|compania|societatea|scoala|colegiul|casa|cnas|anaf|anpc|cec)\b"
)

_CUVINTE_STOP_NUME = {"domiciliul", "domiciliu", "prin", "ales", "la", "cu", "si", "mandatar"}


def este_entitate_nepersonala(nume: str, este_asociatie: bool = False) -> bool:
    if este_asociatie:
        return True
    return bool(RE_ENTITATE_NEPERSONALA.search(normalizeaza(nume)))


def nume_public(nume: str, este_asociatie: bool = False) -> str:
    """Numele de afișat public. Persoană juridică/publică → integral; persoană fizică
    → inițiale (protecția datelor, vezi PLAN.md §8)."""
    if not nume:
        return "—"
    nume = nume.strip()
    if este_entitate_nepersonala(nume, bool(este_asociatie)):
        return nume
    initiale: list[str] = []
    for w in re.split(r"[\s,]+", nume):
        if w.lower() in _CUVINTE_STOP_NUME:
            break
        if w and w[0].isalpha():
            initiale.append(w[0].upper() + ".")
        if len(initiale) >= 3:
            break
    return " ".join(initiale) if initiale else "—"


def detecteaza_domeniu(text_normalizat: str) -> str | None:
    """Întoarce primul domeniu ale cărui cuvinte-cheie apar în text, sau None.

    Ordine: bancar > consumatori > mediu (bancar e mai specific decât consumatori
    pentru „clauze abuzive")."""
    for domeniu, cuvinte in DOMENII.items():
        if any(kw in text_normalizat for kw in cuvinte):
            return domeniu
    return None

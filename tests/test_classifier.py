"""Teste pentru clasificatorul determinist.

Fixturile reproduc cazuri REALE văzute pe portal.just.ro (Faza 1), plus cazuri
sintetice de margine. Cheia: cazurile individuale (cuplu vs. bancă) trebuie RESPINSE,
iar cazurile cu asociație / mulți reclamanți trebuie ridicate.
"""

from __future__ import annotations

from app.classifier import clasifica
from app.client.models import Dosar, Parte


def _dosar(obiect: str, parti: list[Parte], *, categorie: str = "", stadiu: str = "Fond") -> Dosar:
    return Dosar(
        numar="0/0/2024",
        numar_vechi="",
        data="2024-01-01T00:00:00",
        institutie="TribunalulBUCURESTI",
        departament="",
        categorie=categorie,
        stadiu=stadiu,
        obiect=obiect,
        data_modificare="2024-01-01T00:00:00",
        parti=parti,
    )


# --- cazuri REALE care trebuie RESPINSE (individuale) ------------------------

def test_cuplu_vs_banca_e_respins():
    """Caz real (10905/300/2019): 2 soți vs. FIRST BANK — individual, nu colectiv."""
    d = _dosar(
        "acţiune în constatare clauze abuzive, oblig. de a face, pretenţii - contract de credit",
        [
            Parte("KONRAD CAROL BOGDAN", "Reclamant"),
            Parte("KONRAD ANDREEA", "Reclamant"),
            Parte("FIRST BANK SA", "Pârât"),
        ],
        categorie="Litigii cu profesioniştii",
    )
    r = clasifica(d)
    assert r.nivel == "respins", r
    assert r.domeniu == "bancar"  # domeniul tot îl detectăm, dar scorul e mic


def test_un_reclamant_vs_banca_e_respins():
    d = _dosar(
        "acţiune în constatare clauze abuzive",
        [Parte("ENE MARIUS", "Reclamant"), Parte("BANCA TRANSILVANIA", "Pârât")],
        categorie="Litigii cu profesioniştii",
    )
    assert clasifica(d).nivel == "respins"


# --- cazuri care trebuie EXCLUSE direct -------------------------------------

def test_divort_e_respins():
    d = _dosar("divorţ cu minori", [Parte("X", "Reclamant"), Parte("Y", "Pârât")])
    r = clasifica(d)
    assert r.nivel == "respins"
    assert r.scor == 0


def test_caz_administrativ_asociatie_e_respins():
    """Caz real (1781/302/2024): AURSF își modifică actele constitutive — nu e acțiune."""
    d = _dosar(
        "modificări acte constitutive persoane juridice OG nr.26/2000 - asociaţie",
        [Parte("ASOCIAŢIA UTILIZATORILOR ROMÂNI DE SERVICII FINANCIARE", "Petent")],
        categorie="Civil",
    )
    r = clasifica(d)
    assert r.nivel == "respins", r  # excludere chiar dacă e o asociație cunoscută


# --- cazuri care trebuie CONFIRMATE / ridicate ------------------------------

def test_asociatie_in_reprezentare_e_confirmat():
    d = _dosar(
        "acţiune în reprezentare pentru protecţia intereselor colective ale consumatorilor",
        [
            Parte("ASOCIAŢIA PRO CONSUMATORI (APC)", "Reclamant"),
            Parte("VODAFONE ROMANIA SA", "Pârât"),
        ],
        categorie="Litigii cu profesioniştii",
    )
    r = clasifica(d)
    assert r.nivel == "confirmat", r
    assert r.domeniu in ("consumatori", "bancar")
    assert r.rezumat  # rezumat generat


def test_asociatie_necunoscuta_dar_in_reprezentare_e_ridicat():
    d = _dosar(
        "acţiune în reprezentare - interese colective ale consumatorilor",
        [
            Parte("ASOCIAŢIA CONSUMATORILOR DIN ARDEAL", "Reclamant"),
            Parte("ENGIE ROMANIA SA", "Pârât"),
        ],
    )
    r = clasifica(d)
    assert r.este_colectiv  # cel puțin revizuire
    assert r.scor >= 70  # marker explicit (45) + indiciu asociație (35) > 70 → confirmat


def test_actiune_de_masa_multi_reclamanti():
    parti = [Parte(f"RECLAMANT {i}", "Reclamant") for i in range(25)]
    parti.append(Parte("BANCA X SA", "Pârât"))
    d = _dosar("acţiune privind clauze abuzive contract de credit", parti)
    r = clasifica(d)
    # 25 reclamanți (55) + bancar (15) + pârât PJ (5) = 75 → confirmat
    assert r.nivel == "confirmat", r


def test_mediu_cu_ong():
    d = _dosar(
        "obligaţia de a face - protecţia mediului, poluare",
        [Parte("ASOCIAŢIA AGENT GREEN", "Reclamant"), Parte("COMPLEXUL ENERGETIC SA", "Pârât")],
    )
    r = clasifica(d)
    assert r.domeniu == "mediu"
    assert r.este_colectiv


# --- comportament de scor ----------------------------------------------------

def test_nivel_creste_cu_semnalele():
    individual = clasifica(
        _dosar("clauze abuzive", [Parte("A", "Reclamant"), Parte("BANCA SA", "Pârât")])
    )
    colectiv = clasifica(
        _dosar(
            "acţiune în reprezentare interese colective",
            [Parte("ASOCIAŢIA PRO CONSUMATORI", "Reclamant"), Parte("BANCA SA", "Pârât")],
        )
    )
    assert colectiv.scor > individual.scor

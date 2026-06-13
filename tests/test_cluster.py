"""Teste pentru detectarea valurilor de litigii (clustering)."""

from __future__ import annotations

import pytest

from app.client.models import Dosar, Parte
from app.cluster import bucket_obiect, descopera_valuri, scaneaza_grupuri
from app.cluster.analyzer import _canon_firma, _canon_parat
from app.storage import conecteaza, get_grup, init_db, list_grupuri, statistici


def test_canon_parat_consolideaza_insolventa():
    base = "NORDIS MANAGEMENT SRL"
    assert _canon_parat(base) == base
    assert _canon_parat("CITR FILIALA BUCURESTI SPRL - ADMINISTRATOR JUDICIAR AL DEBITOAREI NORDIS MANAGEMENT SRL") == base
    assert _canon_parat("CITR FILIALA BUCURESTI SPRL ADMINISTRATOR JUDICIAR AL NORDIS MANAGEMENT SRL") == base
    assert _canon_parat("NORDIS MANAGEMENT SRL PRIN ADMINISTRATOR JUDICIAR CITR FILIALA BUCURESTI") == base


def _dosar(numar, parat, obiect, parat_calitate="Pârât"):
    return Dosar(
        numar=numar, numar_vechi="", data="2025-01-10T00:00:00", institutie="TribunalulCONSTANTA",
        departament="", categorie="", stadiu="Fond", obiect=obiect,
        data_modificare="2025-01-10T00:00:00",
        parti=[Parte(f"RECLAMANT {numar}", "Reclamant"), Parte(parat, parat_calitate)],
    )


class FakeClient:
    def __init__(self, dosare):
        self.dosare = dosare

    def cautare_dosare(self, *, numar=None, obiect=None, parte=None,
                       institutie=None, data_start=None, data_stop=None):
        return list(self.dosare)


@pytest.fixture()
def conn():
    c = conecteaza(":memory:")
    init_db(c)
    yield c
    c.close()


# --- bucketing ---------------------------------------------------------------

def test_bucket_canonic():
    assert bucket_obiect("contestaţie decizie de pensionare") == "Contestație decizie de pensionare"
    assert bucket_obiect("RECALCULARE PENSIE militară") == "Recalculare pensie"
    assert bucket_obiect("anulare decizie de impunere") == "Contestație decizie de impunere / act fiscal"


def test_bucket_imobiliare_nordis():
    # tiparul real Nordis: rezoluțiune + hotărâre care ține loc de act
    assert bucket_obiect("rezoluţiune contract") == "Rezoluțiune / desființare contract"
    assert bucket_obiect("hotarâre care să țină loc de act autentic") == \
        "Hotărâre care ține loc de act (predare imobil)"


def test_bucket_fallback():
    # obiect necunoscut → fallback pe primele cuvinte (nu crapă)
    b = bucket_obiect("ceva obiect cu totul neobisnuit aici")
    assert b and b != "(neprecizat)"


# --- agregare valuri ---------------------------------------------------------

PARAT = "CASA JUDETEANA DE PENSII CONSTANTA"
_PM = [{"nume_oficial": "Case de Pensii", "query": "Casa Judeteana de Pensii",
        "variante": ["casa judeteana de pensii"], "domeniu": "pensii"}]


def test_val_peste_prag_se_salveaza(conn):
    dosare = [_dosar(f"{i}/118/2025", PARAT, "contestaţie decizie de pensionare") for i in range(4)]
    raport = scaneaza_grupuri(conn, FakeClient(dosare), parati=_PM, prag=3)
    assert raport.grupuri == 1
    g = list_grupuri(conn)
    assert len(g) == 1
    assert g[0]["nr_dosare"] == 4
    assert g[0]["obiect_tip"] == "Contestație decizie de pensionare"
    assert g[0]["domeniu"] == "pensii"


def test_sub_prag_nu_se_salveaza(conn):
    dosare = [_dosar(f"{i}/118/2025", PARAT, "contestaţie decizie de pensionare") for i in range(2)]
    raport = scaneaza_grupuri(conn, FakeClient(dosare), parati=_PM, prag=3)
    assert raport.grupuri == 0
    assert statistici(conn)["grupuri"] == 0


def test_paratul_ca_reclamant_e_ignorat(conn):
    # dacă instituția e RECLAMANT (nu pârât), nu e un val de oameni care o dau în judecată
    dosare = [_dosar(f"{i}/118/2025", PARAT, "contestaţie decizie de pensionare",
                     parat_calitate="Reclamant") for i in range(5)]
    raport = scaneaza_grupuri(conn, FakeClient(dosare), parati=_PM, prag=3)
    assert raport.grupuri == 0


def test_grupare_separata_pe_obiect(conn):
    dosare = (
        [_dosar(f"p{i}/118/2025", PARAT, "contestaţie decizie de pensionare") for i in range(3)]
        + [_dosar(f"r{i}/118/2025", PARAT, "recalculare pensie") for i in range(3)]
    )
    scaneaza_grupuri(conn, FakeClient(dosare), parati=_PM, prag=3)
    tipuri = {g["obiect_tip"] for g in list_grupuri(conn)}
    assert tipuri == {"Contestație decizie de pensionare", "Recalculare pensie"}


# --- descoperire automată -----------------------------------------------------

def test_canon_firma_consolideaza_forme_juridice():
    assert _canon_firma("SC NORDIS MANAGEMENT S.R.L.") == "nordis management"
    assert _canon_firma("NORDIS MANAGEMENT SRL") == "nordis management"
    assert _canon_firma("Engie Romania SA") == "engie romania"


def _dosar_dev(numar, dev, obiect="rezolutiune contract"):
    return Dosar(
        numar=numar, numar_vechi="", data="2024-01-10T00:00:00", institutie="TribunalulBUCURESTI",
        departament="", categorie="", stadiu="Fond", obiect=obiect,
        data_modificare="2024-01-10T00:00:00",
        parti=[Parte(f"CUMPARATOR {numar}", "Reclamant"), Parte(dev, "Pârât")],
    )


def test_descopera_firma_necunoscuta(conn):
    # un dezvoltator pe care NU îl avem în registru, în multe dosare → descoperit
    dosare = (
        [_dosar_dev(f"{i}/3/2024", "ALFA DEVELOPMENT SRL") for i in range(6)]
        + [_dosar_dev(f"x{i}/3/2024", "SC ALFA DEVELOPMENT S.R.L.") for i in range(4)]  # variantă
    )
    obiecte = [{"query": "rezolutiune", "label": "Rezoluțiune", "domeniu": "imobiliare"}]
    raport = descopera_valuri(conn, FakeClient(dosare), obiecte=obiecte, prag=8)
    g = list_grupuri(conn)
    assert len(g) == 1                      # cele două variante de nume → un singur val
    assert g[0]["nr_dosare"] == 10
    assert "ALFA DEVELOPMENT" in g[0]["parat"].upper()
    assert g[0]["domeniu"] == "imobiliare"


def test_descoperirea_ignora_persoanele_fizice(conn):
    # pârât persoană fizică → NU se descoperă (doar persoane juridice)
    dosare = [_dosar_dev(f"{i}/3/2024", "POPESCU ION") for i in range(10)]
    obiecte = [{"query": "rezolutiune", "label": "Rezoluțiune", "domeniu": "imobiliare"}]
    raport = descopera_valuri(conn, FakeClient(dosare), obiecte=obiecte, prag=5)
    assert raport.grupuri == 0


def test_detaliu_grup_cu_exemple(conn):
    dosare = [_dosar(f"{i}/118/2025", PARAT, "contestaţie decizie de pensionare") for i in range(5)]
    scaneaza_grupuri(conn, FakeClient(dosare), parati=_PM, prag=3)
    gid = list_grupuri(conn)[0]["id"]
    detaliu = get_grup(conn, gid)
    assert detaliu["parat"] == PARAT
    assert len(detaliu["exemple"]) == 5
    assert detaliu["instante"].get("TribunalulCONSTANTA") == 5

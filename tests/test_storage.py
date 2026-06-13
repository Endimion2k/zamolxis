"""Teste pentru stratul de stocare (SQLite în memorie)."""

from __future__ import annotations

import pytest

from app.classifier import clasifica
from app.client.models import Dosar, Parte, Sedinta
from app.storage import (
    conecteaza,
    get_caz,
    init_db,
    list_cazuri,
    statistici,
    upsert_caz,
)


@pytest.fixture()
def conn():
    c = conecteaza(":memory:")
    init_db(c)
    yield c
    c.close()


def _dosar_colectiv(numar: str = "100/3/2024") -> Dosar:
    return Dosar(
        numar=numar, numar_vechi="", data="2024-01-01T00:00:00",
        institutie="TribunalulBUCURESTI", departament="", categorie="Litigii",
        stadiu="Fond",
        obiect="acţiune în reprezentare interese colective ale consumatorilor",
        data_modificare="2024-02-01T00:00:00",
        parti=[
            Parte("ASOCIAŢIA PRO CONSUMATORI", "Reclamant"),
            Parte("VODAFONE ROMANIA SA", "Pârât"),
        ],
        sedinte=[Sedinta("2024-03-01T00:00:00", "09:00", "Amânat", "", "C1", "")],
    )


def test_upsert_si_dedup(conn):
    d = _dosar_colectiv()
    c = clasifica(d)
    assert upsert_caz(conn, d, c) is True   # nou
    assert upsert_caz(conn, d, c) is False  # același număr → update, nu duplicat
    total = conn.execute("SELECT COUNT(*) n FROM caz").fetchone()["n"]
    assert total == 1


def test_prima_data_vazut_se_pastreaza(conn):
    d = _dosar_colectiv()
    c = clasifica(d)
    upsert_caz(conn, d, c)
    prima = conn.execute("SELECT prima_data_vazut FROM caz").fetchone()[0]
    # a doua oară: stadiul se schimbă, dar prima_data_vazut rămâne
    d.stadiu = "Apel"
    upsert_caz(conn, d, c)
    row = conn.execute("SELECT prima_data_vazut, stadiu FROM caz").fetchone()
    assert row["prima_data_vazut"] == prima
    assert row["stadiu"] == "Apel"


def test_partile_se_rescriu_nu_se_acumuleaza(conn):
    d = _dosar_colectiv()
    c = clasifica(d)
    upsert_caz(conn, d, c)
    upsert_caz(conn, d, c)
    n_parti = conn.execute("SELECT COUNT(*) n FROM parte").fetchone()["n"]
    assert n_parti == 2  # nu 4


def test_list_si_filtre(conn):
    d = _dosar_colectiv()
    upsert_caz(conn, d, clasifica(d))
    # un dosar individual (respins) nu trebuie să apară în lista colectivelor
    ind = Dosar(
        numar="200/3/2024", numar_vechi="", data="2024-01-01T00:00:00",
        institutie="TribunalulBUCURESTI", departament="", categorie="Litigii",
        stadiu="Fond", obiect="clauze abuzive", data_modificare="2024-01-01T00:00:00",
        parti=[Parte("POPESCU ION", "Reclamant"), Parte("BANCA SA", "Pârât")],
    )
    upsert_caz(conn, ind, clasifica(ind))

    colective = list_cazuri(conn)  # doar_colective=True implicit
    numere = {c["numar"] for c in colective}
    assert "100/3/2024" in numere
    assert "200/3/2024" not in numere

    assert list_cazuri(conn, domeniu="consumatori")
    assert not list_cazuri(conn, domeniu="mediu")
    assert list_cazuri(conn, cauta="reprezentare")


def test_get_caz_cu_detalii(conn):
    d = _dosar_colectiv()
    upsert_caz(conn, d, clasifica(d))
    caz = get_caz(conn, "100/3/2024")
    assert caz is not None
    assert len(caz["parti"]) == 2
    assert len(caz["termene"]) == 1
    assert any(p["este_asociatie"] for p in caz["parti"])
    assert isinstance(caz["motive"], list)
    assert get_caz(conn, "inexistent") is None


def test_statistici(conn):
    d = _dosar_colectiv()
    upsert_caz(conn, d, clasifica(d))
    s = statistici(conn)
    assert s["total"] == 1
    assert sum(s["pe_nivel"].values()) == 1

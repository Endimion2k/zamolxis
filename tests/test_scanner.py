"""Teste pentru orchestratorul scanării — cu client fals (fără rețea).

Acoperă: dedup global, filtrarea respinselor, și împărțirea adaptivă pe date la
atingerea plafonului de 1000.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from app.client.models import Dosar, Parte
from app.scanner import scaneaza
from app.scanner.orchestrator import MAX_SUBINTEROGARI
from app.storage import conecteaza, init_db, statistici


class FakeClient:
    def __init__(self, responder):
        self.responder = responder
        self.calls: list[dict] = []

    def cautare_dosare(self, *, numar=None, obiect=None, parte=None,
                       institutie=None, data_start=None, data_stop=None):
        self.calls.append({"parte": parte, "obiect": obiect,
                           "start": data_start, "stop": data_stop})
        return self.responder(parte, obiect, data_start, data_stop)


def _asoc(query, domeniu="consumatori"):
    return {"nume_oficial": query, "query": query, "variante": [query.lower()],
            "domeniu": domeniu}


def _colectiv(numar):
    return Dosar(
        numar=numar, numar_vechi="", data="2020-01-01T00:00:00", institutie="X",
        departament="", categorie="", stadiu="Fond",
        obiect="acţiune în reprezentare interese colective ale consumatorilor",
        data_modificare="2020-01-01T00:00:00",
        parti=[Parte("ASOCIAŢIA PRO CONSUMATORI", "Reclamant"),
               Parte("VODAFONE SA", "Pârât")],
    )


def _individual(numar):
    return Dosar(
        numar=numar, numar_vechi="", data="2020-01-01T00:00:00", institutie="X",
        departament="", categorie="", stadiu="Fond", obiect="clauze abuzive",
        data_modificare="2020-01-01T00:00:00",
        parti=[Parte("POPESCU ION", "Reclamant"), Parte("BANCA SA", "Pârât")],
    )


@pytest.fixture()
def conn():
    c = conecteaza(":memory:")
    init_db(c)
    yield c
    c.close()


def test_dedup_global(conn):
    """Două interogări care întorc același dosar → un singur dosar unic stocat."""
    client = FakeClient(lambda parte, obiect, s, e: [_colectiv("1/3/2020")])
    raport = scaneaza(
        conn, client, asociatii=[_asoc("A"), _asoc("B")], obiecte_query=[],
    )
    assert raport.unice == 1
    assert raport.noi == 1
    assert statistici(conn)["total"] == 1


def test_respinsele_sunt_sarite(conn):
    client = FakeClient(lambda parte, obiect, s, e: [_individual("9/3/2020")])
    raport = scaneaza(conn, client, asociatii=[_asoc("A")], obiecte_query=[])
    assert raport.sarite == 1
    assert raport.noi == 0
    assert statistici(conn)["total"] == 0


def test_store_all_pastreaza_respinsele(conn):
    client = FakeClient(lambda parte, obiect, s, e: [_individual("9/3/2020")])
    scaneaza(conn, client, asociatii=[_asoc("A")], obiecte_query=[], doar_colective=False)
    assert statistici(conn)["total"] == 1


def test_impartire_adaptiva_la_plafon(conn):
    """Fereastra plină atinge 1000 → se sparge în jumătăți care întorc puține."""
    def responder(parte, obiect, start, stop):
        span = (stop - start).days
        if span > 4000:                       # fereastra plină → trunchiat
            return [_individual(f"{i}/3/2020") for i in range(1000)]
        return [_colectiv(f"col-{start.year}/3/2020")]  # jumătate → un colectiv

    client = FakeClient(responder)
    raport = scaneaza(conn, client, asociatii=[_asoc("A")], obiecte_query=[])

    # 1 interogare pe fereastra plină + 2 pe jumătăți
    assert len(client.calls) == 3
    # dosarele celor 1000 (fereastra plină) NU au fost procesate; doar jumătățile
    assert raport.unice == 2
    assert raport.noi == 2
    assert not raport.trunchieri  # jumătățile au coborât sub plafon


def test_trunchiere_logata_cand_nu_se_mai_poate_imparti(conn):
    """Fereastră mică + 1000 rezultate → nu se mai împarte, se loghează trunchiere."""
    client = FakeClient(lambda parte, obiect, s, e: [_colectiv(f"{i}/3/2020") for i in range(1000)])
    raport = scaneaza(
        conn, client, asociatii=[_asoc("A")], obiecte_query=[],
        data_start=datetime(2024, 1, 1), data_stop=datetime(2024, 1, 2),  # 1 zi < MIN
    )
    assert raport.trunchieri
    assert len(client.calls) == 1  # nu s-a împărțit


def test_buget_limiteaza_explozia(conn):
    """Parte hiper-activă (mereu 1000) → împărțirea e plafonată de buget, nu explodează."""
    client = FakeClient(lambda parte, obiect, s, e: [_individual(f"{s.year}-{i}/3/2020") for i in range(1000)])
    raport = scaneaza(conn, client, asociatii=[_asoc("Hiperactiv")], obiecte_query=[])
    assert len(client.calls) <= MAX_SUBINTEROGARI
    assert any("buget epuizat" in t for t in raport.trunchieri)


def test_filtreaza_domeniile_in_scop(conn):
    """Implicit, scanează doar consumatori/bancar/mediu — nu muncă/sănătate/alt."""
    client = FakeClient(lambda parte, obiect, s, e: [])
    scaneaza(conn, client, obiecte_query=[])  # asociatii=None → registru real, în scop
    interogate = {c["parte"] for c in client.calls}
    assert "Pro Consumatori" in interogate   # consumatori
    assert "Agent Green" in interogate        # mediu
    assert "SANITAS" not in interogate        # munca = out of scope
    assert "COPAC" not in interogate          # sanatate = out of scope


def test_obiect_ingusteaza_parte(conn):
    """Un actor cu filtru de obiect trimite ambii parametri la client."""
    client = FakeClient(lambda parte, obiect, s, e: [])
    asoc = {"nume_oficial": "ANPC", "query": "ANPC", "variante": ["anpc"],
            "domeniu": "consumatori", "obiect": "clauze abuzive"}
    scaneaza(conn, client, asociatii=[asoc], obiecte_query=[])
    assert client.calls[0]["parte"] == "ANPC"
    assert client.calls[0]["obiect"] == "clauze abuzive"

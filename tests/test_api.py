"""Teste pentru stratul web (FastAPI) + anonimizarea părților."""

from __future__ import annotations

import warnings

import pytest

from app.api import main
from app.classifier import taxonomy as fmt
from app.classifier import clasifica
from app.client.models import Dosar, Parte
from app.storage import conecteaza, init_db, upsert_caz

# TestClient (starlette) emite un DeprecationWarning despre httpx — irelevant aici
warnings.filterwarnings("ignore")
from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db = tmp_path / "test.db"
    # populăm DB-ul de test
    conn = conecteaza(db)
    init_db(conn)
    d = Dosar(
        numar="500/3/2024", numar_vechi="", data="2024-01-01T00:00:00",
        institutie="TribunalulBUCURESTI", departament="", categorie="Litigii",
        stadiu="Fond",
        obiect="acţiune în reprezentare interese colective ale consumatorilor",
        data_modificare="2024-02-01T00:00:00",
        parti=[
            Parte("ASOCIAŢIA PRO CONSUMATORI", "Reclamant"),
            Parte("POPESCU ION MARIN", "Pârât"),  # persoană fizică → anonimizat
        ],
    )
    upsert_caz(conn, d, clasifica(d))
    conn.close()
    # direcționăm aplicația spre DB-ul de test
    monkeypatch.setattr(main, "DB_PATH", str(db))
    return TestClient(main.app)


def test_home_ok(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "ZAMOLXIS" in r.text


def test_api_lista_si_filtre(client):
    r = client.get("/api/cazuri?domeniu=consumatori")
    assert r.status_code == 200
    assert any(c["numar"] == "500/3/2024" for c in r.json())
    assert client.get("/api/cazuri?domeniu=mediu").json() == []


def test_api_detaliu_si_404(client):
    assert client.get("/api/cazuri/500/3/2024").status_code == 200
    assert client.get("/api/cazuri/0/0/0").status_code == 404


def test_anonimizare_in_pagina_caz(client):
    html = client.get("/caz/500/3/2024").text
    assert "ASOCIAŢIA PRO CONSUMATORI" in html  # persoană juridică → integral
    assert "POPESCU ION MARIN" not in html      # persoană fizică → ascuns
    assert "P. I. M." in html                   # afișat ca inițiale


# --- teste unitare pe anonimizare -------------------------------------------

def test_nume_public():
    assert fmt.nume_public("BANCA TRANSILVANIA SA") == "BANCA TRANSILVANIA SA"
    assert fmt.nume_public("ASOCIAŢIA PRO CONSUMATORI", True) == "ASOCIAŢIA PRO CONSUMATORI"
    assert fmt.nume_public("POPESCU ION") == "P. I."
    assert fmt.nume_public("RUDAREANU ALINA domiciliul ales la Cabinet Avocat") == "R. A."

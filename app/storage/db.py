"""Conexiune și schemă SQLite.

Schema urmează PLAN.md §6. Cheia naturală a unui dosar e `numar` (număr unic ECRIS),
ceea ce ne dă dedup gratuit (serviciul întoarce dosare duplicate).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

DEFAULT_DB = "data/portal.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS caz (
    numar              TEXT PRIMARY KEY,
    numar_vechi        TEXT,
    instanta           TEXT,
    departament        TEXT,
    categorie          TEXT,
    stadiu             TEXT,
    obiect             TEXT,
    data_inregistrare  TEXT,
    data_modificare    TEXT,
    scor               INTEGER NOT NULL DEFAULT 0,
    nivel              TEXT    NOT NULL DEFAULT 'respins',
    domeniu            TEXT,
    motive             TEXT,            -- JSON: listă de string-uri
    rezumat            TEXT,
    prima_data_vazut   TEXT NOT NULL,
    ultima_actualizare TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_caz_nivel   ON caz(nivel);
CREATE INDEX IF NOT EXISTS idx_caz_domeniu ON caz(domeniu);
CREATE INDEX IF NOT EXISTS idx_caz_scor    ON caz(scor);

CREATE TABLE IF NOT EXISTS parte (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    caz_numar      TEXT NOT NULL REFERENCES caz(numar) ON DELETE CASCADE,
    nume           TEXT,
    calitate       TEXT,
    este_asociatie INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_parte_caz ON parte(caz_numar);

CREATE TABLE IF NOT EXISTS termen (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    caz_numar      TEXT NOT NULL REFERENCES caz(numar) ON DELETE CASCADE,
    data           TEXT,
    ora            TEXT,
    solutie_sumar  TEXT,
    numar_document TEXT
);
CREATE INDEX IF NOT EXISTS idx_termen_caz ON termen(caz_numar);

-- „valuri" de procese individuale identice: același pârât + același tip de obiect,
-- agregate din MULTE dosare separate (ex. mii de contestații pensionare vs. o Casă
-- de Pensii). Reprezintă litigiul de masă individual, complementar acțiunilor colective.
CREATE TABLE IF NOT EXISTS grup (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    parat              TEXT,            -- numele specific al pârâtului (afișare)
    parat_key          TEXT NOT NULL,   -- normalizat (cheie)
    obiect_tip         TEXT NOT NULL,   -- eticheta bucket-ului de obiect
    domeniu            TEXT,
    nr_dosare          INTEGER NOT NULL DEFAULT 0,
    aprox              INTEGER NOT NULL DEFAULT 0,  -- 1 = subevaluat (trunchiere)
    instante           TEXT,            -- JSON: {instanta: count}
    exemple            TEXT,            -- JSON: [{numar, instanta, data}]
    prima_data         TEXT,            -- cel mai vechi dosar
    ultima_data        TEXT,            -- cel mai nou dosar
    prima_data_vazut   TEXT NOT NULL,
    ultima_actualizare TEXT NOT NULL,
    UNIQUE(parat_key, obiect_tip)
);
CREATE INDEX IF NOT EXISTS idx_grup_domeniu ON grup(domeniu);
CREATE INDEX IF NOT EXISTS idx_grup_nr      ON grup(nr_dosare);

-- audit al scanărilor: ce interogare, câte rezultate, dacă a fost trunchiată (1000)
CREATE TABLE IF NOT EXISTS scan_log (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    tip        TEXT,            -- 'parte' | 'obiect'
    valoare    TEXT,
    count      INTEGER,
    trunchiat  INTEGER NOT NULL DEFAULT 0,
    rulat_la   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_scanlog_rulat ON scan_log(rulat_la);
"""


def conecteaza(path: str | Path = DEFAULT_DB) -> sqlite3.Connection:
    """Deschide o conexiune (creează directorul dacă lipsește)."""
    if str(path) != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()

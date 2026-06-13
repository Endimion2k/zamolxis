"""Operații pe baza de date: upsert (cu dedup) + interogări pentru API/portal."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any

from app.classifier import Clasificare
from app.classifier import taxonomy as tx
from app.client.models import Dosar


def _acum() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _este_asociatie(nume: str) -> bool:
    n = tx.normalizeaza(nume)
    return any(a in n for a in tx.ASOCIATII_CUNOSCUTE) or any(
        i in n for i in tx.INDICII_ASOCIATIE
    )


def upsert_caz(
    conn: sqlite3.Connection, dosar: Dosar, clas: Clasificare
) -> bool:
    """Inserează sau actualizează un dosar + părți + termene. Dedup pe `numar`.

    Întoarce True dacă dosarul e nou, False dacă a fost actualizat.
    `prima_data_vazut` se păstrează la actualizare.
    """
    if not dosar.numar:
        raise ValueError("dosar fără număr — nu poate fi stocat (cheie naturală)")

    acum = _acum()
    row = conn.execute(
        "SELECT prima_data_vazut FROM caz WHERE numar = ?", (dosar.numar,)
    ).fetchone()
    este_nou = row is None
    prima = acum if este_nou else row["prima_data_vazut"]

    conn.execute(
        """
        INSERT INTO caz (numar, numar_vechi, instanta, departament, categorie,
                         stadiu, obiect, data_inregistrare, data_modificare,
                         scor, nivel, domeniu, motive, rezumat,
                         prima_data_vazut, ultima_actualizare)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(numar) DO UPDATE SET
            numar_vechi=excluded.numar_vechi, instanta=excluded.instanta,
            departament=excluded.departament, categorie=excluded.categorie,
            stadiu=excluded.stadiu, obiect=excluded.obiect,
            data_inregistrare=excluded.data_inregistrare,
            data_modificare=excluded.data_modificare, scor=excluded.scor,
            nivel=excluded.nivel, domeniu=excluded.domeniu, motive=excluded.motive,
            rezumat=excluded.rezumat, ultima_actualizare=excluded.ultima_actualizare
        """,
        (
            dosar.numar, dosar.numar_vechi, dosar.institutie, dosar.departament,
            dosar.categorie, dosar.stadiu, dosar.obiect, dosar.data,
            dosar.data_modificare, clas.scor, clas.nivel, clas.domeniu,
            json.dumps(clas.motive, ensure_ascii=False), clas.rezumat,
            prima, acum,
        ),
    )

    # părți și termene sunt instantanee → le rescriem complet
    conn.execute("DELETE FROM parte WHERE caz_numar = ?", (dosar.numar,))
    if dosar.parti:
        conn.executemany(
            "INSERT INTO parte (caz_numar, nume, calitate, este_asociatie) "
            "VALUES (?,?,?,?)",
            [
                (dosar.numar, p.nume, p.calitate, int(_este_asociatie(p.nume)))
                for p in dosar.parti
            ],
        )
    conn.execute("DELETE FROM termen WHERE caz_numar = ?", (dosar.numar,))
    if dosar.sedinte:
        conn.executemany(
            "INSERT INTO termen (caz_numar, data, ora, solutie_sumar, numar_document) "
            "VALUES (?,?,?,?,?)",
            [
                (dosar.numar, s.data, s.ora, s.solutie_sumar, s.numar_document)
                for s in dosar.sedinte
            ],
        )
    conn.commit()
    return este_nou


# --- interogări pentru API / portal -----------------------------------------

def _caz_dict(row: sqlite3.Row) -> dict[str, Any]:
    d = dict(row)
    d["motive"] = json.loads(d["motive"]) if d.get("motive") else []
    return d


def list_cazuri(
    conn: sqlite3.Connection,
    *,
    nivel: str | None = None,
    domeniu: str | None = None,
    instanta: str | None = None,
    cauta: str | None = None,
    doar_colective: bool = True,
    limit: int = 50,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """Listă filtrabilă, ordonată după scor desc apoi recență."""
    clauze = []
    params: list[Any] = []
    if doar_colective:
        clauze.append("nivel != 'respins'")
    if nivel:
        clauze.append("nivel = ?")
        params.append(nivel)
    if domeniu:
        clauze.append("domeniu = ?")
        params.append(domeniu)
    if instanta:
        clauze.append("instanta = ?")
        params.append(instanta)
    if cauta:
        clauze.append("(obiect LIKE ? OR rezumat LIKE ? OR numar LIKE ?)")
        like = f"%{cauta}%"
        params += [like, like, like]

    where = (" WHERE " + " AND ".join(clauze)) if clauze else ""
    sql = (
        "SELECT numar, instanta, categorie, stadiu, obiect, domeniu, scor, nivel, "
        "rezumat, data_modificare, "
        "(SELECT COUNT(*) FROM parte p WHERE p.caz_numar = caz.numar) AS nr_parti "
        f"FROM caz{where} "
        "ORDER BY scor DESC, data_modificare DESC "
        "LIMIT ? OFFSET ?"
    )
    params += [limit, offset]
    return [_caz_dict(r) for r in conn.execute(sql, params).fetchall()]


def get_caz(conn: sqlite3.Connection, numar: str) -> dict[str, Any] | None:
    row = conn.execute("SELECT * FROM caz WHERE numar = ?", (numar,)).fetchone()
    if row is None:
        return None
    caz = _caz_dict(row)
    caz["parti"] = [
        dict(r)
        for r in conn.execute(
            "SELECT nume, calitate, este_asociatie FROM parte WHERE caz_numar = ?",
            (numar,),
        ).fetchall()
    ]
    caz["termene"] = [
        dict(r)
        for r in conn.execute(
            "SELECT data, ora, solutie_sumar, numar_document FROM termen "
            "WHERE caz_numar = ? ORDER BY data",
            (numar,),
        ).fetchall()
    ]
    return caz


def upsert_grup(
    conn: sqlite3.Connection,
    *,
    parat: str,
    parat_key: str,
    obiect_tip: str,
    domeniu: str | None,
    nr_dosare: int,
    aprox: bool,
    instante: dict[str, int],
    exemple: list[dict[str, str]],
    prima_data: str,
    ultima_data: str,
) -> bool:
    """Inserează/actualizează un val de litigii. Cheie: (parat_key, obiect_tip)."""
    acum = _acum()
    row = conn.execute(
        "SELECT prima_data_vazut FROM grup WHERE parat_key = ? AND obiect_tip = ?",
        (parat_key, obiect_tip),
    ).fetchone()
    este_nou = row is None
    prima_vazut = acum if este_nou else row["prima_data_vazut"]
    conn.execute(
        """
        INSERT INTO grup (parat, parat_key, obiect_tip, domeniu, nr_dosare, aprox,
                          instante, exemple, prima_data, ultima_data,
                          prima_data_vazut, ultima_actualizare)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(parat_key, obiect_tip) DO UPDATE SET
            parat=excluded.parat, domeniu=excluded.domeniu, nr_dosare=excluded.nr_dosare,
            aprox=excluded.aprox, instante=excluded.instante, exemple=excluded.exemple,
            prima_data=excluded.prima_data, ultima_data=excluded.ultima_data,
            ultima_actualizare=excluded.ultima_actualizare
        """,
        (parat, parat_key, obiect_tip, domeniu, nr_dosare, int(aprox),
         json.dumps(instante, ensure_ascii=False),
         json.dumps(exemple, ensure_ascii=False),
         prima_data, ultima_data, prima_vazut, acum),
    )
    conn.commit()
    return este_nou


def list_grupuri(
    conn: sqlite3.Connection,
    *,
    domeniu: str | None = None,
    cauta: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict[str, Any]]:
    clauze, params = [], []
    if domeniu:
        clauze.append("domeniu = ?")
        params.append(domeniu)
    if cauta:
        clauze.append("(parat LIKE ? OR obiect_tip LIKE ?)")
        params += [f"%{cauta}%", f"%{cauta}%"]
    where = (" WHERE " + " AND ".join(clauze)) if clauze else ""
    sql = (
        "SELECT id, parat, obiect_tip, domeniu, nr_dosare, aprox, prima_data, "
        f"ultima_data FROM grup{where} ORDER BY nr_dosare DESC LIMIT ? OFFSET ?"
    )
    params += [limit, offset]
    return [dict(r) for r in conn.execute(sql, params).fetchall()]


def get_grup(conn: sqlite3.Connection, grup_id: int) -> dict[str, Any] | None:
    row = conn.execute("SELECT * FROM grup WHERE id = ?", (grup_id,)).fetchone()
    if row is None:
        return None
    g = dict(row)
    g["instante"] = json.loads(g["instante"]) if g.get("instante") else {}
    g["exemple"] = json.loads(g["exemple"]) if g.get("exemple") else []
    return g


def log_scan(
    conn: sqlite3.Connection, tip: str, valoare: str, count: int, trunchiat: bool
) -> None:
    conn.execute(
        "INSERT INTO scan_log (tip, valoare, count, trunchiat, rulat_la) "
        "VALUES (?,?,?,?,?)",
        (tip, valoare, count, int(trunchiat), _acum()),
    )
    conn.commit()


def statistici(conn: sqlite3.Connection) -> dict[str, Any]:
    pe_nivel = {
        r["nivel"]: r["n"]
        for r in conn.execute("SELECT nivel, COUNT(*) n FROM caz GROUP BY nivel")
    }
    pe_domeniu = {
        r["domeniu"]: r["n"]
        for r in conn.execute(
            "SELECT domeniu, COUNT(*) n FROM caz WHERE domeniu IS NOT NULL "
            "GROUP BY domeniu"
        )
    }
    total = conn.execute("SELECT COUNT(*) n FROM caz").fetchone()["n"]
    grupuri = conn.execute("SELECT COUNT(*) n FROM grup").fetchone()["n"]
    dosare_in_grupuri = conn.execute(
        "SELECT COALESCE(SUM(nr_dosare), 0) s FROM grup"
    ).fetchone()["s"]
    return {
        "total": total,
        "pe_nivel": pe_nivel,
        "pe_domeniu": pe_domeniu,
        "grupuri": grupuri,
        "dosare_in_grupuri": dosare_in_grupuri,
    }

"""Aplicația FastAPI: API JSON + portal HTML.

Rulare:
  .\\.venv\\Scripts\\python.exe -m uvicorn app.api.main:app --reload

Config prin variabilă de mediu:
  PORTAL_DB  — calea către baza SQLite (implicit data/portal.db)
"""

from __future__ import annotations

import math
import os
import sqlite3
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.classifier.taxonomy import nume_public
from app.storage import (
    conecteaza,
    get_caz,
    get_grup,
    init_db,
    list_cazuri,
    list_grupuri,
    statistici,
)

DB_PATH = os.environ.get("PORTAL_DB", "data/portal.db")
TEMPLATES = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
TEMPLATES.env.filters["public"] = nume_public

DOMENII_AFISARE = {
    "consumatori": "Protecția consumatorilor",
    "bancar": "Clauze abuzive bancare",
    "mediu": "Mediu",
    "munca": "Litigii de muncă (colective)",
    "sanatate": "Sănătate / pacienți",
    "imobiliare": "Imobiliare / dezvoltatori",
    "fiscal": "Fiscal / taxe",
    "pensii": "Pensii",
    "proprietati": "Restituiri proprietăți",
    "agricultura": "Agricultură (subvenții)",
    "alt": "Alte interese colective",
}
NIVEL_AFISARE = {
    "confirmat": "Confirmat",
    "revizuire": "De verificat",
}

app = FastAPI(title="Zamolxis — Legea celor mulți", version="0.1.0")


def get_conn():
    conn = conecteaza(DB_PATH)
    init_db(conn)  # idempotent — sigur dacă DB-ul nu există încă
    try:
        yield conn
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# API JSON
# ---------------------------------------------------------------------------

@app.get("/api/statistici")
def api_statistici(conn: sqlite3.Connection = Depends(get_conn)) -> dict[str, Any]:
    return statistici(conn)


@app.get("/api/cazuri")
def api_cazuri(
    conn: sqlite3.Connection = Depends(get_conn),
    nivel: str | None = None,
    domeniu: str | None = None,
    instanta: str | None = None,
    cauta: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[dict[str, Any]]:
    return list_cazuri(
        conn, nivel=nivel, domeniu=domeniu, instanta=instanta, cauta=cauta,
        limit=limit, offset=offset,
    )


@app.get("/api/cazuri/{numar:path}")
def api_caz(numar: str, conn: sqlite3.Connection = Depends(get_conn)) -> dict[str, Any]:
    caz = get_caz(conn, numar)
    if caz is None:
        raise HTTPException(status_code=404, detail="Dosar inexistent")
    return caz


@app.get("/api/grupuri")
def api_grupuri(
    conn: sqlite3.Connection = Depends(get_conn),
    domeniu: str | None = None,
    cauta: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[dict[str, Any]]:
    return list_grupuri(conn, domeniu=domeniu, cauta=cauta, limit=limit, offset=offset)


@app.get("/api/grupuri/{grup_id}")
def api_grup(grup_id: int, conn: sqlite3.Connection = Depends(get_conn)) -> dict[str, Any]:
    g = get_grup(conn, grup_id)
    if g is None:
        raise HTTPException(status_code=404, detail="Val inexistent")
    return g


# ---------------------------------------------------------------------------
# Portal HTML
# ---------------------------------------------------------------------------

PAGE_SIZE = 20


@app.get("/", response_class=HTMLResponse)
def pagina_lista(
    request: Request,
    conn: sqlite3.Connection = Depends(get_conn),
    domeniu: str | None = None,
    nivel: str | None = None,
    cauta: str | None = None,
    pagina: int = Query(1, ge=1),
):
    offset = (pagina - 1) * PAGE_SIZE
    cazuri = list_cazuri(
        conn, domeniu=domeniu or None, nivel=nivel or None, cauta=cauta or None,
        limit=PAGE_SIZE + 1, offset=offset,
    )
    mai_sunt = len(cazuri) > PAGE_SIZE
    cazuri = cazuri[:PAGE_SIZE]
    stats = statistici(conn)
    return TEMPLATES.TemplateResponse(
        request,
        "index.html",
        {
            "cazuri": cazuri,
            "stats": stats,
            "domenii": DOMENII_AFISARE,
            "niveluri": NIVEL_AFISARE,
            "f_domeniu": domeniu or "",
            "f_nivel": nivel or "",
            "f_cauta": cauta or "",
            "pagina": pagina,
            "mai_sunt": mai_sunt,
            "activ": "colective",
        },
    )


@app.get("/caz/{numar:path}", response_class=HTMLResponse)
def pagina_caz(
    request: Request,
    numar: str,
    conn: sqlite3.Connection = Depends(get_conn),
):
    caz = get_caz(conn, numar)
    if caz is None:
        return HTMLResponse("<h1>Dosar inexistent</h1>", status_code=404)
    return TEMPLATES.TemplateResponse(
        request,
        "caz.html",
        {
            "caz": caz,
            "domenii": DOMENII_AFISARE,
            "niveluri": NIVEL_AFISARE,
        },
    )


@app.get("/valuri", response_class=HTMLResponse)
def pagina_valuri(
    request: Request,
    conn: sqlite3.Connection = Depends(get_conn),
    domeniu: str | None = None,
    cauta: str | None = None,
    pagina: int = Query(1, ge=1),
):
    offset = (pagina - 1) * PAGE_SIZE
    grupuri = list_grupuri(
        conn, domeniu=domeniu or None, cauta=cauta or None,
        limit=PAGE_SIZE + 1, offset=offset,
    )
    mai_sunt = len(grupuri) > PAGE_SIZE
    grupuri = grupuri[:PAGE_SIZE]
    return TEMPLATES.TemplateResponse(
        request, "valuri.html",
        {
            "grupuri": grupuri, "stats": statistici(conn), "domenii": DOMENII_AFISARE,
            "f_domeniu": domeniu or "", "f_cauta": cauta or "",
            "pagina": pagina, "mai_sunt": mai_sunt, "activ": "valuri",
        },
    )


@app.get("/val/{grup_id}", response_class=HTMLResponse)
def pagina_val(request: Request, grup_id: int, conn: sqlite3.Connection = Depends(get_conn)):
    g = get_grup(conn, grup_id)
    if g is None:
        return HTMLResponse("<h1>Val inexistent</h1>", status_code=404)
    return TEMPLATES.TemplateResponse(
        request, "val.html", {"g": g, "domenii": DOMENII_AFISARE}
    )


@app.get("/despre", response_class=HTMLResponse)
def pagina_despre(request: Request):
    return TEMPLATES.TemplateResponse(request, "despre.html", {"activ": "despre"})


@app.get("/sanatate")
def sanatate() -> JSONResponse:
    return JSONResponse({"status": "ok"})

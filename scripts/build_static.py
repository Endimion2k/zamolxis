"""Generează site-ul static (web/data.json) din baza de date.

Exportă DOAR datele de interes public, ANONIMIZATE (persoane fizice → inițiale),
pentru a fi servite de GitHub Pages cu căutare client-side.

Rulare:
  py scripts\\build_static.py [--db data\\portal.db] [--out web\\data.json] [--data 2026-06-13]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.classifier.taxonomy import nume_public  # noqa: E402
from app.storage import conecteaza, get_caz, get_grup, list_cazuri, list_grupuri, statistici  # noqa: E402

DOMENII = {
    "consumatori": "Protecția consumatorilor", "bancar": "Clauze abuzive bancare",
    "mediu": "Mediu", "munca": "Litigii de muncă", "sanatate": "Sănătate / pacienți",
    "imobiliare": "Imobiliare / dezvoltatori", "fiscal": "Fiscal / taxe", "pensii": "Pensii",
    "proprietati": "Restituiri proprietăți", "agricultura": "Agricultură",
    "asigurari": "Asigurări", "telecom": "Telecom / internet",
    "recuperare": "Recuperare creanțe / IFN", "retail": "Retail / garanții produse",
    "turism": "Turism / transport", "investitii": "Investiții / fraude",
    "servicii": "Servicii cu abonament", "alt": "Altele",
}
NIVELURI = {"confirmat": "Confirmat", "revizuire": "De verificat"}


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/portal.db")
    ap.add_argument("--out", default="web/data.json")
    ap.add_argument("--data", default="", help="data afișată (YYYY-MM-DD); gol = necunoscut")
    args = ap.parse_args()

    conn = conecteaza(args.db)

    cazuri = []
    for c in list_cazuri(conn, limit=100000):
        d = get_caz(conn, c["numar"])
        if not d:
            continue
        cazuri.append({
            "numar": d["numar"], "instanta": d["instanta"], "stadiu": d["stadiu"],
            "domeniu": d["domeniu"], "scor": d["scor"], "nivel": d["nivel"],
            "obiect": d["obiect"], "rezumat": d["rezumat"],
            "motive": d.get("motive", []),
            "parti": [
                {"nume": nume_public(p["nume"], p["este_asociatie"]), "calitate": p["calitate"]}
                for p in d.get("parti", [])
            ],
        })

    grupuri = []
    for g in list_grupuri(conn, limit=100000):
        det = get_grup(conn, g["id"])
        if not det:
            continue
        grupuri.append({
            "parat": det["parat"], "obiect_tip": det["obiect_tip"], "domeniu": det["domeniu"],
            "nr_dosare": det["nr_dosare"], "aprox": bool(det["aprox"]),
            "prima_data": det["prima_data"], "ultima_data": det["ultima_data"],
            "instante": det.get("instante", {}), "exemple": det.get("exemple", []),
        })

    s = statistici(conn)
    payload = {
        "generat_la": args.data,
        "domenii": DOMENII,
        "niveluri": NIVELURI,
        "stats": {"confirmate": s["pe_nivel"].get("confirmat", 0)},
        "cazuri": cazuri,
        "grupuri": grupuri,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Scris {out}: {len(cazuri)} cazuri, {len(grupuri)} valuri "
          f"({out.stat().st_size // 1024} KB)")
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Faza 8 — DESCOPERIRE AUTOMATĂ de valuri: găsește firme/instituții acționate în masă,
fără listă prealabilă de pârâți (caută pe tip de problemă → grupează după pârâtul-firmă).

Exemple:
  py scripts\\discover_waves.py --obiect "rezolutiune" --prag 20 --since 2022-01-01
  py scripts\\discover_waves.py --domenii imobiliare,bancar --since 2021-01-01
  py scripts\\discover_waves.py            # toate tipurile de obiect din registru (lung)
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import registry  # noqa: E402
from app.client import PortalClient  # noqa: E402
from app.cluster import descopera_valuri  # noqa: E402
from app.cluster.analyzer import PRAG_GRUP  # noqa: E402
from app.storage import conecteaza, statistici  # noqa: E402
from app.storage.db import DEFAULT_DB  # noqa: E402


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

    ap = argparse.ArgumentParser(description="Descoperă automat valuri de litigii (pârâți noi).")
    ap.add_argument("--db", default=DEFAULT_DB)
    ap.add_argument("--throttle", type=float, default=0.4)
    ap.add_argument("--prag", type=int, default=PRAG_GRUP)
    ap.add_argument("--since", help="dată de start YYYY-MM-DD")
    ap.add_argument("--obiect", action="append",
                    help="tip de obiect de descoperit (se poate repeta). Implicit: din registru.")
    ap.add_argument("--domenii", help="filtrează tipurile de obiect pe domenii (virgulă)")
    args = ap.parse_args()

    data_start = None
    if args.since:
        try:
            data_start = datetime.strptime(args.since, "%Y-%m-%d")
        except ValueError:
            ap.error("--since trebuie să fie YYYY-MM-DD")

    if args.obiect:
        obiecte = [{"query": o, "label": o.capitalize(), "domeniu": "alt"} for o in args.obiect]
    else:
        domenii = tuple(d.strip() for d in args.domenii.split(",")) if args.domenii else None
        obiecte = registry.obiecte_descoperire(domenii)

    conn = conecteaza(args.db)
    client = PortalClient(throttle=args.throttle)
    print(f">> Descopăr valuri pe {len(obiecte)} tipuri de obiect...", flush=True)
    raport = descopera_valuri(
        conn, client, obiecte=obiecte, prag=args.prag, data_start=data_start,
        on_progress=lambda m: print(f"   · {m}", flush=True),
    )
    print("\n=== Raport descoperire ===")
    print(raport.rezumat())
    s = statistici(conn)
    print(f"\n=== DB ({args.db}) ===")
    print(f"  valuri (grupuri): {s['grupuri']}  ({s['dosare_in_grupuri']} dosare acoperite)")
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

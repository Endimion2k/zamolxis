"""Detectează „valuri" de litigii (dosare individuale identice) și le salvează.

Exemple:
  py scripts\\run_cluster_scan.py
  py scripts\\run_cluster_scan.py --prag 50 --since 2023-01-01

Interoghează pârâții de masă din registru (Case de Pensii, ANAF, inspectorate etc.),
grupează dosarele după (pârât + tip obiect) și salvează grupurile peste prag.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.client import PortalClient  # noqa: E402
from app.cluster import scaneaza_grupuri  # noqa: E402
from app.cluster.analyzer import PRAG_GRUP  # noqa: E402
from app.storage import conecteaza, statistici  # noqa: E402
from app.storage.db import DEFAULT_DB  # noqa: E402


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

    ap = argparse.ArgumentParser(description="Detectează valuri de litigii identice.")
    ap.add_argument("--db", default=DEFAULT_DB)
    ap.add_argument("--throttle", type=float, default=0.5)
    ap.add_argument("--prag", type=int, default=PRAG_GRUP,
                    help=f"nr. minim de dosare pentru un val (implicit {PRAG_GRUP})")
    ap.add_argument("--since", help="dată de start YYYY-MM-DD")
    ap.add_argument("--domenii", help="domenii de scanat, separate prin virgulă "
                    "(ex: pensii,fiscal). Implicit: toate.")
    args = ap.parse_args()

    domenii = None
    if args.domenii:
        domenii = tuple(d.strip() for d in args.domenii.split(",") if d.strip())

    data_start = None
    if args.since:
        try:
            data_start = datetime.strptime(args.since, "%Y-%m-%d")
        except ValueError:
            ap.error("--since trebuie să fie YYYY-MM-DD")

    conn = conecteaza(args.db)
    client = PortalClient(throttle=args.throttle)
    print(">> Detectez valuri de litigii...", flush=True)
    raport = scaneaza_grupuri(
        conn, client, prag=args.prag, data_start=data_start, domenii=domenii,
        on_progress=lambda m: print(f"   · {m}", flush=True),
    )
    print("\n=== Raport valuri ===")
    print(raport.rezumat())
    s = statistici(conn)
    print(f"\n=== DB ({args.db}) ===")
    print(f"  valuri (grupuri): {s['grupuri']}  ({s['dosare_in_grupuri']} dosare acoperite)")
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Faza 4 — scanner orchestrat: parcurge tot registrul, clasifică, actualizează DB.

Exemple:
  py scripts\\run_scanner.py
  py scripts\\run_scanner.py --no-obiecte          # doar asociații (mai rapid)
  py scripts\\run_scanner.py --since 2024-01-01     # doar dosare din 2024 încoace
  py scripts\\run_scanner.py --store-all            # salvează și respinse

Gândit pentru rulare zilnică (vezi scripts\\install_task_windows.ps1).
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.client import PortalClient  # noqa: E402
from app.scanner import scaneaza  # noqa: E402
from app.storage import conecteaza, statistici  # noqa: E402
from app.storage.db import DEFAULT_DB  # noqa: E402


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

    ap = argparse.ArgumentParser(description="Scanner acțiuni colective (registru complet).")
    ap.add_argument("--db", default=DEFAULT_DB)
    ap.add_argument("--throttle", type=float, default=1.0)
    ap.add_argument("--no-obiecte", action="store_true",
                    help="sare peste interogările pe obiect (doar asociații)")
    ap.add_argument("--store-all", action="store_true",
                    help="salvează și dosarele respinse")
    ap.add_argument("--since", help="dată de start YYYY-MM-DD (delta)")
    ap.add_argument("--domenii", help="domenii de scanat, separate prin virgulă "
                    "(implicit: consumatori,bancar,mediu)")
    ap.add_argument("--toate", action="store_true",
                    help="scanează toate domeniile din registru (inclusiv munca/sanatate/alt)")
    args = ap.parse_args()

    from app import registry  # noqa: E402
    domenii = None  # None → domeniile în scop (consumatori/bancar/mediu)
    if args.toate:
        domenii = tuple({a["domeniu"] for a in registry.ASOCIATII})
    elif args.domenii:
        domenii = tuple(d.strip() for d in args.domenii.split(",") if d.strip())

    data_start = None
    if args.since:
        try:
            data_start = datetime.strptime(args.since, "%Y-%m-%d")
        except ValueError:
            ap.error("--since trebuie să fie YYYY-MM-DD")

    conn = conecteaza(args.db)
    client = PortalClient(throttle=args.throttle)

    print(">> Pornesc scanarea registrului...", flush=True)
    raport = scaneaza(
        conn, client,
        doar_colective=not args.store_all,
        include_obiecte=not args.no_obiecte,
        data_start=data_start,
        domenii=domenii,
        on_progress=lambda m: print(f"   · {m}", flush=True),
    )

    print("\n=== Raport scanare ===")
    print(raport.rezumat())

    s = statistici(conn)
    print(f"\n=== DB ({args.db}) ===")
    print(f"  total : {s['total']}")
    print(f"  nivel : {s['pe_nivel']}")
    print(f"  domeniu: {s['pe_domeniu']}")
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

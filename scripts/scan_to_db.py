"""Faza 3 — scanează o interogare, clasifică și salvează în SQLite.

Exemple:
  py scripts\\scan_to_db.py --parte "Asociatia Pro Consumatori"
  py scripts\\scan_to_db.py --obiect "clauze abuzive" --institutie TribunalulBUCURESTI --store-all

Implicit salvează doar candidații colectivi (nivel != respins). --store-all salvează tot.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.classifier import clasifica  # noqa: E402
from app.client import PortalClient, PortalError  # noqa: E402
from app.storage import conecteaza, init_db, statistici, upsert_caz  # noqa: E402
from app.storage.db import DEFAULT_DB  # noqa: E402


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

    ap = argparse.ArgumentParser()
    ap.add_argument("--obiect")
    ap.add_argument("--parte")
    ap.add_argument("--numar")
    ap.add_argument("--institutie")
    ap.add_argument("--db", default=DEFAULT_DB)
    ap.add_argument("--store-all", action="store_true",
                    help="salvează și dosarele respinse (implicit: doar colective)")
    ap.add_argument("--throttle", type=float, default=1.0)
    args = ap.parse_args()
    if not any((args.obiect, args.parte, args.numar)):
        ap.error("dă cel puțin --obiect / --parte / --numar")

    conn = conecteaza(args.db)
    init_db(conn)

    client = PortalClient(throttle=args.throttle)
    print(">> Interoghez portal.just.ro ...", flush=True)
    try:
        dosare = client.cautare_dosare(
            numar=args.numar, obiect=args.obiect, parte=args.parte,
            institutie=args.institutie,
        )
    except PortalError as exc:
        print(f"!! {exc}", file=sys.stderr)
        return 1

    # dedup pe număr (serviciul întoarce dosare duplicate)
    unice: dict[str, object] = {}
    for d in dosare:
        if d.numar and d.numar not in unice:
            unice[d.numar] = d
    print(f"<< {len(dosare)} returnate, {len(unice)} unice")

    noi = actualizate = sarite = 0
    for d in unice.values():
        c = clasifica(d)
        if not args.store_all and not c.este_colectiv:
            sarite += 1
            continue
        if upsert_caz(conn, d, c):
            noi += 1
        else:
            actualizate += 1

    print(f"   stocate: {noi} noi, {actualizate} actualizate, {sarite} sărite (respinse)")
    s = statistici(conn)
    print(f"\n=== DB ({args.db}) ===")
    print(f"  total în DB : {s['total']}")
    print(f"  pe nivel    : {s['pe_nivel']}")
    print(f"  pe domeniu  : {s['pe_domeniu']}")
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

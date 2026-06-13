"""Preview Faza 2+4: trage dosare reale, le clasifică, arată distribuția.

Exemple:
  py scripts\\scan_preview.py --obiect "clauze abuzive" --institutie TribunalulBUCURESTI
  py scripts\\scan_preview.py --obiect "in reprezentare"
  py scripts\\scan_preview.py --parte "Asociatia Pro Consumatori"

Validează că filtrul pe obiect singur produce multe RESPINSE (individuale) și că
semnalele de colectiv ridică doar cazurile potrivite.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.classifier import clasifica  # noqa: E402
from app.client import PortalClient, PortalError  # noqa: E402


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
    ap.add_argument("--arata", type=int, default=8, help="câte cazuri ridicate să detalieze")
    args = ap.parse_args()
    if not any((args.obiect, args.parte, args.numar)):
        ap.error("dă cel puțin --obiect / --parte / --numar")

    client = PortalClient(throttle=1.0)
    print(">> Interoghez ...", flush=True)
    try:
        dosare = client.cautare_dosare(
            numar=args.numar, obiect=args.obiect, parte=args.parte,
            institutie=args.institutie,
        )
    except PortalError as exc:
        print(f"!! {exc}", file=sys.stderr)
        return 1

    rezultate = [(d, clasifica(d)) for d in dosare]
    dist = Counter(c.nivel for _, c in rezultate)
    dom = Counter(c.domeniu for _, c in rezultate if c.domeniu)

    print(f"\n=== {len(dosare)} dosare ===")
    for nivel in ("confirmat", "revizuire", "respins"):
        print(f"  {nivel:<10}: {dist.get(nivel, 0)}")
    print(f"  domenii    : {dict(dom)}")

    ridicate = sorted(
        (rc for rc in rezultate if rc[1].este_colectiv),
        key=lambda rc: rc[1].scor, reverse=True,
    )
    print(f"\n=== top {min(args.arata, len(ridicate))} candidați colectivi ===")
    for d, c in ridicate[: args.arata]:
        print("-" * 68)
        print(f"  [{c.scor:>3}] {c.nivel:<10} {d.numar}  ({c.domeniu or '-'})")
        print(f"  motive : {'; '.join(c.motive)}")
        print(f"  rezumat: {c.rezumat}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

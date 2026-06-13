"""Faza 1 — validare: trage dosare reale din portal.just.ro și le afișează.

Exemple:
  py scripts\\fetch_sample.py --obiect "clauze abuzive" --institutie TribunalulBUCURESTI --max 15
  py scripts\\fetch_sample.py --parte "Asociatia pentru Protectia Consumatorilor"
  py scripts\\fetch_sample.py --obiect "actiune in reprezentare"

Scop: să vedem cum arată câmpurile reale (obiect, categorie, calități părți)
ca să calibrăm clasificatorul. NU clasifică încă nimic.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# permite rularea ca script (fără instalare de pachet)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.client import PortalClient, PortalError  # noqa: E402


def main() -> int:
    # Consola Windows e adesea cp1252 — forțăm UTF-8 ca să afișăm diacriticele.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

    ap = argparse.ArgumentParser(description="Trage dosare reale pentru calibrare.")
    ap.add_argument("--numar", help="număr dosar (ex. 1234/3/2024)")
    ap.add_argument("--obiect", help="text în obiectul dosarului")
    ap.add_argument("--parte", help="nume parte")
    ap.add_argument("--institutie", help="cod instanță (ex. TribunalulBUCURESTI)")
    ap.add_argument("--max", type=int, default=15, help="câte dosare să afișeze")
    ap.add_argument("--throttle", type=float, default=1.0)
    args = ap.parse_args()

    if not any((args.numar, args.obiect, args.parte)):
        ap.error("dă cel puțin unul dintre --numar / --obiect / --parte")

    client = PortalClient(throttle=args.throttle)
    print(">> Interoghez portal.just.ro ...", flush=True)
    try:
        dosare = client.cautare_dosare(
            numar=args.numar,
            obiect=args.obiect,
            parte=args.parte,
            institutie=args.institutie,
        )
    except PortalError as exc:
        print(f"!! Eroare: {exc}", file=sys.stderr)
        return 1

    total = len(dosare)
    print(f"<< {total} dosare returnate", end="")
    if total >= 1000:
        print("  [ATENȚIE: 1000 = posibilă trunchiere, restrânge filtrul]")
    else:
        print()

    for d in dosare[: args.max]:
        print("=" * 70)
        print(f"  {d.numar}   [{d.institutie}]  stadiu: {d.stadiu or '-'}")
        print(f"  categorie : {d.categorie or '-'}")
        print(f"  obiect    : {d.obiect or '-'}")
        print(f"  părți ({d.numar_parti}):")
        for p in d.parti[:8]:
            print(f"     - {p.calitate or '?':<14} {p.nume}")
        if d.numar_parti > 8:
            print(f"     ... și încă {d.numar_parti - 8}")
    if total > args.max:
        print("=" * 70)
        print(f"(afișate {args.max} din {total})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

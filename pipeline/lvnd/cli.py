"""Ligne de commande : lvnd download (build, check et sync-admin viendront à l'étape 2)."""

import argparse
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
RAW = RACINE / "data/raw"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="lvnd", description=__doc__)
    sub = ap.add_subparsers(dest="commande", required=True)
    d = sub.add_parser("download", help="télécharge et extrait les dumps AN")
    d.add_argument("--raw", type=Path, default=RAW)
    d.add_argument("sources", nargs="*", help="clés de sources (défaut : toutes)")
    args = ap.parse_args(argv)

    if args.commande == "download":
        from . import sources
        sources.download(args.raw, args.sources or None)
    return 0


if __name__ == "__main__":
    sys.exit(main())

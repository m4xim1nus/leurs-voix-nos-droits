"""Ligne de commande : lvnd download | build | check | editorial | sync-admin."""

import argparse
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
RAW = RACINE / "data/raw"
SQLITE = RACINE / "data/lvnd.sqlite"
EXPORT = RACINE / "data/export"
ADMIN = RACINE / "admin"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="lvnd", description=__doc__)
    sub = ap.add_subparsers(dest="commande", required=True)
    d = sub.add_parser("download", help="télécharge et extrait les dumps AN")
    d.add_argument("--raw", type=Path, default=RAW)
    d.add_argument("sources", nargs="*", help="clés de sources (défaut : toutes)")
    b = sub.add_parser("build", help="dumps → data/lvnd.sqlite + data/export/")
    b.add_argument("--raw", type=Path, default=RAW)
    b.add_argument("--sqlite", type=Path, default=SQLITE)
    b.add_argument("--export", type=Path, default=EXPORT)
    c = sub.add_parser("check", help="invariants et textes témoins sur la base produite")
    c.add_argument("--sqlite", type=Path, default=SQLITE)
    e = sub.add_parser("editorial", help="écrit data/editorial.json depuis referentiels/temoins.yaml (amorçage)")
    e.add_argument("--force", action="store_true", help="écrase un editorial.json existant")
    s = sub.add_parser("sync-admin", help="pousse le catalogue (data/export/) dans la base D1 de l'admin")
    cible = s.add_mutually_exclusive_group(required=True)
    cible.add_argument("--local", dest="cible", action="store_const", const="local", help="D1 locale (wrangler dev)")
    cible.add_argument("--remote", dest="cible", action="store_const", const="remote", help="D1 en ligne")
    cible.add_argument("--sql", dest="cible", action="store_const", const="sql", help="écrit le script SQL seulement")
    s.add_argument("--editorial", action="store_true",
                   help="ajoute les qualifications publiées absentes de D1 (sans écraser de brouillon)")
    s.add_argument("--export", type=Path, default=EXPORT)
    s.add_argument("--sortie", type=Path, help="chemin du script SQL (défaut : admin/.wrangler/sync-admin.sql)")
    args = ap.parse_args(argv)

    if args.commande == "download":
        from . import sources
        sources.download(args.raw, args.sources or None)
    elif args.commande == "build":
        from . import build
        build.build(args.raw, args.sqlite, args.export)
    elif args.commande == "check":
        from . import check
        ok, lignes = check.verifier(args.sqlite)
        print("\n".join(lignes))
        print("\nTous les contrôles passent." if ok else "\nCONTRÔLE EN ÉCHEC.", file=sys.stderr)
        return 0 if ok else 1
    elif args.commande == "editorial":
        from . import editorial, referentiels
        if editorial.CHEMIN.exists() and not args.force:
            print(f"{editorial.CHEMIN} existe déjà (--force pour l'écraser)", file=sys.stderr)
            return 1
        editorial.CHEMIN.write_text(editorial.serialiser(editorial.depuis_temoins(referentiels.temoins())))
        print(editorial.CHEMIN, file=sys.stderr)
    elif args.commande == "sync-admin":
        from . import sync_admin
        sync_admin.sync(args.export, ADMIN, args.cible, args.editorial, args.sortie)
    return 0


if __name__ == "__main__":
    sys.exit(main())

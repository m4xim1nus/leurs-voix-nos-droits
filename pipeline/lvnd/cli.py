"""Ligne de commande : lvnd download | archiver | build | check | editorial | scores | annuaire | sync-admin."""

import argparse
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
RAW = RACINE / "data/raw"
SQLITE = RACINE / "data/lvnd.sqlite"
EXPORT = RACINE / "data/export"
ANNUAIRE = RACINE / "data/annuaire"
ADMIN = RACINE / "admin"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="lvnd", description=__doc__)
    sub = ap.add_subparsers(dest="commande", required=True)
    d = sub.add_parser("download", help="télécharge et extrait les dumps AN")
    d.add_argument("--raw", type=Path, default=RAW)
    d.add_argument("--secours-max", type=int, metavar="MINUTES",
                   help="durée maximale du plan B amendement par amendement (repris au lancement suivant)")
    d.add_argument("--leger", action="store_true",
                   help="passe quotidienne : dossiers, scrutins, agenda et Dosleg seulement, archives déjà là pour le reste")
    d.add_argument("sources", nargs="*", help="clés de sources (défaut : toutes)")
    ar = sub.add_parser("archiver", help="zip d'une source figée, à verser dans la release donnees-figees")
    ar.add_argument("source", help="clé de la source (an_amendements_16)")
    ar.add_argument("--raw", type=Path, default=RAW)
    ar.add_argument("--sortie", type=Path, required=True)
    b = sub.add_parser("build", help="dumps → data/lvnd.sqlite + data/export/")
    b.add_argument("--raw", type=Path, default=RAW)
    b.add_argument("--sqlite", type=Path, default=SQLITE)
    b.add_argument("--export", type=Path, default=EXPORT)
    c = sub.add_parser("check", help="invariants et textes témoins sur la base produite")
    c.add_argument("--sqlite", type=Path, default=SQLITE)
    e = sub.add_parser("editorial", help="écrit data/editorial.json depuis referentiels/temoins.yaml (amorçage)")
    e.add_argument("--force", action="store_true", help="écrase un editorial.json existant")
    sc = sub.add_parser("scores", help="recalcule les scores depuis data/export/ et data/editorial.json (sans dump)")
    sc.add_argument("--export", type=Path, default=EXPORT)
    an_ = sub.add_parser("annuaire", help="code postal → circonscription et courriels des députés → data/annuaire/")
    an_.add_argument("--raw", type=Path, default=RAW)
    an_.add_argument("--sortie", type=Path, default=ANNUAIRE)
    s = sub.add_parser("sync-admin", help="pousse le catalogue (data/export/) dans la base D1 de l'admin")
    cible = s.add_mutually_exclusive_group(required=True)
    cible.add_argument("--local", dest="cible", action="store_const", const="local", help="D1 locale (wrangler dev)")
    cible.add_argument("--remote", dest="cible", action="store_const", const="remote", help="D1 en ligne")
    cible.add_argument("--sql", dest="cible", action="store_const", const="sql", help="écrit le script SQL seulement")
    s.add_argument("--editorial", action="store_true",
                   help="ajoute les qualifications publiées absentes de D1 (sans écraser de brouillon)")
    s.add_argument("--brouillons", type=Path, metavar="DOSSIER",
                   help="ajoute seulement les qualifications préparées dans DOSSIER/*.yaml (à relire), "
                        "sans toucher au catalogue ni écraser une qualification existante")
    s.add_argument("--valider", metavar="COMMENTAIRE",
                   help="avec --brouillons : écrit ces qualifications au statut validé (ou écarté), sur décision "
                        "explicite de Max ; COMMENTAIRE va dans la révision")
    s.add_argument("--ecarter-publie", action="store_true",
                   help="avec --valider : autorise à écarter un texte publié comme qualifié (refusé sinon)")
    s.add_argument("--remplacer", metavar="COMMENTAIRE",
                   help="avec --brouillons : remplace les qualifications existantes (requalification) et les "
                        "repasse à relire ; COMMENTAIRE va dans la révision")
    s.add_argument("--complet", action="store_true",
                   help="efface et réécrit tout le catalogue (≈ 80 000 lignes écrites) au lieu des seules différences")
    s.add_argument("--simuler", action="store_true",
                   help="sync incrémental : affiche le nombre de lignes à écrire, sans rien écrire")
    s.add_argument("--export", type=Path, default=EXPORT)
    s.add_argument("--sortie", type=Path, help="chemin du script SQL (défaut : admin/.wrangler/sync-admin.sql)")
    args = ap.parse_args(argv)

    if args.commande == "download":
        from . import sources
        sources.download(args.raw, args.sources or None, args.secours_max and args.secours_max * 60, args.leger)
    elif args.commande == "archiver":
        from . import sources
        n, sha = sources.archiver(args.raw, args.source, args.sortie)
        print(f"{args.sortie} : {n:,} fichiers, sha256 {sha}")
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
    elif args.commande == "scores":
        from . import editorial, scores
        qualif = editorial.charger()
        sc = scores.depuis_export(args.export, qualif)
        scores.ecrire(args.export, sc)
        print(f"{len(qualif['textes'])} textes qualifiés, {len(sc['scores_scrutins'])} lignes de scrutins comptés, "
              f"{len(sc['scores_deputes'])} scores de députés, {len(sc['scores_groupes'])} de groupes, "
              f"{len(sc['participation'])} taux de participation", file=sys.stderr)
    elif args.commande == "annuaire":
        from . import annuaire
        annuaire.annuaire(args.raw, args.sortie)
    elif args.commande == "sync-admin":
        from . import sync_admin
        sync_admin.sync(args.export, ADMIN, args.cible, args.editorial, args.sortie, args.brouillons, args.valider,
                        args.complet, args.simuler, args.remplacer, args.ecarter_publie)
    return 0


if __name__ == "__main__":
    sys.exit(main())

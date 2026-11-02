"""Ligne de commande : lvnd download | archiver | build | check | editorial | scores | annuaire | sync-admin | proposer."""

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
    d = sub.add_parser("download", help="télécharge et extrait les dumps AN et Sénat")
    d.add_argument("--raw", type=Path, default=RAW)
    d.add_argument("--secours-max", type=int, metavar="MINUTES",
                   help="durée maximale du plan B amendement par amendement (repris au lancement suivant)")
    d.add_argument("--leger", action="store_true",
                   help="passe quotidienne : dossiers, scrutins, agenda, Dosleg et sénateurs seulement, archives déjà là pour le reste")
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
    e.add_argument("--ajouter", type=Path, metavar="DOSSIER",
                   help="ajoute à editorial.json les brouillons DOSSIER/*.yaml validés par Max, sans passer par l'admin")
    e.add_argument("--remplacer", action="store_true", help="avec --ajouter : remplace un texte déjà présent")
    e.add_argument("--export", type=Path, default=EXPORT)
    sc = sub.add_parser("scores", help="recalcule les scores depuis data/export/ et data/editorial.json (sans dump)")
    sc.add_argument("--export", type=Path, default=EXPORT)
    an_ = sub.add_parser("annuaire", help="code postal → circonscription et département, courriels des députés → data/annuaire/")
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
    s.add_argument("--recherche", action="store_true",
                   help="reprise unique de referentiels/termes_recherche.yaml dans le bloc `recherche` des documents de D1 "
                        "(sans toucher aux statuts ; à publier ensuite dans l'admin)")
    s.add_argument("--complet", action="store_true",
                   help="efface et réécrit tout le catalogue (≈ 80 000 lignes écrites) au lieu des seules différences")
    s.add_argument("--simuler", action="store_true",
                   help="sync incrémental seul : affiche le nombre de lignes à écrire, sans rien écrire (refusé avec --brouillons, --valider, --complet ou --sql)")
    s.add_argument("--export", type=Path, default=EXPORT)
    s.add_argument("--sortie", type=Path, help="chemin du script SQL (défaut : admin/.wrangler/sync-admin.sql)")
    pr = sub.add_parser("proposer", help="proposition de qualification par LLM pour des dossiers (brouillons YAML, "
                                         "contrôlés ; ni validés ni publiés)")
    pr.add_argument("dossiers", nargs="*", metavar="DOSSIER", help="dossier AN (DLR5L17N…)")
    pr.add_argument("--alertes", action="store_true",
                    help="une proposition par nouvelle alerte, écrite dans D1 (table propositions) : Action propositions.yml")
    pr.add_argument("--types",
                    help="avec --alertes : types d'alerte retenus, séparés par des virgules (défaut : tous)")
    pr.add_argument("--max", type=int, default=5, help="avec --alertes : propositions par passe (défaut : 5)")
    cible_p = pr.add_mutually_exclusive_group()
    cible_p.add_argument("--local", dest="cible", action="store_const", const="local",
                         help="réglages et journal dans la D1 locale (défaut : en ligne)")
    cible_p.add_argument("--remote", dest="cible", action="store_const", const="remote")
    pr.set_defaults(cible="remote")
    pr.add_argument("--mode", choices=("complet", "ecart", "requalification", "suivi", "senat"),
                    help="défaut : d'après la dernière alerte du dossier (en_cours_alertes.csv)")
    pr.add_argument("--a-blanc", action="store_true",
                    help="sans la version publiée ni l'alerte (mesure de l'accord, item 4) : mode complet")
    pr.add_argument("--tache", default="proposition", help="libellé du journal des appels (défaut : proposition)")
    pr.add_argument("--sortie", type=Path, help="dossier des brouillons (défaut : source/propositions/AAAA-MM-JJ)")
    pr.add_argument("--prompt", action="store_true", help="écrit le prompt dans --sortie, sans aucun appel")
    pr.add_argument("--export", type=Path, default=EXPORT)
    v = sub.add_parser("veille", help="veille des sources : flux de referentiels/sources_veille.yaml, rapprochés des "
                                      "textes publiés par le LLM ; une proposition par correspondance, écrite dans D1")
    cible_v = v.add_mutually_exclusive_group()
    cible_v.add_argument("--local", dest="cible", action="store_const", const="local")
    cible_v.add_argument("--remote", dest="cible", action="store_const", const="remote")
    v.set_defaults(cible="remote")
    v.add_argument("--jours", type=int, default=8, help="publications des N derniers jours (défaut : 8)")
    v.add_argument("--max", type=int, default=3, help="propositions au plus (défaut : 3)")
    v.add_argument("--simuler", action="store_true", help="lit les flux et compte les publications, sans appel au LLM")
    v.add_argument("--essai", action="store_true", help="passage à la main, même si la liste des flux n'est pas validée")
    v.add_argument("--export", type=Path, default=EXPORT)
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
        if args.ajouter:
            import polars as pl
            import yaml
            from . import check
            brouillons = [yaml.safe_load(f.read_text()) for f in sorted(args.ajouter.glob("*.yaml"))]
            colonnes = ("id", "dossier_id", "etape", "objet", "pour", "contre")
            infos = {r["id"]: {**r, "division": None} for r in pl.read_csv(args.export / "scrutins.csv", infer_schema_length=None)
                     .select(colonnes).iter_rows(named=True)}
            senat = {r["id"]: r for r in pl.read_csv(args.export / "senat/scrutins.csv", infer_schema_length=None)
                     .select("id", "dossier_id", "objet", "pour", "contre").iter_rows(named=True)}
            doc, changes = editorial.ajouter(editorial.charger(), brouillons, infos, senat, args.remplacer)
            contenu = editorial.serialiser(doc)
            if trouves := check.termes_interdits(contenu):
                print(f"{len(trouves)} terme(s) interdit(s) : rien n'est écrit", file=sys.stderr)
                return 1
            editorial.CHEMIN.write_text(contenu)
            print("\n".join(changes) or "rien de nouveau", file=sys.stderr)
            print(f"{len(changes)} texte(s) écrit(s) dans {editorial.CHEMIN}", file=sys.stderr)
            return 0
        if editorial.CHEMIN.exists() and not args.force:
            print(f"{editorial.CHEMIN} existe déjà (--force pour l'écraser)", file=sys.stderr)
            return 1
        editorial.CHEMIN.write_text(editorial.serialiser(editorial.depuis_temoins(referentiels.temoins())))
        print(editorial.CHEMIN, file=sys.stderr)
    elif args.commande == "scores":
        from . import editorial, recherche, scores
        recherche.ecrire(args.export)
        qualif = editorial.charger()
        sc = scores.depuis_export(args.export, qualif)
        scores.ecrire(args.export, sc)
        sc_senat = scores.senat_depuis_export(args.export, qualif)
        scores.ecrire_senat(args.export, sc_senat)
        print(f"Sénat : {len({l['texte_id'] for l in sc_senat['scores_scrutins']})} décisifs, "
              f"{len(sc_senat['scores_senateurs'])} scores de sénateurs, {len(sc_senat['scores_groupes'])} de groupes",
              file=sys.stderr)
        print(f"{len(qualif['textes'])} textes qualifiés, {len(sc['scores_scrutins'])} lignes de scrutins comptés, "
              f"{len(sc['scores_deputes'])} scores de députés, {len(sc['scores_groupes'])} de groupes, "
              f"{len(sc['participation'])} taux de participation", file=sys.stderr)
    elif args.commande == "annuaire":
        from . import annuaire
        annuaire.annuaire(args.raw, args.sortie)
    elif args.commande == "sync-admin":
        from . import sync_admin
        sync_admin.sync(args.export, ADMIN, args.cible, args.editorial, args.sortie, args.brouillons, args.valider,
                        args.complet, args.simuler, args.remplacer, args.ecarter_publie, args.recherche)
    elif args.commande == "veille":
        from . import veille
        return veille.lancer(args.export, ADMIN, args.cible, args.jours, args.max, args.simuler, args.essai)
    elif args.commande == "proposer":
        from . import propositions
        if args.alertes:
            if args.dossiers:
                ap.error("--alertes ne prend pas de dossier")
            return propositions.lancer_alertes(args.export, ADMIN, args.cible, set(args.types.split(",")) if args.types else set(propositions.proposer.MODES), args.max)
        if not args.dossiers:
            ap.error("un dossier au moins, ou --alertes")
        return propositions.lancer(args.dossiers, args.export, ADMIN, args.cible, args.mode, args.a_blanc,
                                   args.tache, args.sortie, args.prompt)
    return 0


if __name__ == "__main__":
    sys.exit(main())

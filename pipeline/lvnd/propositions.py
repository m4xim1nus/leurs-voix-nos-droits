"""`lvnd proposer` : propositions par LLM pour une liste de dossiers, contrôlées, écrites en brouillons YAML.

Chaque brouillon porte, sous `relecture`, son origine (« proposition LLM », modèle, date, coût) et le résultat
des contrôles sans LLM. Rien n'est chargé dans l'admin ni publié ici : un brouillon se charge « à relire »
par le circuit habituel (`lvnd sync-admin --brouillons`), après lecture.
"""

import sys
from datetime import date
from pathlib import Path

import polars as pl
import yaml

from . import controles, editorial, llm, proposer

RACINE = Path(__file__).resolve().parents[2]


def derniere_alerte(export: Path, dossier: str) -> dict | None:
    f = export / "en_cours_alertes.csv"
    if not f.exists():
        return None
    df = pl.read_csv(f, infer_schema=False).filter(pl.col("dossier_id") == dossier).sort("date")
    return df.row(-1, named=True) if df.height else None


def preparer(export: Path, dossier: str, mode: str | None, a_blanc: bool, publication: dict):
    """Mode, alerte et version publiée à donner au LLM."""
    if a_blanc:
        return "complet", None, None
    alerte = derniere_alerte(export, dossier)
    version = proposer.publie(dossier, publication)
    if mode is None:
        if alerte is None:
            raise SystemExit(f"{dossier} : aucune alerte en cours ; préciser --mode (ou --a-blanc)")
        mode = proposer.MODES[alerte["type"]]
    return mode, alerte, version


def brouillon(p: proposer.Proposition, r: controles.Resultat | None, modele: str) -> dict:
    """Le brouillon écrit sur disque : celui du LLM, `relecture` complétée."""
    doc = dict(p.doc or {"dossier_an": p.dossier_an, "statut": "echec"})
    relecture = dict(doc.get("relecture") or {})
    relecture["origine"] = (f"proposition LLM ({modele}, {date.today().strftime('%d/%m/%Y')}, mode {p.mode}, "
                            f"{p.appels} appel(s), {p.cout_usd:.2f} $)")
    if p.echec:
        relecture["echec"] = p.echec
    if r is not None:
        relecture["controles"] = r.dict()
    relecture["documents_lus"] = sorted(p.documents)
    doc["relecture"] = relecture
    return doc


def lancer(dossiers: list[str], export: Path, admin: Path, cible: str, mode: str | None, a_blanc: bool, tache: str,
           sortie: Path | None, prompt_seul: bool) -> int:
    sortie = sortie or RACINE / "source/propositions" / date.today().isoformat()
    sortie.mkdir(parents=True, exist_ok=True)
    publication = editorial.charger()

    if prompt_seul:
        systeme = proposer.contexte_fixe()
        (sortie / "prompt-systeme.md").write_text(systeme)
        for d in dossiers:
            m, alerte, version = preparer(export, d, mode, a_blanc, publication)
            (sortie / f"prompt-{d}.md").write_text(
                proposer.message_tache(export, d, m, alerte, version, date.today().isoformat()))
        print(f"prompts écrits dans {sortie} (système : {len(systeme):,} caractères), aucun appel", file=sys.stderr)
        return 0

    try:
        session = llm.Session(llm.D1(cible, admin), tache)
    except llm.Indisponible as ex:
        print(f"aucune proposition : {ex}", file=sys.stderr)
        return 0
    infos_an, infos_senat = controles.infos_scrutins(export)
    ids = controles.publies_ids(publication)
    code = 0
    for d in dossiers:
        m, alerte, version = preparer(export, d, mode, a_blanc, publication)
        try:
            p = proposer.proposer(session, export, d, m, alerte, version)
        except llm.Indisponible as ex:
            print(f"{d} : arrêt, {ex}", file=sys.stderr)
            break
        except Exception as ex:  # erreur d'API : journalisée par la session ; on passe au dossier suivant
            print(f"{d} : erreur, {type(ex).__name__} : {str(ex)[:200]}", file=sys.stderr)
            code = 1
            continue
        r = None
        if p.doc is not None:
            r = controles.controler(p.doc, p.yaml_brut, d, infos_an, infos_senat, ids, p.documents)
        doc = brouillon(p, r, session.modele)
        nom = (p.doc or {}).get("id") or d
        f = sortie / f"{nom}.yaml"
        f.write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False, width=1000))
        etat = p.echec or ("contrôles passés" if r.ok else f"{len(r.erreurs)} erreur(s) de contrôle")
        print(f"{d} [{m}] → {f.relative_to(RACINE) if f.is_relative_to(RACINE) else f} : {etat}, "
              f"{p.cout_usd:.2f} $", file=sys.stderr)
        for e in (r.erreurs if r else []):
            print(f"   ERREUR {e}", file=sys.stderr)
    print(f"dépense du mois : {session.depense:.2f} $ sur {session.reglages.plafond_usd:.2f} $", file=sys.stderr)
    return code

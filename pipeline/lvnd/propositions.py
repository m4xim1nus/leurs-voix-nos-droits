"""`lvnd proposer` : propositions par LLM pour une liste de dossiers, contrôlées, écrites en brouillons YAML.

Chaque brouillon porte, sous `relecture`, son origine (« proposition LLM », modèle, date, coût) et le résultat
des contrôles sans LLM. Rien n'est chargé dans l'admin ni publié ici : un brouillon se charge « à relire »
par le circuit habituel (`lvnd sync-admin --brouillons`), après lecture.
"""

import json
import sys
from datetime import date
from pathlib import Path

import polars as pl
import yaml

from . import alertes as alertes_
from . import controles, editorial, llm, proposer, sync_admin

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


# File des alertes (item 5) ---------------------------------------------------------------------

def reste_a_traiter(a: dict, statut: str | None, doc: str | None, motif: str | None = None) -> bool:
    """L'alerte reste-t-elle à traiter, vu la qualification de D1 ? Même règle que l'admin
    (admin/src/lib/alertes.ts, `resteATraiter`)."""
    t = a["type"]
    q = json.loads(doc) if doc else {}
    if t in ("unanimite_contestee", "ecart_revote"):
        return statut == "ecarte"
    if t == "vote_posterieur":
        return not doc or not any(s["id"] == a.get("scrutin_id") for s in q.get("scrutins") or [])
    if t == "lecture_posterieure":
        if not doc:
            return True
        jour = "/".join(reversed(a["date"][:10].split("-")))
        return not ((a.get("scrutin_id") and any(s["id"] == a["scrutin_id"] for s in q.get("scrutins") or []))
                    or jour in (q.get("note") or ""))
    if t in ("senat_premier_vote", "senat_vote_posterieur"):
        if statut == "ecarte" and not alertes_.SANS_VOTE_AN.search(motif or ""):
            return False
        senat = q.get("senat") if doc else None
        if t == "senat_premier_vote":
            return not senat
        return not any(s["id"] == a.get("scrutin_id") for s in (senat or {}).get("scrutins") or [])
    if t in ("premier_decisif", "vote_sans_decisif"):
        return statut in (None, "a-suivre")
    return statut is None


def alertes_a_proposer(export: Path, d1, types: set[str]) -> list[dict]:
    """Alertes en cours, encore à traiter dans D1, d'un type retenu, et sans proposition déjà faite (jamais
    recalculée, réussie ou non)."""
    f = export / "en_cours_alertes.csv"
    if not f.exists():
        return []
    alertes = [a for a in pl.read_csv(f, infer_schema=False).sort("date").iter_rows(named=True) if a["type"] in types]
    if not alertes:
        return []
    faites = {r["alerte_id"] for r in d1.lire("SELECT alerte_id FROM propositions")}
    qualifs = {r["dossier_an"]: (r["statut"], r["doc"], r["motif_ecart"]) for r in d1.lire(
        "SELECT dossier_an, statut, doc, motif_ecart FROM qualifications WHERE dossier_an IN ("
        + ", ".join(f"'{a['dossier_id']}'" for a in alertes) + ")")}
    return [a for a in alertes if a["id"] not in faites
            and reste_a_traiter(a, *qualifs.get(a["dossier_id"], (None, None, None)))]


def ligne_d1(alerte: dict, p: proposer.Proposition, r: controles.Resultat | None, modele: str) -> dict:
    doc = brouillon(p, r, modele)
    relecture = doc.pop("relecture")
    if p.echec or r is None:
        statut, motif = "echec", p.echec or "aucun brouillon"
    elif not r.ok:
        statut, motif = "echec", f"{len(r.erreurs)} erreur(s) de contrôle"
    else:
        statut, motif = "proposee", None
    return {"alerte_id": alerte["id"], "dossier_an": p.dossier_an, "mode": p.mode, "date": llm.maintenant(),
            "modele": modele, "cout_usd": round(p.cout_usd, 6),
            "doc": json.dumps(doc, ensure_ascii=False, default=str) if p.doc else None,
            "relecture": json.dumps(relecture, ensure_ascii=False, default=str), "statut": statut, "motif": motif}


COLONNES_D1 = ("alerte_id", "dossier_an", "mode", "date", "modele", "cout_usd", "doc", "relecture", "statut", "motif")


def lancer_alertes(export: Path, admin: Path, cible: str, types: set[str], maximum: int) -> int:
    """Propositions pour les nouvelles alertes (Action `propositions.yml`), écrites dans D1. Ne fait jamais
    échouer la passe : LLM coupé, plafond atteint ou erreur d'API arrêtent les propositions, sans plus."""
    d1 = llm.D1(cible, admin)
    try:
        session = llm.Session(d1, "proposition")
    except llm.Indisponible as ex:
        print(f"aucune proposition : {ex}", file=sys.stderr)
        return 0
    a_faire = alertes_a_proposer(export, d1, types)
    print(f"{len(a_faire)} alerte(s) sans proposition", file=sys.stderr)
    publication = editorial.charger()
    infos_an, infos_senat = controles.infos_scrutins(export)
    ids = controles.publies_ids(publication)
    for a in a_faire[:maximum]:
        d = a["dossier_id"]
        version = proposer.publie(d, publication)
        try:
            p = proposer.proposer(session, export, d, proposer.MODES[a["type"]], a, version)
        except llm.Indisponible as ex:
            print(f"{a['id']} : arrêt, {ex}", file=sys.stderr)
            break
        except Exception as ex:  # erreur d'API, journalisée par la session : on réessaiera à la passe suivante
            print(f"{a['id']} : erreur, {type(ex).__name__} : {str(ex)[:200]}", file=sys.stderr)
            continue
        r = None
        if p.doc is not None:
            r = controles.controler(p.doc, p.yaml_brut, d, infos_an, infos_senat, ids, p.documents)
        ligne = ligne_d1(a, p, r, session.modele)
        d1.ecrire(sync_admin.inserts("propositions", COLONNES_D1, [ligne])[0])
        print(f"{a['id']} → {ligne['statut']}{' : ' + ligne['motif'] if ligne['motif'] else ''}, "
              f"{p.cout_usd:.2f} $", file=sys.stderr)
    if len(a_faire) > maximum:
        print(f"{len(a_faire) - maximum} alerte(s) reportée(s) à la passe suivante (--max {maximum})", file=sys.stderr)
    print(f"dépense du mois : {session.depense:.2f} $ sur {session.reglages.plafond_usd:.2f} $", file=sys.stderr)
    return 0

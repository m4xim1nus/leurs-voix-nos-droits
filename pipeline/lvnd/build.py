"""Build : dumps → data/lvnd.sqlite (local) + data/export/ (CSV et JSON versionnés)."""

import json
import shutil
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

import polars as pl

from . import agenda, amendements, an, candidats, editorial, encours, parcours, positions, referentiels, scores, senat, textes
from .sources import lire_manifeste, racine

# Votes nominatifs compacts (docs/SOURCES.md) : numéro de scrutin, identifiant numérique du
# député (PA123 → 123), position en une lettre.
CODES = {"pour": "P", "contre": "C", "abstention": "A", "non_votant": "N"}


def _log(msg: str) -> None:
    print(msg, file=sys.stderr)


def _df(rows: list[dict]) -> pl.DataFrame:
    return pl.DataFrame(rows, infer_schema_length=None)


# --- SQLite ----------------------------------------------------------------------

TYPES = {pl.Int64: "INTEGER", pl.Int32: "INTEGER", pl.UInt32: "INTEGER", pl.Float64: "REAL", pl.Boolean: "INTEGER"}
CLES = {"scrutins": "id", "textes": "id", "deputes": "id", "mandats": "id", "groupes": "id", "amendements": "id",
        "en_cours": "id", "en_cours_etats": "id"}
INDEX = ("positions_groupes(scrutin_id)", "votes(scrutin_id)", "votes(acteur_id)", "scrutins(dossier_id)",
         "mandats(acteur_id)", "appartenances(acteur_id)", "scores_deputes(acteur_id)")


def _ecrire_sqlite(chemin: Path, tables: dict[str, pl.DataFrame]) -> None:
    tmp = chemin.with_suffix(".tmp")
    tmp.unlink(missing_ok=True)
    con = sqlite3.connect(tmp)
    for nom, df in tables.items():
        cols = []
        for c, t in df.schema.items():
            sql = f'"{c}" {TYPES.get(t, "TEXT")}'
            if CLES.get(nom) == c:
                sql += " PRIMARY KEY"
            cols.append(sql)
        con.execute(f"CREATE TABLE {nom} ({', '.join(cols)})")
        lignes = [tuple(int(v) if isinstance(v, bool) else v for v in r) for r in df.iter_rows()]
        con.executemany(f"INSERT INTO {nom} VALUES ({', '.join('?' * df.width)})", lignes)
    for idx in INDEX:
        con.execute(f"CREATE INDEX IF NOT EXISTS i_{idx.replace('(', '_').rstrip(')')} ON {idx}")
    con.commit()
    con.execute("VACUUM")
    con.close()
    tmp.replace(chemin)


def _ecrire_votes(export: Path, votes: pl.DataFrame, scr: pl.DataFrame) -> int:
    """Un CSV par législature et par mois : votes/<législature>/<AAAA-MM>.csv, trié."""
    v = (votes.join(scr.select("id", "legislature", "numero", "date"), left_on="scrutin_id", right_on="id")
         .select("legislature", pl.col("date").str.slice(0, 7).alias("mois"), pl.col("numero").alias("scrutin"),
                 pl.col("acteur_id").str.slice(2).cast(pl.Int32).alias("acteur"),
                 pl.col("position").replace_strict(CODES))
         .sort("legislature", "scrutin", "acteur"))
    n = 0
    for (leg, mois), part in v.group_by("legislature", "mois", maintain_order=True):
        d = export / "votes" / str(leg)
        d.mkdir(parents=True, exist_ok=True)
        part.select("scrutin", "acteur", "position").write_csv(d / f"{mois}.csv")
        n += 1
    return n


# --- Build ----------------------------------------------------------------------

def date_reference(raw: Path) -> str:
    """Date de l'instantané : téléchargement du dump des dossiers AN de la législature en cours. Elle
    fixe l'« aujourd'hui » des textes en cours (inactivité, séances à venir), pour un build reproductible."""
    return lire_manifeste(raw)[f"an_dossiers_{max(an.LEGISLATURES)}"]["telecharge_le"][:10]


def build(raw: Path, sqlite: Path, export: Path) -> None:
    _log("== Dossiers")
    dossier_de, titres = textes.documents(raw)
    dossiers = textes.tous_dossiers(raw)
    titre_de = {u: d["titreDossier"]["titre"] for u, d in dossiers.items()}
    _log(f"   {len(dossiers)} dossiers, {len(dossier_de)} documents")

    scr, ventil, votes, mises, amdts, par_amdt = [], [], [], [], [], {}
    for leg in an.LEGISLATURES:
        _log(f"== Scrutins XV{'I' * (leg - 15)}e")
        r = an.scrutins(raw, leg)
        scr += r["scrutins"]
        ventil += r["ventilations"]
        votes += r["votes"]
        mises += r["mises_au_point"]
        _log(f"   {len(r['scrutins']):,} scrutins, {len(r['votes']):,} votes nominatifs, "
             f"{len(r['mises_au_point']):,} mises au point")
        if not (racine(raw, f"an_amendements_{leg}") / "json").exists():
            _log(f"   ATTENTION : amendements XV{'I' * (leg - 15)}e absents (lancer `lvnd download "
                 f"an_amendements_{leg}`), scrutins sur amendement rattachés par la séance seulement")
            continue
        a = amendements.lire(raw, leg, dossier_de)
        amdts.append(a)
        par_amdt |= amendements.rattacher(r["scrutins"], a, titre_de)

    _log("== Rattachement des scrutins aux dossiers")
    liens = textes.rattacher(scr, dossiers, titres, par_amdt)
    for s in scr:
        lien = liens.get(s["id"], {})
        s["dossier_id"] = lien.get("dossier_id")
        s["etape"] = lien.get("etape")
        s["rattachement"] = lien.get("rattachement")
        s["amendement_id"] = (par_amdt.get(s["id"]) or {}).get("amendement_id")
    _log(f"   {len(liens):,} scrutins rattachés sur {len(scr):,}")

    _log("== Où en est chaque texte (Dosleg)")
    tables = senat.dosleg(raw)
    idx = parcours.Index(scr, senat.scrutins(tables).to_dicts())
    classes, exclus = parcours.classer(dossiers, titres, idx, senat.lois(tables))
    date_ref = date_reference(raw)
    points = agenda.points(raw, date_ref)
    en_cours, lect_ec, evt_ec, etats = encours.textes(
        classes, idx, {"decisions": senat.decisions_seance(tables), "activite": senat.activite(tables),
                       "seances": senat.seances(tables), "etats": senat.etats(tables)}, exclus, date_ref, points)
    _log(f"   {sum(not t['motif_ecart'] for t in en_cours)} textes en cours au {date_ref}, "
         f"{sum(bool(t['motif_ecart']) for t in en_cours)} écartés, {len(points)} points d'agenda à venir")

    _log("== Catalogue des textes")
    # Les textes en cours ou inscrits entrent au catalogue même sans scrutin public à l'AN.
    suivis = {t["id"] for t in en_cours if not t["motif_ecart"]} | {p["dossier_id"] for p in points}
    cat = textes.catalogue(dossiers, scr, liens, suivis)
    candidats.annoter(cat, titres)
    ids = {t["id"] for t in cat}
    etats = [e for e in etats if e["id"] in ids]
    _log(f"   {len(cat)} textes, dont {sum(not t['n_scrutins'] for t in cat)} sans scrutin public à l'AN et "
         f"{sum(bool(t['droits_candidats'] or t['etiquettes_candidates']) for t in cat)} candidats par mots-clés")

    _log("== Députés et groupes")
    dep, mandats, appart = an.deputes(raw)
    grp = an.groupes(raw, {v["groupe_id"] for v in ventil} | {a["groupe_id"] for a in appart})
    pos = positions.positions(ventil)

    qualif = editorial.charger()
    _log(f"== Scores ({len(qualif['textes'])} textes qualifiés, "
         f"{'data/editorial.json' if editorial.CHEMIN.exists() else 'textes témoins'})")
    sc = scores.calculer(qualif, votes)

    amd = (amendements.utiles(pl.concat(amdts, how="diagonal"), {a["amendement_id"] for a in par_amdt.values()})
           if amdts else pl.DataFrame())
    scr_df = _df(scr)
    votes_df = _df(votes)
    dfs = {
        "textes": _df(cat),
        "scrutins": scr_df,
        "positions_groupes": _df(pos),
        "amendements": amd,
        "groupes": _df(grp),
        "deputes": _df(dep),
        "mandats": _df(mandats),
        "appartenances": _df(appart),
        "mises_au_point": _df(mises),
        **{k: _df(v) for k, v in sc.items()},
        # où en est chaque texte : à part, sans effet sur les scores (lvnd/encours.py)
        "en_cours": _df(en_cours),
        "en_cours_lectures": _df(lect_ec),
        "en_cours_evenements": _df(evt_ec),
        "en_cours_etats": _df(etats),
        "en_cours_agenda": _df(points),
    }

    _log("== Écriture")
    sqlite.parent.mkdir(parents=True, exist_ok=True)
    _ecrire_sqlite(sqlite, {**dfs, "votes": votes_df})
    if export.exists():
        shutil.rmtree(export)
    export.mkdir(parents=True)
    for nom, df in dfs.items():
        df.write_csv(export / f"{nom}.csv")
    n = _ecrire_votes(export, votes_df, scr_df)
    meta = {
        "genere_le": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sources": lire_manifeste(raw),
        "comptes": {**{k: v.height for k, v in dfs.items()}, "votes": votes_df.height, "fichiers_votes": n},
        "votes_codes": {v: k for k, v in CODES.items()},
        "referentiels": {n: referentiels.charger(n) for n in ("droits", "mots_cles")},
        "en_cours": {"date_reference": date_ref, "inactivite_mois": encours.INACTIVITE_MOIS, "debut": encours.DEBUT},
    }
    (export / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1, default=str) + "\n")
    _log(f"   {sqlite} ({sqlite.stat().st_size / 1e6:.1f} Mo), {export}/ ({n} fichiers de votes)")
    # Fichiers propres à `lvnd scores` (participation, scores par texte) : build.sh les recalcule
    # aussi, mais l'export versionné doit les contenir.
    scores.ecrire(export, scores.depuis_export(export, qualif))

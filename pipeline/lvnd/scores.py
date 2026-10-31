"""Scores calculés depuis une qualification (data/editorial.json, ou referentiels/temoins.yaml).

Pour chaque scrutin compté et chaque droit touché par le texte, un vote est *favorable aux
droits* ou *défavorable* :

- `pour: texte` (scrutin décisif) : voter pour soutient le texte, donc favorable si le texte
  étend le droit, défavorable s'il le restreint ;
- `pour: contre-texte` (amendement de suppression, motion) : l'inverse.

Le score d'un député (ou d'un groupe) sur un droit est la part pondérée de ses votes favorables
parmi ses votes comptés, de 0 à 100. Les règles de calcul (docs/METHODO.md, règles 14 à 19) sont
rassemblées dans `REGLES` : valeurs validées par Max le 29/10/2026. Les autres options restent disponibles pour simuler une variante.

`lvnd scores` (`depuis_export`) refait ce calcul sans dump, depuis data/export/ et
data/editorial.json (docs/CONCEPTION.md, choix F1) : les députés depuis les votes nominatifs
versionnés, les groupes depuis les ventilations officielles, comme l'aperçu de l'admin. Le
score d'un groupe agrège les votes de ses membres, ce que la ventilation donne directement.
build.sh l'exécute avant le build du site : une publication depuis l'admin met le site à jour.

Le Sénat a ses propres fichiers, dans data/export/senat/ (règle 26) : même calcul, sur son seul décisif.
Aucun score ne mélange les deux chambres (règle 28).
"""

import json
from collections import defaultdict
from pathlib import Path

import polars as pl

from .referentiels import lignee

# Les scores de groupe réunissent les organes d'une même lignée (referentiels/groupes.yaml).
# Comptés : le scrutin décisif et les amendements clés au sens fixé (docs/METHODO.md, règles 9 à 11).
COMPTES = {"decisif", "amendement"}

REGLES = {
    # Règle 16. "exclue" : l'abstention n'entre pas au dénominateur (affichée à part) ;
    # "demi" : elle compte pour moitié favorable.
    "abstention": "exclue",
    # Règle 17. Absents et non-votants (dont la présidence de séance) : hors du
    # calcul, affichés en taux de participation. Pas d'autre option envisagée.
    "absence": "exclue",
    # Règle 18. "texte" : chaque texte pèse 1, partagé entre le décisif (part `part_decisif`) et ses
    # amendements clés (le reste, à parts égales) ; "scrutin" : chaque scrutin compté pèse 1 ;
    # "decisif" : seul le décisif compte, les amendements clés sont affichés.
    "ponderation": "texte",
    "part_decisif": 0.5,
    # Règle 19, seule option implémentée. "vote" : un vote compte pour le groupe auquel le député
    # appartenait ce jour-là (ventilation officielle), réuni par lignée ; le score d'un député
    # réunit tous ses votes.
    "groupe": "vote",
    # Règle 15. "principal" : le score d'un droit ne prend que les textes dont c'est
    # le droit principal ; "tous" : aussi ceux où il est secondaire (avec le sens propre à ce droit).
    "droits": "tous",
}


def _favorable(sens: str, pour: str) -> str | None:
    """Position (« pour » / « contre ») favorable aux droits, ou None si le sens du scrutin n'est pas fixé."""
    if pour not in ("texte", "contre-texte"):
        return None
    soutien = "pour" if pour == "texte" else "contre"
    return soutien if sens == "etend" else {"pour": "contre", "contre": "pour"}[soutien]


def scrutins_comptes(temoins: dict, regles: dict) -> list[dict]:
    """Une ligne par (texte, scrutin compté, droit) : poids et position favorable."""
    out = []
    for t in temoins["textes"]:
        comptes = [s for s in t["scrutins"] if s["role"] in COMPTES and s["pour"] in ("texte", "contre-texte")]
        decisif = [s for s in comptes if s["role"] == "decisif"]
        if not decisif:
            continue  # adopté par 49.3 sans vote final : affiché, compté nulle part (règle 9)
        amdts = [s for s in comptes if s["role"] == "amendement"]
        if regles["ponderation"] == "decisif":
            amdts = []
        for s in decisif + amdts:
            if regles["ponderation"] == "scrutin":
                poids = 1.0
            elif s["role"] == "decisif":
                poids = regles["part_decisif"] if amdts else 1.0
            else:
                poids = (1 - regles["part_decisif"]) / len(amdts)
            for d in t["droits"]:
                if regles["droits"] == "principal" and d["role"] != "principal":
                    continue
                out.append({"texte_id": t["id"], "scrutin_id": s["id"], "role": s["role"], "droit": d["code"],
                            "droit_role": d["role"], "sens": d["sens"], "poids": poids,
                            "favorable": _favorable(d["sens"], s["pour"])})
            principal = next(d for d in t["droits"] if d["role"] == "principal")
            out.append({"texte_id": t["id"], "scrutin_id": s["id"], "role": s["role"], "droit": "global",
                        "droit_role": "principal", "sens": principal["sens"], "poids": poids,
                        "favorable": _favorable(principal["sens"], s["pour"])})
    return out


def _valeur(position: str, favorable: str, regles: dict) -> float | None:
    """Valeur d'un vote : 1 favorable, 0 défavorable, None hors calcul."""
    if position in ("pour", "contre"):
        return 1.0 if position == favorable else 0.0
    if position == "abstention":
        return 0.5 if regles["abstention"] == "demi" else None
    return None  # non-votant


def _agreger(lignes: list[tuple], cle) -> list[dict]:
    """lignes : (entité, droit, texte, poids, valeur, position, nombre de votes identiques)."""
    acc: dict[tuple, dict] = defaultdict(lambda: {"num": 0.0, "den": 0.0, "textes": set(), "pour_droits": 0,
                                                  "contre_droits": 0, "abstentions": 0, "non_votants": 0})
    for ent, droit, texte, poids, valeur, position, n in lignes:
        a = acc[(ent, droit)]
        a["textes"].add(texte)
        if valeur is not None:
            a["num"] += n * poids * valeur
            a["den"] += n * poids
        if position == "abstention":
            a["abstentions"] += n
        elif position == "non_votant":
            a["non_votants"] += n
        elif valeur == 1.0:
            a["pour_droits"] += n
        elif valeur == 0.0:
            a["contre_droits"] += n
    return [{cle: ent, "droit": droit, "n_textes": len(a["textes"]), "votes_favorables": a["pour_droits"],
             "votes_defavorables": a["contre_droits"], "abstentions": a["abstentions"],
             "non_votants": a["non_votants"],
             "score": round(100 * a["num"] / a["den"], 1) if a["den"] else None}
            for (ent, droit), a in sorted(acc.items())]


def _lignes(comptes: list[dict], votes: list[dict], regles: dict,
            ventilations: list[dict] | None) -> tuple[list[tuple], list[tuple]]:
    """Lignes à agréger (voir `_agreger`) des députés et des groupes."""
    par_scrutin: dict[str, list[dict]] = defaultdict(list)
    for c in comptes:
        par_scrutin[c["scrutin_id"]].append(c)
    lignes_dep, lignes_grp = [], []
    for v in votes:
        for c in par_scrutin.get(v["scrutin_id"], ()):
            if c["favorable"] is None:
                continue
            val = _valeur(v["position"], c["favorable"], regles)
            lignes_dep.append((v["acteur_id"], c["droit"], c["texte_id"], c["poids"], val, v["position"], 1))
            if ventilations is None:
                lignes_grp.append((lignee(v["groupe_id"]), c["droit"], c["texte_id"], c["poids"], val,
                                   v["position"], 1))
    for g in ventilations or ():
        for c in par_scrutin.get(g["scrutin_id"], ()):
            if c["favorable"] is None:
                continue
            for position in ("pour", "contre", "abstention", "non_votant"):
                n = g["non_votants" if position == "non_votant" else position]
                if n:
                    lignes_grp.append((lignee(g["groupe_id"]), c["droit"], c["texte_id"], c["poids"],
                                       _valeur(position, c["favorable"], regles), position, n))
    return lignes_dep, lignes_grp


def calculer(temoins: dict, votes: list[dict], regles: dict | None = None,
             ventilations: list[dict] | None = None) -> dict[str, list[dict]]:
    """Scores des scrutins comptés, des députés et des groupes.

    `votes` : votes nominatifs (scrutin_id, acteur_id, position, et groupe_id sans `ventilations`).
    `ventilations` : décompte par groupe et par scrutin (scrutin_id, groupe_id, pour, contre,
    abstention, non_votants) ; s'il est donné, les scores de groupe en viennent.
    """
    regles = {**REGLES, **(regles or {})}
    comptes = scrutins_comptes(temoins, regles)
    lignes_dep, lignes_grp = _lignes(comptes, votes, regles, ventilations)
    return {
        "scores_scrutins": comptes,
        "scores_deputes": _agreger(lignes_dep, "acteur_id"),
        "scores_groupes": _agreger(lignes_grp, "lignee"),
    }


def par_texte(temoins: dict, votes: list[dict], ventilations: list[dict] | None = None,
              regles: dict | None = None) -> dict[str, list[dict]]:
    """Score de chaque député et de chaque groupe sur chaque texte, au sens de son droit principal
    (comme le score global, restreint à un texte)."""
    regles = {**REGLES, **(regles or {})}
    comptes = [{**c, "droit": c["texte_id"]} for c in scrutins_comptes(temoins, regles) if c["droit"] == "global"]
    lignes_dep, lignes_grp = _lignes(comptes, votes, regles, ventilations)

    def renommer(rows, cle):
        return [{cle: r[cle], "texte_id": r["droit"],
                 **{k: v for k, v in r.items() if k not in (cle, "droit", "n_textes")}} for r in rows]
    return {"scores_deputes_textes": renommer(_agreger(lignes_dep, "acteur_id"), "acteur_id"),
            "scores_groupes_textes": renommer(_agreger(lignes_grp, "lignee"), "lignee")}


# --- lvnd scores : depuis data/export/ (sans dump) -----------------------------------------------

FICHIERS = ("scores_scrutins", "scores_deputes", "scores_groupes", "scores_deputes_textes", "scores_groupes_textes",
            "participation")


def _votes_export(export: Path, scrutins: pl.DataFrame) -> pl.DataFrame:
    """Votes nominatifs versionnés (votes/<législature>/<AAAA-MM>.csv) des scrutins donnés."""
    codes = {v: k for k, v in json.loads((export / "meta.json").read_text())["votes_codes"].items()}
    parts = []
    for (leg, mois), s in scrutins.group_by("legislature", pl.col("date").str.slice(0, 7), maintain_order=True):
        v = pl.read_csv(export / "votes" / str(leg) / f"{mois}.csv", schema_overrides={"position": pl.String})
        parts.append(v.join(s.select("id", pl.col("numero").alias("scrutin")), on="scrutin"))
    if not parts:
        return pl.DataFrame(schema={"scrutin_id": pl.String, "acteur_id": pl.String, "position": pl.String})
    return pl.concat(parts).select(
        pl.col("id").alias("scrutin_id"),
        pl.format("PA{}", pl.col("acteur")).alias("acteur_id"),
        pl.col("position").replace_strict({c: p for p, c in codes.items()}),
    )


def participation(comptes: list[dict], scrutins: pl.DataFrame, votes: pl.DataFrame,
                  mandats: pl.DataFrame) -> list[dict]:
    """Taux de participation de chaque député aux scrutins comptés tenus pendant ses mandats (règle 17).

    Il prend part au vote quand il vote pour, contre ou s'abstient. Absent ou non-votant, il n'y
    prend pas part.
    """
    ids = sorted({c["scrutin_id"] for c in comptes if c["favorable"] is not None})
    s = scrutins.filter(pl.col("id").is_in(ids)).select("id", "legislature", "date")
    en_mandat = (mandats.select("acteur_id", "legislature", "debut", "fin")
                 .join(s, on="legislature")
                 .filter((pl.col("date") >= pl.col("debut"))
                         & (pl.col("fin").is_null() | (pl.col("date") <= pl.col("fin"))))
                 .select("acteur_id", pl.col("id").alias("scrutin_id")).unique())
    par_depute = (en_mandat.join(votes, on=["acteur_id", "scrutin_id"], how="left")
                  .group_by("acteur_id")
                  .agg(pl.len().alias("scrutins"),
                       pl.col("position").is_in(["pour", "contre", "abstention"]).sum().alias("votes"),
                       (pl.col("position") == "non_votant").sum().alias("non_votants"))
                  .sort("acteur_id"))
    return [{**r, "taux": round(100 * r["votes"] / r["scrutins"], 1)} for r in par_depute.iter_rows(named=True)]


def depuis_export(export: Path, qualif: dict) -> dict[str, list[dict]]:
    """Scores et participation depuis data/export/ et une qualification, sans dump."""
    ids = {s["id"] for t in qualif["textes"] for s in t["scrutins"]}
    scrutins = pl.read_csv(export / "scrutins.csv", infer_schema=False).with_columns(
        pl.col("legislature", "numero").cast(pl.Int64))
    utiles = scrutins.filter(pl.col("id").is_in(ids))
    votes = _votes_export(export, utiles)
    ventil = (pl.read_csv(export / "positions_groupes.csv", infer_schema=False)
              .filter(pl.col("scrutin_id").is_in(ids))
              .with_columns(pl.col("pour", "contre", "abstention", "non_votants").cast(pl.Int64)))
    sc = calculer(qualif, votes.to_dicts(), ventilations=ventil.to_dicts())
    sc |= par_texte(qualif, votes.to_dicts(), ventilations=ventil.to_dicts())
    mandats = pl.read_csv(export / "mandats.csv", infer_schema=False).with_columns(pl.col("legislature").cast(pl.Int64))
    sc["participation"] = participation(sc["scores_scrutins"], scrutins, votes, mandats)
    return sc


# --- Sénat (règles 23 à 28) ------------------------------------------------------------------------

REGLES_SENAT = {"ponderation": "decisif"}  # règle 26 : chaque texte pèse 1, son décisif seul
CODES_SENAT = {"P": "pour", "C": "contre", "A": "abstention", "N": "non_votant"}
COLONNES_SENAT = {
    "scores_scrutins": ("texte_id", "scrutin_id", "role", "droit", "droit_role", "sens", "poids", "favorable"),
    "scores_senateurs": ("senateur_id", "droit", "n_textes", "votes_favorables", "votes_defavorables", "abstentions",
                         "non_votants", "score"),
    "scores_groupes": ("groupe_id", "droit", "n_textes", "votes_favorables", "votes_defavorables", "abstentions",
                       "non_votants", "score"),
    "scores_senateurs_textes": ("senateur_id", "texte_id", "votes_favorables", "votes_defavorables", "abstentions",
                                "non_votants", "score"),
    "scores_groupes_textes": ("groupe_id", "texte_id", "votes_favorables", "votes_defavorables", "abstentions",
                              "non_votants", "score"),
}


def qualif_senat(qualif: dict) -> dict:
    """Les textes comptés au Sénat, au format d'une qualification : le décisif du Sénat, et les droits de
    la version votée. Pas de décisif, pas de compte (règle 23)."""
    textes = []
    for t in qualif["textes"]:
        s = t.get("senat") or {}
        decisif = [x for x in s.get("scrutins", []) if x["role"] == "decisif"]
        if decisif:
            textes.append({"id": t["id"], "droits": s["droits"] if s["version"] == "autre" else t["droits"],
                           "scrutins": decisif})
    return {"textes": textes}


def _votes_senat(export: Path, ids: set[str], dates: dict[str, str]) -> list[dict]:
    """Votes nominatifs versionnés (senat/votes/<AAAA-MM>.csv) des scrutins donnés."""
    out = []
    for mois in sorted({dates[i][:7] for i in ids}):
        v = pl.read_csv(export / "senat/votes" / f"{mois}.csv", infer_schema=False)
        for r in v.filter(pl.format("SN{}", "scrutin").is_in(ids)).iter_rows(named=True):
            out.append({"scrutin_id": f"SN{r['scrutin']}", "acteur_id": r["senateur"], "position": CODES_SENAT[r["position"]]})
    return out


def senat_depuis_export(export: Path, qualif: dict) -> dict[str, list[dict]]:
    """Scores du Sénat depuis data/export/senat/ et une qualification, sans dump. Le score d'un groupe
    agrège les votes de ses membres, ce que la ventilation donne directement."""
    doc = qualif_senat(qualif)
    ids = {x["id"] for t in doc["textes"] for x in t["scrutins"]}
    scrutins = pl.read_csv(export / "senat/scrutins.csv", infer_schema=False)
    dates = dict(scrutins.select("id", "date").iter_rows())
    votes = _votes_senat(export, ids, dates)
    ventil = (pl.read_csv(export / "senat/positions_groupes.csv", infer_schema=False)
              .filter(pl.col("scrutin_id").is_in(ids))
              .with_columns(pl.col("pour", "contre", "abstention", "non_votants").cast(pl.Int64)).to_dicts())
    sc = calculer(doc, votes, REGLES_SENAT, ventil)
    pt = par_texte(doc, votes, ventil, REGLES_SENAT)

    def renommer(rows: list[dict], avant: str, apres: str) -> list[dict]:
        return [{(apres if k == avant else k): v for k, v in r.items()} for r in rows]
    return {
        "scores_scrutins": sc["scores_scrutins"],
        "scores_senateurs": renommer(sc["scores_deputes"], "acteur_id", "senateur_id"),
        "scores_groupes": renommer(sc["scores_groupes"], "lignee", "groupe_id"),
        "scores_senateurs_textes": renommer(pt["scores_deputes_textes"], "acteur_id", "senateur_id"),
        "scores_groupes_textes": renommer(pt["scores_groupes_textes"], "lignee", "groupe_id"),
    }


def ecrire_senat(export: Path, sc: dict[str, list[dict]]) -> None:
    """Écrit les scores du Sénat dans data/export/senat/ (en-têtes seuls tant qu'aucun décisif n'est publié)."""
    for nom, cols in COLONNES_SENAT.items():
        lignes = [{c: r[c] for c in cols} for r in sc[nom]]
        df = pl.DataFrame(lignes, infer_schema_length=None) if lignes else pl.DataFrame(schema=dict.fromkeys(cols, pl.String))
        df.write_csv(export / "senat" / f"{nom}.csv")


def ecrire(export: Path, sc: dict[str, list[dict]]) -> None:
    """Écrit les scores dans data/export/, au format de `lvnd build`."""
    for nom in FICHIERS:
        pl.DataFrame(sc[nom], infer_schema_length=None).write_csv(export / f"{nom}.csv")
    # Les référentiels (grille des droits) peuvent changer sans nouveau build : le site les lit ici.
    from . import referentiels
    if not (export / "meta.json").exists():
        return
    meta = json.loads((export / "meta.json").read_text())
    meta["referentiels"] = {n: referentiels.charger(n) for n in ("droits", "mots_cles")}
    (export / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1, default=str) + "\n")

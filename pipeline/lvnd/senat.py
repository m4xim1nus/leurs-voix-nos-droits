"""Lecture de Dosleg (dump PostgreSQL du Sénat), adaptée de quifaitlaloi.

Seulement ce qui dit où en est un texte : décisions de séance, séances, activité, état des dossiers.
Les votes des sénateurs (`votsen`) ne sont pas lus : ils restent au cycle Sénat. Les décomptes des
scrutins publics (`scr`) ne servent qu'à dater une décision absente des textes de Dosleg.
"""

import re
from pathlib import Path

import polars as pl

from .sources import extraits
from .texte import nettoyer, objet_scrutin

TABLES = {
    "scr": ["sesann", "scrnum", "code", "scrint", "scrdat", "scrvotsea", "scrsufsea", "scrpousea", "scrconsea"],
    "date_seance": ["code", "lecidt", "date_s"],
    "lecass": ["lecassidt", "lecidt", "codass"],
    "lecture": ["lecidt", "loicod", "typleccod"],
    "loi": ["loicod", "typloicod", "etaloicod", "signet", "date_loi", "loititjo"],
    "texte": ["texcod", "oritxtcod", "lecassidt", "txtoritxtdat"],
    "oritxt": ["oritxtcod", "oritxtlib", "oritxtado"],
}
ESC = {"t": "\t", "n": "\n", "r": "\r", "\\": "\\"}
DEBUT = "2022-06-28"  # début de la XVIe : scrutins publics lus à partir de cette date


def _champ(v: str):
    if v == r"\N":
        return None
    return re.sub(r"\\(.)", lambda m: ESC.get(m.group(1), m.group(1)), v).strip() if "\\" in v else v.strip()


def dosleg(raw: Path) -> dict[str, pl.DataFrame]:
    """Tables utiles de Dosleg, colonnes en texte, champs `char` débarrassés de leurs blancs."""
    sql = extraits(raw, "senat_dosleg") / "dosleg.sql"
    if not sql.exists():
        raise SystemExit(f"{sql} absent : lancer `lvnd download senat_dosleg`")
    out: dict[str, pl.DataFrame] = {}
    with sql.open(encoding="utf-8") as f:
        nom = None
        for ligne in f:
            if nom is None:
                m = re.match(r"COPY (?:public\.)?(\w+) \((.*)\) FROM stdin;", ligne)
                if m and m.group(1) in TABLES:
                    nom = m.group(1)
                    cols = [c.strip().strip('"') for c in m.group(2).split(",")]
                    idx = [cols.index(c) for c in TABLES[nom]]
                    lignes = []
            elif ligne == "\\.\n":
                out[nom] = pl.DataFrame(lignes, schema={c: pl.Utf8 for c in TABLES[nom]}, orient="row")
                nom = None
            else:
                v = ligne.rstrip("\n").split("\t")
                lignes.append([_champ(v[i]) for i in idx])
    manquantes = set(TABLES) - set(out)
    if manquantes:
        raise SystemExit(f"Dosleg : tables absentes du dump : {sorted(manquantes)}")
    return out


def adoptes_definitivement(tables: dict[str, pl.DataFrame]) -> set[str]:
    """Lois (loicod) dont un texte est « adopté définitivement » (oritxt.oritxtado = D).

    Sert à repérer les textes adoptés mais pas encore promulgués quand le Sénat a eu le dernier mot :
    le dossier AN code parfois ces décisions « modifié » (docs/SOURCES.md).
    """
    d = (tables["texte"].join(tables["oritxt"], on="oritxtcod")
         .filter(pl.col("oritxtado") == "D")
         .join(tables["lecass"].select("lecassidt", "lecidt"), on="lecassidt")
         .join(tables["lecture"], on="lecidt"))
    return set(d["loicod"].drop_nulls())


# Textes « adoptés » ou « rejetés » par le Sénat en séance (table oritxt), pour les décisions que le
# dossier AN n'a pas encore enregistrées. Les textes de commission (29, 23, 33…) n'en sont pas.
ORITXT_SEANCE = {"2": "adopte", "6": "adopte", "7": "adopte", "9": "adopte", "11": "adopte",
                 "8": "rejete", "21": "rejete", "27": "rejete", "31": "rejete", "40": "rejete",
                 "42": "rejete", "43": "rejete"}
# État d'une loi dans Dosleg (table etaloi) : 01 en cours, 02 fusionné, 03 rejeté, 04 promulgué
# (ou adopté), 05 caduc, 06 retiré.
ETATS = {"01": "en_cours", "02": "fusionne", "03": "rejete", "04": "promulgue", "05": "caduc", "06": "retire"}


def _lectures_senat(tables: dict[str, pl.DataFrame]) -> pl.DataFrame:
    """lecassidt → (loicod, typleccod) des lectures du Sénat."""
    return (tables["lecass"].filter(pl.col("codass") == "S").select("lecassidt", "lecidt")
            .join(tables["lecture"], on="lecidt"))


def decisions_seance(tables: dict[str, pl.DataFrame]) -> dict[tuple[str, str], tuple[str, str]]:
    """(loicod, typleccod) → (date, issue) de la décision du Sénat en séance, d'après le texte
    adopté ou rejeté. Le dossier AN enregistre ces décisions avec retard (casseurs-payeurs :
    voté le 27/10/2026, absent du dossier AN le 28/10)."""
    d = (tables["texte"].filter(pl.col("oritxtcod").is_in(list(ORITXT_SEANCE)))
         .join(_lectures_senat(tables), on="lecassidt")
         .with_columns(pl.col("txtoritxtdat").str.slice(0, 10).alias("date"))
         .sort("date"))
    return {(r["loicod"], r["typleccod"]): (r["date"], ORITXT_SEANCE[r["oritxtcod"]])
            for r in d.to_dicts() if r["date"]}


def activite(tables: dict[str, pl.DataFrame]) -> dict[str, list[str]]:
    """loicod → dates connues côté Sénat : textes (dépôt, commission, séance) et séances, y compris
    les séances déjà inscrites à l'ordre du jour (date à venir)."""
    t = (tables["texte"].join(tables["lecass"].select("lecassidt", "lecidt"), on="lecassidt")
         .join(tables["lecture"], on="lecidt").select("loicod", pl.col("txtoritxtdat").alias("d")))
    s = (tables["date_seance"].select(pl.col("lecidt").alias("lecassidt"), pl.col("date_s").alias("d"))
         .join(tables["lecass"].select("lecassidt", "lecidt"), on="lecassidt")
         .join(tables["lecture"], on="lecidt").select("loicod", "d"))
    out: dict[str, list[str]] = {}
    for r in pl.concat([t, s]).drop_nulls().to_dicts():
        out.setdefault(r["loicod"], []).append(r["d"][:10])
    return out


def seances(tables: dict[str, pl.DataFrame]) -> dict[str, list[str]]:
    """loicod → dates des séances du Sénat consacrées au texte (table date_seance)."""
    s = (tables["date_seance"].select(pl.col("lecidt").alias("lecassidt"), pl.col("date_s").alias("d"))
         .join(_lectures_senat(tables), on="lecassidt").select("loicod", "d").drop_nulls())
    out: dict[str, list[str]] = {}
    for r in s.to_dicts():
        out.setdefault(r["loicod"], []).append(r["d"][:10])
    return out


def etats(tables: dict[str, pl.DataFrame]) -> dict[str, str | None]:
    """loicod → état du dossier dans Dosleg (`ETATS`)."""
    return {r["loicod"]: ETATS.get(r["etaloicod"]) for r in tables["loi"].select("loicod", "etaloicod").to_dicts()}


def lois(tables: dict[str, pl.DataFrame]) -> dict[str, dict]:
    """Dossiers du Sénat : `par_signet` (signet → loi), `par_date` (date de la loi → lois, secours
    sans signet) et `definitifs` (`adoptes_definitivement`)."""
    loi = tables["loi"].filter(pl.col("date_loi").is_not_null() | pl.col("signet").is_not_null())
    par_signet = {r["signet"]: {**r, "titre": r["loititjo"]} for r in loi.to_dicts() if r["signet"]}
    par_date: dict[str, list[dict]] = {}
    for r in loi.to_dicts():
        if r["date_loi"]:
            par_date.setdefault(r["date_loi"][:10], []).append({**r, "titre": r["loititjo"]})
    return {"par_signet": par_signet, "par_date": par_date, "definitifs": adoptes_definitivement(tables)}


def scrutins(tables: dict[str, pl.DataFrame]) -> pl.DataFrame:
    """Scrutins publics du Sénat depuis DEBUT (décomptes seulement), rattachés à leur loi et type de
    lecture Dosleg."""
    lec = (tables["date_seance"].select("code", pl.col("lecidt").alias("lecassidt"))
           .join(tables["lecass"].select("lecassidt", "lecidt"), on="lecassidt", how="left")
           .join(tables["lecture"], on="lecidt", how="left")
           .unique("code"))
    s = (tables["scr"].filter(pl.col("scrdat") >= DEBUT)
         .join(lec.select("code", "loicod", "typleccod"), on="code", how="left"))
    num = lambda c: pl.col(c).cast(pl.Int64).fill_null(0)
    s = s.with_columns(
        pl.format("SN{}-{}", "sesann", "scrnum").alias("id"),
        pl.col("scrint").map_elements(nettoyer, return_dtype=pl.Utf8).alias("titre"),
        num("scrpousea").alias("pour"), num("scrconsea").alias("contre"),
        num("scrsufsea").alias("exprimes"),
    )
    return (s.with_columns(
                pl.col("scrnum").cast(pl.Int64).alias("numero"),
                pl.col("scrdat").str.slice(0, 10).alias("date"),
                pl.col("titre").map_elements(objet_scrutin, return_dtype=pl.Utf8).alias("objet"),
                (pl.col("exprimes") // 2 + 1).alias("requis"))
            .with_columns(pl.when(pl.col("pour") >= pl.col("requis")).then(pl.lit("adopte"))
                          .otherwise(pl.lit("rejete")).alias("sort"))
            .select("id", "numero", "date", "titre", "objet", "sort", "pour", "contre", "loicod", "typleccod")
            .sort("date", "numero"))

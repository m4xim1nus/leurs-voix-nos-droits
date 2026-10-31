"""Lecture de Dosleg (dump PostgreSQL du Sénat) et des fichiers ODSEN, adaptée de quifaitlaloi.

Deux usages, séparés : ce qui dit où en est un texte (décisions de séance, séances, activité, état des
dossiers, sans effet sur les votes de l'AN) et les votes du Sénat (`votsen`, sénateurs, groupes datés),
exportés à part dans data/export/senat/ (docs/SOURCES.md).
"""

import re
from datetime import date, timedelta
from pathlib import Path

import polars as pl

from .sources import extraits
from .texte import nettoyer, norm, objet_scrutin

TABLES = {
    "scr": ["sesann", "scrnum", "code", "scrint", "scrdat", "scrvotsea", "scrsufsea", "scrpousea", "scrconsea",
            "scrbaspag"],
    "votsen": ["sesann", "scrnum", "senmat", "posvotcod", "stavotidt", "senmatdel", "votsenmar"],
    "stavot": ["stavotidt", "stavotlib"],
    "corscr": ["sesann", "scrnum", "corscrord", "corscrtxt", "corscrurl"],
    "typlec": ["typleccod", "typleclib"],
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


# --- Votes du Sénat ---------------------------------------------------------------

POSITIONS = {"1": "pour", "2": "contre", "3": "abstention", "4": "non_votant"}
SANS_GROUPE = "AUCUN"  # quelques jours après un renouvellement : ni un groupe, ni les non-inscrits (NI)
FUSION_GROUPE = 10  # jours : deux périodes dans le même groupe, séparées par ce blanc au plus, n'en font qu'une
URL_SCRUTIN = "https://www.senat.fr/scrutin-public/{session}/scr{session}-{numero}.html"
# Circonscriptions du Sénat absentes des mandats de l'AN : autre libellé, ou collectivités que l'AN réunit.
DEPARTEMENTS_SENAT = {"saint barthelemy": "977", "saint martin": "978", "la reunion": "974", "iles wallis et futuna": "986"}


def _odsen(raw: Path, cle: str) -> pl.DataFrame:
    """Fichier ODSEN : CSV latin-1, précédé de sa requête en lignes `%`."""
    chemin = extraits(raw, cle)
    if not chemin.exists():
        raise SystemExit(f"{chemin} absent : lancer `lvnd download {cle}`")
    lignes = chemin.read_text(encoding="latin-1").splitlines()
    return pl.read_csv("\n".join(l for l in lignes if not l.startswith("%")).encode(), infer_schema=False)


def _jour(col: str) -> pl.Expr:
    return pl.col(col).str.slice(0, 10)


def appartenances(raw: Path, date_ref: str) -> pl.DataFrame:
    """Périodes de chaque sénateur dans un groupe (ODSEN_HISTOGROUPES). `AUCUN` ne compte pas comme un
    groupe. Une fin postérieure à `date_ref` est une erreur de saisie (2029 pour un mandat en cours) :
    la période est en cours. Une fiche par fonction occupée au sein du groupe : on ne garde que les
    appartenances, réunies quand elles se suivent (le renouvellement en coupe beaucoup)."""
    df = (_odsen(raw, "senat_groupes")
          .select(senateur_id="Matricule", groupe_id="Code du groupe politique",
                  debut=_jour("Date de début d'appartenance"), fin=_jour("Date de fin d'appartenance"))
          .unique().filter(pl.col("groupe_id") != SANS_GROUPE)
          .with_columns(pl.when(pl.col("fin") > date_ref).then(None).otherwise(pl.col("fin")).alias("fin"))
          .sort("senateur_id", pl.col("debut").fill_null("")))
    out: list[dict] = []
    for r in df.to_dicts():
        p = out[-1] if out else None
        if (p and p["senateur_id"] == r["senateur_id"] and p["groupe_id"] == r["groupe_id"] and p["fin"] and r["debut"]
                and date.fromisoformat(r["debut"]) - date.fromisoformat(p["fin"]) <= timedelta(days=FUSION_GROUPE)):
            p["fin"] = r["fin"]
        else:
            out.append(r)
    return pl.DataFrame(out, schema=df.schema)


def groupes(raw: Path, ids: set[str], date_ref: str) -> pl.DataFrame:
    """Groupes des votes. Le code reste le même quand un groupe change de nom (`UMP` : Les Républicains ;
    `LREM` : RDPI), et les fichiers ne donnent que le nom actuel : sigle lu sur les membres en poste
    (ODSEN_GENERAL), nom lu dans l'historique."""
    h = (_odsen(raw, "senat_groupes").select(id="Code du groupe politique", senateur_id="Matricule",
                                             nom=pl.col("Nom court du groupe politique").str.replace(r"^Groupe (du )?", ""))
         .filter(pl.col("id").is_in(ids)))
    actifs = (_odsen(raw, "senat_senateurs").filter(pl.col("État") == "ACTIF")
              .select(senateur_id="Matricule", sigle="Groupe politique"))
    courants = appartenances(raw, date_ref).filter(pl.col("fin").is_null()).select("senateur_id", "groupe_id")
    sigles = (actifs.join(courants, on="senateur_id").group_by("groupe_id", "sigle").len()
              .sort("len", "sigle", descending=True).unique("groupe_id", keep="first", maintain_order=True)
              .select(id="groupe_id", sigle="sigle"))
    return (h.select("id", "nom").unique().join(sigles, on="id", how="left")
            .with_columns(pl.col("sigle").fill_null(pl.col("id"))).select("id", "sigle", "nom").sort("id"))


def mandats(raw: Path, ids: set[str]) -> pl.DataFrame:
    """Mandats datés des sénateurs retenus (ODSEN_ELUSEN)."""
    return (_odsen(raw, "senat_mandats").filter(pl.col("Matricule").is_in(ids))
            .select(senateur_id="Matricule", debut=_jour("Date de début de mandat"), fin=_jour("Date de fin de mandat"),
                    motif_debut="Motif début de mandat", motif_fin="Motif fin de mandat")
            .sort("senateur_id", "debut"))


def senateurs(raw: Path, ids: set[str], departements: dict[str, str]) -> pl.DataFrame:
    """Sénateurs retenus (ODSEN_GENERAL). `departements` : nom normalisé → code, tiré des mandats de
    l'AN, qui ne connaît pas tout (`DEPARTEMENTS_SENAT`). Un courriel « Non public » n'est pas exporté."""
    codes = departements | DEPARTEMENTS_SENAT
    df = (_odsen(raw, "senat_senateurs").filter(pl.col("Matricule").is_in(ids))
          .select(id="Matricule", civ="Qualité", prenom="Prénom usuel", nom="Nom usuel", etat=pl.col("État").str.to_lowercase(),
                  type_appartenance="Type d'app au grp politique", circonscription="Circonscription",
                  courriel=pl.col("Courrier électronique").replace("Non public", None))
          .with_columns(departement=pl.col("circonscription").map_elements(
              lambda c: codes.get(norm(c)), return_dtype=pl.String))
          .select("id", "civ", "prenom", "nom", "etat", "type_appartenance", "circonscription", "departement", "courriel")
          .sort("id"))
    inconnues = sorted(set(df.filter(pl.col("departement").is_null())["circonscription"].to_list()), key=str)
    if inconnues:
        raise SystemExit(f"circonscriptions du Sénat sans code de département : {inconnues}")
    return df


def votes(tables: dict[str, pl.DataFrame], scr: pl.DataFrame, appart: pl.DataFrame) -> pl.DataFrame:
    """Votes nominatifs depuis DEBUT, avec le groupe du jour du vote (`null` si aucun : `lvnd check`
    échoue). `delegue_a` : sénateur qui a voté pour lui, par délégation (`senmatdel` est porté par la ligne de
    celui qui reçoit la délégation et nomme celui qui l'a donnée) ; `mise_au_point` : la liste officielle
    l'étoile, renvoyant à `corscr` ou à la note du scrutin. `statut` : président de séance, membre du
    gouvernement, déport."""
    v = (tables["votsen"]
         .with_columns(pl.format("SN{}-{}", "sesann", "scrnum").alias("scrutin_id"))
         .join(scr.select(pl.col("id").alias("scrutin_id"), "date", "numero"), on="scrutin_id")
         .join(tables["stavot"], on="stavotidt", how="left")
         .select("scrutin_id", "date", "numero", senateur_id="senmat",
                 position=pl.col("posvotcod").replace_strict(POSITIONS),
                 statut=pl.when(pl.col("stavotidt") == "0").then(None).otherwise(pl.col("stavotlib")),
                 delegant="senmatdel", mise_au_point=pl.col("votsenmar").fill_null("") == "*"))
    recues = v.filter(pl.col("delegant").is_not_null()).select(
        "scrutin_id", senateur_id="delegant", delegue_a="senateur_id")
    v = v.drop("delegant").join(recues, on=["scrutin_id", "senateur_id"], how="left")
    g = (v.select("scrutin_id", "senateur_id", "date")
         .join(appart.with_columns(pl.col("debut").fill_null("0000"), pl.col("fin").fill_null("9999")), on="senateur_id")
         .filter((pl.col("debut") <= pl.col("date")) & (pl.col("date") <= pl.col("fin")))
         .sort("debut").unique(["scrutin_id", "senateur_id"], keep="last")
         .select("scrutin_id", "senateur_id", "groupe_id"))
    return (v.join(g, on=["scrutin_id", "senateur_id"], how="left")
            .select("scrutin_id", "date", "numero", "senateur_id", "groupe_id", "position", "statut", "delegue_a", "mise_au_point")
            .sort("date", "numero", "senateur_id"))


def ventilations(v: pl.DataFrame) -> list[dict]:
    """Décompte de chaque groupe par scrutin, au format de l'AN (`positions.positions`)."""
    return (v.group_by("scrutin_id", "groupe_id")
            .agg(membres=pl.len(), pour=(pl.col("position") == "pour").sum(), contre=(pl.col("position") == "contre").sum(),
                 abstention=(pl.col("position") == "abstention").sum(), non_votants=(pl.col("position") == "non_votant").sum())
            .with_columns(pl.col("membres", "pour", "contre", "abstention", "non_votants").cast(pl.Int64))
            .sort("scrutin_id", "groupe_id").to_dicts())


def completer(s: pl.DataFrame, fiches: list[dict]) -> pl.DataFrame:
    """`scrutins`, plus ceux que Dosleg donne sans fiche (referentiels/scrutins_senat.yaml). Chacun reprend
    la loi et la lecture de son scrutin `comme` ; le décompte vient ensuite de la liste nominative."""
    par_id = {r["id"]: r for r in s.to_dicts()}
    lignes = []
    for f in fiches:
        frere = par_id.get(f["comme"], {})
        lignes.append({"id": f"SN{f['session']}-{f['numero']}", "numero": f["numero"], "date": str(f["date"]), "titre": f["titre"],
                       "objet": objet_scrutin(f["titre"]), "sort": None, "pour": None, "contre": None,
                       "loicod": frere.get("loicod"), "typleccod": frere.get("typleccod")})
    return pl.concat([s, pl.DataFrame(lignes, schema=s.schema)]).sort("date", "numero")


def sans_fiche(tables: dict[str, pl.DataFrame], s: pl.DataFrame) -> list[str]:
    """Scrutins dont `votsen` donne les votes, absents de `s` : à ajouter à referentiels/scrutins_senat.yaml."""
    ids = (tables["votsen"].filter(pl.col("sesann") >= DEBUT[:4])
           .select(pl.format("SN{}-{}", "sesann", "scrnum").alias("id")).unique())
    return sorted(set(ids["id"]) - set(s["id"]))


def export_scrutins(tables: dict[str, pl.DataFrame], s: pl.DataFrame, v: pl.DataFrame, dossier_de: dict[str, str]) -> pl.DataFrame:
    """Scrutins publics depuis DEBUT (`s`) : décompte `scrutins`, compté sur la liste nominative quand elle
    s'en écarte (voir docs/SOURCES.md), lecture, signet et dossier de l'AN."""
    n = v.group_by("scrutin_id").agg(
        pour=(pl.col("position") == "pour").sum(), contre=(pl.col("position") == "contre").sum(),
        abstention=(pl.col("position") == "abstention").sum(), non_votants=(pl.col("position") == "non_votant").sum()
    ).with_columns(pl.col("pour", "contre", "abstention", "non_votants").cast(pl.Int64))
    extra = tables["scr"].select(id=pl.format("SN{}-{}", "sesann", "scrnum"), note="scrbaspag",
                                 pour_scr=pl.col("scrpousea").cast(pl.Int64), contre_scr=pl.col("scrconsea").cast(pl.Int64))
    return (s.drop("pour", "contre", "sort")
            .join(n, left_on="id", right_on="scrutin_id", how="left").join(extra, on="id", how="left")
            .join(tables["loi"].select("loicod", "signet"), on="loicod", how="left")
            .join(tables["typlec"], on="typleccod", how="left")
            .with_columns(session=pl.col("id").str.extract(r"^SN(\d+)-"))
            .with_columns(
                votants=pl.col("pour") + pl.col("contre") + pl.col("abstention"),
                exprimes=pl.col("pour") + pl.col("contre"),
                requis=(pl.col("pour") + pl.col("contre")) // 2 + 1,
                dossier_id=pl.col("loicod").replace_strict(dossier_de, default=None, return_dtype=pl.String),
                url=pl.struct("session", "numero").map_elements(lambda r: URL_SCRUTIN.format(**r), return_dtype=pl.String))
            .with_columns(sort=pl.when(pl.col("pour") >= pl.col("requis")).then(pl.lit("adopte")).otherwise(pl.lit("rejete")))
            .select("id", "session", "numero", "date", "titre", "objet", "sort", "pour", "contre", "abstention", "non_votants",
                    "votants", "exprimes", "requis", "pour_scr", "contre_scr", "loicod", "signet", lecture="typleclib",
                    dossier_id="dossier_id", note="note", url="url"))


def mises_au_point(tables: dict[str, pl.DataFrame], scr: pl.DataFrame) -> pl.DataFrame:
    """Mises au point publiées (`corscr`, souvent une ligne vide), affichées et non comptées (règle 13)."""
    return (tables["corscr"].with_columns(pl.format("SN{}-{}", "sesann", "scrnum").alias("scrutin_id"))
            .filter(pl.col("scrutin_id").is_in(scr["id"].to_list()) & (pl.col("corscrtxt").fill_null("").str.len_chars() > 0))
            .select("scrutin_id", ordre=pl.col("corscrord").cast(pl.Int64),
                    texte=pl.col("corscrtxt").map_elements(nettoyer, return_dtype=pl.String), url="corscrurl")
            .sort("scrutin_id", "ordre", "texte"))

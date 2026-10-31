"""Annuaire du site : code postal → circonscription(s) et département, et courriel de chaque député.

Écrit data/annuaire/ (versionné), lu au build du site (docs/CONCEPTION.md, Site public). Lancé
en local, depuis les dumps : il ne change qu'avec le découpage, les communes ou les députés.

    cd pipeline && uv run lvnd annuaire

Code postal → circonscription : aucune table officielle (docs/SOURCES.md). On joint deux sources
officielles, reprises du spike (explo/circos.py) :

- La Poste : code postal → communes (base officielle des codes postaux) ;
- ministère de l'Intérieur, législatives 2024, 1er tour, par bureau de vote : commune ×
  circonscription, avec le poids de chaque circonscription en inscrits. Le fichier 2024 n'a
  pas de colonne circonscription : on la retrouve en appariant la liste des candidats du bureau
  avec celle de la circonscription.

Les codes commune 2024 sont ramenés au COG en vigueur (fusions), et Paris, Lyon et Marseille
sont découpés en arrondissements, comme chez La Poste. Sources dans data/raw/circos/.
"""

import io
import sys
from pathlib import Path

import polars as pl

from . import an

FICHIERS = ("laposte_hexasmal.csv", "mi2024_t1_bureaux.csv", "mi2024_t1_circos.csv", "cog2026_communes.csv",
            "cog2026_comer.csv", "cog2026_mvt.csv")

# Codes département du ministère de l'Intérieur → numDepartement de l'AN.
DEP_MI = {"ZA": "971", "ZB": "972", "ZC": "973", "ZD": "974", "ZM": "976", "ZS": "975", "ZX": "977",
          "ZN": "988", "ZP": "987", "ZW": "986", "ZZ": "099"}
# Codes commune du MI 2024 sans équivalent direct au COG (vérifiés à la main au spike).
CODES_SPECIAUX = {
    # Partie axonaise (ex-Gernicourt) de la commune nouvelle de Cormicy (Marne).
    "02899": ["51171"],
    # Wallis-et-Futuna : une « commune » au MI, trois circonscriptions territoriales au COG.
    "98601": ["98611", "98612", "98613"],
}
# Communes à arrondissements municipaux : code commune → préfixe de l'arrondissement.
PLM = {"75056": "751", "13055": "132", "69123": "6938"}


def _log(msg: str) -> None:
    print(msg, file=sys.stderr)


def _csv(path: Path, latin1: bool = False, sep: str = ";") -> pl.DataFrame:
    data = path.read_bytes()
    if latin1:
        data = data.decode("latin-1").encode("utf-8")
    return pl.read_csv(io.BytesIO(data), separator=sep, infer_schema=False)


def _dep_an(dep_mi: str) -> str:
    dep_mi = dep_mi.strip()
    if dep_mi in DEP_MI:
        return DEP_MI[dep_mi]
    return dep_mi.zfill(2) if dep_mi.isdigit() else dep_mi


def _cle_candidats(df: pl.DataFrame) -> pl.Expr:
    n = max(int(c.rsplit(" ", 1)[1]) for c in df.columns if c.startswith("Nom candidat "))
    parts = [pl.concat_str([pl.col(f"Numéro de panneau {i}"), pl.col(f"Nom candidat {i}"),
                            pl.col(f"Prénom candidat {i}")], separator=":") for i in range(1, n + 1)]
    return pl.concat_list(parts).list.drop_nulls().list.sort().list.join("|")


def _insee(com_mi: str, bv: str) -> str | None:
    """Code commune Insee d'un bureau 2024 (arrondissement pour Paris, Lyon et Marseille)."""
    if com_mi.startswith("ZZ"):
        return None  # Français de l'étranger
    code = "97" + com_mi[2:] if com_mi.startswith("ZX") else com_mi.zfill(5)
    if code in PLM:
        arr = int(bv) // 100  # le n° de bureau commence par le n° d'arrondissement
        if arr == 0:
            return None  # bureau hors numérotation (rare), ignoré
        return PLM[code] + (f"{arr:02d}" if len(PLM[code]) == 3 else str(arr))
    return code


def bureaux_2024(raw: Path) -> pl.DataFrame:
    """Bureaux de vote 2024 : commune Insee, inscrits, circonscription (« 33-04 »)."""
    circos = _csv(raw / "mi2024_t1_circos.csv")
    circos = circos.select(
        dep=pl.col("Code département").map_elements(_dep_an, return_dtype=pl.String),
        circo=pl.concat_str([pl.col("Code département").map_elements(_dep_an, return_dtype=pl.String),
                             pl.col("Code circonscription législative").str.slice(-2)], separator="-"),
        cle=_cle_candidats(circos))
    if circos.height != 577 or circos["cle"].n_unique() != 577:
        raise SystemExit("mi2024_t1_circos.csv : 577 circonscriptions à listes de candidats distinctes attendues")
    bv = _csv(raw / "mi2024_t1_bureaux.csv")
    bv = bv.with_columns(dep=pl.col("Code département").map_elements(_dep_an, return_dtype=pl.String),
                         cle=_cle_candidats(bv)).join(circos, on=["dep", "cle"], how="left")
    sans = bv.filter(pl.col("circo").is_null()).height
    if sans:
        raise SystemExit(f"{sans} bureaux 2024 sans circonscription retrouvée")
    return bv.select(
        insee=pl.struct("Code commune", "Code BV").map_elements(
            lambda s: _insee(s["Code commune"], s["Code BV"]), return_dtype=pl.String),
        inscrits=pl.col("Inscrits").cast(pl.Int64), circo="circo")


def _cog(raw: Path):
    """Communes en vigueur, suivi des fusions (ancien code → code actuel), libellés, rétablissements."""
    com = pl.read_csv(raw / "cog2026_communes.csv", infer_schema=False)
    comer = pl.read_csv(raw / "cog2026_comer.csv", infer_schema=False)
    mvt = pl.read_csv(raw / "cog2026_mvt.csv", infer_schema=False)
    vraies = com.filter(pl.col("TYPECOM").is_in(["COM", "ARM"]))
    libelles = dict(zip(vraies["COM"], vraies["LIBELLE"])) | dict(
        zip(comer.filter(pl.col("NATURE_ZONAGE") == "COM")["COM_COMER"],
            comer.filter(pl.col("NATURE_ZONAGE") == "COM")["LIBELLE"]))
    m = (mvt.filter((pl.col("TYPECOM_AV") == "COM") & (pl.col("TYPECOM_AP") == "COM")
                    & (pl.col("COM_AV") != pl.col("COM_AP")))
         .sort("DATE_EFF").group_by("COM_AV").agg(pl.col("COM_AP").last()))
    suite = dict(zip(m["COM_AV"], m["COM_AP"]))

    def actuel(code: str) -> str:
        vu = set()
        while code not in libelles and code in suite and code not in vu:
            vu.add(code)
            code = suite[code]
        return code

    ret = mvt.filter((pl.col("MOD") == "21") & (pl.col("TYPECOM_AV") == "COM") & (pl.col("TYPECOM_AP") == "COM")
                     & (pl.col("COM_AV") != pl.col("COM_AP")))
    parents = dict(zip(ret["COM_AP"], ret["COM_AV"]))
    return libelles, actuel, parents


def commune_circo(raw: Path) -> pl.DataFrame:
    """Commune (COG en vigueur) × circonscription, avec la part des inscrits de la commune."""
    libelles, actuel, parents = _cog(raw)
    b = bureaux_2024(raw).filter(pl.col("insee").is_not_null())
    b = (b.with_columns(insee=pl.col("insee").map_elements(lambda c: CODES_SPECIAUX.get(c, [c]),
                                                           return_dtype=pl.List(pl.String))).explode("insee")
         .with_columns(insee=pl.col("insee").map_elements(actuel, return_dtype=pl.String)))
    cc = b.group_by("insee", "circo").agg(pl.col("inscrits").sum())
    # Commune rétablie depuis 2024 : circonscription(s) de la commune dont elle sort.
    connues = set(cc["insee"])
    ajouts = [(code, c, 0) for code in sorted(set(libelles) - connues)
              if parents.get(code) in connues for c in cc.filter(pl.col("insee") == parents[code])["circo"]]
    if ajouts:
        cc = pl.concat([cc, pl.DataFrame(ajouts, schema=cc.schema, orient="row")])
    return (cc.with_columns(part=(pl.col("inscrits") / pl.col("inscrits").sum().over("insee")).fill_nan(None),
                            commune=pl.col("insee").replace_strict(libelles, default=None))
            .sort("insee", "circo"))


def codes_postaux(raw: Path) -> pl.DataFrame:
    """Code postal × commune × circonscription (La Poste, puis commune_circo)."""
    lp = _csv(raw / "laposte_hexasmal.csv", latin1=True)
    lp = lp.select(insee=pl.col(lp.columns[0]), cp=pl.col("Code_postal")).unique()
    cc = commune_circo(raw)
    j = lp.join(cc, on="insee", how="inner")
    _log(f"   {lp['cp'].n_unique():,} codes postaux La Poste, {j['cp'].n_unique():,} rattachés à une circonscription "
         f"({lp.join(cc, on='insee', how='anti').height} couples code postal × commune sans circonscription)")
    return (j.select("cp", "insee", "commune", "circo", pl.col("part").round(3))
            .sort("cp", "insee", "circo"))


def departement(insee: str) -> str:
    """Département ou collectivité d'une commune, au sens des circonscriptions du Sénat. Saint-Barthélemy
    (977) et Saint-Martin (978) ont chacun leur sénateur."""
    return insee[:3] if insee.startswith(("97", "98")) else insee[:2]


def codes_postaux_departements(cp: pl.DataFrame) -> pl.DataFrame:
    """Code postal × département, pour retrouver ses sénateurs (senat/senateurs.csv)."""
    return (cp.select("cp", departement=pl.col("insee").map_elements(departement, return_dtype=pl.String))
            .unique().sort("cp", "departement"))


def contacts(raw: Path) -> pl.DataFrame:
    """Courriel et site de chaque député ayant siégé depuis 2022 (adresses de l'AMO)."""
    rows = []
    for uid, a in sorted(an._acteurs(raw).items()):
        ms = an._liste((a.get("mandats") or {}).get("mandat"))
        if not any(m.get("typeOrgane") == "ASSEMBLEE" and an._int(m.get("legislature")) in an.LEGISLATURES
                   for m in ms):
            continue
        adresses = an._liste((a.get("adresses") or {}).get("adresse"))
        mels = [x.get("valElec") for x in adresses if x.get("typeLibelle") == "Mèl" and x.get("valElec")]
        # L'adresse de l'Assemblée d'abord : c'est celle que l'on interpelle.
        mels.sort(key=lambda m: not m.lower().endswith("@assemblee-nationale.fr"))
        sites = [x.get("valElec") for x in adresses if x.get("typeLibelle") == "Site internet" and x.get("valElec")]
        rows.append({"acteur_id": uid, "courriel": mels[0] if mels else None, "site": sites[0] if sites else None})
    return pl.DataFrame(rows, schema={"acteur_id": pl.String, "courriel": pl.String, "site": pl.String})


def annuaire(raw: Path, sortie: Path) -> None:
    circos = raw / "circos"
    manquants = [f for f in FICHIERS if not (circos / f).exists()]
    if manquants:
        raise SystemExit(f"{circos} : fichiers absents ({', '.join(manquants)}), voir docs/SOURCES.md")
    sortie.mkdir(parents=True, exist_ok=True)
    _log("== Codes postaux")
    cp = codes_postaux(circos)
    cp.write_csv(sortie / "codes_postaux.csv")
    codes_postaux_departements(cp).write_csv(sortie / "cp_departements.csv")
    _log("== Contacts des députés")
    ct = contacts(raw)
    ct.write_csv(sortie / "contacts.csv")
    _log(f"   {ct.height} députés, {ct['courriel'].is_not_null().sum()} courriels")
    _log(f"   {sortie}/")

"""Scores calculés depuis une qualification (referentiels/temoins.yaml en attendant l'admin).

Pour chaque scrutin compté et chaque droit touché par le texte, un vote est *favorable aux
droits* ou *défavorable* :

- `pour: texte` (scrutin décisif) : voter pour soutient le texte, donc favorable si le texte
  étend le droit, défavorable s'il le restreint ;
- `pour: contre-texte` (amendement de suppression, motion) : l'inverse.

Le score d'un député (ou d'un groupe) sur un droit est la part pondérée de ses votes favorables
parmi ses votes comptés, de 0 à 100. Les règles de calcul (docs/METHODO.md, règles 14 à 19) sont
rassemblées dans `REGLES` : valeurs validées par Max le 29/10/2026. Les autres options restent disponibles pour simuler une variante.
"""

from collections import defaultdict

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
    """lignes : (entité, droit, texte, poids, valeur, position)."""
    acc: dict[tuple, dict] = defaultdict(lambda: {"num": 0.0, "den": 0.0, "textes": set(), "pour_droits": 0,
                                                  "contre_droits": 0, "abstentions": 0, "non_votants": 0})
    for ent, droit, texte, poids, valeur, position in lignes:
        a = acc[(ent, droit)]
        a["textes"].add(texte)
        if valeur is not None:
            a["num"] += poids * valeur
            a["den"] += poids
        if position == "abstention":
            a["abstentions"] += 1
        elif position == "non_votant":
            a["non_votants"] += 1
        elif valeur == 1.0:
            a["pour_droits"] += 1
        elif valeur == 0.0:
            a["contre_droits"] += 1
    return [{cle: ent, "droit": droit, "n_textes": len(a["textes"]), "votes_favorables": a["pour_droits"],
             "votes_defavorables": a["contre_droits"], "abstentions": a["abstentions"],
             "non_votants": a["non_votants"],
             "score": round(100 * a["num"] / a["den"], 1) if a["den"] else None}
            for (ent, droit), a in sorted(acc.items())]


def calculer(temoins: dict, votes: list[dict], regles: dict | None = None) -> dict[str, list[dict]]:
    regles = {**REGLES, **(regles or {})}
    comptes = scrutins_comptes(temoins, regles)
    par_scrutin: dict[str, list[dict]] = defaultdict(list)
    for c in comptes:
        par_scrutin[c["scrutin_id"]].append(c)
    lignes_dep, lignes_grp = [], []
    for v in votes:
        for c in par_scrutin.get(v["scrutin_id"], ()):
            if c["favorable"] is None:
                continue
            val = _valeur(v["position"], c["favorable"], regles)
            lignes_dep.append((v["acteur_id"], c["droit"], c["texte_id"], c["poids"], val, v["position"]))
            lignes_grp.append((lignee(v["groupe_id"]), c["droit"], c["texte_id"], c["poids"], val, v["position"]))
    return {
        "scores_scrutins": comptes,
        "scores_deputes": _agreger(lignes_dep, "acteur_id"),
        "scores_groupes": _agreger(lignes_grp, "lignee"),
    }

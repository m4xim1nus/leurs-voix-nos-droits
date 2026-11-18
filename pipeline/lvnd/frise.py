"""Grandes étapes du parcours d'un texte, pour la frise de sa fiche : dépôt (avec l'origine du texte),
lectures votées, commission mixte paritaire, Conseil constitutionnel, promulgation.

Tout vient du dossier AN et des lectures déjà calculées par `parcours`. Ce module ne juge rien : il
liste les actes datés. L'issue finale d'un texte non promulgué (à l'arrêt, rejeté…) se lit dans
`en_cours_etats.csv`.
"""

from pathlib import Path

from . import an, parcours
from .textes import _date, _initiative

COLONNES = ("texte_id", "ordre", "etape", "chambre", "lecture", "date", "issue", "detail",
            "origine", "auteur_id", "auteur_groupe", "cosignataires")
# Lectures du Sénat et de l'AN : l'étape CMP est rendue par ses événements (une ligne, pas deux).
CMP_ISSUES = {"cmp_accord": "accord", "cmp_desaccord": "desaccord", "cmp_convoquee": "convoquee"}


def origine(d: dict, raw: Path | None, date_depot: str | None) -> dict:
    """Qui dépose : le gouvernement (projet de loi) ou des parlementaires (proposition). Pour une
    proposition : premier·e signataire (auteur·ice), son groupe politique à la date du dépôt si
    l'annuaire des députés le connaît, et le nombre de cosignataires. Un·e sénateur·ice n'est pas dans
    l'annuaire des députés : l'origine reste alors « parlementaire », sans groupe."""
    ini = _initiative(d)
    vide = {"origine": None, "auteur_id": None, "auteur_groupe": None, "cosignataires": None}
    if ini == "projet":
        return {**vide, "origine": "gouvernement"}
    if ini != "proposition":
        return vide
    acteurs = an._liste(((d.get("initiateur") or {}).get("acteurs") or {}).get("acteur"))
    refs = [a["acteurRef"] for a in acteurs if a.get("acteurRef")]
    out = {**vide, "origine": "parlementaire"}
    if refs:
        out["auteur_id"] = refs[0]
        out["cosignataires"] = len(refs) - 1
        if raw is not None and date_depot:
            out["auteur_groupe"] = an._groupe_a_date(raw, refs[0], date_depot) or None
    return out


def etapes(c: dict, raw: Path | None = None) -> list[dict]:
    """Lignes de frise d'un dossier classé (`parcours.classer`), dans l'ordre chronologique."""
    d, uid = c["dossier"], c["uid"]
    depots = sorted((a for e in an.enfants(d) for a in an.parcourir(e)
                     if a["codeActe"].endswith("-DEPOT") and a.get("texteAssocie") and _date(a)), key=_date)
    rows: list[dict] = []
    if depots:
        premier = depots[0]
        rows.append({"etape": "depot", "chambre": premier["codeActe"][:2], "lecture": "", "date": _date(premier),
                     "issue": "", "detail": "", **origine(d, raw, _date(premier))})
    for l in c["lectures"]:
        if l["dec"] is None or l["etape"] == "CMP":
            continue
        rows.append({"etape": "lecture", "chambre": l["chambre"], "lecture": l["type_lecture"], "date": l["date"],
                     "issue": parcours._statut(l["dec"])["issue"], "detail": ""})
    cmps = [e for e in c["evts"] if e["type"] in CMP_ISSUES and e["date"]]
    for e in cmps:
        if e["type"] == "cmp_convoquee" and any(x["type"] != "cmp_convoquee" and x["date"] >= e["date"] for x in cmps):
            continue  # la convocation précède son résultat : une seule ligne
        rows.append({"etape": "cmp", "chambre": "", "lecture": "", "date": e["date"], "issue": CMP_ISSUES[e["type"]],
                     "detail": ""})
    for e in c["evts"]:
        if e["type"] == "decision_cc" and e["date"]:
            libelle = (e["detail"] or "").partition(" | ")[0]
            rows.append({"etape": "cc", "chambre": "", "lecture": "", "date": e["date"], "issue": "",
                         "detail": libelle if libelle != "None" else ""})
        elif e["type"] == "promulgation" and e["date"]:
            rows.append({"etape": "promulgation", "chambre": "", "lecture": "", "date": e["date"], "issue": "",
                         "detail": e["detail"] or ""})
    rank = {"depot": 0, "lecture": 1, "cmp": 1, "cc": 2, "promulgation": 3}
    rows.sort(key=lambda r: (r["date"], rank[r["etape"]]))
    return [{"texte_id": uid, "ordre": i, **{k: r.get(k) or None for k in COLONNES[2:]}} for i, r in enumerate(rows, 1)]

"""Lecture des dumps de l'Assemblée nationale : scrutins, votes nominatifs, dossiers, députés.

Repris de quifaitlaloi (scrutins, ventilations et correction `PO0`, dossiers), complété des
votes nominatifs, des mises au point et des mandats des députés (docs/SOURCES.md).
"""

import json
import sys
from collections import Counter
from functools import cache
from pathlib import Path

from .referentiels import lignee
from .sources import extraits
from .texte import objet_scrutin

LEGISLATURES = (16, 17)
# Positions nominatives : clé du dump → code des exports
POSITIONS = {"pours": "pour", "contres": "contre", "abstentions": "abstention", "nonVotants": "non_votant"}


def _int(v) -> int:
    return int(v or 0)


def _liste(v) -> list:
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


def nul(v):
    """Valeur d'un champ, `None` pour les nils XML (`{"@xsi:nil": "true"}`)."""
    return None if isinstance(v, dict) and "@xsi:nil" in v else v


def _votants(bloc) -> list[dict]:
    """Votants d'un bloc nominatif. Le dump les range tantôt sous `votant`, tantôt dans une
    liste dont certains éléments sont nuls (mises au point)."""
    out = []
    for b in _liste(bloc):
        if isinstance(b, dict):
            out += [v for v in _liste(b.get("votant")) if v]
    return out


# --- Mandats (AMO) ---------------------------------------------------------------

@cache
def _acteurs(raw: Path) -> dict[str, dict]:
    out = {}
    for p in (extraits(raw, "an_amo") / "json/acteur").glob("*.json"):
        a = json.loads(p.read_text())["acteur"]
        uid = a["uid"]["#text"] if isinstance(a["uid"], dict) else a["uid"]
        out[uid] = a
    return out


@cache
def _mandats_gp(raw: Path) -> dict[str, list[tuple[str, str, str]]]:
    """acteurRef → [(organeRef, début, fin)] des mandats de groupe politique."""
    out: dict[str, list] = {}
    for uid, a in _acteurs(raw).items():
        for m in _liste((a.get("mandats") or {}).get("mandat")):
            if m.get("typeOrgane") == "GP":
                out.setdefault(uid, []).append(
                    (m["organes"]["organeRef"], m["dateDebut"], m.get("dateFin") or "9999"))
    return out


def _groupe_a_date(raw: Path, acteur: str, date: str) -> str | None:
    for organe, debut, fin in _mandats_gp(raw).get(acteur, []):
        if debut <= date <= fin:
            return organe
    return None


def _resoudre_organe(raw: Path, groupe: dict, date: str) -> str | None:
    """Organe d'une ventilation notée `PO0` (anomalie du dump) : groupe majoritaire de ses votants à la date."""
    nom = groupe["vote"].get("decompteNominatif") or {}
    c = Counter(o for k in POSITIONS for v in _votants(nom.get(k)) if (o := _groupe_a_date(raw, v["acteurRef"], date)))
    return c.most_common(1)[0][0] if c else None


def deputes(raw: Path) -> tuple[list[dict], list[dict], list[dict]]:
    """Députés ayant siégé sous les législatures du périmètre : identité, mandats de député
    (circonscription, dates) et mandats de groupe."""
    rows, mandats, groupes = [], [], []
    for uid, a in sorted(_acteurs(raw).items()):
        ms = _liste((a.get("mandats") or {}).get("mandat"))
        an_ = [m for m in ms if m.get("typeOrgane") == "ASSEMBLEE" and _int(m.get("legislature")) in LEGISLATURES]
        if not an_:
            continue
        ident = a["etatCivil"]["ident"]
        rows.append({"id": uid, "civ": ident["civ"], "prenom": ident["prenom"], "nom": ident["nom"],
                     "nom_tri": ident["alpha"]})
        for m in an_:
            lieu = m["election"]["lieu"]
            mandats.append({"id": m["uid"], "acteur_id": uid, "legislature": _int(m["legislature"]),
                            "departement": lieu["departement"], "num_departement": lieu["numDepartement"],
                            "num_circo": _int(lieu["numCirco"]), "debut": m["dateDebut"],
                            "fin": nul(m.get("dateFin")), "cause_mandat": m["election"].get("causeMandat"),
                            "cause_fin": nul((m.get("mandature") or {}).get("causeFin"))})
        for m in ms:
            if m.get("typeOrgane") == "GP" and _int(m.get("legislature")) in LEGISLATURES:
                groupes.append({"acteur_id": uid, "groupe_id": m["organes"]["organeRef"],
                                "legislature": _int(m["legislature"]), "debut": m["dateDebut"],
                                "fin": nul(m.get("dateFin")), "qualite": m["infosQualite"]["codeQualite"]})
    return rows, mandats, groupes


def groupes(raw: Path, ids: set[str]) -> list[dict]:
    """Groupes politiques (organes GP) cités par les ventilations."""
    out = []
    for ref in sorted(ids):
        o = json.loads((extraits(raw, "an_amo") / f"json/organe/{ref}.json").read_text())["organe"]
        v = o.get("viMoDe") or {}
        out.append({"id": ref, "lignee": lignee(ref), "legislature": _int(o.get("legislature")),
                    "sigle": o.get("libelleAbrev"),
                    "nom": o.get("libelle"), "date_debut": v.get("dateDebut"), "date_fin": v.get("dateFin"),
                    "couleur": o.get("couleurAssociee")})
    return out


# --- Scrutins ----------------------------------------------------------------

def scrutins(raw: Path, legislature: int) -> dict[str, list[dict]]:
    """Scrutins publics d'une législature (hors Congrès), avec leur ventilation par groupe, les votes
    nominatifs et les mises au point."""
    rows, ventil, votes, mises = [], [], [], []
    anomalies = 0
    for p in sorted((extraits(raw, f"an_scrutins_{legislature}") / "json").glob("VTANR5*.json")):
        s = json.loads(p.read_text())["scrutin"]
        sv = s["syntheseVote"]
        dec = sv["decompte"]
        obj = s.get("objet") or {}
        dl = obj.get("dossierLegislatif")
        rows.append({
            "id": s["uid"],
            "legislature": legislature,
            "numero": int(s["numero"]),
            "date": s["dateScrutin"],
            "seance": s.get("seanceRef"),
            "type_vote": s["typeVote"]["codeTypeVote"],
            "titre": s["titre"],
            "objet": objet_scrutin(s["titre"]),
            "sort": "adopte" if s["sort"]["code"] == "adopté" else "rejete",
            "pour": _int(dec["pour"]),
            "contre": _int(dec["contre"]),
            "abstention": _int(dec["abstentions"]),
            "non_votants": _int(dec.get("nonVotants")),
            "votants": _int(sv["nombreVotants"]),
            "exprimes": _int(sv["suffragesExprimes"]),
            "requis": _int(sv["nbrSuffragesRequis"]),
            "demandeur": (s.get("demandeur") or {}).get("texte"),
            "dossier_objet": dl.get("dossierRef") if isinstance(dl, dict) else None,
        })
        for g in _liste(s["ventilationVotes"]["organe"]["groupes"]["groupe"]):
            organe = g["organeRef"]
            if organe == "PO0":
                anomalies += 1
                organe = _resoudre_organe(raw, g, s["dateScrutin"])
                if organe is None:
                    continue  # aucun votant : la ventilation n'apporte aucune voix
            dv = g["vote"]["decompteVoix"]
            ventil.append({
                "scrutin_id": s["uid"],
                "groupe_id": organe,
                "membres": _int(g["nombreMembresGroupe"]),
                "pour": _int(dv["pour"]),
                "contre": _int(dv["contre"]),
                "abstention": _int(dv["abstentions"]),
                # nonVotantsVolontaires recopie toujours les abstentions (XVIe et XVIIe) : ignoré
                "non_votants": _int(dv.get("nonVotants")),
            })
            nom = g["vote"].get("decompteNominatif") or {}
            for k, pos in POSITIONS.items():
                for v in _votants(nom.get(k)):
                    votes.append({"scrutin_id": s["uid"], "acteur_id": v["acteurRef"], "groupe_id": organe,
                                  "position": pos, "delegation": v.get("parDelegation") == "true"})
        for k, pos in POSITIONS.items():
            for v in _votants((s.get("miseAuPoint") or {}).get(k)):
                mises.append({"scrutin_id": s["uid"], "acteur_id": v["acteurRef"], "position": pos})
    if anomalies:
        print(f"AN XV{'I' * (legislature - 15)}e : {anomalies} ventilations sans organe (PO0) "
              "rattachées par les mandats de leurs votants", file=sys.stderr)
    return {"scrutins": rows, "ventilations": ventil, "votes": votes, "mises_au_point": mises}


# --- Dossiers ----------------------------------------------------------------

def dossiers(raw: Path, legislature: int) -> dict[str, dict]:
    """uid → dossierParlementaire."""
    d = extraits(raw, f"an_dossiers_{legislature}") / "json/dossierParlementaire"
    return {p.stem: json.loads(p.read_text())["dossierParlementaire"] for p in d.glob("*.json")}


def enfants(acte: dict) -> list[dict]:
    return _liste((acte.get("actesLegislatifs") or {}).get("acteLegislatif"))


def parcourir(acte: dict):
    yield acte
    for e in enfants(acte):
        yield from parcourir(e)


def vote_refs(acte: dict) -> list[str]:
    return _liste((acte.get("voteRefs") or {}).get("voteRef"))

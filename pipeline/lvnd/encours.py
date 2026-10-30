"""Où en est chaque texte (adapté de quifaitlaloi, docs/SOURCES.md).

Textes en cours : un dossier AN, ni promulgué ni adopté définitivement, dont au moins une lecture a
été conclue en séance (AN ou Sénat) depuis le début de la XVIIe. Il est écarté s'il est retiré, rejeté
(Dosleg, ou rejet en première lecture par la première assemblée saisie, hors textes financiers), caduc
ou fusionné, ou s'il n'a connu aucun acte de procédure depuis `INACTIVITE_MOIS` mois. Les écartés
restent dans l'export, avec leur motif (`motif_ecart`), pour l'audit.

État : une valeur pour chaque texte du catalogue, y compris ceux de la XVIe (`etat`).

Ces exports (`en_cours*.csv`) sont à part : ils décrivent des textes et n'entrent dans aucun score.
"""

import re
from datetime import date

from . import an, parcours
from .texte import typographie
from .textes import URL_AN, _date, _initiative

INACTIVITE_MOIS = 12
DEBUT = parcours.DEBUTS[max(parcours.DEBUTS)]
FINANCIERS = ("finances", "financement_ss")
AUTRE_CHAMBRE = {"AN": "SN", "SN": "AN"}
URL_SENAT = "https://www.senat.fr/dossier-legislatif/{signet}.html"


def seuil_inactivite(date_ref: str, mois: int = INACTIVITE_MOIS) -> str:
    """Date avant laquelle un texte sans acte de procédure est jugé à l'arrêt (`date_ref` − `mois`)."""
    d = date.fromisoformat(date_ref)
    a, m = divmod(d.month - 1 - mois, 12)
    an_, mois_ = d.year + a, m + 1
    jour = min(d.day, 28 if mois_ == 2 else 30 if mois_ in (4, 6, 9, 11) else 31)
    return date(an_, mois_, jour).isoformat()


def _sans_doublon(titre: str) -> str:
    """« Projet de loi Projet de loi-cadre relatif… » (titre de dossier AN) → « Projet de loi-cadre relatif… »."""
    return re.sub(r"^(?:projet|proposition) de loi\s+(?=(?:projet|proposition) de loi)", "", titre, flags=re.I)


def closes(lectures: list[dict]) -> list[dict]:
    return [l for l in lectures if l["dec"] is not None]


def completer_senat(lectures: list[dict], loicod: str | None, decisions: dict, idx: parcours.Index) -> None:
    """Décision d'une lecture du Sénat que le dossier AN n'a pas encore enregistrée : lue dans
    Dosleg (texte adopté ou rejeté en séance), à défaut sur le scrutin public sur l'ensemble (ou la
    question préalable adoptée) de la même lecture. La lecture est marquée `decision_dosleg`."""
    if not loicod:
        return
    for l in lectures:
        if l["chambre"] != "SN" or l["dec"] is not None:
            continue
        dec = decisions.get((loicod, l["typlec"]))
        if dec is None:
            scr = [s for s in idx.sn.get((loicod, l["typlec"]), [])
                   if s["objet"] in ("ensemble", "article_unique") or (s["objet"] == "motion_rejet" and s["sort"] == "adopte")]
            if scr:
                s = max(scr, key=lambda s: (s["date"], s["numero"]))
                dec = (s["date"], "rejete" if s["objet"] == "motion_rejet" or s["sort"] == "rejete" else "adopte")
        if dec is None:
            continue
        jour, issue = dec
        l["dec"] = {"uid": f"{l['dossier']}-{l['etape']}-dosleg", "codeActe": f"{l['etape']}-DEBATS-DEC",
                    "dateActe": jour, "statutConclusion": {"fam_code": "TSORTF01" if issue == "adopte" else "TSORTF07"}}
        l["date"] = jour
        l["decision_dosleg"] = True
    lectures.sort(key=lambda l: (l["date"] or "9999", l["ordre_brut"]))


def motif_ecart(lectures: list[dict], evts: list[dict], type_loi: str, etat_dosleg: str | None,
                derniere_activite: str, date_ref: str) -> str | None:
    """Règle de périmètre : None si le texte est vivant, sinon le motif de son écart.

    Dans l'ordre : retrait (dossier AN ou Dosleg) ; rejet, caducité ou fusion selon Dosleg ;
    rejet de la première lecture par la première assemblée saisie (le texte n'est pas transmis),
    sauf pour une loi de finances ou de financement, transmise malgré le rejet ; aucun acte de
    procédure (dépôt, commission, séance, vote, y compris une séance déjà inscrite à l'ordre du
    jour) depuis `INACTIVITE_MOIS` mois. Un rejet suivi d'une autre lecture dans le dossier n'écarte
    pas le texte (il a été transmis).
    """
    if etat_dosleg == "retire" or any(e["type"] == "retrait" for e in evts):
        return "retire"
    if etat_dosleg in ("rejete", "caduc", "fusionne"):
        return etat_dosleg
    if lectures:
        premiere = min(lectures, key=lambda l: l["rang"])
        suite = any(l["rang"] > premiere["rang"] for l in lectures)  # transmis malgré le rejet (comptes de la Sécurité sociale)
        if (premiere["dec"] is not None and premiere["type_lecture"] == "premiere" and type_loi not in FINANCIERS
                and not suite and parcours._statut(premiere["dec"])["issue"] == "rejete"):
            return "rejete"
    if derniere_activite < seuil_inactivite(date_ref):
        return "inactif"
    return None


def attente(lectures: list[dict], evts: list[dict], type_loi: str = "ordinaire") -> dict:
    """Où en est le texte, d'après ce que les dossiers enregistrent (aucun calendrier supposé).

    - `lecture` : une étape est ouverte dans le dossier (texte déposé ou transmis, pas encore voté) ;
    - `cmp` : commission mixte paritaire convoquée, sans issue enregistrée ;
    - `cmp_conclusions` : accord en CMP, conclusions pas encore votées dans les deux chambres ;
    - `transmis` : dernier vote favorable, étape suivante pas encore ouverte dans le dossier (le texte
      va à l'autre chambre, art. 45 de la Constitution). Un texte financier rejeté en première lecture
      par l'Assemblée est lui aussi transmis au Sénat (art. 47 et 47-1) ;
    - `navette` : dernier vote défavorable, ou désaccord en CMP, sans suite enregistrée.
    """
    cl = closes(lectures)
    der = max(cl, key=lambda l: (l["date"], l["rang"]))
    ouvertes = [l for l in lectures if l["dec"] is None and l["rang"] > der["rang"]]
    if ouvertes:
        o = max(ouvertes, key=lambda l: l["rang"])
        return {"attente": "lecture", "etape": o["etape"], "chambre": o["chambre"], "type_lecture": o["type_lecture"]}
    if der["type_lecture"] == "cmp":
        lues = {l["chambre"] for l in cl if l["type_lecture"] == "cmp"}
        reste = [c for c in ("AN", "SN") if c not in lues]
        return {"attente": "cmp_conclusions", "etape": "CMP", "chambre": reste[0] if len(reste) == 1 else None,
                "type_lecture": "cmp"}
    cmp_ = [e for e in evts if e["type"] in ("cmp_convoquee", "cmp_accord", "cmp_desaccord") and e["date"]
            and e["date"] >= der["date"]]
    if cmp_:
        rang = {"cmp_convoquee": 0, "cmp_accord": 1, "cmp_desaccord": 1}
        e = max(cmp_, key=lambda e: (e["date"], rang[e["type"]]))
        if e["type"] == "cmp_accord":
            return {"attente": "cmp_conclusions", "etape": "CMP", "chambre": None, "type_lecture": "cmp"}
        if e["type"] == "cmp_convoquee":
            return {"attente": "cmp", "etape": "CMP", "chambre": "CMP", "type_lecture": "cmp"}
        return {"attente": "navette", "etape": None, "chambre": None, "type_lecture": None}
    issue = parcours._statut(der["dec"])["issue"]
    if issue == "adopte" or (type_loi in FINANCIERS and der["chambre"] == "AN" and der["type_lecture"] == "premiere"):
        return {"attente": "transmis", "etape": None, "chambre": AUTRE_CHAMBRE.get(der["chambre"]), "type_lecture": None}
    return {"attente": "navette", "etape": None, "chambre": None, "type_lecture": None}


def seance_inscrite(d: dict, att: dict | None, seances_senat: list[str], seances_agenda: list[str],
                    date_ref: str) -> str | None:
    """Première séance à venir (date ≥ `date_ref`) où le texte est inscrit : agenda de l'AN ; pour
    l'étape attendue, séance du dossier AN (`…-DEBATS-SEANCE` datée) ou du Sénat dans Dosleg (table
    date_seance). Inscrit ne veut pas dire voté."""
    futures = [s for s in seances_agenda if s >= date_ref]
    if att and att["attente"] in ("lecture", "cmp_conclusions"):
        for e in an.enfants(d):
            if e["codeActe"] != att["etape"]:
                continue
            for a in an.parcourir(e):
                c = a["codeActe"]
                if "-DEBATS-" in c and c.endswith("-SEANCE") and _date(a) >= date_ref:
                    ch = "SN" if (c.startswith("SN") or "-SN-" in c) else "AN"
                    if att["chambre"] in (None, ch):
                        futures.append(_date(a))
        if att["chambre"] in ("SN", None):
            futures += [s for s in seances_senat if s >= date_ref]
    return min(futures, default=None)


def etat(statut: str, lectures: list[dict], motif: str | None) -> str:
    """État d'un texte : `loi`, `adopte` (pas encore promulgué), `en_navette`, `avant_vote` (déposé ou
    en commission, aucun vote en séance), `hors_navette` (résolution, engagement de la responsabilité :
    aucune lecture), `a_l_arret` (aucun acte depuis `INACTIVITE_MOIS` mois), `rejete`, `retire`,
    `caduc` ou `fusionne`."""
    if statut == "promulguee":
        return "loi"
    if statut == "adoptee":
        return "adopte"
    if not lectures:
        return "hors_navette"
    if motif == "inactif":
        return "a_l_arret"
    if motif:
        return motif
    return "en_navette" if closes(lectures) else "avant_vote"


def textes(classes: list[dict], idx: parcours.Index, dosleg: dict, exclus: set[str], date_ref: str,
           points_agenda: list[dict] = ()) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    """Textes en cours (et écartés, avec leur motif), leurs lectures votées, leurs événements, et l'état
    de chaque dossier.

    `classes` : `parcours.classer`. `exclus` : scrutins déjà décisifs pour une loi, qu'une lecture d'un
    texte en cours ne peut pas reprendre. `dosleg` : `decisions` (senat.decisions_seance), `activite`
    et `seances` (par loicod), `etats` (loicod → état Dosleg). `points_agenda` : `agenda.points`.
    """
    rows, toutes, rows_evt, rows_etat = [], [], [], []
    inscrit: dict[str, list[str]] = {}  # dossier → dates où il est inscrit, séance ou commission
    en_seance: dict[str, list[str]] = {}
    for p in points_agenda:
        inscrit.setdefault(p["dossier_id"], []).append(p["date"])
        if p["instance"] == "seance":
            en_seance.setdefault(p["dossier_id"], []).append(p["date"])
    autres = [c for c in classes if c["statut"] == "autre"]

    # Un dossier Sénat peut correspondre à deux dossiers AN (projet de loi constitutionnelle sur la
    # Corse : dossier du dépôt au Sénat, puis dossier du texte examiné). Les décisions lues dans
    # Dosleg ne complètent que le dossier principal : le plus avancé, puis le plus récent.
    def avance(c: dict) -> tuple:
        return (len(closes(c["lectures"])), max((l["date"] or "" for l in c["lectures"]), default=""), c["uid"])
    principal: dict[str, str] = {}
    for c in sorted(autres, key=avance):
        if c["sn"]:
            principal[c["sn"]["loicod"]] = c["uid"]
    for c in classes:
        uid, d, lectures, evts, sn = c["uid"], c["dossier"], c["lectures"], c["evts"], c["sn"]
        loicod = sn["loicod"] if sn else None
        if c["statut"] != "autre":
            rows_etat.append(_ligne_etat(uid, etat(c["statut"], lectures, None), None, lectures, None, None, None, date_ref))
            continue
        if loicod and principal.get(loicod) == uid:
            completer_senat(lectures, loicod, dosleg["decisions"], idx)
        cl = closes(lectures)
        titre = typographie(d["titreDossier"]["titre"])
        complet = next((typographie(t) for t in c["titres"][1:] if t and t.lower().startswith(("projet", "proposition"))),
                       None) if not titre.lower().startswith(("projet", "proposition")) else titre
        complet = complet[:1].upper() + complet[1:] if complet else None  # titres de documents en minuscule
        typ, sous_type = parcours.type_loi(d, complet or titre, sn["typloicod"] if sn else None)
        actes = [a for e in an.enfants(d) for a in an.parcourir(e)]
        dates = [_date(a) for a in actes if _date(a)] + [l["date"] for l in cl]
        dates += dosleg["activite"].get(loicod, []) if loicod else []
        dates += inscrit.get(uid, [])
        etat_dosleg = dosleg["etats"].get(loicod) if loicod else None
        motif = motif_ecart(lectures, evts, typ, etat_dosleg, max(dates, default=""), date_ref)
        att = attente(lectures, evts, typ) if cl else None
        seance = seance_inscrite(d, att, dosleg["seances"].get(loicod, []) if loicod else [],
                                 en_seance.get(uid, []), date_ref)
        rows_etat.append(_ligne_etat(uid, etat("autre", lectures, motif), motif, lectures, att, dates, seance, date_ref))
        if not any(l["date"] >= DEBUT for l in cl):
            continue
        for l in lectures:
            l["ctx"] = (c["titres"], typ)
            l["exclus"] = set(exclus)
            l.update(parcours.qualifier(l, idx, *l["ctx"]))
            l["texte_id"] = uid
        der = max(cl, key=lambda l: (l["date"], l["rang"]))
        rows.append({
            "id": uid,
            "statut": "en_cours",
            "motif_ecart": motif,
            "titre": _sans_doublon(complet or titre),
            "titre_dossier": titre,
            "type": typ,
            "sous_type": sous_type,
            "initiative": _initiative(d),
            "procedure_an": (d.get("procedureParlementaire") or {}).get("libelle"),
            "date_depot": min((_date(a) for a in actes if a["codeActe"].endswith("-DEPOT") and _date(a)), default=None),
            "date_derniere_lecture": der["date"],
            "issue_derniere_lecture": parcours._statut(der["dec"])["issue"],
            "date_derniere_activite": _derniere_activite(dates, date_ref),
            "attente": att["attente"],
            "attente_etape": att["etape"],
            "attente_chambre": att["chambre"],
            "attente_type_lecture": att["type_lecture"],
            "seance_inscrite": seance,
            "legislature": parcours.legislature(der["date"]),
            "dossier_an": uid,
            "signet_senat": sn["signet"] if sn else c["signet"],
            "loicod_senat": loicod,
            "etat_dosleg": etat_dosleg,
            "url_an": URL_AN.format(leg=d.get("legislature") or 17, chemin=d["titreDossier"]["titreChemin"]),
            "url_senat": URL_SENAT.format(signet=sn["signet"] if sn else c["signet"]) if (sn or c["signet"]) else None,
            "procedure_acceleree": any(e["type"] == "procedure_acceleree" for e in evts),
        })
        # lectures votées seulement : l'étape ouverte est décrite par `attente`. Une lecture close sans
        # décision et suivie d'une autre (délais budgétaires) reste, comme pour les lois.
        toutes += [l for l in lectures if l["dec"] is not None or l["rang"] < der["rang"]]
        rows_evt += [{"texte_id": uid, **e} for e in evts]
    parcours._departager(toutes, idx)
    cols = ("id", "texte_id", "dossier", "etape", "chambre", "type_lecture", "date", "statut_code", "statut",
            "issue", "decision_deduite", "art_49_3", "mode_adoption", "scrutin_id", "rattachement")
    rows_lect = [{**{k: l[k] for k in cols}, "decision_dosleg": bool(l.get("decision_dosleg"))} for l in toutes]
    return rows, rows_lect, rows_evt, rows_etat


def _derniere_activite(dates: list[str], date_ref: str) -> str | None:
    return max((x for x in dates if x <= date_ref), default=None)


def _ligne_etat(uid: str, etat_: str, motif: str | None, lectures: list[dict], att: dict | None,
                dates: list[str] | None, seance: str | None, date_ref: str) -> dict:
    cl = closes(lectures)
    der = max(cl, key=lambda l: (l["date"], l["rang"])) if cl else None
    return {
        "id": uid,
        "etat": etat_,
        "attente": att["attente"] if att and not motif else None,
        "attente_chambre": att["chambre"] if att and not motif else None,
        "date_derniere_lecture": der["date"] if der else None,
        "issue_derniere_lecture": parcours._statut(der["dec"])["issue"] if der else None,
        "date_derniere_activite": _derniere_activite(dates, date_ref) if dates else None,
        "seance_inscrite": seance if not motif else None,
    }

"""Textes (dossiers législatifs AN) et rattachement de chaque scrutin à son dossier.

Le dossier d'un scrutin se lit, dans l'ordre :

1. `objet.dossierLegislatif` du scrutin (depuis mars 2026 seulement) ;
2. `voteRefs` d'une décision du dossier ;
3. l'amendement mis aux voix (`amendements.rattacher`) ;
4. la séance : les dossiers débattus dans la séance du scrutin, départagés par le titre (seuil
   `SEUIL_TITRE`) et par la mention « loi organique » de l'intitulé.

Le scrutin décisif *proposé* est le dernier scrutin de l'AN sur l'ensemble du texte
(docs/METHODO.md, règle 9). Il n'est qu'une proposition : la qualification le confirme.
"""

import json
import re
from collections import defaultdict
from pathlib import Path

from . import an
from .sources import extraits
from .texte import norm, similarite

SEUIL_TITRE = 0.5
ENSEMBLE = ("ensemble", "article_unique")
ELI = "https://www.legifrance.gouv.fr/eli/loi/{a}/{m}/{j}/{nor}/jo/texte"
URL_AN = "https://www.assemblee-nationale.fr/dyn/{leg}/dossiers/{chemin}"


def _date(a: dict) -> str:
    return (a.get("dateActe") or "")[:10]


def documents(raw: Path) -> tuple[dict[str, str], dict[str, set[str]]]:
    """(texte → dossier, dossier → titres des textes déposés ou adoptés). Le titre d'un texte change
    en navette : l'intitulé d'un scrutin reprend parfois celui du dépôt."""
    dossier_de, titres = {}, defaultdict(set)
    for leg in an.LEGISLATURES:
        for p in (extraits(raw, f"an_dossiers_{leg}") / "json/document").glob("*.json"):
            doc = json.loads(p.read_text())["document"]
            if not doc.get("dossierRef"):
                continue
            dossier_de[doc["uid"]] = doc["dossierRef"]
            if p.stem.startswith(("PRJL", "PION")) and "BTC" not in p.stem:  # textes de commission : titres tronqués
                titres[doc["dossierRef"]].add(doc["titres"]["titrePrincipal"])
    return dossier_de, titres


def tous_dossiers(raw: Path) -> dict[str, dict]:
    """Dossiers des dumps du périmètre. Un dossier présent dans deux dumps : la version la plus
    récente est au moins aussi complète."""
    return {uid: d for leg in an.LEGISLATURES for uid, d in an.dossiers(raw, leg).items()}


def _organique(d: dict) -> bool:
    return "organique" in norm((d.get("procedureParlementaire") or {}).get("libelle"))


class Index:
    """Séances et `voteRefs` des dossiers, côté AN."""

    def __init__(self, dossiers: dict[str, dict]):
        self.par_seance: dict[str, set[str]] = defaultdict(set)
        self.par_jour: dict[str, set[str]] = defaultdict(set)
        self.vote_refs: dict[str, str] = {}
        self.etape: dict[tuple[str, str], str] = {}  # (dossier, séance) → étape (AN1, CMP…)
        self.etape_jour: dict[tuple[str, str], str] = {}  # (dossier, jour) → étape, à défaut de séance
        for uid, d in dossiers.items():
            for e in an.enfants(d):
                for a in an.parcourir(e):
                    c = a["codeActe"]
                    for r in an.vote_refs(a):
                        self.vote_refs.setdefault(r, uid)
                    if "-DEBATS-" not in c or "-SN-" in c or c.startswith("SN"):
                        continue
                    if a.get("reunionRef"):
                        self.par_seance[a["reunionRef"]].add(uid)
                        self.etape[(uid, a["reunionRef"])] = e["codeActe"]
                    elif not c.endswith("-DEC"):
                        continue
                    # XVIe : des lectures de CMP n'ont que l'acte de décision, sans séance (industrie verte, LOPMI)
                    if jour := _date(a):
                        self.par_jour[jour].add(uid)
                        self.etape_jour.setdefault((uid, jour), e["codeActe"])


def rattacher(scrutins: list[dict], dossiers: dict[str, dict], titres: dict[str, set[str]],
              par_amendement: dict[str, dict]) -> dict[str, dict]:
    """scrutin_id → {dossier_id, etape, rattachement}."""
    idx = Index(dossiers)

    def titres_de(uid: str) -> list[str]:
        return [dossiers[uid]["titreDossier"]["titre"], *sorted(titres.get(uid, ()))]

    def par_titre(s: dict, cands: set[str]) -> str | None:
        org = "loi organique" in norm(s["titre"])
        cands = {c for c in cands if c in dossiers}
        if len(cands) > 1:
            cands = {c for c in cands if _organique(dossiers[c]) == org} or cands
        notes = sorted(((max(similarite(s["titre"], t) for t in titres_de(c)), c) for c in cands), reverse=True)
        if not notes:
            return None
        if len(notes) == 1 and s["objet"] not in ("ensemble", "article_unique", "motion_rejet"):
            return notes[0][1]  # un seul dossier débattu dans la séance
        if notes[0][0] >= SEUIL_TITRE and (len(notes) == 1 or notes[0][0] > notes[1][0]):
            return notes[0][1]
        return None

    out = {}
    for s in scrutins:
        uid, how = None, None
        if s["dossier_objet"]:
            uid, how = s["dossier_objet"], "objet"
        elif s["id"] in idx.vote_refs:
            uid, how = idx.vote_refs[s["id"]], "voteRefs"
        elif s["id"] in par_amendement and par_amendement[s["id"]]["dossier_id"]:
            uid, how = par_amendement[s["id"]]["dossier_id"], "amendement"
        elif s["seance"] and (u := par_titre(s, idx.par_seance.get(s["seance"], set()))):
            uid, how = u, "seance"
        elif u := par_titre(s, idx.par_jour.get(s["date"], set())):
            uid, how = u, "jour"
        if uid:
            etape = idx.etape.get((uid, s["seance"])) or idx.etape_jour.get((uid, s["date"]))
            out[s["id"]] = {"dossier_id": uid, "etape": etape, "rattachement": how}
    return out


def _acte(d: dict, code: str) -> dict | None:
    actes = [a for e in an.enfants(d) for a in an.parcourir(e) if a["codeActe"] == code]
    return actes[-1] if actes else None


def _decision(cc: dict) -> str | None:
    """Numéro de la décision du Conseil constitutionnel. Il porte l'année de la saisine, que l'URL
    conserve (« 2023-863 DC », rendue le 25/01/2024) ; `anneeDecision` donne celle de la décision."""
    if m := re.search(r"/(\d{4})(\d+)DC\.htm", cc.get("urlConclusion") or ""):
        return f"{m.group(1)}-{int(m.group(2))} DC"
    return f"{cc['anneeDecision']}-{cc['numDecision']} DC" if cc.get("numDecision") else None


def _initiative(d: dict) -> str:
    for e in an.enfants(d):
        for a in an.parcourir(e):
            if a["codeActe"].endswith("-DEPOT") and a.get("texteAssocie"):
                return "projet" if a["texteAssocie"].startswith("PRJL") else "proposition"
    return "inconnue"


def catalogue(dossiers: dict[str, dict], scrutins: list[dict], liens: dict[str, dict]) -> list[dict]:
    """Une ligne par dossier ayant au moins un scrutin public à l'AN dans le périmètre."""
    par_dossier: dict[str, list[dict]] = defaultdict(list)
    for s in scrutins:
        if s["id"] in liens:
            par_dossier[liens[s["id"]]["dossier_id"]].append(s)
    rows = []
    for uid, ss in sorted(par_dossier.items()):
        d = dossiers.get(uid)
        if d is None:
            continue  # dossier d'une autre législature (XVe) cité par `objet`
        ss.sort(key=lambda s: (s["date"], s["numero"]))
        ensembles = [s for s in ss if s["objet"] in ENSEMBLE]
        prom = _acte(d, "PROM-PUB")
        cc = _acte(d, "CC-CONCLUSION")
        jo = (prom or {}).get("infoJO") or {}
        date_loi = _date(prom) if prom else None
        url_loi = None
        if date_loi and jo.get("referenceNOR"):
            a, m, j = date_loi.split("-")
            url_loi = ELI.format(a=a, m=int(m), j=int(j), nor=jo["referenceNOR"])
        rows.append({
            "id": uid,
            "legislature": int(d["legislature"]),
            "titre": d["titreDossier"]["titre"],
            "procedure": (d.get("procedureParlementaire") or {}).get("libelle"),
            "initiative": _initiative(d),
            "url_an": URL_AN.format(leg=d["legislature"], chemin=d["titreDossier"]["titreChemin"]),
            "loi": (prom or {}).get("codeLoi"),
            "date_loi": date_loi,
            "nor": jo.get("referenceNOR"),
            "url_loi": url_loi,
            "cc_decision": _decision(cc) if cc else None,
            "cc_sens": (cc.get("statutConclusion") or {}).get("libelle") if cc else None,
            "cc_url": ((cc.get("urlConclusion") or "").replace("http://", "https://") or None) if cc else None,
            "n_scrutins": len(ss),
            "n_amendements": sum(s["objet"] in ("amendement", "suppression_article_unique") for s in ss),
            "n_ensemble": len(ensembles),
            "decisif_propose": ensembles[-1]["id"] if ensembles else None,
            "premier_scrutin": ss[0]["date"],
            "dernier_scrutin": ss[-1]["date"],
        })
    return rows


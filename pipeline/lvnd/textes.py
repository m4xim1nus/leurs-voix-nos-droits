"""Textes (dossiers législatifs AN) et rattachement de chaque scrutin à son dossier.

Le dossier d'un scrutin se lit, dans l'ordre :

1. `objet.dossierLegislatif` du scrutin (depuis mars 2026 seulement) ;
2. `voteRefs` d'une décision du dossier ; une motion de censure citée par le texte et par son engagement de
   responsabilité va à l'engagement, dans tous les cas ;
3. l'amendement mis aux voix (`amendements.rattacher`), sauf s'il est contredit par le référentiel ou par le titre
   du scrutin : il porte alors le même numéro dans un autre texte, et il est refusé ;
4. la séance : les dossiers débattus dans la séance du scrutin, départagés par le titre (seuil
   `SEUIL_TITRE`) et par la mention « loi organique » de l'intitulé ;
5. pour une poignée de scrutins de la XVe, figée, `referentiels/rattachements.yaml`.

Le scrutin décisif *proposé* est le dernier scrutin de l'AN sur l'ensemble du texte
(docs/METHODO.md, règle 9). Il n'est qu'une proposition : la qualification le confirme.
"""

import json
import re
from collections import defaultdict
from pathlib import Path

from . import an
from .referentiels import rattachements
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
    return (an.dossiers_xiv(raw, rattachements()["dossiers_xiv"])
            | {uid: d for leg in an.LEGISLATURES for uid, d in an.dossiers(raw, leg).items()})


def _organique(d: dict) -> bool:
    return "organique" in norm((d.get("procedureParlementaire") or {}).get("libelle"))


def _engagement(d: dict) -> bool:
    """Dossier d'engagement de responsabilité (article 49, alinéa 3)."""
    return (d.get("procedureParlementaire") or {}).get("code") == "13"


class Index:
    """Séances et `voteRefs` des dossiers, côté AN."""

    def __init__(self, dossiers: dict[str, dict]):
        self.par_seance: dict[str, set[str]] = defaultdict(set)
        self.par_jour: dict[str, set[str]] = defaultdict(set)
        self.vote_refs: dict[str, str] = {}
        self.etape: dict[tuple[str, str], str] = {}  # (dossier, séance) → étape (AN1, CMP…)
        self.etape_jour: dict[tuple[str, str], str] = {}  # (dossier, jour) → étape, à défaut de séance
        for uid in sorted(dossiers, key=lambda u: (not _engagement(dossiers[u]), u)):  # `setdefault` : les engagements d'abord
            d = dossiers[uid]
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


CODE_DECLARATION = "11"  # procédure « Déclaration du gouvernement avec ou sans vote sans engagement de responsabilité »


def _rattachements_fixes() -> dict[str, dict]:
    """scrutin → {dossier_id, etape}, d'après le référentiel (numéros « 57 » ou « 57-84 », de la XVe)."""
    out = {}
    for r in rattachements()["scrutins"]:
        for n in str(r["numeros"]).split():
            debut, _, fin = n.partition("-")
            for i in range(int(debut), int(fin or debut) + 1):
                out[f"VTANR5L15V{i}"] = {"dossier_id": r["dossier"], "etape": r.get("etape")}
    return out


def rattacher(scrutins: list[dict], dossiers: dict[str, dict], titres: dict[str, set[str]],
              par_amendement: dict[str, dict]) -> dict[str, dict]:
    """scrutin_id → {dossier_id, etape, rattachement} ; `amendement_refuse` si l'amendement ne vient pas du bon texte."""
    idx = Index(dossiers)
    fixes = _rattachements_fixes()

    def titres_de(uid: str) -> list[str]:
        return [dossiers[uid]["titreDossier"]["titre"], *sorted(titres.get(uid, ()))]

    def note(s: dict, uid: str) -> float:
        return max(similarite(s["titre"], t) for t in titres_de(uid))

    def classement(s: dict, cands: set[str]) -> list[tuple[float, str]]:
        org = "loi organique" in norm(s["titre"])
        cands = {c for c in cands if c in dossiers}
        if len(cands) > 1:
            cands = {c for c in cands if _organique(dossiers[c]) == org} or cands
        return sorted(((note(s, c), c) for c in cands), reverse=True)

    def amendement_refuse(s: dict, uid: str) -> bool:
        """Même numéro dans un autre texte : le référentiel, ou un autre dossier débattu ce jour-là au titre nettement
        plus proche, le contredit."""
        if s["id"] in fixes:
            return fixes[s["id"]]["dossier_id"] != uid
        notes = classement(s, idx.par_seance.get(s["seance"]) or idx.par_jour.get(s["date"]) or set())
        return (bool(notes) and notes[0][1] != uid and notes[0][0] >= SEUIL_TITRE
                and (len(notes) == 1 or notes[0][0] > notes[1][0])
                and notes[0][0] > (note(s, uid) if uid in dossiers else 0))

    def par_titre(s: dict, cands: set[str]) -> str | None:
        # Déclaration du Gouvernement (art. 49 ou 50-1) : débattue le jour d'un texte, sans porter sur lui. Seul son
        # propre dossier, quand elle en a un, peut la recevoir.
        if norm(s["titre"]).startswith("la declaration"):
            cands = {c for c in cands if (dossiers.get(c, {}).get("procedureParlementaire") or {}).get("code") == CODE_DECLARATION}
        notes = classement(s, cands)
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
        d_amdt = (par_amendement.get(s["id"]) or {}).get("dossier_id")
        refuse = bool(d_amdt) and not s["dossier_objet"] and s["id"] not in idx.vote_refs and amendement_refuse(s, d_amdt)
        if s["dossier_objet"]:
            uid, how = s["dossier_objet"], "objet"
        elif s["id"] in idx.vote_refs:
            uid, how = idx.vote_refs[s["id"]], "voteRefs"
        elif d_amdt and not refuse:
            uid, how = d_amdt, "amendement"
        elif s["id"] in fixes:  # lu à la main : prime sur la proximité dans la séance
            out[s["id"]] = {**fixes[s["id"]], "rattachement": "referentiel", "amendement_refuse": refuse}
            continue
        elif s["seance"] and (u := par_titre(s, idx.par_seance.get(s["seance"], set()))):
            uid, how = u, "seance"
        elif u := par_titre(s, idx.par_jour.get(s["date"], set())):
            uid, how = u, "jour"
        if uid:
            etape = idx.etape.get((uid, s["seance"])) or idx.etape_jour.get((uid, s["date"]))
            out[s["id"]] = {"dossier_id": uid, "etape": etape, "rattachement": how, "amendement_refuse": refuse}
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


def _url_decision(cc: dict) -> str | None:
    """Adresse de la décision. Son dossier est l'année où elle est rendue, que l'open data peut manquer
    (2022-846 DC, rendue le 19/01/2023, donnée sous /decision/2022/, en 404) : `dateActe` fait foi."""
    url = (cc.get("urlConclusion") or "").replace("http://", "https://")
    url = url[url.rfind("https://"):]  # 2019-790 DC : l'open data répète le préfixe de l'adresse
    annee = (cc.get("dateActe") or "")[:4]
    return (re.sub(r"/decision/\d{4}/", f"/decision/{annee}/", url) if annee else url) or None


def _initiative(d: dict) -> str:
    for e in an.enfants(d):
        for a in an.parcourir(e):
            if a["codeActe"].endswith("-DEPOT") and a.get("texteAssocie"):
                return "projet" if a["texteAssocie"].startswith("PRJL") else "proposition"
    return "inconnue"


def _decisif(ss: list[dict], ensembles: list[dict]) -> str | None:
    """Dernier vote sur l'ensemble ; à défaut, la suppression adoptée de l'article unique (règle 9)."""
    if ensembles:
        return ensembles[-1]["id"]
    suppr = [s for s in ss if s["objet"] == "suppression_article_unique" and s["sort"] == "adopte"]
    return suppr[-1]["id"] if suppr else None


def catalogue(dossiers: dict[str, dict], scrutins: list[dict], liens: dict[str, dict],
              sans_scrutin: set[str] = frozenset()) -> list[dict]:
    """Une ligne par dossier ayant au moins un scrutin public à l'AN dans le périmètre, et par dossier
    de `sans_scrutin` (texte en cours ou inscrit à l'ordre du jour, sans scrutin public à l'AN)."""
    par_dossier: dict[str, list[dict]] = defaultdict(list)
    for uid in sans_scrutin:
        par_dossier[uid] = []
    for s in scrutins:
        if s["id"] in liens:
            par_dossier[liens[s["id"]]["dossier_id"]].append(s)
    rows = []
    for uid, ss in sorted(par_dossier.items()):
        d = dossiers.get(uid)
        if d is None:
            continue  # dossier hors des dumps, cité par `objet`
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
            "cc_url": _url_decision(cc) if cc else None,
            "n_scrutins": len(ss),
            "n_amendements": sum(s["objet"] in ("amendement", "suppression_article_unique") for s in ss),
            "n_ensemble": len(ensembles),
            "decisif_propose": _decisif(ss, ensembles),
            "premier_scrutin": ss[0]["date"] if ss else None,
            "dernier_scrutin": ss[-1]["date"] if ss else None,
            **(rattachements().get("catalogue") or {}).get(uid, {}),
        })
    return rows


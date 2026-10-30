"""Parcours d'un texte : lectures, issue de chacune, scrutin décisif et mode (adapté de quifaitlaloi).

Le dossier AN sert d'ossature : il porte toutes les lectures, Sénat compris. Le scrutin décisif d'une
lecture AN se trouve par `voteRefs`, à défaut par la séance et le titre. Les lectures du Sénat n'ont
pas de scrutin ici : ses votes restent au cycle Sénat.

Ce module décrit où en est un texte. Il ne touche ni au rattachement des scrutins aux dossiers
(`textes.rattacher`), ni aux scrutins retenus par une qualification, ni aux scores.
"""

import re
from collections import defaultdict
from difflib import SequenceMatcher

from . import an, referentiels
from .texte import cle_titre, mots_ordonnes, norm, similarite
from .textes import _date

# Début de chaque législature (première séance de l'AN).
DEBUTS = {16: "2022-06-28", 17: "2024-07-18"}
DECISIFS = {"ensemble", "article_unique", "partie", "motion_rejet", "suppression_article_unique"}
DEBUT_SCRUTINS = DEBUTS[16]  # scrutins ingérés : depuis la XVIe


def _statut(a: dict) -> dict:
    code = (a.get("statutConclusion") or {}).get("fam_code") or "TSORTFnull"
    try:
        return {"code": code, **referentiels.codes_actes()["statuts"][code]}
    except KeyError:
        raise SystemExit(f"statut de décision inconnu {code} ({a['uid']}) : compléter codes_actes.yaml") from None


# --- Lectures d'un dossier ---------------------------------------------------

def _chambres_cmp(decs: list[dict], dates: dict[str, set[str]]) -> list[str]:
    """Chambre de chaque lecture des conclusions de CMP.

    L'étiquette du code n'est pas fiable (une décision « SN » peut porter un scrutin AN, une décision
    peut n'avoir aucune chambre). Dans l'ordre : un `voteRefs` AN, la date d'une séance de la chambre
    (`dates`), l'étiquette, puis la chambre restante.
    """
    out: list[str | None] = [None] * len(decs)
    for i, a in enumerate(decs):
        if any(r.startswith("VTANR5") for r in an.vote_refs(a)):
            out[i] = "AN"
    for i, a in enumerate(decs):
        seule = [c for c in ("AN", "SN") if _date(a) in dates[c]]
        if out[i] is None and a["codeActe"] == "CMP-DEBATS-DEC" and len(seule) == 1 and seule[0] not in out:
            out[i] = seule[0]
    for i, a in enumerate(decs):
        lab = {"CMP-DEBATS-AN-DEC": "AN", "CMP-DEBATS-SN-DEC": "SN"}.get(a["codeActe"])
        if out[i] is None and lab and lab not in out:
            out[i] = lab
    for i in range(len(decs)):
        if out[i] is None:
            libres = [c for c in ("AN", "SN") if c not in out]
            out[i] = libres[0] if libres else "?"
    return out


def lectures_dossier(d: dict) -> tuple[list[dict], list[dict]]:
    """Lectures (une par décision de séance) et événements d'un dossier AN."""
    conf = referentiels.codes_actes()
    lectures, evts = [], []
    egarees: list[dict] = []  # décisions rangées sous une CMP en désaccord
    etapes = an.enfants(d)
    promulgue = any(a["codeActe"] == "PROM-PUB" for e in etapes for a in an.parcourir(e))
    for rang, etape in enumerate(etapes):
        code = etape["codeActe"]
        sous = list(an.parcourir(etape))
        evts += _evenements(code, sous)
        if code in conf["hors_lecture"]:
            continue
        if code not in conf["lectures"]:
            raise SystemExit(f"étape {code} inconnue ({d['uid']}) : compléter codes_actes.yaml")
        c = conf["lectures"][code]
        dgvt = [a for a in sous if a["codeActe"].endswith("-DGVT")]
        motions = [a for a in sous if a["codeActe"].endswith("-MOTION-VOTE")]
        seances = {a.get("reunionRef") for a in sous
                   if "-DEBATS-" in a["codeActe"] and a["codeActe"].endswith("-SEANCE") and "-SN-" not in a["codeActe"]}
        base = {"dossier": d["uid"], "etape": code, "type_lecture": c["type"], "typlec": c["typlec"], "rang": rang}
        if c["chambre"] == "CMP":
            cmp_dec = [a for a in sous if a["codeActe"] == "CMP-DEC"]
            decs = [a for a in sous if a["codeActe"] in ("CMP-DEBATS-AN-DEC", "CMP-DEBATS-SN-DEC", "CMP-DEBATS-DEC")]
            if cmp_dec and (cmp_dec[-1].get("statutConclusion") or {}).get("fam_code") == "TCCMP02":
                # Désaccord : pas de conclusions à lire. Une décision présente ici
                # appartient à la lecture suivante (vu sur DLR5L17N50692).
                egarees += decs
                continue
            dates = {c: {_date(a) for a in sous if a["codeActe"] == f"CMP-DEBATS-{c}-SEANCE"} for c in ("AN", "SN")}
            chambres = _chambres_cmp(decs, dates)
            if promulgue and cmp_dec:
                # Conclusions d'un texte promulgué : chaque chambre les a adoptées. Si la
                # décision d'une chambre manque mais que sa séance est datée, on la déduit.
                for ch in ("AN", "SN"):
                    if ch not in chambres and dates[ch]:
                        decs.append({"uid": f"{d['uid']}-CMP-{ch}-deduite", "codeActe": f"CMP-DEBATS-{ch}-DEC",
                                     "dateActe": max(dates[ch]), "statutConclusion": {"fam_code": "TSORTF18"},
                                     "deduite": True})
                        chambres.append(ch)
            for a, ch in zip(decs, chambres):
                an_ = ch == "AN"
                lectures.append({**base, "chambre": ch, "dec": a, "dgvt": dgvt if an_ else [],
                                 "motions": motions if an_ else [], "seances": seances if an_ else set()})
            continue
        decs = [a for a in sous if a["codeActe"] == f"{code}-DEBATS-DEC"]
        if not decs and any(e["codeActe"] == code for e in etapes[rang + 1:]):
            continue  # étape rouverte plus loin : texte redéposé après la dissolution de 2024
        if not decs and egarees:
            decs = [egarees.pop(0)]
        if not decs:
            # Lecture close sans décision : texte transmis à l'expiration des délais
            # (art. 47 et 47-1), ou lecture en cours.
            suivante = etapes[rang + 1] if rang + 1 < len(etapes) else None
            date = min((_date(a) for a in an.parcourir(suivante) if _date(a)), default="") if suivante else ""
            lectures.append({**base, "chambre": c["chambre"], "dec": None, "date_sans_dec": date,
                             "dgvt": dgvt, "motions": motions, "seances": seances})
            continue
        lectures.append({**base, "chambre": c["chambre"], "dec": max(decs, key=_date),
                         "dgvt": dgvt, "motions": motions, "seances": seances})
    for i, l in enumerate(lectures):
        l["date"] = _date(l["dec"]) if l["dec"] else l["date_sans_dec"]
        l["id"] = f"{d['uid']}-{l['etape']}" + (f"-{l['chambre']}" if l["etape"] == "CMP" else "")
        l["ordre_brut"] = i
        l["decision_deduite"] = bool(l["dec"] and l["dec"].get("deduite"))
    lectures.sort(key=lambda l: (l["date"] or "9999", l["ordre_brut"]))
    return lectures, evts


def _evenements(code: str, sous: list[dict]) -> list[dict]:
    out = []
    for a in sous:
        c = a["codeActe"]
        e = {"date": _date(a), "etape": code, "scrutin_id": None, "detail": None}
        if c.endswith("-PROCACC"):
            out.append({**e, "type": "procedure_acceleree"})
        elif c.endswith("-DGVT"):
            out.append({**e, "type": "engagement_49_3"})
        elif c.endswith("-MOTION-VOTE"):
            dec = (a.get("decision") or {}).get("fam_code")
            refs = an.vote_refs(a)
            out.append({**e, "type": "motion_censure", "scrutin_id": refs[0] if refs else None,
                        "detail": referentiels.codes_actes()["motions"].get(dec, dec)})
        elif c == "CMP-SAISIE":
            out.append({**e, "type": "cmp_convoquee"})
        elif c == "CMP-DEC":
            st = (a.get("statutConclusion") or {}).get("fam_code")
            # La décision est parfois saisie après coup (budget 2026 : réunion le 19/12/2025,
            # acte daté du 02/01/2026) : on la date de la réunion de la commission.
            reunion = [_date(x) for x in sous if x["codeActe"] == "CMP-COM-NOMIN" and _date(x)]
            date = min(reunion + [e["date"]]) if e["date"] else (min(reunion) if reunion else "")
            out.append({**e, "date": date, "type": "cmp_" + referentiels.codes_actes()["cmp"].get(st, "inconnu")})
        elif c.startswith("CC-SAISIE"):
            out.append({**e, "type": "saisine_cc", "detail": (a.get("casSaisine") or {}).get("libelle")})
        elif c == "CC-CONCLUSION":
            out.append({**e, "type": "decision_cc",
                        "detail": f"{(a.get('statutConclusion') or {}).get('libelle')} | {a.get('urlConclusion') or ''}"})
        elif c == "PROM-PUB":
            out.append({**e, "type": "promulgation", "detail": a.get("codeLoi")})
        elif c.endswith("-RTRINI"):
            out.append({**e, "type": "retrait"})
    return out


# --- Rattachement des scrutins -----------------------------------------------

def _choisir(cands: list[dict], issue: str, titres: list[str]) -> dict | None:
    """Scrutin décisif parmi des candidats, compte tenu de l'issue de la lecture."""
    if issue == "rejete":
        ok = [s for s in cands if s["objet"] in ("motion_rejet", "suppression_article_unique") and s["sort"] == "adopte"] or \
             [s for s in cands if s["objet"] in ("ensemble", "article_unique", "partie") and s["sort"] == "rejete"]
    elif issue == "adopte":
        ok = [s for s in cands if s["objet"] in ("ensemble", "article_unique") and s["sort"] == "adopte"]
    else:
        ok = [s for s in cands if s["objet"] in ("ensemble", "article_unique")]
    if not ok:
        return None
    if len(ok) > 1 and titres:
        ok.sort(key=lambda s: -max(similarite(s["titre"], t) for t in titres if t))
    return ok[0]


SEUIL_SIMILARITE = 0.6
SEUIL_MEME_SEANCE = 0.4
# Suffixe des intitulés de scrutins AN selon le type de lecture (coquilles vues dans les
# intitulés : « 1ère lecture », « lecture défintive », « commission paritaire »)
SUFFIXES = {"premiere": r"(premiere|1ere) lecture", "deuxieme": r"(deuxieme|2e|2eme) lecture",
            "troisieme": r"(troisieme|3e|3eme) lecture", "nouvelle": r"nouvelle lecture",
            "definitive": r"lecture def", "cmp": r"commission (mixte )?paritaire"}


def _meme_texte(s: dict, cles: list[str], titres: list[str], seuil: float = SEUIL_SIMILARITE,
                organique: bool | None = None) -> bool:
    """Le scrutin porte-t-il sur ce texte ? Début de titre identique, ou au moins 60 % des mots
    significatifs d'un des titres du texte (le titre change parfois en navette). Une loi organique et
    la loi ordinaire qui l'accompagne ont le même titre : l'intitulé du scrutin dit laquelle."""
    if organique is not None and ("loi organique" in norm(s["titre"])) != organique:
        return False
    t = " ".join(mots_ordonnes(s["titre"]))
    return any(k and k in t for k in cles) or any(similarite(s["titre"], x) >= seuil for x in titres if x)


class Index:
    """Scrutins indexés pour le rattachement. Ceux du Sénat ne servent qu'à dater une décision."""

    def __init__(self, scr_an: list[dict], scr_sn: list[dict]):
        self.an = {s["id"]: s for s in scr_an}
        self.par_seance: dict[str, list[dict]] = defaultdict(list)
        self.par_date: dict[str, list[dict]] = defaultdict(list)
        for s in scr_an:
            if s["objet"] in DECISIFS:
                self.par_seance[s["seance"]].append(s)
                self.par_date[s["date"]].append(s)
        self.sn: dict[tuple, list[dict]] = defaultdict(list)
        for s in scr_sn:
            if s["objet"] in DECISIFS and s["loicod"]:
                self.sn[(s["loicod"], s["typleccod"])].append(s)


def _scrutin_an(l: dict, idx: Index, titres: list[str], issue: str, organique: bool) -> tuple[dict | None, str]:
    refs = [idx.an[r] for r in an.vote_refs(l["dec"]) if r in idx.an]
    if refs and (s := _choisir(refs, issue, titres)):
        return s, "voteRefs"
    # sinon (les voteRefs ne citent parfois qu'une motion rejetée) : par la séance
    seances = {l["dec"].get("reunionRef")} | l["seances"]
    cles = [cle_titre(t) for t in titres if t]
    exclus = l.get("exclus", set())
    cands = [s for se in seances if se for s in idx.par_seance.get(se, [])
             if s["id"] not in exclus and _meme_texte(s, cles, titres, organique=organique)]
    if not any(seances):
        # décision sans séance renseignée (vu sur DLR5L17N53981) : scrutins du jour de la décision
        cands = [s for s in idx.par_date.get(l["date"], [])
                 if s["id"] not in exclus and _meme_texte(s, cles, titres, organique=organique)]
    s = _choisir(cands, issue, titres)
    # Second passage, limité à la séance de la décision, puis à son jour (la séance
    # du dossier n'est pas toujours celle du scrutin) : seuil plus bas, mais le type
    # de lecture de l'intitulé doit concorder (« (première lecture) »…).
    suffixe = re.compile(SUFFIXES.get(l["type_lecture"], ""))
    for pool in (idx.par_seance.get(l["dec"].get("reunionRef"), []), idx.par_date.get(l["date"], [])):
        if s is None:
            cands = [x for x in pool if x["id"] not in exclus and suffixe.search(norm(x["titre"]))
                     and _meme_texte(x, cles, titres, SEUIL_MEME_SEANCE, organique)]
            s = _choisir(cands, issue, titres)
    return s, ("seance" if s else "aucun")


# --- Mode d'adoption ----------------------------------------------------------

def qualifier(l: dict, idx: Index, titres: list[str], type_loi: str) -> dict:
    """Issue, scrutin décisif et mode d'adoption d'une lecture."""
    if l["dec"] is None:
        mode = "DELAI_EXPIRE" if type_loi in ("finances", "financement_ss") else "SANS_DECISION"
        return {"statut_code": None, "statut": "sans décision", "issue": "sans_decision",
                "scrutin_id": None, "rattachement": None, "mode_adoption": mode, "art_49_3": False}
    st = _statut(l["dec"])
    art493 = bool(st.get("art_49_3")) or bool(l["dgvt"])
    out = {"statut_code": st["code"], "statut": st["libelle"], "issue": st["issue"], "art_49_3": art493}
    if art493:
        # scrutin miroir : la motion de censure la plus votée de la lecture
        refs = [idx.an[r] for m in l["motions"] for r in an.vote_refs(m) if r in idx.an]
        miroir = max(refs, key=lambda s: s["pour"], default=None)
        return {**out, "scrutin_id": miroir["id"] if miroir else None,
                "rattachement": "motion_censure" if miroir else "aucun", "mode_adoption": "ART_49_3"}
    if l["chambre"] != "AN":
        return {**out, "scrutin_id": None, "rattachement": "senat", "mode_adoption": "NON_RENSEIGNE"}
    if l["date"] < DEBUT_SCRUTINS:
        return {**out, "scrutin_id": None, "rattachement": "scrutins_non_ingeres", "mode_adoption": "NON_RENSEIGNE"}
    s, how = _scrutin_an(l, idx, titres, st["issue"], type_loi == "organique")
    if s is None:
        mode = "MAIN_LEVEE"
    elif s["objet"] == "motion_rejet" and s["sort"] == "adopte":
        mode = "MOTION_REJET"
    else:
        mode = {"SPS": "SCRUTIN_SOLENNEL", "SPO": "SCRUTIN_ORDINAIRE"}[s["type_vote"]]
    return {**out, "scrutin_id": s["id"] if s else None, "rattachement": how, "mode_adoption": mode}


# --- Textes -------------------------------------------------------------------

def type_loi(d: dict, titre: str, typ_dosleg: str | None) -> tuple[str, str | None]:
    """(type, sous-type) d'un texte. Conventions : la catégorie « convention » l'emporte si l'une des
    deux sources le dit ou si le titre l'annonce."""
    proc = norm((d.get("procedureParlementaire") or {}).get("libelle"))
    t = norm(titre)
    if "loi speciale" in t:
        return "finances", "loi_speciale"
    if "finances rectificative" in proc:
        return "finances", "LFR"
    if "finances de l annee" in proc:
        return "finances", "LFI"
    if "resultats de la gestion" in t or "reglement du budget" in t:
        return "finances", "reglement"
    if "organique" in proc:  # avant le titre : lois organiques relatives aux LFSS (2022-354)
        return "organique", None
    if "financement de la securite sociale" in proc or re.match(r"loi de financement (rectificative )?de la securite", t):
        return "financement_ss", "LFRSS" if "rectificative" in t else "LFSS"
    if "constitutionnelle" in proc:
        return "constitutionnelle", None
    if ("ratification des traites" in proc or typ_dosleg == "cvn"
            or re.search(r"autorisant (l approbation|la ratification|l adhesion)", t)):
        return "convention", None
    return "ordinaire", None


def adoption_definitive(lectures: list[dict], evts: list[dict]) -> bool:
    """Texte adopté définitivement mais pas (encore) promulgué.

    Indices, dans l'ordre : saisine du Conseil constitutionnel (qui suit l'adoption définitive) ;
    dernière lecture adoptée en lecture définitive, en CMP dans les deux chambres, ou « sans
    modification ». Le statut des décisions du Sénat n'étant pas toujours fiable, la détection est
    incomplète pour les textes adoptés conformes au Sénat depuis moins de quinze jours.
    """
    if any(e["type"] == "saisine_cc" for e in evts):
        return True
    closes = [l for l in lectures if l["dec"] is not None]
    if not closes:
        return False
    der = closes[-1]
    st = _statut(der["dec"])
    if st["issue"] != "adopte":
        return False
    if der["type_lecture"] == "definitive" or st["code"] in ("TSORTF03", "TSORTF19"):
        return True
    if der["type_lecture"] == "cmp":
        cmp_ = [l for l in closes if l["type_lecture"] == "cmp"]
        return {l["chambre"] for l in cmp_} >= {"AN", "SN"} and all(_statut(l["dec"])["issue"] == "adopte" for l in cmp_)
    return False


def legislature(date: str) -> int:
    return max((l for l, d in DEBUTS.items() if date >= d), default=min(DEBUTS))


def classer(dossiers: dict[str, dict], titres_textes: dict[str, set[str]], idx: Index, dosleg_lois: dict
            ) -> tuple[list[dict], set[str]]:
    """Chaque dossier avec ses lectures, son dossier Sénat et son `statut` : `promulguee`, `adoptee`
    (adopté définitivement, pas encore promulgué) ou `autre` (lectures non qualifiées, candidat au
    périmètre des textes en cours). Renvoie aussi les scrutins décisifs des lois, qu'un texte en cours
    ne peut pas reprendre."""
    par_signet, par_date = dosleg_lois["par_signet"], dosleg_lois["par_date"]
    out, lois = [], []
    for uid, d in sorted(dossiers.items()):
        actes = [a for e in an.enfants(d) for a in an.parcourir(e)]
        proms = [a for a in actes if a["codeActe"] == "PROM-PUB"]
        prom = proms[-1] if proms else None
        lectures, evts = lectures_dossier(d)
        m = re.search(r"/([^/]+)\.html$", d["titreDossier"].get("senatChemin") or "")
        signet = m.group(1) if m else None
        sn = par_signet.get(signet) if signet else None
        if sn is None and prom and par_date.get(_date(prom)):
            ref = norm(prom.get("titreLoi"))
            sn = max(par_date[_date(prom)], key=lambda r: SequenceMatcher(None, norm(r["titre"]), ref).ratio())
        titres = [d["titreDossier"]["titre"], sn["titre"] if sn else None, *sorted(titres_textes.get(uid, ()))]
        if prom:
            statut = "promulguee"
        elif (lectures and (lectures[-1]["date"] or "") >= DEBUTS[max(DEBUTS)]
              and (adoption_definitive(lectures, evts) or (sn and sn["loicod"] in dosleg_lois["definitifs"]))):
            # adopté non promulgué : seulement pour la législature en cours (un texte ancien sans
            # promulgation a été censuré en entier ou abandonné)
            statut = "adoptee"
        else:
            statut = "autre"
        c = {"uid": uid, "dossier": d, "lectures": lectures, "evts": evts, "sn": sn, "signet": signet,
             "titres": titres, "statut": statut}
        out.append(c)
        if statut != "autre":
            typ = type_loi(d, titres[0], sn["typloicod"] if sn else None)[0]
            ts = [*titres, prom.get("titreLoi") if prom else None]
            for l in lectures:
                l["ctx"] = (ts, typ)
                l.update(qualifier(l, idx, *l["ctx"]))
            lois += lectures
    _departager(lois, idx)
    return out, {l["scrutin_id"] for l in lois if l["scrutin_id"] and not l["art_49_3"]}


def _departager(lectures: list[dict], idx: Index) -> None:
    """Un scrutin décisif ne sert qu'une lecture. Deux textes voisins (conventions au titre presque
    identique) peuvent se disputer un scrutin trouvé par la séance : il revient à la lecture qui le
    référence (`voteRefs`), sinon au titre le plus proche ; l'autre est requalifiée sans lui."""
    for _ in range(5):
        par_scrutin: dict[str, list[dict]] = defaultdict(list)
        for l in lectures:
            if l.get("scrutin_id") and not l["art_49_3"]:
                par_scrutin[l["scrutin_id"]].append(l)
        conflits = {sid: ls for sid, ls in par_scrutin.items() if len(ls) > 1}
        if not conflits:
            return
        for sid, ls in conflits.items():
            titre = idx.an[sid]["titre"] if sid in idx.an else ""
            ls.sort(key=lambda l: (l["rattachement"] != "voteRefs",
                                   -max(similarite(titre, t) for t in l["ctx"][0] if t)))
            for l in ls[1:]:
                l.setdefault("exclus", set()).add(sid)
                l.update(qualifier(l, idx, *l["ctx"]))

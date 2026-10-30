"""Qualifications publiées : data/editorial.json (docs/CONCEPTION.md, format d'editorial.json).

L'admin écrit ce fichier à chaque publication ; le pipeline le lit pour calculer les scores. Tant
qu'il n'existe pas, la qualification vient de referentiels/temoins.yaml, convertie au même format.

Le fichier est déterministe (ordre des clés fixe, textes triés, indentation de 2) pour qu'une
publication donne un diff lisible. L'admin (admin/src/lib/qualification.ts) produit les mêmes
octets : un test croisé le vérifie.

`valider` porte les contrôles d'une qualification, les mêmes que ceux de l'admin : erreurs
bloquantes et avertissements. `valider_suivi` porte ceux d'une fiche de suivi : droits touchés et
sources, sans sens ni scrutin (texte qui n'a pas encore de vote qualifié).
"""

import json
import re
from pathlib import Path

from . import referentiels

FORMAT = 1
CHEMIN = Path(__file__).resolve().parents[2] / "data/editorial.json"

ROLES_DROIT = ("principal", "secondaire")
SENS = ("etend", "restreint")
# `censure` : motion de censure sur un texte adopté par 49.3 sans vote final (règle 9), affichée seulement.
ROLES_SCRUTIN = ("decisif", "ensemble", "motion", "article", "amendement", "censure")
POUR = ("texte", "contre-texte", "a-trancher")

# Ordre des clés dans le fichier (le même dans l'admin).
CLES_TEXTE = ("id", "dossier_an", "legislature", "titre", "resume", "droits", "etiquettes", "vigilance",
              "conseil_constitutionnel", "note", "sources", "scrutins")
CLES_DROIT = ("code", "role", "sens", "sources", "justification")
CLES_SOURCE = ("auteur", "titre", "date", "url")
CLES_SCRUTIN = ("id", "role", "pour", "objet")
CLES_VIGILANCE = ("texte", "sources")
CLES_ECARTE = ("dossier_an", "legislature", "titre", "motif")
CLES_SUIVI = ("id", "dossier_an", "legislature", "titre", "resume", "droits", "note", "sources")
CLES_DROIT_SUIVI = ("code", "sources", "justification")


def _ordonner(d: dict, cles: tuple[str, ...]) -> dict:
    return {k: d[k] for k in cles if k in d}


def normaliser(t: dict) -> dict:
    """Une qualification au format 1, clés dans l'ordre du fichier."""
    vigilance = [v if isinstance(v, dict) else {"texte": v, "sources": []} for v in t.get("vigilance") or []]
    cc = t.get("conseil_constitutionnel") or ""
    if isinstance(cc, dict):
        cc = cc.get("resume", "")
    out = {
        "id": t["id"],
        "dossier_an": t["dossier_an"],
        "legislature": int(t["legislature"]),
        "titre": t["titre"],
        "resume": (t.get("resume") or "").strip(),
        "droits": [_ordonner({**d, "sources": list(d.get("sources") or []),
                              "justification": (d.get("justification") or "").strip()}, CLES_DROIT)
                   for d in t["droits"]],
        "etiquettes": list(t.get("etiquettes") or []),
        "vigilance": [_ordonner({"texte": v["texte"].strip(), "sources": list(v.get("sources") or [])},
                                CLES_VIGILANCE) for v in vigilance],
        # espaces ASCII seulement : les espaces insécables de la typographie française restent
        "conseil_constitutionnel": re.sub(r"[ \t\n\r]+", " ", cc).strip(),
        "note": (t.get("note") or "").strip(),
        "sources": {k: _ordonner({**s, "date": str(s.get("date") or "")}, CLES_SOURCE)
                    for k, s in sorted((t.get("sources") or {}).items())},
        "scrutins": [_ordonner(s, CLES_SCRUTIN) for s in t["scrutins"]],
    }
    return _ordonner(out, CLES_TEXTE)


def ecarte(e: dict) -> dict:
    """Document minimal d'un texte écarté (statut `ecarte` dans l'admin)."""
    return normaliser({"id": "", "dossier_an": e["dossier_an"], "legislature": e.get("legislature", 0),
                       "titre": e["titre"], "droits": [], "scrutins": []})


def suivi(t: dict) -> dict:
    """Entrée de `suivis` : d'une qualification normalisée, ne garde ni sens, ni rôle, ni scrutin."""
    n = normaliser({**t, "scrutins": []})
    return _ordonner({**n, "droits": [_ordonner(d, CLES_DROIT_SUIVI) for d in n["droits"]]}, CLES_SUIVI)


def doc_suivi(s: dict) -> dict:
    """Document D1 d'une fiche de suivi : une qualification complète, sans sens ni scrutin."""
    return normaliser({**s, "scrutins": []})


def depuis_temoins(temoins: dict) -> dict:
    """Convertit referentiels/temoins.yaml au format d'editorial.json."""
    return document([normaliser(t) for t in temoins["textes"]], [])


def document(textes: list[dict], ecartes: list[dict], suivis: list[dict] = ()) -> dict:
    """`suivis` n'apparaît que s'il n'est pas vide : ajout compatible avec le format 1."""
    doc = {
        "format": FORMAT,
        "grille": referentiels.droits()["version"],
        "textes": sorted(textes, key=lambda t: t["id"]),
        "ecartes": sorted((_ordonner(e, CLES_ECARTE) for e in ecartes), key=lambda e: e["dossier_an"]),
    }
    if suivis:
        doc["suivis"] = sorted((suivi(s) for s in suivis), key=lambda s: s["id"])
    return doc


def serialiser(doc: dict) -> str:
    return json.dumps(doc, ensure_ascii=False, indent=2) + "\n"


def charger(chemin: Path = CHEMIN) -> dict:
    """Qualifications publiées, ou celles des textes témoins tant qu'aucune publication n'existe."""
    if chemin.exists():
        doc = json.loads(chemin.read_text())
        if doc.get("format") != FORMAT:
            raise SystemExit(f"{chemin} : format {doc.get('format')} inconnu (attendu {FORMAT})")
        return doc
    return depuis_temoins(referentiels.temoins())


def _controler_sources(sources: dict, citees: set[str], err: list[str], avert: list[str]) -> None:
    for s in sorted(citees - set(sources)):
        err.append(f"source citée mais non définie : {s}")
    for k, s in sources.items():
        if not (s.get("url") or "").startswith("http"):
            err.append(f"source {k} : URL manquante")
        if not s.get("auteur") or not s.get("titre"):
            err.append(f"source {k} : auteur ou titre manquant")
        if not re.fullmatch(r"\d{4}(-\d{2}(-\d{2})?)?", str(s.get("date") or "")):
            err.append(f"source {k} : date attendue au format AAAA-MM-JJ (ou AAAA-MM)")
    for k in sorted(set(sources) - citees):
        avert.append(f"source {k} définie mais citée nulle part")


def valider_suivi(t: dict) -> tuple[list[str], list[str]]:
    """Erreurs bloquantes et avertissements d'une fiche de suivi (docs/CONCEPTION.md, contrôles)."""
    codes = {d["code"] for d in referentiels.droits()["droits"]}
    err, avert = [], []
    if not t.get("id"):
        err.append("identifiant manquant")
    if not t.get("titre", "").strip():
        err.append("titre manquant")
    droits = t.get("droits") or []
    if not droits:
        err.append("il faut au moins un droit touché")
    vus = set()
    for d in droits:
        c = d.get("code")
        if c not in codes:
            err.append(f"droit inconnu : {c}")
        if c in vus:
            err.append(f"droit en double : {c}")
        vus.add(c)
        if d.get("sens") or d.get("role"):
            err.append(f"{c} : ni sens ni rôle avant le vote")
        if not d.get("sources"):
            err.append(f"{c} : aucune source")
    if t.get("scrutins"):
        err.append("aucun scrutin retenu avant le vote")
    _controler_sources(t.get("sources") or {}, {s for d in droits for s in d.get("sources") or []}, err, avert)
    return err, avert


def valider(t: dict, scrutins_dossier: dict[str, dict] | None = None) -> tuple[list[str], list[str]]:
    """Erreurs bloquantes et avertissements d'une qualification (docs/CONCEPTION.md, contrôles).

    `scrutins_dossier` : scrutin → {dossier_id, etape, division, objet, pour, contre} pour les scrutins du
    catalogue (objet, pour et contre facultatifs) ;
    sans lui, les contrôles qui portent sur l'open data sont sautés.
    """
    grille = referentiels.droits()
    codes = {d["code"] for d in grille["droits"]}
    etiquettes = {e["code"] for e in grille["etiquettes"]}
    sources = t.get("sources") or {}
    err, avert = [], []

    if not t.get("id"):
        err.append("identifiant manquant")
    if not t.get("titre", "").strip():
        err.append("titre manquant")
    droits = t.get("droits") or []
    if sum(d.get("role") == "principal" for d in droits) != 1:
        err.append("il faut exactement un droit principal")
    vus = set()
    for d in droits:
        c = d.get("code")
        if c not in codes:
            err.append(f"droit inconnu : {c}")
        if c in vus:
            err.append(f"droit en double : {c}")
        vus.add(c)
        if d.get("role") not in ROLES_DROIT:
            err.append(f"{c} : rôle inconnu ({d.get('role')})")
        if d.get("sens") not in SENS:
            err.append(f"{c} : sens inconnu ({d.get('sens')})")
        if not d.get("sources"):
            err.append(f"{c} : aucune source")
    for e in t.get("etiquettes") or []:
        if e not in etiquettes:
            err.append(f"étiquette inconnue : {e}")
    citees = {s for d in droits for s in d.get("sources") or []}
    citees |= {s for v in t.get("vigilance") or [] for s in v.get("sources") or []}
    _controler_sources(sources, citees, err, avert)

    scrutins = t.get("scrutins") or []
    n_decisifs = sum(s.get("role") == "decisif" for s in scrutins)
    if n_decisifs > 1 or (n_decisifs == 0 and not any(s.get("role") == "censure" for s in scrutins)):
        err.append("il faut exactement un scrutin décisif (ou, pour un texte adopté par 49.3 sans vote final, "
                    "au moins une motion de censure)")
    ids = [s.get("id") for s in scrutins]
    for i in sorted({i for i in ids if ids.count(i) > 1}):
        err.append(f"scrutin en double : {i}")
    for s in scrutins:
        if s.get("role") not in ROLES_SCRUTIN:
            err.append(f"{s.get('id')} : rôle inconnu ({s.get('role')})")
        if s.get("pour") not in POUR:
            err.append(f"{s.get('id')} : sens inconnu ({s.get('pour')})")
        elif s["pour"] == "a-trancher":
            avert.append(f"{s['id']} : sens à trancher, scrutin non compté")
    principal = next((d for d in droits if d.get("role") == "principal"), {})
    if principal.get("sens") == "etend" and not any(v.get("sources") for v in t.get("vigilance") or []):
        avert.append("le texte étend son droit principal : la règle 7 demande une source critique en vigilance")

    if scrutins_dossier is not None:
        par_article: dict[tuple, list[str]] = {}
        for s in scrutins:
            info = scrutins_dossier.get(s.get("id"))
            if s.get("role") == "censure":
                # Une motion de censure n'est pas toujours rattachée au dossier du texte.
                if info is None or info.get("objet") != "motion_censure":
                    err.append(f"{s.get('id')} : pas une motion de censure")
                continue
            if info is None or info.get("dossier_id") != t.get("dossier_an"):
                err.append(f"{s.get('id')} : scrutin absent du dossier {t.get('dossier_an')}")
                continue
            if s.get("role") == "decisif" and (info.get("pour") == 0 or info.get("contre") == 0):
                err.append(f"{s['id']} : décisif unanime ({info.get('pour')}-{info.get('contre')}), "
                           "texte à écarter (règle 9)")
            if s.get("role") == "amendement" and s.get("pour") != "a-trancher":
                if info.get("objet") == "suppression_article_unique":
                    err.append(f"{s['id']} : suppression d'un article unique, pas un amendement clé (règle 11)")
                if info.get("pour") == 0 or info.get("contre") == 0:
                    err.append(f"{s['id']} : amendement unanime ({info.get('pour')}-{info.get('contre')}), "
                               "pas un amendement clé (règle 11)")
                if info.get("division"):
                    par_article.setdefault((info.get("etape"), info["division"]), []).append(s["id"])
        for (_, division), ss in sorted(par_article.items(), key=lambda x: str(x[0])):
            if len(ss) > 1:
                err.append(f"plusieurs amendements clés sur « {division} » dans la même lecture : {', '.join(ss)}")
    return err, avert

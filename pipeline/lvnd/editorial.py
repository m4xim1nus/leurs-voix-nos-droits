"""Qualifications publiées : data/editorial.json (docs/CONCEPTION.md, format d'editorial.json).

L'admin écrit ce fichier à chaque publication ; le pipeline le lit pour calculer les scores. Tant
qu'il n'existe pas, la qualification vient de referentiels/temoins.yaml, convertie au même format.

Le fichier est déterministe (ordre des clés fixe, textes triés, indentation de 2) pour qu'une
publication donne un diff lisible. L'admin (admin/src/lib/qualification.ts) produit les mêmes
octets : un test croisé le vérifie.

`valider` porte les contrôles d'une qualification, les mêmes que ceux de l'admin : erreurs
bloquantes et avertissements.
"""

import json
import re
from pathlib import Path

from . import referentiels

FORMAT = 1
CHEMIN = Path(__file__).resolve().parents[2] / "data/editorial.json"

ROLES_DROIT = ("principal", "secondaire")
SENS = ("etend", "restreint")
ROLES_SCRUTIN = ("decisif", "ensemble", "motion", "article", "amendement")
POUR = ("texte", "contre-texte", "a-trancher")

# Ordre des clés dans le fichier (le même dans l'admin).
CLES_TEXTE = ("id", "dossier_an", "legislature", "titre", "resume", "droits", "etiquettes", "vigilance",
              "conseil_constitutionnel", "note", "sources", "scrutins")
CLES_DROIT = ("code", "role", "sens", "sources", "justification")
CLES_SOURCE = ("auteur", "titre", "date", "url")
CLES_SCRUTIN = ("id", "role", "pour", "objet")
CLES_VIGILANCE = ("texte", "sources")
CLES_ECARTE = ("dossier_an", "legislature", "titre", "motif")


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


def depuis_temoins(temoins: dict) -> dict:
    """Convertit referentiels/temoins.yaml au format d'editorial.json."""
    return document([normaliser(t) for t in temoins["textes"]], [])


def document(textes: list[dict], ecartes: list[dict]) -> dict:
    return {
        "format": FORMAT,
        "grille": referentiels.droits()["version"],
        "textes": sorted(textes, key=lambda t: t["id"]),
        "ecartes": sorted((_ordonner(e, CLES_ECARTE) for e in ecartes), key=lambda e: e["dossier_an"]),
    }


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


def valider(t: dict, scrutins_dossier: dict[str, dict] | None = None) -> tuple[list[str], list[str]]:
    """Erreurs bloquantes et avertissements d'une qualification (docs/CONCEPTION.md, contrôles).

    `scrutins_dossier` : scrutin → {dossier_id, etape, division} pour les scrutins du catalogue ;
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

    scrutins = t.get("scrutins") or []
    if sum(s.get("role") == "decisif" for s in scrutins) != 1:
        err.append("il faut exactement un scrutin décisif")
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
            if info is None or info.get("dossier_id") != t.get("dossier_an"):
                err.append(f"{s.get('id')} : scrutin absent du dossier {t.get('dossier_an')}")
                continue
            if s.get("role") == "amendement" and s.get("pour") != "a-trancher" and info.get("division"):
                par_article.setdefault((info.get("etape"), info["division"]), []).append(s["id"])
        for (_, division), ss in sorted(par_article.items(), key=lambda x: str(x[0])):
            if len(ss) > 1:
                err.append(f"plusieurs amendements clés sur « {division} » dans la même lecture : {', '.join(ss)}")
    return err, avert

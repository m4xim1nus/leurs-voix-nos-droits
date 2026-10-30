"""Agenda de l'AN : points de séance et de commission à venir, reliés à un dossier (docs/SOURCES.md).

Un point d'agenda dit qu'un texte est **inscrit**, jamais qu'il sera voté : une niche n'examine pas
toujours tous ses textes, et une séance peut lever la discussion sans vote.
"""

import json
from pathlib import Path

from .an import _liste
from .sources import extraits

CLE = "an_agenda_17"
ETATS = {"Confirmé": "confirme", "Eventuel": "eventuel"}  # les réunions et points Annulé ou Supprimé sont écartés
INSTANCES = {"seance_type": "seance", "reunionCommission_type": "commission"}
COLONNES = ("point_id", "dossier_id", "date", "heure", "instance", "organe_id", "organe", "etat", "type_point", "objet",
            "procedure")


def _organes(raw: Path) -> dict[str, str | None]:
    """Mémoïse le libellé des organes (AMO) d'un lancement."""
    cache: dict[str, str | None] = {}

    def libelle(ref: str | None) -> str | None:
        if ref and ref not in cache:
            p = extraits(raw, "an_amo") / f"json/organe/{ref}.json"
            cache[ref] = json.loads(p.read_text())["organe"].get("libelle") if p.exists() else None
        return cache.get(ref)
    return libelle


def points_reunion(r: dict, libelle=lambda ref: None) -> list[dict]:
    """Points d'une réunion du dump : une ligne par point non supprimé et par dossier."""
    instance = INSTANCES.get(r.get("@xsi:type"))
    etat_reunion = ETATS.get((r.get("cycleDeVie") or {}).get("etat"))
    if instance is None or etat_reunion is None:
        return []
    out = []
    for p in _liste(((r.get("ODJ") or {}).get("pointsODJ") or {}).get("pointODJ")):
        etat = ETATS.get((p.get("cycleDeVie") or {}).get("etat"))
        if etat is None:
            continue
        for dossier in _liste((p.get("dossiersLegislatifsRefs") or {}).get("dossierRef")):
            out.append({
                "point_id": p["uid"],
                "dossier_id": dossier,
                "date": r["timeStampDebut"][:10],
                "heure": r["timeStampDebut"][11:16],
                "instance": instance,
                "organe_id": r.get("organeReuniRef"),
                "organe": libelle(r.get("organeReuniRef")),
                # un point confirmé dans une réunion éventuelle reste éventuel
                "etat": "eventuel" if "eventuel" in (etat, etat_reunion) else "confirme",
                "type_point": p.get("typePointODJ"),
                "objet": p.get("objet"),
                "procedure": p.get("procedure"),
            })
    return out


def points(raw: Path, date_ref: str) -> list[dict]:
    """Points inscrits à partir de `date_ref`, triés (date, heure, point, dossier)."""
    dossier = extraits(raw, CLE) / "json/reunion"
    if not dossier.exists():
        raise SystemExit(f"{dossier} absent : lancer `lvnd download {CLE}`")
    libelle = _organes(raw)
    out = []
    for p in dossier.glob("*.json"):
        r = json.loads(p.read_text())["reunion"]
        if r["timeStampDebut"][:10] >= date_ref:
            out += points_reunion(r, libelle)
    return sorted(out, key=lambda x: (x["date"], x["heure"], x["point_id"], x["dossier_id"]))

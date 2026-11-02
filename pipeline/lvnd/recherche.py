"""Clés de la recherche du site : termes courants et surnoms des textes, pays → circonscription des Français de l'étranger.

Les termes d'un texte vivent dans son bloc `recherche` d'editorial.json, saisi dans l'admin ou proposé par le LLM (cycle
Pré-qualification, décision de Max du 02/11/2026 ; l'ancien referentiels/termes_recherche.yaml y a été repris et retiré).
Les pays restent dans pays_circonscriptions.yaml. Le tout est exporté en CSV dans data/export/, que le site lit au build, et
n'entre dans aucun score.
"""
import csv
from pathlib import Path

from . import editorial, referentiels

COLONNES_TERMES = ("cle", "type", "terme")
COLONNES_PAYS = ("pays", "circo", "hors_tableau", "alias")
CIRCONSCRIPTIONS = 11


def termes_publies(doc: dict) -> dict[str, dict]:
    """Blocs `recherche` d'editorial.json : `id` d'un texte ou d'une fiche de suivi, dossier d'un écarté → bloc."""
    out = {t["id"]: t["recherche"] for t in [*doc["textes"], *doc.get("suivis", [])] if t.get("recherche")}
    out |= {e["dossier_an"]: e["recherche"] for e in doc.get("ecartes", []) if e.get("recherche")}
    return out


def lignes_termes(doc: dict | None = None) -> list[dict]:
    """Une ligne par terme ou surnom, d'après editorial.json."""
    doc = editorial.charger() if doc is None else doc
    out = []
    for cle, v in termes_publies(doc).items():
        for type_, champ in (("terme", "termes"), ("surnom", "surnoms")):
            out += [{"cle": cle, "type": type_, "terme": str(t)} for t in v.get(champ) or []]
    return out


def lignes_pays(ref: dict | None = None) -> list[dict]:
    """Une ligne par pays, avec le code de la circonscription tel que l'écrit l'AN (099-07)."""
    ref = referentiels.charger("pays_circonscriptions") if ref is None else ref
    alias = ref.get("alias") or {}
    out = []
    for bloc, hors in (("circonscriptions", False), ("hors_tableau", True)):
        for num, pays in ref[bloc].items():
            out += [{"pays": p, "circo": f"099-{num:02d}", "hors_tableau": "oui" if hors else "",
                     "alias": "|".join(str(a) for a in alias.get(p, []))} for p in pays]
    return sorted(out, key=lambda l: (l["circo"], l["pays"]))


def controler_termes(doc: dict) -> tuple[list[str], list[str]]:
    """Erreurs (terme en double dans un même texte) et textes qualifiés ou suivis sans terme (signalés, sans bloquer)."""
    publies = termes_publies(doc)
    err = []
    for cle, v in publies.items():
        vus = [str(t).casefold() for champ in ("termes", "surnoms") for t in v.get(champ) or []]
        if len(set(vus)) != len(vus):
            err.append(f"{cle} : terme en double")
    ids = [t["id"] for t in [*doc["textes"], *doc.get("suivis", [])]]
    return err, sorted(set(ids) - set(publies))


def controler_pays(ref: dict | None = None) -> list[str]:
    """Onze circonscriptions, chaque pays et chaque alias une seule fois, chaque alias rattaché à un pays connu."""
    ref = referentiels.charger("pays_circonscriptions") if ref is None else ref
    err = []
    if sorted(ref["circonscriptions"]) != list(range(1, CIRCONSCRIPTIONS + 1)):
        err.append("il faut les circonscriptions 1 à 11")
    pays = [p for bloc in ("circonscriptions", "hors_tableau") for l in ref[bloc].values() for p in l]
    alias = [str(a) for l in (ref.get("alias") or {}).values() for a in l]
    doublons = {n for n in pays + alias if (pays + alias).count(n) > 1}
    if doublons:
        err.append(f"en double : {', '.join(sorted(doublons))}")
    if inconnus := set(ref.get("alias") or {}) - set(pays):
        err.append(f"alias d'un pays inconnu : {', '.join(sorted(inconnus))}")
    return err


def _ecrire(chemin: Path, colonnes: tuple[str, ...], lignes: list[dict]) -> None:
    with chemin.open("w", newline="") as f:
        w = csv.DictWriter(f, colonnes, lineterminator="\n")
        w.writeheader()
        w.writerows(lignes)


def ecrire(export: Path) -> None:
    _ecrire(export / "termes_recherche.csv", COLONNES_TERMES, lignes_termes())
    _ecrire(export / "pays_circonscriptions.csv", COLONNES_PAYS, lignes_pays())

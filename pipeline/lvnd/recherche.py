"""Clés de la recherche du site : termes courants et surnoms des textes, pays → circonscription des Français de l'étranger.

Les deux référentiels sont maintenus à la main (referentiels/termes_recherche.yaml, pays_circonscriptions.yaml) et exportés
en CSV dans data/export/, que le site lit au build. Ils n'entrent ni dans editorial.json, ni dans l'admin, ni dans les scores.
"""
import csv
from pathlib import Path

from . import referentiels

COLONNES_TERMES = ("cle", "type", "terme")
COLONNES_PAYS = ("pays", "circo", "hors_tableau", "alias")
CIRCONSCRIPTIONS = 11


def lignes_termes(ref: dict | None = None) -> list[dict]:
    """Une ligne par terme ou surnom. YAML lit « 49.3 » en nombre : tout passe par str."""
    ref = referentiels.charger("termes_recherche") if ref is None else ref
    out = []
    for bloc in ("textes", "ecartes"):
        for cle, v in (ref.get(bloc) or {}).items():
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


def controler_termes(doc: dict, ref: dict | None = None) -> tuple[list[str], list[str]]:
    """Erreurs (clé inconnue, terme vide ou en double) et textes qualifiés sans terme, à signaler sans bloquer."""
    ref = referentiels.charger("termes_recherche") if ref is None else ref
    qualifies = {t["id"] for t in doc["textes"]} | {s["id"] for s in doc.get("suivis", [])}
    ecartes = {e["dossier_an"] for e in doc.get("ecartes", [])}
    err = []
    for bloc, connus in (("textes", qualifies), ("ecartes", ecartes)):
        for cle, v in (ref.get(bloc) or {}).items():
            if cle not in connus:
                err.append(f"{cle} : inconnu dans {bloc} d'editorial.json")
            vus = [str(t).strip() for champ in ("termes", "surnoms") for t in v.get(champ) or []]
            if not vus or not all(vus):
                err.append(f"{cle} : terme vide")
            if len({t.casefold() for t in vus}) != len(vus):
                err.append(f"{cle} : terme en double")
    sans = sorted(qualifies - set(ref.get("textes") or {}))
    return err, sans


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

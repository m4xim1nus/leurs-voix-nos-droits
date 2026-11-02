"""Clés de la recherche du site : termes courants et surnoms des textes, pays → circonscription des Français de l'étranger.

Les termes d'un texte vivent dans son bloc `recherche` d'editorial.json, saisi dans l'admin (cycle Pré-qualification,
décision de Max du 02/11/2026). referentiels/termes_recherche.yaml, l'ancien référentiel tenu à la main, ne sert plus que
de repli pour un texte dont la version publiée n'a pas encore ce bloc ; il disparaîtra quand tout sera repris. Les pays
restent dans pays_circonscriptions.yaml. Le tout est exporté en CSV dans data/export/, que le site lit au build, et
n'entre dans aucun score.
"""
import csv
from pathlib import Path

from . import editorial, referentiels

COLONNES_TERMES = ("cle", "type", "terme")
COLONNES_PAYS = ("pays", "circo", "hors_tableau", "alias")
CIRCONSCRIPTIONS = 11


def _qualifies_par_dossier(doc: dict | None) -> dict[str, str]:
    """Dossier de l'AN → `id` des textes qualifiés et des fiches de suivi."""
    if doc is None:
        return {}
    return {t["dossier_an"]: t["id"] for t in [*doc["textes"], *doc.get("suivis", [])] if t.get("dossier_an")}


def lignes_termes(ref: dict | None = None, doc: dict | None = None) -> list[dict]:
    """Une ligne par terme ou surnom. YAML lit « 49.3 » en nombre : tout passe par str.

    Avec `doc` (editorial.json), une clé d'`ecartes` dont le dossier a depuis été qualifié ou mis en suivi suit le texte :
    elle sort sous son `id`, sans attendre qu'on déplace la ligne du YAML (publication du 01/11/2026)."""
    ref = referentiels.charger("termes_recherche") if ref is None else ref
    suit = _qualifies_par_dossier(doc)
    par_cle: dict[str, dict] = {}
    for bloc in ("textes", "ecartes"):
        for cle, v in (ref.get(bloc) or {}).items():
            par_cle[suit.get(cle, cle) if bloc == "ecartes" else cle] = v
    # editorial.json l'emporte, texte par texte, sur le YAML.
    for cle, r in _editorial(doc).items():
        par_cle[cle] = r
    out = []
    for cle, v in par_cle.items():
        for type_, champ in (("terme", "termes"), ("surnom", "surnoms")):
            out += [{"cle": cle, "type": type_, "terme": str(t)} for t in v.get(champ) or []]
    return out


def _editorial(doc: dict | None) -> dict[str, dict]:
    """Blocs `recherche` d'editorial.json : `id` d'un texte ou d'une fiche de suivi, dossier d'un écarté → bloc."""
    if doc is None:
        return {}
    out = {t["id"]: t["recherche"] for t in [*doc["textes"], *doc.get("suivis", [])] if t.get("recherche")}
    out |= {e["dossier_an"]: e["recherche"] for e in doc.get("ecartes", []) if e.get("recherche")}
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


def controler_termes(doc: dict, ref: dict | None = None) -> tuple[list[str], list[str], list[str]]:
    """Erreurs (terme vide ou en double), clés à déplacer et textes qualifiés sans terme.

    Seules les erreurs bloquent. Une clé dont le texte a changé de statut depuis la rédaction du YAML (qualifié puis
    écarté, écarté puis qualifié) ne bloque ni les tests ni la passe de données : elle est signalée, et une clé d'écarté
    devenue qualifiée suit d'elle-même (`lignes_termes`)."""
    ref = referentiels.charger("termes_recherche") if ref is None else ref
    qualifies = {t["id"] for t in doc["textes"]} | {s["id"] for s in doc.get("suivis", [])}
    ecartes = {e["dossier_an"] for e in doc.get("ecartes", [])}
    suit = _qualifies_par_dossier(doc)
    err, a_deplacer = [], []
    for bloc, connus in (("textes", qualifies), ("ecartes", ecartes)):
        for cle, v in (ref.get(bloc) or {}).items():
            if bloc == "ecartes" and cle in suit:
                a_deplacer.append(f"{cle} : qualifié ou suivi sous `{suit[cle]}`, ligne à déplacer dans `textes` "
                                  "(ses termes le suivent déjà)")
            elif cle not in connus:
                a_deplacer.append(f"{cle} : inconnu dans {bloc} d'editorial.json, ses termes ne servent plus "
                                  "(texte écarté ? sa ligne va dans `ecartes`, sous son dossier)")
            vus = [str(t).strip() for champ in ("termes", "surnoms") for t in v.get(champ) or []]
            if not vus or not all(vus):
                err.append(f"{cle} : terme vide")
            if len({t.casefold() for t in vus}) != len(vus):
                err.append(f"{cle} : terme en double")
    publies = _editorial(doc)
    for bloc in ("textes", "ecartes"):
        for cle in ref.get(bloc) or {}:
            if suit.get(cle, cle) in publies:
                a_deplacer.append(f"{cle} : termes publiés dans editorial.json, ligne du YAML à retirer")
    for cle, v in publies.items():
        vus = [t.casefold() for champ in ("termes", "surnoms") for t in v.get(champ) or []]
        if len(set(vus)) != len(vus):
            err.append(f"{cle} : terme en double (editorial.json)")
    sans = sorted(qualifies - set(ref.get("textes") or {}) - {suit[c] for c in ref.get("ecartes") or {} if c in suit}
                  - set(publies))
    return err, a_deplacer, sans


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
    _ecrire(export / "termes_recherche.csv", COLONNES_TERMES, lignes_termes(doc=editorial.charger()))
    _ecrire(export / "pays_circonscriptions.csv", COLONNES_PAYS, lignes_pays())

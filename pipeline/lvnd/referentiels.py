"""Référentiels maintenus à la main (pipeline/referentiels/*.yaml)."""

from functools import cache
from pathlib import Path

import yaml

DOSSIER = Path(__file__).resolve().parents[1] / "referentiels"


@cache
def charger(nom: str) -> dict:
    return yaml.safe_load((DOSSIER / f"{nom}.yaml").read_text())


def droits() -> dict:
    return charger("droits")


def mots_cles() -> dict:
    return charger("mots_cles")


def temoins() -> dict:
    return charger("temoins")


def lignee(organe: str) -> str:
    """Organe le plus récent de la lignée d'un groupe (referentiels/groupes.yaml)."""
    suivant = {ancien: nouveau for nouveau, ancien in charger("groupes")["suites"].items()}
    while organe in suivant:
        organe = suivant[organe]
    return organe

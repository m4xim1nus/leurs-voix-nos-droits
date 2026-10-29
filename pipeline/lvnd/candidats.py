"""Présélection des textes candidats par mots-clés (referentiels/mots_cles.yaml).

Aide au tri dans l'admin, jamais une qualification (docs/METHODO.md). Pour chaque texte : les
droits et étiquettes dont un motif apparaît dans un titre, et les motifs trouvés.
"""

import re
from functools import cache

from . import referentiels
from .texte import norm


@cache
def _motifs() -> dict[str, list[tuple[str, re.Pattern]]]:
    mc = referentiels.mots_cles()
    return {code: [(m, re.compile(rf"\b{m}")) for m in motifs]
            for famille in ("droits", "etiquettes") for code, motifs in mc[famille].items()}


def nature(procedure: str | None, titre: str) -> str:
    """Nature d'un texte, d'après la procédure AN et le titre : sert à filtrer les candidats."""
    p, t = norm(procedure), norm(titre)
    if "resolution" in p:
        return "resolution"
    if "ratification des traites" in p or re.search(r"autorisant (l approbation|la ratification|l adhesion)", t):
        return "convention"
    if "finances" in p or "financement de la securite sociale" in p or "loi speciale" in t:
        return "budget"
    if "constitutionnelle" in p:
        return "constitutionnelle"
    if "organique" in p:
        return "organique"
    return "ordinaire"


def reperer(titres: list[str]) -> dict[str, list[str]]:
    """code → motifs trouvés dans les titres."""
    t = " | ".join(norm(x) for x in titres if x)
    out = {}
    for code, motifs in _motifs().items():
        if trouves := [m for m, rx in motifs if rx.search(t)]:
            out[code] = trouves
    return out


def annoter(rows: list[dict], titres: dict[str, set[str]]) -> None:
    """Ajoute nature, droits et étiquettes candidats à chaque ligne du catalogue."""
    etiquettes = set(referentiels.mots_cles()["etiquettes"])
    for r in rows:
        r["nature"] = nature(r["procedure"], r["titre"])
        trouves = reperer([r["titre"], *sorted(titres.get(r["id"], ()))])
        r["droits_candidats"] = ";".join(c for c in trouves if c not in etiquettes)
        r["etiquettes_candidates"] = ";".join(c for c in trouves if c in etiquettes)
        r["motifs"] = ";".join(sorted({m for ms in trouves.values() for m in ms}))

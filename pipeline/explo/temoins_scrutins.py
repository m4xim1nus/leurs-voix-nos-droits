"""Spike : scrutins publics AN des six textes témoins, repérés par l'intitulé du scrutin.

Liste les scrutins hors amendements (ensemble, motions, articles) et compte les amendements.

    uv run python explo/temoins_scrutins.py
"""

import json
import re
from collections import Counter
from pathlib import Path

RAW = Path(__file__).resolve().parents[2] / "data/raw"

TEMOINS = {
    "JO 2024": (16, r"jeux olympiques et paralympiques de 2024"),
    "Immigration": (16, r"contrôler l.immigration, améliorer"),
    "Kasbarian-Bergé": (16, r"protéger les logements contre l.occupation illicite"),
    "Narcotrafic": (17, r"piège du narcotrafic|parquet national anticriminalité"),
    "Justice des mineurs": (17, r"autorité de la justice à l.égard des mineurs"),
    "Aide à mourir": (17, r"aide à mourir"),
}


def nature(titre: str) -> str:
    t = titre.lower()
    for mot, n in (("amendement", "amendement"), ("ensemble", "ensemble"), ("motion", "motion")):
        if mot in t[:40]:
            return n
    return "article" if "article" in t[:20] else "autre"


def main():
    scr = {leg: [json.loads(p.read_text())["scrutin"] for p in (RAW / f"an_scrutins_{leg}/x/json").glob("VTANR5*.json")]
           for leg in (16, 17)}
    for nom, (leg, motif) in TEMOINS.items():
        ss = sorted((s for s in scr[leg] if re.search(motif, s["titre"], re.I)), key=lambda s: int(s["numero"]))
        print(f"\n## {nom} (XV{'I' * (leg - 15)}e) : {len(ss)} scrutins {dict(Counter(nature(s['titre']) for s in ss))}")
        for s in ss:
            if nature(s["titre"]) != "amendement":
                d = s["syntheseVote"]["decompte"]
                print(f"  {s['uid']} {s['dateScrutin']} {s['typeVote']['codeTypeVote']} {s['sort']['code']:7} "
                      f"{d['pour']}-{d['contre']} | {s['titre'][:110]}")


if __name__ == "__main__":
    main()

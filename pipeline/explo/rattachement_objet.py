"""Scrutins rattachés par `objet.dossierLegislatif` dont le titre nomme un autre texte que ceux de leur dossier.

Le titre d'un scrutin nomme son texte (« … du projet de loi d'urgence agricole (première lecture) »). On compare ce nom
aux noms des autres scrutins du même dossier, et au titre du dossier. Un scrutin isolé, qui ne ressemble à rien dans
son dossier, est à lire à la main. Usage : `uv run python explo/rattachement_objet.py` (lit data/lvnd.sqlite).
"""
import re
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

from lvnd.textes import norm, similarite

NOM = re.compile(r"(?:projet|proposition) de (?:loi|resolution)(?: organique| constitutionnelle)?\b(.*)", re.I)
SUITE = re.compile(r"\((?:premiere|deuxieme|nouvelle|lecture|texte|seconde|troisieme).*$")


def nom(titre: str) -> str | None:
    m = NOM.search(norm(titre))
    return SUITE.sub("", m.group(1)).strip() if m else None


con = sqlite3.connect(Path(__file__).parents[2] / "data/lvnd.sqlite")
titres = dict(con.execute("select id, titre from textes"))
par_dossier = defaultdict(list)
for sid, date, titre, dossier, objet, ratt in con.execute(
        "select id, date, titre, dossier_id, objet, rattachement from scrutins where dossier_id is not null"):
    par_dossier[dossier].append((sid, date, titre, objet, ratt, nom(titre)))

n = 0
for dossier, ss in sorted(par_dossier.items()):
    noms = Counter(s[5] for s in ss if s[5])
    for sid, date, titre, objet, ratt, x in ss:
        if not x or ratt != "objet":
            continue
        autres = [y for y in noms if y != x]
        proche = max([similarite(x, y) for y in autres] + [similarite(x, titres.get(dossier) or "")], default=0)
        # isolé : le nom n'apparaît que rarement dans ce dossier et ne ressemble ni aux autres noms ni au titre
        if noms[x] <= 3 and sum(noms.values()) > noms[x] and proche < 0.3:
            n += 1
            print(f"{sid}\t{date}\t{objet}\t{proche:.2f}\t{dossier} ({(titres.get(dossier) or '')[:45]})\t{titre[:110]}")
print(n, "à lire")

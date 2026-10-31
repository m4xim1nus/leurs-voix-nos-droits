"""Contrôle croisé : ventilations de data/export/senat/ contre les pages de senat.fr, sur un échantillon.

    cd pipeline && uv run python explo/controle_senat.py [taille]

Échantillon : les scrutins dont le décompte s'écarte de la table `scr`, ceux qui portent une note, puis
un tirage (graine fixe) parmi les votes sur l'ensemble et parmi les autres. Pages gardées dans
data/raw/senat_pages/. Résultat noté dans docs/SOURCES.md. `EXPORT_SENAT` : contrôler un autre export.
"""

import html
import os
import random
import re
import sys
import time
from pathlib import Path

import httpx
import polars as pl

from lvnd.texte import norm

RACINE = Path(__file__).resolve().parents[2]
EXPORT = Path(os.environ.get("EXPORT_SENAT", RACINE / "data/export/senat"))
CACHE = RACINE / "data/raw/senat_pages"

# Les noms changent, pas le code : mots qui désignent le groupe dans les intitulés de la page.
GROUPES = [("UMP", "republicains"), ("SOC", "socialiste"), ("UC", "union centriste"),
           ("LREM", "rassemblement des democrates"), ("RDSE", "rassemblement democratique"),
           ("RTLI", "independants"), ("CRC", "communiste"), ("GEST", "ecologiste solidarite"),
           ("UNT", "union nationale"), ("NI", "aucun groupe"), ("NI", "non inscrit")]
BLOC = re.compile(r"(Groupe [^:]{3,160}?|R[ée]union administrative[^:]{3,160}?|S[ée]nateurs? ne figurant[^:]{3,160}?)\s*:\s*\|?\s*"
                  r"(\d+)\s*\|\s*s[ée]nateurs?\s*\|\s*Pour\s*:\s*\|\s*(\d+)\s*\|\s*Contre\s*:\s*\|\s*(\d+)\s*\|\s*"
                  r"Abstentions?\s*:\s*\|\s*(\d+)\s*\|\s*N.(?:a|ont)\s*\|?\s*pas pris part au vote\s*:\s*\|?\s*(\d+)")
TOTAL = re.compile(r"(\d+)\s*\|\s*votants\s*\|\s*(\d+)\s*\|\s*suffrages exprimés\s*\|\s*(\d+)\s*\|\s*pour\s*\|\s*(\d+)\s*\|\s*contre")


def _page(client: httpx.Client, url: str) -> str:
    f = CACHE / url.rsplit("/", 1)[1]
    if not f.exists():
        r = client.get(url)
        r.raise_for_status()
        CACHE.mkdir(parents=True, exist_ok=True)
        f.write_text(r.text)
        time.sleep(1)
    t = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", f.read_text(), flags=re.S)
    t = html.unescape(re.sub(r"<[^>]+>", "\n", t))
    t = re.sub(r"[ \t\xa0]+", " ", t)
    return re.sub(r"\s*\n\s*", " | ", t)


def _code(nom: str) -> str | None:
    n = norm(nom)
    return next((c for c, m in GROUPES if m in n), None)


def lire(texte: str) -> tuple[dict, dict]:
    """Totaux et ventilation par groupe (code → membres, pour, contre, abstention, non-votants)."""
    m = TOTAL.search(texte)
    total = dict(zip(("votants", "exprimes", "pour", "contre"), map(int, m.groups()))) if m else {}
    groupes = {}
    for b in BLOC.finditer(texte):
        code = _code(b.group(1))
        groupes[code or b.group(1)] = tuple(map(int, b.groups()[1:]))
    return total, groupes


def main(taille: int = 60) -> int:
    scr = pl.read_csv(EXPORT / "scrutins.csv", infer_schema=False).with_columns(
        pl.col("pour", "contre", "abstention", "non_votants", "votants", "exprimes", "pour_scr", "contre_scr").cast(pl.Int64))
    pos = pl.read_csv(EXPORT / "positions_groupes.csv", infer_schema=False).with_columns(
        pl.col("membres", "pour", "contre", "abstention", "non_votants").cast(pl.Int64))
    ecarts = scr.filter((pl.col("pour") != pl.col("pour_scr")) | (pl.col("contre") != pl.col("contre_scr")))["id"].to_list()
    notes = scr.filter(pl.col("note").is_not_null())["id"].to_list()
    rnd = random.Random(2026)
    ens = sorted(scr.filter(pl.col("objet") == "ensemble")["id"].to_list())
    autres = sorted(scr.filter(pl.col("objet") != "ensemble")["id"].to_list())
    tirage = rnd.sample(ens, taille // 2) + rnd.sample(autres, taille // 2)
    ids = list(dict.fromkeys(ecarts + notes + tirage))
    print(f"{len(ids)} scrutins : {len(ecarts)} écarts à `scr`, {len(notes)} avec note, {len(tirage)} tirés au sort")
    par_id = {r["id"]: r for r in scr.to_dicts()}
    bons, mauvais, lignes = 0, 0, 0
    with httpx.Client(timeout=60, follow_redirects=True) as client:
        for i in ids:
            s = par_id[i]
            total, groupes = lire(_page(client, s["url"]))
            attendu = {r["groupe_id"]: (r["membres"], r["pour"], r["contre"], r["abstention"], r["non_votants"])
                       for r in pos.filter(pl.col("scrutin_id") == i).to_dicts()}
            pb = []
            if not total or not groupes:
                pb.append("page illisible")
            elif (total["pour"], total["contre"], total["votants"], total["exprimes"]) != (s["pour"], s["contre"], s["votants"], s["exprimes"]):
                pb.append(f"totaux page {total} ≠ export {s['pour']}-{s['contre']}")
            pb += [f"{g} : page {groupes.get(g)} ≠ export {v}" for g, v in attendu.items() if groupes and groupes.get(g) != v]
            pb += [f"{g} : sur la page seulement {v}" for g, v in groupes.items() if g not in attendu]
            lignes += len(attendu)
            ecart = " (écart à scr)" if i in ecarts else ""
            if pb:
                mauvais += 1
                print(f"ÉCART {i}{ecart} {s['url']}\n   " + "\n   ".join(pb))
            else:
                bons += 1
                if ecart:
                    print(f"OK {i}{ecart} : page = liste nominative {s['pour']}-{s['contre']}, scr {s['pour_scr']}-{s['contre_scr']}")
    print(f"{bons} scrutins identiques, {mauvais} avec un écart ({lignes} lignes scrutin × groupe comparées)")
    return 1 if mauvais else 0


if __name__ == "__main__":
    sys.exit(main(*map(int, sys.argv[1:])))

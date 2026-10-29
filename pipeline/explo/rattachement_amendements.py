"""Spike : chaque scrutin sur un amendement (ou sous-amendement) se rattache-t-il à son
amendement, donc à son dossier, son auteur et le groupe de l'auteur ?

Le scrutin ne donne qu'un intitulé (« l'amendement n° 1762 de M. Le Coq … à l'article 2 du projet
de loi de finances pour 2025 ») et, depuis mars 2026 seulement, `objet.dossierLegislatif`. Les
amendements sont rangés par dossier (`json/<dossier>/<texte>/<amendement>.json`) avec leur auteur,
le groupe de l'auteur et, une fois sur deux, la séance de discussion.

Règle testée, dans l'ordre :
  1. séance du scrutin = `seanceDiscussionRef` de l'amendement, et même numéro ;
  2. sinon même numéro, examen en séance publique, déposé dans les 120 jours avant le scrutin,
     et nom de l'auteur de l'intitulé présent dans les signataires ; si plusieurs dossiers,
     celui dont le titre ressemble le plus à l'intitulé du scrutin ;
  3. contrôle : quand `objet.dossierLegislatif` existe, il doit être le dossier trouvé.

    uv run python explo/rattachement_amendements.py
"""

import html
import json
import re
import sys
import unicodedata
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

import polars as pl

RAW = Path(__file__).resolve().parents[2] / "data/raw"
ICI = Path(__file__).parent


def liste(v):
    return [] if v is None else v if isinstance(v, list) else [v]


def norm(t: str | None) -> str:
    t = re.sub(r"[’'`]", " ", html.unescape(t or ""))
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", t)).strip()


def nul(v):
    return None if isinstance(v, dict) else v


def amendements(leg: int) -> pl.DataFrame:
    cache = ICI / f"out_amendements_{leg}.parquet"
    if cache.exists():
        return pl.read_parquet(cache)
    rows = []
    for p in (RAW / f"an_amendements_{leg}/x/json").glob("*/*/*.json"):
        a = json.loads(p.read_text())["amendement"]
        ident = a["identification"]
        if ident.get("prefixeOrganeExamen") != "AN":
            continue
        aut = a["signataires"]["auteur"]
        cv = a.get("cycleDeVie") or {}
        rows.append({
            "uid": a["uid"],
            "dossier": p.parent.parent.name,
            "texte": a.get("texteLegislatifRef"),
            "numero": re.sub(r"\s*\(.*\)", "", str(ident["numeroLong"])).strip(),
            "seance": nul(a.get("seanceDiscussionRef")),
            "sous_amendement": isinstance(nul((a.get("amendementParentRef"))), str),
            "type_auteur": aut.get("typeAuteur"),
            "auteur": nul(aut.get("acteurRef")),
            "groupe": nul(aut.get("groupePolitiqueRef")),
            "signataires": html.unescape(a["signataires"].get("libelle") or ""),
            "depot": nul(cv.get("dateDepot")),
            "sort": nul((cv.get("sort") or {}).get("libelle")) if isinstance(cv.get("sort"), dict) else nul(cv.get("sort")),
        })
    df = pl.DataFrame(rows, infer_schema_length=None)
    df.write_parquet(cache)
    return df


def titres_dossiers(leg: int) -> dict[str, str]:
    out = {}
    for p in (RAW / f"an_dossiers_{leg}/x/json/dossierParlementaire").glob("*.json"):
        d = json.loads(p.read_text())["dossierParlementaire"]
        out[d["uid"]] = d["titreDossier"]["titre"]
    return out


RE_NUM = re.compile(r"^(?:l |le |les )?(sous amendement|amendement)s?(?: [a-z ]+?)? n ?(?:o )?(?:de )?((?:[a-z]{1,3} ?)?\d+)\b")
RE_AUTEUR = re.compile(r"\b(?:de m |de mme |de mmes |de mm |du )([a-z][a-z ]*?)(?= a l | apres l | avant l | au | aux | et l | et les | tendant | portant | visant | rectifie |,|$)")


def analyser(titre: str):
    t = norm(titre)
    m = RE_NUM.match(t)
    if not m:
        return None, None, None
    num = m.group(2).replace(" ", "-").upper()  # « i 123 » → « I-123 »
    a = RE_AUTEUR.search(t[m.end():])
    nom = re.split(r" de suppression| de retablissement| de reecriture| (?:\d+e|\d+eme )?rect", a.group(1))[0].strip() if a else None
    return m.group(1), num, nom or None


def mots(t):
    return {w for w in norm(t).split() if len(w) > 3}


def rattacher(leg: int):
    amdts = amendements(leg)
    titres = titres_dossiers(leg)
    par_num: dict[str, list[dict]] = {}
    for a in amdts.iter_rows(named=True):
        par_num.setdefault(a["numero"], []).append(a)
        # PLF : « I-1762 » (première partie) dans le dump, « n° 1762 » dans l'intitulé du scrutin
        if m := re.fullmatch(r"(?:I|II)-(\d+)", a["numero"]):
            par_num.setdefault(m.group(1), []).append(a)
    stats, exemples, rows = Counter(), {}, []
    for p in sorted((RAW / f"an_scrutins_{leg}/x/json").glob("VTANR5*.json")):
        s = json.loads(p.read_text())["scrutin"]
        if "amendement" not in s["titre"].lower()[:40]:
            continue
        nature, num, nom = analyser(s["titre"])
        dl = (s.get("objet") or {}).get("dossierLegislatif")
        dossier_ref = dl.get("dossierRef") if isinstance(dl, dict) else None
        d_scr = date.fromisoformat(s["dateScrutin"])
        trouve, cas = None, None
        if num is None:
            cas = "intitulé non analysé"
        else:
            cands = par_num.get(num, [])
            seance = [a for a in cands if a["seance"] and a["seance"] == s.get("seanceRef")]
            if len(seance) == 1:
                trouve, cas = seance[0], "1. séance + numéro"
            else:
                c2 = [a for a in cands if a["depot"]
                      and d_scr - timedelta(days=120) <= date.fromisoformat(a["depot"]) <= d_scr
                      and (nom is None or nom.split()[-1] in norm(a["signataires"]))]
                if dossier_ref:
                    c2 = [a for a in c2 if a["dossier"] == dossier_ref] or c2
                dossiers = {a["dossier"] for a in c2}
                if len(dossiers) > 1:
                    mt = mots(s["titre"])
                    best = max(dossiers, key=lambda d: len(mt & mots(titres.get(d))))
                    c2 = [a for a in c2 if a["dossier"] == best]
                if len(c2) >= 1:
                    # plusieurs lectures du même dossier : le dépôt le plus récent avant le scrutin
                    trouve = max(c2, key=lambda a: a["depot"])
                    cas = "2. numéro + auteur + date" + (" (plusieurs dossiers)" if len(dossiers) > 1 else "")
                else:
                    cas = "non rattaché"
        if trouve and dossier_ref and trouve["dossier"] != dossier_ref:
            cas += " — DÉSACCORD avec objet.dossierLegislatif"
        stats[cas] += 1
        exemples.setdefault(cas, []).append((s["uid"], s["titre"][:110]))
        rows.append({"scrutin": s["uid"], "legislature": leg, "date": s["dateScrutin"], "nature": nature,
                     "numero": num, "nom_intitule": nom, "cas": cas, "dossier_objet": dossier_ref,
                     **({k: trouve[k] for k in ("uid", "dossier", "texte", "type_auteur", "auteur", "groupe")}
                        if trouve else {})})
    total = sum(stats.values())
    print(f"\nXV{'I' * (leg - 15)}e : {total:,} scrutins sur amendement ou sous-amendement", file=sys.stderr)
    for cas, n in stats.most_common():
        print(f"  {n:6,}  {n / total:6.1%}  {cas}", file=sys.stderr)
        if "non" in cas or "DÉSACCORD" in cas:
            for e in exemples[cas][:4]:
                print(f"            {e}", file=sys.stderr)
    df = pl.DataFrame(rows, infer_schema_length=None)
    ok = df.filter(pl.col("uid").is_not_null())
    print(f"  auteur député avec groupe : {ok.filter(pl.col('groupe').is_not_null()).height:,} ; "
          f"autres auteurs : {dict(ok.filter(pl.col('groupe').is_null()).group_by('type_auteur').len().iter_rows())}",
          file=sys.stderr)
    return df


if __name__ == "__main__":
    legs = [int(a) for a in sys.argv[1:]] or [16, 17]
    pl.concat([rattacher(leg) for leg in legs], how="diagonal").write_parquet(ICI / "out_rattachement.parquet")

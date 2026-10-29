"""Amendements de séance et rattachement des scrutins sur amendement (docs/SOURCES.md).

Le scrutin ne donne que son intitulé (« l'amendement n° 1762 de M. Le Coq … à l'article 2 du
projet de loi de finances pour 2025 ») et, depuis mars 2026 seulement, `objet.dossierLegislatif`.
Règle, dans l'ordre :

1. même séance (`seanceRef` du scrutin = `seanceDiscussionRef` de l'amendement) et même numéro ;
2. sinon : même numéro, amendement déposé dans les 120 jours avant le scrutin, nom de l'auteur de
   l'intitulé présent parmi les signataires ; si plusieurs dossiers restent en lice, `objet.dossier`
   s'il existe, sinon le dossier dont le titre ressemble le plus à l'intitulé.

Un scrutin sur « l'amendement n° X et les amendements identiques » est rattaché au premier ; les
identiques (même `discussionIdentique` dans le même texte) sont exportés avec lui.
"""

import html
import json
import re
import sys
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

import polars as pl

from .an import nul
from .sources import extraits
from .texte import mots, norm

FENETRE = timedelta(days=120)
OBJETS = ("amendement", "suppression_article_unique")


def _ligne(a: dict, dossier: str) -> dict:
    ident = a["identification"]
    aut = a["signataires"]["auteur"]
    cv = a.get("cycleDeVie") or {}
    di = nul(a.get("discussionIdentique")) or {}
    div = ((a.get("pointeurFragmentTexte") or {}).get("division")) or {}
    return {
        "id": a["uid"],
        "dossier_id": dossier,
        "texte_id": a.get("texteLegislatifRef"),
        "numero": re.sub(r"\s*\(.*\)", "", str(ident["numeroLong"])).strip(),
        "seance": nul(a.get("seanceDiscussionRef")),
        "sous_amendement": isinstance(nul(a.get("amendementParentRef")), str),
        "type_auteur": aut.get("typeAuteur"),
        "auteur_id": nul(aut.get("acteurRef")),
        "groupe_id": nul(aut.get("groupePolitiqueRef")),
        "signataires": html.unescape(a["signataires"].get("libelle") or ""),
        "division": nul(div.get("titre")),
        "depot": nul(cv.get("dateDepot")),
        "sort": nul(cv.get("sort")),
        "discussion": di.get("idDiscussion"),
        "rang_identique": di.get("typePosition"),
    }


def lire(raw: Path, legislature: int, dossier_de_texte: dict[str, str]) -> pl.DataFrame:
    """Amendements examinés en séance publique. Lecture longue (≈ 150 000 fichiers) : mise en cache
    à côté de l'archive, refaite quand l'archive est plus récente."""
    cle = f"an_amendements_{legislature}"
    x = extraits(raw, cle)
    cache = raw / cle / "seance.parquet"
    if cache.exists() and cache.stat().st_mtime > x.stat().st_mtime:
        return pl.read_parquet(cache)
    rows = []
    for p in (x / "json").glob("*/*/*.json"):
        a = json.loads(p.read_text())["amendement"]
        if a["identification"].get("prefixeOrganeExamen") != "AN":
            continue
        dossier = p.parent.parent.name
        if dossier == "incorrect_data":  # rangement fautif du dump : on retrouve le dossier par le texte
            dossier = dossier_de_texte.get(a.get("texteLegislatifRef"))
        rows.append(_ligne(a, dossier))
    df = pl.DataFrame(rows, infer_schema_length=None)
    df.write_parquet(cache)
    return df


# Intitulé : « l'amendement (de suppression) n° 1762 (rect.) de M. Le Coq à l'article 2… »
RE_NUM = re.compile(r"^(?:l |le |les )?(sous amendement|amendement)s?(?: [a-z ]+?)? n ?(?:o )?(?:de )?"
                    r"((?:[a-z]{1,3} ?)?\d+)\b")
RE_AUTEUR = re.compile(r"\b(?:de m |de mme |de mmes |de mm |du )([a-z][a-z ]*?)(?= a l | apres l | avant l | au | aux "
                       r"| et l | et les | tendant | portant | visant | rectifie |,|$)")


def analyser(titre: str) -> tuple[str | None, str | None, str | None]:
    """(nature, numéro, nom de l'auteur) d'après l'intitulé d'un scrutin sur amendement."""
    t = norm(html.unescape(titre))
    m = RE_NUM.match(t)
    if not m:
        return None, None, None
    num = m.group(2).replace(" ", "-").upper()  # « i 123 » → « I-123 »
    a = RE_AUTEUR.search(t[m.end():])
    nom = re.split(r" de suppression| de retablissement| de reecriture| (?:\d+e|\d+eme )?rect", a.group(1))[0].strip() \
        if a else None
    return m.group(1), num, nom or None


def rattacher(scrutins: list[dict], amdts: pl.DataFrame, titres: dict[str, str]) -> dict[str, dict]:
    """scrutin_id → {amendement_id, dossier_id, rattachement} pour les scrutins sur amendement."""
    par_num: dict[str, list[dict]] = {}
    for a in amdts.iter_rows(named=True):
        par_num.setdefault(a["numero"], []).append(a)
        # PLF : « I-1762 » (première partie) dans le dump, « n° 1762 » dans l'intitulé du scrutin
        if m := re.fullmatch(r"(?:I|II)-(\d+)", a["numero"]):
            par_num.setdefault(m.group(1), []).append(a)
    out, stats = {}, Counter()
    for s in scrutins:
        if s["objet"] not in OBJETS:
            continue
        _, num, nom = analyser(s["titre"])
        trouve, cas = None, "non_rattache"
        if num is not None:
            cands = par_num.get(num, [])
            seance = [a for a in cands if a["seance"] and a["seance"] == s["seance"]]
            if len(seance) == 1:
                trouve, cas = seance[0], "seance"
            else:
                d_scr = date.fromisoformat(s["date"])
                c2 = [a for a in cands if a["depot"] and d_scr - FENETRE <= date.fromisoformat(a["depot"]) <= d_scr
                      and (nom is None or nom.split()[-1] in norm(a["signataires"]))]
                if s["dossier_objet"]:
                    c2 = [a for a in c2 if a["dossier_id"] == s["dossier_objet"]] or c2
                dossiers = {a["dossier_id"] for a in c2}
                if len(dossiers) > 1:
                    mt = mots(s["titre"])
                    meilleur = max(sorted(dossiers, key=str), key=lambda d: len(mt & mots(titres.get(d))))
                    c2 = [a for a in c2 if a["dossier_id"] == meilleur]
                if c2:
                    # plusieurs lectures du même dossier : le dépôt le plus récent avant le scrutin
                    trouve, cas = max(c2, key=lambda a: (a["depot"], a["id"])), "numero_auteur_date"
        stats[cas] += 1
        if trouve:
            out[s["id"]] = {"amendement_id": trouve["id"], "dossier_id": trouve["dossier_id"], "rattachement": cas}
    total = sum(stats.values())
    print(f"   {total:,} scrutins sur amendement : " + ", ".join(f"{k} {v:,} ({v / total:.1%})"
                                                          for k, v in stats.most_common()), file=sys.stderr)
    return out


def utiles(amdts: pl.DataFrame, ids: set[str]) -> pl.DataFrame:
    """Amendements mis aux voix par scrutin public, et leurs identiques (même discussion, même texte)."""
    vises = amdts.filter(pl.col("id").is_in(list(ids)))
    disc = vises.filter(pl.col("discussion").is_not_null()).select("texte_id", "discussion").unique()
    identiques = amdts.join(disc, on=["texte_id", "discussion"], how="semi")
    return (pl.concat([vises, identiques]).unique("id")
            .drop("signataires", "seance")
            .sort("id"))

"""Contrôles sans LLM d'un brouillon proposé (ROADMAP, cycle Pré-qualification, item 3).

Repris de l'étape 3 du circuit (docs/QUALIFICATION.md) : identifiant, termes interdits, `editorial.valider`,
décomptes `(pour-contre)`, URL qui répondent ; plus ce qu'exige une proposition automatique : chaque extrait
retrouvé mot pour mot dans le document de sa source, et les signataires d'une publication collective passés au
crible de la liste d'exclusion. Une **erreur** écarte la proposition ; un **avertissement** l'accompagne ; un
**point d'attention** va au relecteur.
"""

import base64
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

import httpx
import polars as pl
import yaml

from . import check, editorial

STATUTS = ("a-relire", "ecarte", "a-suivre", "sans-source")


@dataclass
class Resultat:
    erreurs: list[str] = field(default_factory=list)
    avertissements: list[str] = field(default_factory=list)
    points: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.erreurs

    def dict(self) -> dict:
        return {"erreurs": self.erreurs, "avertissements": self.avertissements, "points": self.points}


def infos_scrutins(export: Path) -> tuple[dict[str, dict], dict[str, dict]]:
    """Scrutins de l'AN et du Sénat pour `editorial.valider`, depuis data/export/ (division de l'amendement
    comprise)."""
    amdts = {}
    f = export / "amendements.csv"
    if f.exists() and f.stat().st_size:
        amdts = {r["id"]: r["division"] for r in pl.read_csv(f, infer_schema_length=None)
                 .select("id", "division").iter_rows(named=True)}
    an = {r["id"]: {"dossier_id": r["dossier_id"], "etape": r["etape"], "division": amdts.get(r["amendement_id"] or ""),
                    "objet": r["objet"], "pour": r["pour"], "contre": r["contre"]}
          for r in pl.read_csv(export / "scrutins.csv", infer_schema_length=None)
          .select("id", "dossier_id", "etape", "amendement_id", "objet", "pour", "contre").iter_rows(named=True)}
    senat = {}
    if (export / "senat/scrutins.csv").exists():
        senat = {r["id"]: {"dossier_id": r["dossier_id"], "objet": r["objet"], "pour": r["pour"], "contre": r["contre"]}
                 for r in pl.read_csv(export / "senat/scrutins.csv", infer_schema_length=None)
                 .select("id", "dossier_id", "objet", "pour", "contre").iter_rows(named=True)}
    return an, senat


# Texte normalisé pour retrouver une citation : casse, accents conservés, espaces, apostrophes, guillemets,
# tirets et coupures de ligne (PDF) ramenés à une forme unique.
_EQUIV = str.maketrans({"’": "'", "‘": "'", "ʼ": "'", "`": "'", "“": '"', "”": '"', "«": '"', "»": '"',
                        "–": "-", "—": "-", "‑": "-", " ": " ", " ": " ", " ": " "})


def normaliser(texte: str) -> str:
    t = unicodedata.normalize("NFC", texte).translate(_EQUIV).lower()
    t = re.sub(r"-\s*\n\s*", "", t)  # mot coupé en fin de ligne
    t = re.sub(r'\s*"\s*', '"', t)
    return re.sub(r"\s+", " ", t).strip()


EXTRAIT = re.compile(r"^\s*([\w.-]+)\s*:\s*«\s*(.+?)\s*»\s*$", re.DOTALL)


def segments(citation: str) -> list[str]:
    """Morceaux d'une citation coupée par « […] » ou « (…) », les plus courts ignorés."""
    morceaux = re.split(r"\s*[\[(]\s*(?:…|\.\.\.)\s*[\])]\s*|\s*…\s*", citation)
    return [m for m in (normaliser(m) for m in morceaux) if len(m) >= 12] or [normaliser(citation)]


def _texte_reponse(r: httpx.Response) -> str:
    if r.content[:4] == b"%PDF":
        from .proposer import _texte_pdf
        return _texte_pdf(base64.b64encode(r.content).decode())
    return re.sub(r"<[^>]+>", " ", r.text)


def lire(url: str, client: httpx.Client) -> tuple[int | str, str]:
    """Code HTTP et texte d'une URL (HTML débarrassé de ses balises, PDF extrait)."""
    try:
        r = client.get(url)
        return r.status_code, _texte_reponse(r) if r.status_code == 200 else ""
    except httpx.HTTPError as ex:
        return type(ex).__name__, ""


def controler(doc: dict, yaml_brut: str, dossier: str, infos_an: dict, infos_senat: dict,
              publies: dict[str, str], documents: dict[str, str] | None = None,
              client: httpx.Client | None = None) -> Resultat:
    """Contrôle un brouillon. `publies` : id publié → dossier ; `documents` : URL lue par le LLM → texte
    (complété ici par une lecture directe des URL qu'il n'a pas rendues)."""
    r = Resultat()
    documents = dict(documents or {})
    statut = doc.get("statut") or "a-relire"
    if statut not in STATUTS:
        r.erreurs.append(f"statut {statut!r} inconnu ({', '.join(STATUTS)})")
        return r
    if doc.get("dossier_an") != dossier:
        r.erreurs.append(f"dossier_an {doc.get('dossier_an')!r} ≠ {dossier}")

    # Termes interdits : dans le brouillon (bloquant), dans les signataires listés (bloquant).
    if check.liste_termes() is None:
        r.erreurs.append("liste des termes interdits introuvable : contrôle impossible")
    elif trouves := check.termes_interdits(yaml_brut):
        r.erreurs.append(f"{len(trouves)} terme(s) de la liste d'exclusion dans le brouillon")
    relecture = doc.get("relecture") or {}
    signataires = relecture.get("signataires") or {}
    for cle, liste in signataires.items():
        if check.termes_interdits(" ; ".join(map(str, liste or []))):
            r.erreurs.append(f"source {cle} : publication cosignée par une organisation exclue")
        else:
            r.points.append(f"source {cle} : publication collective, {len(liste or [])} signataires listés, "
                            "contrôlés contre la liste d'exclusion")
    for p in relecture.get("points_attention") or []:
        if str(p).startswith("CAS NON PRÉVU"):
            r.points.append(str(p))

    if statut == "sans-source":
        r.points.append("aucune source admise trouvée : pas de fiche, le texte attend")
        return r

    ident = doc.get("id") or ""
    if statut != "ecarte":
        if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", ident):
            r.erreurs.append(f"id {ident!r} : minuscules, chiffres et tirets")
        elif ident in publies and publies[ident] != dossier:
            r.erreurs.append(f"id {ident} déjà pris par {publies[ident]}")
    elif not (doc.get("motif_ecart") or "").strip():
        r.erreurs.append("texte écarté sans motif")

    # Règles de la méthode, comme l'admin et `lvnd check`.
    if statut == "a-suivre":
        err, avert = editorial.valider_suivi(doc)
        r.erreurs += err
        r.avertissements += avert
    elif statut == "a-relire":
        complement = not doc.get("titre")  # bloc `senat` seul, ajouté à une qualification existante
        if not complement:
            try:
                n = editorial.normaliser({**doc, "droits": doc.get("droits") or [], "scrutins": doc.get("scrutins") or []})
            except (KeyError, TypeError, ValueError) as ex:
                r.erreurs.append(f"brouillon incomplet : {type(ex).__name__} {ex}")
                return r
            err, avert = editorial.valider(n, infos_an, infos_senat)
            r.erreurs += err
            r.avertissements += avert
        for s in doc.get("scrutins") or []:
            i = infos_an.get(s.get("id"))
            m = re.search(r"\((\d+)-(\d+)\)\s*$", s.get("objet") or "")
            if i is None:
                r.erreurs.append(f"{s.get('id')} : scrutin inconnu")
            elif not m or (int(m[1]), int(m[2])) != (i["pour"], i["contre"]):
                r.erreurs.append(f"{s['id']} : décompte {m and m.group(0)} ≠ ({i['pour']}-{i['contre']})")
            elif i["dossier_id"] != dossier:
                r.avertissements.append(f"{s['id']} : rattaché au dossier {i['dossier_id']}")

    # Sources : URL qui répond, extraits retrouvés dans leur document.
    sources = dict(doc.get("sources") or {})
    if (doc.get("senat") or {}).get("sources"):
        sources.update(doc["senat"]["sources"])
    ferme = client is None
    client = client or httpx.Client(follow_redirects=True, timeout=30,
                                    headers={"User-Agent": "Mozilla/5.0 (lvnd, controle des sources)"})
    try:
        for cle, src in sources.items():
            url = (src or {}).get("url") or ""
            if not url.startswith("http") or url in documents:
                continue
            code, texte = lire(url, client)
            if code != 200:
                r.avertissements.append(f"source {cle} : {url} répond {code}")
            elif texte:
                documents[url] = texte
    finally:
        if ferme:
            client.close()
    for cle, src in sources.items():
        url = (src or {}).get("url") or ""
        if url in documents and check.termes_interdits(documents[url]):
            r.points.append(f"source {cle} : le document nomme une organisation exclue ; vérifier que le passage "
                            "cité n'en reprend rien")

    normes = {url: normaliser(t) for url, t in documents.items()}
    extraits = relecture.get("extraits") or []
    if statut in ("a-relire", "a-suivre") and sources and not extraits:
        r.erreurs.append("aucun extrait : chaque jugement doit s'appuyer sur une citation lue")
    for e in extraits:
        m = EXTRAIT.match(str(e))
        if not m:
            r.erreurs.append(f"extrait mal formé (attendu « clé : « citation » ») : {str(e)[:80]}")
            continue
        cle, citation = m[1], m[2]
        src = sources.get(cle)
        if src is None:
            # Un écart n'a pas de sources : il peut citer le dossier de l'AN ou le compte rendu, sans les déclarer.
            (r.avertissements if statut == "ecarte" else r.erreurs).append(f"extrait de {cle} : source non définie")
            continue
        texte = normes.get(src.get("url") or "")
        if texte is None:
            r.erreurs.append(f"extrait de {cle} : document illisible, citation invérifiable")
        elif not all(s in texte for s in segments(citation)):
            r.erreurs.append(f"extrait de {cle} introuvable dans le document : « {citation[:80]} »")
    return r


def publies_ids(doc: dict | None = None) -> dict[str, str]:
    doc = doc or editorial.charger()
    return {t["id"]: t["dossier_an"] for t in (doc.get("textes") or []) + (doc.get("suivis") or [])}


def rapport(r: Resultat) -> str:
    return yaml.safe_dump(r.dict(), allow_unicode=True, sort_keys=False, width=1000)

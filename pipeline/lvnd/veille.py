"""Veille des sources « à l'envers » (ROADMAP, cycle Pré-qualification, item 7 ; décision de Max du 02/11/2026).

Une fois par semaine :
1. **sans LLM**, lecture des flux RSS ou Atom de referentiels/sources_veille.yaml, publications des derniers jours ;
2. **un appel** au LLM rapproche ces publications des textes publiés : qualifiés, suivis, et écartés faute de source
   (c'est là qu'une source nouvelle change la décision) ;
3. pour chaque correspondance, et elle seule, une proposition complète (`lvnd.proposer`, mode `veille`), contrôlée et
   écrite dans D1 comme les autres. Elle arrive dans « À traiter ».

Une correspondance déjà proposée ne l'est plus (clé `veille:dossier:empreinte du lien`). Un flux en panne est signalé et
n'arrête rien.
"""

import hashlib
import html
import json
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

import httpx

from . import check, controles, editorial, llm, proposer, referentiels, sync_admin

JOURS = 8  # une semaine, plus un jour de recouvrement : une correspondance déjà proposée ne revient pas
MAX_PROPOSITIONS = 3
LOT = 150  # publications par appel de rapprochement

ATOM = "{http://www.w3.org/2005/Atom}"
DC = "{http://purl.org/dc/elements/1.1/}"


@dataclass
class Publication:
    flux: str
    auteur: str
    titre: str
    lien: str
    date: str
    resume: str


def _texte(x: str | None, n: int = 400) -> str:
    t = re.sub(r"<[^>]+>", " ", html.unescape(x or ""))
    t = re.sub(r"\s+", " ", t).strip()
    return t[:n] + ("…" if len(t) > n else "")


def _date(x: str | None) -> datetime | None:
    if not x:
        return None
    x = x.strip()
    try:
        d = parsedate_to_datetime(x)
    except (TypeError, ValueError, IndexError):
        try:
            d = datetime.fromisoformat(x.replace("Z", "+00:00"))
        except ValueError:
            return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def lire_flux(contenu: bytes, flux: dict) -> list[Publication]:
    """Publications d'un flux RSS 2.0 ou Atom (dates illisibles : publication ignorée)."""
    racine = ET.fromstring(contenu)
    out = []
    for e in racine.iter():
        if e.tag == "item":
            titre, lien = e.findtext("title"), e.findtext("link")
            date = e.findtext("pubDate") or e.findtext(f"{DC}date")
            resume = e.findtext("description")
        elif e.tag == f"{ATOM}entry":
            titre = e.findtext(f"{ATOM}title")
            l = e.find(f"{ATOM}link[@rel='alternate']")
            l = l if l is not None else e.find(f"{ATOM}link")
            lien = l.get("href") if l is not None else None
            date = e.findtext(f"{ATOM}published") or e.findtext(f"{ATOM}updated")
            resume = e.findtext(f"{ATOM}summary") or e.findtext(f"{ATOM}content")
        else:
            continue
        d = _date(date)
        if not lien or d is None:
            continue
        out.append(Publication(flux["cle"], flux["auteur"], _texte(titre, 300), lien.strip(),
                               d.astimezone(timezone.utc).isoformat(timespec="seconds"), _texte(resume)))
    return out


def collecter(flux: list[dict], depuis: datetime, client: httpx.Client) -> tuple[list[Publication], list[str]]:
    publications, pannes = [], []
    for f in flux:
        try:
            r = client.get(f["url"])
            r.raise_for_status()
            lues = lire_flux(r.content, f)
        except (httpx.HTTPError, ET.ParseError) as ex:
            pannes.append(f"{f['cle']} : {type(ex).__name__} {str(ex)[:120]}")
            continue
        publications += [p for p in lues if p.date >= depuis.isoformat(timespec="seconds")]
    vus, uniques = set(), []
    for p in sorted(publications, key=lambda p: p.date, reverse=True):
        if p.lien not in vus:
            vus.add(p.lien)
            uniques.append(p)
    return uniques, pannes


FAUTE_DE_SOURCE = re.compile(r"source", re.I)


def textes_suivis(publie: dict) -> list[dict]:
    """Textes publiés que la veille regarde : qualifiés, suivis, et écartés faute de source."""
    def ligne(t: dict, statut: str) -> dict:
        r = t.get("recherche") or {}
        return {"dossier_an": t["dossier_an"], "statut": statut, "titre": t["titre"],
                "droits": [d["code"] for d in t.get("droits") or []],
                "termes": [*r.get("termes", []), *r.get("surnoms", [])]}
    return ([ligne(t, "qualifié") for t in publie["textes"]]
            + [ligne(s, "suivi") for s in publie.get("suivis", [])]
            + [ligne(e, "écarté faute de source") for e in publie.get("ecartes", []) if FAUTE_DE_SOURCE.search(e["motif"])])


SYSTEME_RAPPROCHEMENT = """\
Tu fais la veille d'un projet qui qualifie des textes législatifs selon les droits et libertés qu'ils touchent. On te
donne des publications récentes de sources admises (autorités indépendantes, syndicats, ONG…) et la liste des textes
suivis. Retiens une correspondance seulement si la publication porte sur le texte lui-même ou sur une de ses mesures
(avis, analyse, recours, décision, critique ou soutien argumenté), au point qu'elle pourrait servir de source pour le
qualifier. Une publication qui évoque seulement le même thème n'est pas une correspondance. Sois sélectif : dans le
doute, ne retiens pas. `raison` dit en une phrase ce que la publication dit du texte."""

SCHEMA = {
    "type": "object",
    "properties": {"correspondances": {"type": "array", "items": {
        "type": "object",
        "properties": {"lien": {"type": "string"}, "dossier_an": {"type": "string"}, "raison": {"type": "string"}},
        "required": ["lien", "dossier_an", "raison"], "additionalProperties": False}}},
    "required": ["correspondances"], "additionalProperties": False,
}


def rapprocher(session: llm.Session, publications: list[Publication], textes: list[dict]) -> list[dict]:
    """Correspondances publication → texte, par lots ; seules restent celles dont le lien et le dossier existent."""
    liens = {p.lien for p in publications}
    dossiers = {t["dossier_an"] for t in textes}
    liste = json.dumps(textes, ensure_ascii=False, separators=(",", ":"))
    out = []
    for i in range(0, len(publications), LOT):
        lot = [asdict(p) for p in publications[i:i + LOT]]
        message = ("# Textes suivis\n\n" + liste + "\n\n# Publications récentes\n\n"
                   + json.dumps(lot, ensure_ascii=False, separators=(",", ":")))
        if check.termes_interdits(message):  # une publication d'une source exclue ne part pas au LLM
            raise llm.Indisponible("un terme de la liste d'exclusion dans les publications : vérifier les flux")
        r = session.appeler(None, max_tokens=16_000, system=SYSTEME_RAPPROCHEMENT,
                            messages=[{"role": "user", "content": message}],
                            output_config={"effort": "medium", "format": {"type": "json_schema", "schema": SCHEMA}})
        texte = next((b.text for b in r.content if getattr(b, "type", None) == "text"), "{}")
        try:
            trouvees = json.loads(texte).get("correspondances", [])
        except ValueError:
            continue
        out += [c for c in trouvees if c.get("lien") in liens and c.get("dossier_an") in dossiers]
    return out


def cle_alerte(dossier: str, lien: str) -> str:
    return f"veille:{dossier}:{hashlib.sha1(lien.encode()).hexdigest()[:12]}"


def lancer(export: Path, admin: Path, cible: str, jours: int, maximum: int, simuler: bool, essai: bool = False) -> int:
    ref = referentiels.charger("sources_veille")
    if ref.get("statut") != "valide" and not (simuler or essai):
        print("veille non lancée : la liste des flux (referentiels/sources_veille.yaml) n'est pas encore validée par Max "
              "(statut: valide) ; --essai pour un passage à la main", file=sys.stderr)
        return 0
    flux = ref["flux"]
    depuis = datetime.now(timezone.utc) - timedelta(days=jours)
    with httpx.Client(follow_redirects=True, timeout=20,
                      headers={"User-Agent": "Mozilla/5.0 (lvnd, veille des sources)"}) as client:
        publications, pannes = collecter(flux, depuis, client)
    for p in pannes:
        print(f"flux en panne, {p}", file=sys.stderr)
    print(f"{len(publications)} publication(s) depuis le {depuis:%d/%m/%Y}, {len(flux) - len(pannes)} flux lus "
          f"sur {len(flux)}", file=sys.stderr)
    publie = editorial.charger()
    textes = textes_suivis(publie)
    if simuler or not publications:
        return 0
    d1 = llm.D1(cible, admin)
    try:
        session = llm.Session(d1, "veille")
    except llm.Indisponible as ex:
        print(f"aucune veille : {ex}", file=sys.stderr)
        return 0
    from . import propositions  # import tardif : propositions importe proposer, qui importe ce module indirectement
    try:
        correspondances = rapprocher(session, publications, textes)
    except llm.Indisponible as ex:
        print(f"arrêt, {ex}", file=sys.stderr)
        return 0
    faites = {r["alerte_id"] for r in d1.lire("SELECT alerte_id FROM propositions WHERE alerte_id LIKE 'veille:%'")}
    par_lien = {p.lien: p for p in publications}
    nouvelles = [c for c in correspondances if cle_alerte(c["dossier_an"], c["lien"]) not in faites]
    print(f"{len(correspondances)} correspondance(s), dont {len(nouvelles)} nouvelle(s)", file=sys.stderr)
    for c in correspondances:
        p = par_lien[c["lien"]]
        print(f"   {c['dossier_an']} ← {p.auteur}, « {p.titre} » : {c['raison']}", file=sys.stderr)
    infos_an, infos_senat = controles.infos_scrutins(export)
    ids = controles.publies_ids(publie)
    for c in nouvelles[:maximum]:
        d, pub = c["dossier_an"], par_lien[c["lien"]]
        alerte = {"id": cle_alerte(d, c["lien"]), "type": "veille", "dossier_id": d, "scrutin_id": None,
                  "date": pub.date[:10], "detail": f"{pub.auteur} : {pub.titre} ({c['raison']})"}
        try:
            p = proposer.proposer(session, export, d, "veille", alerte, proposer.publie(d, publie),
                                  publication={**asdict(pub), "raison": c["raison"]})
        except llm.Indisponible as ex:
            print(f"{d} : arrêt, {ex}", file=sys.stderr)
            break
        except Exception as ex:
            print(f"{d} : erreur, {type(ex).__name__} : {str(ex)[:200]}", file=sys.stderr)
            continue
        r = None
        if p.doc is not None:
            r = controles.controler(p.doc, p.yaml_brut, d, infos_an, infos_senat, ids, p.documents)
        ligne = propositions.ligne_d1(alerte, p, r, session.modele, publication={**asdict(pub), "raison": c["raison"]})
        d1.ecrire(sync_admin.inserts("propositions", propositions.COLONNES_D1, [ligne])[0])
        print(f"{alerte['id']} → {ligne['statut']}{' : ' + ligne['motif'] if ligne['motif'] else ''}, "
              f"{p.cout_usd:.2f} $", file=sys.stderr)
    if len(nouvelles) > maximum:
        print(f"{len(nouvelles) - maximum} correspondance(s) laissée(s) de côté (--max {maximum}) : elles reviendront "
              "si la publication est encore dans la fenêtre", file=sys.stderr)
    print(f"dépense du mois : {session.depense:.2f} $ sur {session.reglages.plafond_usd:.2f} $", file=sys.stderr)
    return 0

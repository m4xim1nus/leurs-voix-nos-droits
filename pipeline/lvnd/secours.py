"""Plan B quand un dump d'amendements reste injoignable (docs/SOURCES.md).

Le site de l'AN, autre serveur que celui des dumps, sert chaque amendement à part, au même format.
Son identifiant se reconstitue : `AMANR5L<lég.>PO<organe séance><texte>P<partie>D<division>N<numéro>`.
Le scrutin donne le numéro (`amendements.analyser`) et son dossier les textes possibles, qu'on essaie
un à un, en commençant par le dernier texte trouvé pour ce dossier. Un même numéro existe sur plusieurs
textes : on retient l'amendement de la même séance signé de l'auteur nommé par l'intitulé ; à défaut,
après tous les essais, le dépôt le plus récent de cet auteur dans la fenêtre de `amendements.rattacher`,
puis l'amendement de la même séance. Le numéro complet doit toujours correspondre.

Limite : on ne récupère que les amendements mis aux voix, pas leurs identiques, que rien ne permet
de lister sans le dump. Les fichiers sont rangés comme dans le dump, `amendements.lire` les lit donc
sans distinction. Tout est gardé d'un lancement à l'autre : on reprend là où on s'est arrêté.
"""

import json
import re
import sys
import time
from datetime import date
from pathlib import Path

import httpx

from . import amendements, an, textes
from .sources import Injoignable, unitaire
from .texte import norm

URL = "https://www.assemblee-nationale.fr/dyn/opendata/{}.json"
PAUSE = 1.0  # secondes entre deux requêtes
PATIENCE = 600  # secondes d'erreurs serveur d'affilée avant d'abandonner
MAX_ESSAIS = 60  # identifiants essayés par scrutin
RE_TEXTE = re.compile(r"^(?:PRJL|PION|PNRE|PTLE|TAP)[A-Z]*R5L(\d+)(BTC\d+|B\d+)")
RE_CITE = re.compile(r"(?:PRJL|PION|PNRE|PTLE|TAP)[A-Z]*R5L\d+BTC?\d+")


def normaliser(v):
    """Le JSON unitaire écrit `{}` là où le dump écrit un nil XML, et préfixe parfois les signataires."""
    if isinstance(v, dict):
        return {k: normaliser(x) for k, x in v.items()} or None
    if isinstance(v, list):
        return [normaliser(x) for x in v]
    return v.strip() if isinstance(v, str) else v


def textes_par_dossier(dossier_de: dict[str, str], legislature: int,
                       dossiers: dict[str, dict] | None = None) -> dict[str, list[str]]:
    """dossier → parties `B…`/`BTC…` de l'identifiant de ses textes, du plus récent au plus ancien.
    Le dossier lui-même en cite que l'index des documents ignore (`BTC1991`, loi européenne sur l'espace)."""
    out: dict[str, set[str]] = {}
    cites = ((t, uid) for uid, d in (dossiers or {}).items() for t in RE_CITE.findall(json.dumps(d)))
    for texte, dossier in (*dossier_de.items(), *cites):
        if (m := RE_TEXTE.match(texte)) and int(m[1]) == legislature:
            # Des amendements de séance portent `B<n>` alors que seul `BTC<n>` est un texte (V1191 en XVIIe).
            out.setdefault(dossier, set()).update({m[2], m[2].replace("BTC", "B")})
    return {d: sorted(b, key=lambda x: (-int(re.sub(r"\D", "", x)), "TC" not in x)) for d, b in out.items()}


def candidats(legislature: int, organe: str, numero: str, bases: list[str]) -> list[str]:
    """Identifiants possibles. Division 1, parties 0, puis 1 et 2 (PLF), d'abord ; la division 2 est rare."""
    n = int(re.sub(r"\D", "", numero))
    return [f"AMANR5L{legislature}PO{organe}{b}P{p}D{d}N{n:06d}" for d in "12" for b in bases for p in "012"]


def meme_numero(a: dict, numero: str, seconde_partie: bool = False) -> bool:
    """Le numéro complet (l'identifiant ne porte que ses chiffres). Au PLF, « I-1762 » et « II-1762 » valent
    « 1762 » : un intitulé qui nomme la seconde partie exclut la première, où le même numéro existe aussi."""
    lu = re.sub(r"\s*\(.*\)", "", str((a.get("identification") or {}).get("numeroLong"))).strip()
    return lu == numero or bool(re.fullmatch(rf"{'II' if seconde_partie else '(?:I|II)'}-{re.escape(numero)}", lu))


def signe(a: dict, nom: str | None) -> bool:
    """L'auteur nommé par l'intitulé du scrutin figure parmi les signataires."""
    return nom is None or nom.split()[-1] in norm((a.get("signataires") or {}).get("libelle") or "")


def depose_avant(a: dict, s: dict) -> bool:
    depot, d = (a.get("cycleDeVie") or {}).get("dateDepot"), date.fromisoformat(s["date"])
    return bool(depot) and d - amendements.FENETRE <= date.fromisoformat(depot[:10]) <= d


def _lire_unitaire(client: httpx.Client, uid: str, patience: int = PATIENCE) -> dict | None:
    """L'amendement, ou None s'il n'existe pas. Un refus du serveur arrête tout : on n'insiste pas."""
    debut, attente = time.monotonic(), 5
    while True:
        time.sleep(PAUSE)
        try:
            r = client.get(URL.format(uid))
            if r.status_code == 200:
                return normaliser(r.json())
            if r.status_code == 404:
                return None
            if r.status_code in (401, 403):
                raise SystemExit(f"plan B : accès refusé par le site de l'AN ({r.status_code}), arrêt")
            if r.status_code == 429 and r.headers.get("retry-after", "").isdigit():
                attente = max(attente, int(r.headers["retry-after"]))
        except (httpx.TransportError, ValueError):
            pass
        if time.monotonic() - debut > patience:
            raise Injoignable(f"plan B : le site de l'AN ne répond plus depuis {patience} s")
        time.sleep(attente)
        attente = min(2 * attente, 120)


def _lisible(p: Path) -> bool:
    """Un arrêt brutal de la machine peut laisser un fichier vide ou tronqué : on l'écarte, il sera redemandé."""
    try:
        json.loads(p.read_text())
        return True
    except ValueError:
        p.unlink()
        return False


def parcourir(client: httpx.Client, dossier: Path, legislature: int, organe: str, vises: list[dict],
              liens: dict[str, dict], seances: dict[str, set[str]], dossier_de: dict[str, str],
              bases: dict[str, list[str]], duree_max: int | None = None) -> dict:
    """Récupère dans `dossier` l'amendement de chaque scrutin de `vises` ; renvoie le bilan."""
    chemin_etat = dossier / "etat.json"
    etat = json.loads(chemin_etat.read_text()) if chemin_etat.exists() else {"scrutins": {}, "absents": []}
    connus = {p.stem: p for p in dossier.glob("json/*/*/*.json") if _lisible(p)}
    etat["scrutins"] = {k: u for k, u in etat["scrutins"].items() if u is None or u in connus}
    absents, debut, requetes, dernier = set(etat["absents"]), time.monotonic(), 0, {}

    def sauver():
        etat["absents"] = sorted(absents)
        chemin_etat.with_suffix(".tmp").write_text(json.dumps(etat))
        chemin_etat.with_suffix(".tmp").replace(chemin_etat)

    dossier.mkdir(parents=True, exist_ok=True)
    for i, s in enumerate(vises):
        if s["id"] in etat["scrutins"]:
            continue
        if duree_max and time.monotonic() - debut > duree_max:
            sauver()
            raise SystemExit(f"plan B : durée maximale atteinte ({i}/{len(vises)} scrutins), à reprendre")
        _, num, nom = amendements.analyser(s["titre"])
        trouve = None
        if num is not None:
            principal = liens.get(s["id"], {}).get("dossier_id")
            # Les autres dossiers de la séance seulement à défaut : un même numéro du même auteur y passerait le contrôle.
            cands = [principal] if principal else sorted(seances.get(s["seance"], set()))
            ordre = [dernier[d] for d in cands if d in dernier]
            ordre += [b for d in cands for b in bases.get(d, [])]
            auteur_date, seance_seule = None, None
            for uid in candidats(legislature, organe, num, list(dict.fromkeys(ordre)))[:MAX_ESSAIS]:
                if uid in absents:
                    continue
                if uid in connus:
                    a = json.loads(connus[uid].read_text())["amendement"]
                else:
                    a = _lire_unitaire(client, uid)
                    requetes += 1
                    if a is None:
                        absents.add(uid)
                        continue
                if not meme_numero(a, num, "seconde partie" in norm(s["titre"])):
                    continue
                meme_seance = bool(s["seance"]) and a.get("seanceDiscussionRef") == s["seance"]
                if meme_seance and signe(a, nom):
                    trouve = (uid, a)
                    break
                if signe(a, nom) and depose_avant(a, s):  # le dépôt le plus récent avant le scrutin
                    if not auteur_date or (a["cycleDeVie"]["dateDepot"], uid) > (auteur_date[1]["cycleDeVie"]["dateDepot"], auteur_date[0]):
                        auteur_date = (uid, a)
                elif meme_seance:
                    seance_seule = seance_seule or (uid, a)
            trouve = trouve or auteur_date or seance_seule
            if trouve:
                uid, a = trouve
                texte = a.get("texteLegislatifRef")
                maison = dossier_de.get(texte) or principal or "inconnu"
                if uid not in connus:
                    p = dossier / "json" / maison / str(texte) / f"{uid}.json"
                    p.parent.mkdir(parents=True, exist_ok=True)
                    p.with_suffix(".tmp").write_text(json.dumps({"amendement": a}, ensure_ascii=False))
                    p.with_suffix(".tmp").replace(p)
                    connus[uid] = p
                dernier[maison] = re.search(r"PO\d+(B(?:TC)?\d+)P", uid)[1]
                trouve = uid
        etat["scrutins"][s["id"]] = trouve
        if requetes and requetes % 25 == 0:
            sauver()
        if (i + 1) % 100 == 0:
            n = sum(v is not None for v in etat["scrutins"].values())
            print(f"  {i + 1:,} / {len(vises):,} scrutins, {n:,} amendements, {requetes:,} requêtes", file=sys.stderr)
    sauver()
    return {"scrutins_sur_amendement": len(vises),
            "amendements_trouves": sum(v is not None for v in etat["scrutins"].values()),
            "requetes": requetes}


def recuperer(client: httpx.Client, raw: Path, cle: str, legislature: int, organe: str,
              duree_max: int | None = None) -> dict:
    """Plan B d'une législature : demande que scrutins et dossiers aient déjà été téléchargés."""
    dossier_de, titres = textes.documents(raw)
    dossiers = textes.tous_dossiers(raw)
    scrutins = an.scrutins(raw, legislature)["scrutins"]
    liens = textes.rattacher(scrutins, dossiers, titres, {})
    vises = sorted((s for s in scrutins if s["objet"] in amendements.OBJETS), key=lambda s: (s["date"], s["numero"]))
    dossier = unitaire(raw, cle)
    dossier.mkdir(parents=True, exist_ok=True)
    return parcourir(client, dossier, legislature, organe, vises, liens, textes.Index(dossiers).par_seance,
                     dossier_de, textes_par_dossier(dossier_de, legislature, dossiers), duree_max)

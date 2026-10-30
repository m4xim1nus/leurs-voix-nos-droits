"""Sources open data et téléchargement (docs/SOURCES.md).

Repris de quifaitlaloi. Les dumps AN sont régénérés chaque nuit : on ne les
épingle pas par sha256. `download` les récupère, les extrait dans
`<raw>/<cle>/x/` et note dans `<raw>/manifeste.json` l'URL, le
`Last-Modified`, la taille et le sha256 de chaque archive. Ce manifeste est
recopié dans l'export : il date l'instantané versionné.

Si un dump d'amendements reste injoignable, `download` bascule seul sur le
plan B (`secours.py`, amendement par amendement) ; le manifeste le note
(`mode: secours`) et chaque lancement suivant retente le dump, qui remplace tout.
"""

import fcntl

import hashlib
import json
import shutil
import sys
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import httpx

AN = "https://data.assemblee-nationale.fr/static/openData/repository"

SOURCES: dict[str, dict] = {
    "an_scrutins_17": {"url": f"{AN}/17/loi/scrutins/Scrutins.json.zip"},
    "an_dossiers_17": {"url": f"{AN}/17/loi/dossiers_legislatifs/Dossiers_Legislatifs.json.zip"},
    "an_amendements_17": {"url": f"{AN}/17/loi/amendements_div_legis/Amendements.json.zip",
                          "secours": {"legislature": 17, "organe": "838901"}},
    "an_scrutins_16": {"url": f"{AN}/16/loi/scrutins/Scrutins.json.zip"},
    "an_dossiers_16": {"url": f"{AN}/16/loi/dossiers_legislatifs/Dossiers_Legislatifs.json.zip"},
    "an_amendements_16": {"url": f"{AN}/16/loi/amendements_div_legis/Amendements.json.zip",
                          "secours": {"legislature": 16, "organe": "791932"}},
    "an_amo": {"url": f"{AN}/17/amo/tous_acteurs_mandats_organes_xi_legislature/"
                      "AMO30_tous_acteurs_tous_mandats_tous_organes_historique.json.zip"},
    "an_agenda_17": {"url": f"{AN}/17/vp/reunions/Agenda.json.zip"},
    "senat_dosleg": {"url": "https://data.senat.fr/data/dosleg/dosleg.zip"},
}

MANIFESTE = "manifeste.json"
PATIENCE_AVANT_SECOURS = 1200  # secondes sans aucun octet avant de basculer sur le plan B


class Injoignable(SystemExit):
    """Le dump n'a livré aucun octet pendant toute la patience."""


def sha256_fichier(chemin: Path) -> str:
    h = hashlib.sha256()
    with chemin.open("rb") as f:
        for bloc in iter(lambda: f.read(1 << 20), b""):
            h.update(bloc)
    return h.hexdigest()


def extraits(raw: Path, cle: str) -> Path:
    """Dossier où la source `cle` est extraite (ou le fichier lui-même s'il n'est pas zippé)."""
    src = SOURCES[cle]
    if src.get("zip", True):
        return raw / cle / "x"
    return raw / cle / src["url"].rsplit("/", 1)[1]


def unitaire(raw: Path, cle: str) -> Path:
    """Dossier du plan B : mêmes `json/<dossier>/<texte>/<amendement>.json` que l'archive extraite."""
    return raw / cle / "unitaire"


def racine(raw: Path, cle: str) -> Path:
    """Où lire une source : l'archive extraite, à défaut ce qu'a récupéré le plan B."""
    x = extraits(raw, cle)
    return x if (x / "json").exists() or not (unitaire(raw, cle) / "json").exists() else unitaire(raw, cle)


def lire_manifeste(raw: Path) -> dict:
    p = raw / MANIFESTE
    return json.loads(p.read_text()) if p.exists() else {}


BLOC = 1 << 18  # 256 Kio : au-delà, le serveur de l'AN coupe presque chaque requête par plage


def _etat(cible: Path) -> tuple[Path, Path]:
    """Fichier partiel et son état (`Last-Modified`, taille), qui permettent de reprendre d'un lancement à l'autre."""
    return cible.with_name(cible.name + ".part"), cible.with_name(cible.name + ".part.json")


def telecharger(client: httpx.Client, url: str, cible: Path, patience: int = 3600,
                connu: dict | None = None) -> str | None:
    """Télécharge `url` dans `cible` et renvoie son `Last-Modified`.

    Le serveur de l'AN (derrière un CDN) coupe souvent la connexion au milieu des gros dumps
    (amendements, ~350 Mo). Une requête par plage peut ensuite renvoyer `206` sans aucun octet, ou
    s'interrompre en cours de route, plusieurs heures durant. On télécharge donc d'abord d'un seul
    flux, puis, en cas de coupure, par plages de 256 Kio redemandées jusqu'à ce que le serveur les
    serve. Chaque octet reçu est gardé, même si la plage s'interrompt. Le fichier partiel
    (`<cible>.part`) survit à l'arrêt du processus : un nouveau lancement reprend là où le
    précédent s'est arrêté, si le fichier distant n'a pas changé (même `Last-Modified`, même
    taille). On abandonne après `patience` secondes sans aucun octet reçu. `If-Range` garantit que
    le fichier n'a pas changé entre-temps.
    """
    part, etat = _etat(cible)
    h = client.head(url)
    h.raise_for_status()
    modifie = h.headers.get("last-modified")
    taille = int(h.headers["content-length"]) if "content-length" in h.headers else None
    attendu = {"url": url, "last_modified": modifie, "taille": taille}
    # Archive déjà là et inchangée (même date, même taille que dans le manifeste) : rien à faire.
    if (connu and modifie and cible.exists() and connu.get("last_modified") == modifie
            and cible.stat().st_size == taille == connu.get("taille")):
        print("  inchangé depuis le dernier téléchargement", file=sys.stderr)
        return modifie
    if part.exists() and etat.exists() and json.loads(etat.read_text()) == attendu and modifie and taille:
        recu = part.stat().st_size
        print(f"  reprise à {recu:,} / {taille:,} o", file=sys.stderr)
    else:
        part.unlink(missing_ok=True)
        etat.write_text(json.dumps(attendu))
        recu = 0
        try:
            with client.stream("GET", url) as r, part.open("wb") as f:
                r.raise_for_status()
                for morceau in r.iter_bytes():  # sans tampon : une coupure ne perd rien
                    f.write(morceau)
        except httpx.TransportError as e:
            if taille is None or modifie is None:
                raise
            print(f"  coupure à {part.stat().st_size:,} o ({type(e).__name__}) : suite par plages", file=sys.stderr)
        recu = part.stat().st_size
    progres, attente, palier = time.monotonic(), 5, recu
    with part.open("ab") as f:
        while taille is not None and recu < taille:
            fin = min(recu + BLOC, taille) - 1
            try:
                with client.stream("GET", url, headers={"Range": f"bytes={recu}-{fin}", "If-Range": modifie}) as r:
                    if r.status_code == 200:
                        raise SystemExit(f"{url} a changé pendant le téléchargement : relancer")
                    r.raise_for_status()
                    if not r.headers.get("content-range", "").startswith(f"bytes {recu}-"):
                        raise httpx.RemoteProtocolError(f"plage inattendue : {r.headers.get('content-range')}")
                    for morceau in r.iter_bytes():
                        f.write(morceau)
                        f.flush()
                        recu += len(morceau)
                        progres, attente = time.monotonic(), 5
            except (httpx.TransportError, httpx.HTTPStatusError):
                pass
            if recu - palier >= 20 * BLOC or recu == taille:
                print(f"  {recu:,} / {taille:,} o", file=sys.stderr)
                palier = recu
            if recu >= taille:
                break
            if time.monotonic() - progres > patience:
                raise Injoignable(f"{url} : aucun octet reçu depuis {patience} s, arrêt à {recu:,} / {taille:,} o")
            if time.monotonic() - progres > 1:
                time.sleep(attente)
                attente = min(2 * attente, 120)
    if taille is not None and part.stat().st_size != taille:
        raise SystemExit(f"{url} : taille {part.stat().st_size:,} o, attendu {taille:,} o")
    part.replace(cible)
    etat.unlink(missing_ok=True)
    return modifie


def download(raw: Path, cles: list[str] | None = None, secours_max: int | None = None) -> None:
    """Télécharge chaque source, l'extrait et met à jour le manifeste. `secours_max` : durée maximale
    du plan B, en secondes (ce qui est récupéré reste acquis pour le lancement suivant)."""
    raw.mkdir(parents=True, exist_ok=True)
    with (raw / ".download.lock").open("w") as verrou:
        try:  # deux processus écriraient dans le même fichier partiel
            fcntl.flock(verrou, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit(f"un autre `lvnd download` tourne déjà sur {raw}") from None
        _download(raw, cles, secours_max)


def _download(raw: Path, cles: list[str] | None, secours_max: int | None) -> None:
    manifeste = lire_manifeste(raw)
    # délai de lecture court : le serveur de l'AN laisse parfois une connexion pendante sans la fermer
    with httpx.Client(timeout=httpx.Timeout(60, connect=30), follow_redirects=True) as client:
        for cle in cles or list(SOURCES):
            src = SOURCES[cle]
            dossier = raw / cle
            dossier.mkdir(parents=True, exist_ok=True)
            cible = dossier / src["url"].rsplit("/", 1)[1]
            print(f"{cle} : téléchargement de {src['url']}", file=sys.stderr)
            avant = manifeste.get(cle)
            try:
                modifie = telecharger(client, src["url"], cible, connu=avant,
                                      patience=PATIENCE_AVANT_SECOURS if "secours" in src else 3600)
            except (Injoignable, httpx.HTTPError) as e:
                # Une archive plus ancienne reste une source complète : on n'y substitue pas un plan B partiel.
                if "secours" not in src or cible.exists():
                    raise
                print(f"{cle} : dump injoignable ({e}), plan B amendement par amendement", file=sys.stderr)
                from . import secours
                bilan = secours.recuperer(client, raw, cle, **src["secours"], duree_max=secours_max)
                manifeste[cle] = {"url": secours.URL, "mode": "secours", **bilan,
                                  "telecharge_le": datetime.now(timezone.utc).isoformat(timespec="seconds")}
                (raw / MANIFESTE).write_text(json.dumps(manifeste, indent=2, ensure_ascii=False) + "\n")
                continue
            shutil.rmtree(unitaire(raw, cle), ignore_errors=True)  # le dump remplace le plan B
            inchange = bool(avant) and avant.get("last_modified") == modifie and avant.get("taille") == cible.stat().st_size
            if src.get("zip", True) and not (inchange and extraits(raw, cle).exists()):
                x = extraits(raw, cle)
                if x.exists():
                    shutil.rmtree(x)
                with zipfile.ZipFile(cible) as z:
                    z.extractall(x)
            if inchange:
                continue
            manifeste[cle] = {
                "url": src["url"],
                "last_modified": modifie,
                "taille": cible.stat().st_size,
                "sha256": sha256_fichier(cible),
                "telecharge_le": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            }
            print(f"{cle} : {cible} ({manifeste[cle]['taille']:,} o, {modifie})", file=sys.stderr)
            (raw / MANIFESTE).write_text(json.dumps(manifeste, indent=2, ensure_ascii=False) + "\n")

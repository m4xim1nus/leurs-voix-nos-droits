"""Sources open data et téléchargement (docs/SOURCES.md).

Repris de quifaitlaloi. Les dumps AN sont régénérés chaque nuit : on ne les
épingle pas par sha256. `download` les récupère, les extrait dans
`<raw>/<cle>/x/` et note dans `<raw>/manifeste.json` l'URL, le
`Last-Modified`, la taille et le sha256 de chaque archive. Ce manifeste est
recopié dans l'export : il date l'instantané versionné.
"""

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
    "an_amendements_17": {"url": f"{AN}/17/loi/amendements_div_legis/Amendements.json.zip"},
    "an_scrutins_16": {"url": f"{AN}/16/loi/scrutins/Scrutins.json.zip"},
    "an_dossiers_16": {"url": f"{AN}/16/loi/dossiers_legislatifs/Dossiers_Legislatifs.json.zip"},
    "an_amendements_16": {"url": f"{AN}/16/loi/amendements_div_legis/Amendements.json.zip"},
    "an_amo": {"url": f"{AN}/17/amo/tous_acteurs_mandats_organes_xi_legislature/"
                      "AMO30_tous_acteurs_tous_mandats_tous_organes_historique.json.zip"},
}

MANIFESTE = "manifeste.json"


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


def lire_manifeste(raw: Path) -> dict:
    p = raw / MANIFESTE
    return json.loads(p.read_text()) if p.exists() else {}


def telecharger(client: httpx.Client, url: str, cible: Path, essais: int = 10) -> str | None:
    """Télécharge `url` dans `cible` et renvoie son `Last-Modified`. Le serveur de l'AN coupe
    parfois la connexion au milieu des gros dumps (amendements, ~350 Mo) : on reprend là où le
    transfert s'est arrêté (en-tête `Range`), en vérifiant que le fichier n'a pas changé entre-temps."""
    cible.unlink(missing_ok=True)
    modifie = None
    for essai in range(1, essais + 1):
        recu = cible.stat().st_size if cible.exists() else 0
        entetes = {"Range": f"bytes={recu}-", "If-Range": modifie} if recu and modifie else {}
        try:
            with client.stream("GET", url, headers=entetes) as r:
                r.raise_for_status()
                if recu and r.status_code != 206:  # fichier modifié ou reprise refusée : on repart de zéro
                    recu = 0
                modifie = r.headers.get("last-modified")
                with cible.open("ab" if recu else "wb") as f:
                    for bloc in r.iter_bytes(1 << 20):
                        f.write(bloc)
            return modifie
        except (httpx.RemoteProtocolError, httpx.ReadError, httpx.ReadTimeout) as e:
            if essai == essais:
                raise
            attente = 30 * essai
            print(f"  coupure à {cible.stat().st_size:,} o ({type(e).__name__}), reprise dans {attente} s "
                  f"({essai}/{essais})", file=sys.stderr)
            time.sleep(attente)


def download(raw: Path, cles: list[str] | None = None) -> None:
    """Télécharge chaque source, l'extrait et met à jour le manifeste."""
    manifeste = lire_manifeste(raw)
    # délai de lecture court : le serveur de l'AN laisse parfois une connexion pendante sans la fermer
    with httpx.Client(timeout=httpx.Timeout(60, connect=30), follow_redirects=True) as client:
        for cle in cles or list(SOURCES):
            src = SOURCES[cle]
            dossier = raw / cle
            dossier.mkdir(parents=True, exist_ok=True)
            cible = dossier / src["url"].rsplit("/", 1)[1]
            print(f"{cle} : téléchargement de {src['url']}", file=sys.stderr)
            modifie = telecharger(client, src["url"], cible)
            if src.get("zip", True):
                x = extraits(raw, cle)
                if x.exists():
                    shutil.rmtree(x)
                with zipfile.ZipFile(cible) as z:
                    z.extractall(x)
            manifeste[cle] = {
                "url": src["url"],
                "last_modified": modifie,
                "taille": cible.stat().st_size,
                "sha256": sha256_fichier(cible),
                "telecharge_le": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            }
            print(f"{cle} : {cible} ({manifeste[cle]['taille']:,} o, {modifie})", file=sys.stderr)
            (raw / MANIFESTE).write_text(json.dumps(manifeste, indent=2, ensure_ascii=False) + "\n")

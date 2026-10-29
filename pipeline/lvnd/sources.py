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


BLOC = 1 << 20


def telecharger(client: httpx.Client, url: str, cible: Path, patience: int = 3600) -> str | None:
    """Télécharge `url` dans `cible` et renvoie son `Last-Modified`.

    Le serveur de l'AN (derrière un CDN) coupe souvent la connexion au milieu des gros dumps
    (amendements, ~350 Mo), et une reprise d'un seul tenant (`Range: bytes=N-`) peut ensuite
    renvoyer `206` sans aucun octet, plusieurs fois de suite. On télécharge donc d'abord d'un seul
    flux, puis, en cas de coupure, par blocs de 1 Mio redemandés jusqu'à ce que le serveur les
    serve. On abandonne après `patience` secondes sans progrès. `If-Range` garantit que le fichier
    n'a pas changé entre-temps.
    """
    cible.unlink(missing_ok=True)
    modifie, taille = None, None
    try:
        with client.stream("GET", url) as r:
            r.raise_for_status()
            modifie = r.headers.get("last-modified")
            taille = int(r.headers["content-length"]) if "content-length" in r.headers else None
            with cible.open("wb") as f:
                for bloc in r.iter_bytes(BLOC):
                    f.write(bloc)
    except httpx.TransportError as e:
        if taille is None or modifie is None:
            raise
        print(f"  coupure à {cible.stat().st_size:,} o ({type(e).__name__}) : suite par blocs", file=sys.stderr)
    recu = cible.stat().st_size
    if taille is None or recu == taille:
        return modifie
    progres, attente, palier = time.monotonic(), 5, recu
    with cible.open("ab") as f:
        while recu < taille:
            try:
                r = client.get(url, headers={"Range": f"bytes={recu}-{min(recu + BLOC, taille) - 1}",
                                             "If-Range": modifie})
                if r.status_code == 200:
                    raise SystemExit(f"{url} a changé pendant le téléchargement : relancer")
                r.raise_for_status()
                if r.content:
                    f.write(r.content)
                    recu += len(r.content)
                    progres, attente = time.monotonic(), 5
                    if recu - palier >= 20 * BLOC or recu == taille:
                        print(f"  {recu:,} / {taille:,} o", file=sys.stderr)
                        palier = recu
                    continue
            except httpx.TransportError:
                pass
            if time.monotonic() - progres > patience:
                raise SystemExit(f"{url} : aucun octet reçu depuis {patience} s, arrêt à {recu:,} / {taille:,} o")
            time.sleep(attente)
            attente = min(2 * attente, 120)
    return modifie


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

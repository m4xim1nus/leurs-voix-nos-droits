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
                raise SystemExit(f"{url} : aucun octet reçu depuis {patience} s, arrêt à {recu:,} / {taille:,} o")
            if time.monotonic() - progres > 1:
                time.sleep(attente)
                attente = min(2 * attente, 120)
    if taille is not None and part.stat().st_size != taille:
        raise SystemExit(f"{url} : taille {part.stat().st_size:,} o, attendu {taille:,} o")
    part.replace(cible)
    etat.unlink(missing_ok=True)
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
            avant = manifeste.get(cle)
            modifie = telecharger(client, src["url"], cible, connu=avant)
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

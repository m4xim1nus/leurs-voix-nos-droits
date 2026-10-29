"""Téléchargement robuste aux coupures du serveur de l'AN (sources.telecharger)."""

import json

import httpx
import pytest

from lvnd import sources

DONNEES = bytes(range(256)) * 4096  # 1 Mio
LM = "Fri, 28 Jun 2024 08:25:47 GMT"


class Coupe(httpx.SyncByteStream):
    """Flux qui livre `n` octets puis coupe la connexion."""

    def __init__(self, data: bytes, n: int):
        self.data, self.n = data, n

    def __iter__(self):
        if self.n:
            yield self.data[:self.n]
        if self.n < len(self.data):
            raise httpx.RemoteProtocolError("coupure")


def serveur(coupure_flux: int, plages: list[int]):
    """Flux complet coupé à `coupure_flux` ; chaque requête par plage livre `plages[i]` octets (0 : rien)."""
    appels = {"plages": 0}

    def gerer(req: httpx.Request) -> httpx.Response:
        h = {"last-modified": LM, "content-length": str(len(DONNEES))}
        if req.method == "HEAD":
            return httpx.Response(200, headers=h)
        if "range" not in req.headers:
            return httpx.Response(200, headers=h, stream=Coupe(DONNEES, coupure_flux))
        assert req.headers["if-range"] == LM
        debut, fin = map(int, req.headers["range"].removeprefix("bytes=").split("-"))
        morceau = DONNEES[debut:fin + 1]
        i = appels["plages"]
        appels["plages"] += 1
        n = plages[i] if i < len(plages) else len(morceau)
        return httpx.Response(206, headers={"content-range": f"bytes {debut}-{fin}/{len(DONNEES)}",
                                            "last-modified": LM},
                              stream=Coupe(morceau, min(n, len(morceau))))

    return httpx.MockTransport(gerer), appels


@pytest.fixture(autouse=True)
def sans_attente(monkeypatch):
    monkeypatch.setattr(sources.time, "sleep", lambda s: None)


def test_coupures_et_plages_partielles(tmp_path):
    transport, appels = serveur(300_000, [0, 1000, 0, 50_000])
    cible = tmp_path / "a.zip"
    with httpx.Client(transport=transport) as c:
        assert sources.telecharger(c, "https://an/a.zip", cible) == LM
    assert cible.read_bytes() == DONNEES
    assert not sources._etat(cible)[0].exists() and not sources._etat(cible)[1].exists()
    assert appels["plages"] > 4


def test_reprise_d_un_lancement_a_l_autre(tmp_path):
    cible = tmp_path / "a.zip"
    part, etat = sources._etat(cible)
    part.write_bytes(DONNEES[:400_000])
    etat.write_text(json.dumps({"url": "https://an/a.zip", "last_modified": LM, "taille": len(DONNEES)}))
    transport, appels = serveur(0, [])
    with httpx.Client(transport=transport) as c:
        sources.telecharger(c, "https://an/a.zip", cible)
    assert cible.read_bytes() == DONNEES
    assert appels["plages"] == -(-(len(DONNEES) - 400_000) // sources.BLOC)  # rien de redemandé avant 400 000


def test_fichier_distant_change_on_repart_de_zero(tmp_path):
    cible = tmp_path / "a.zip"
    part, etat = sources._etat(cible)
    part.write_bytes(b"x" * 400_000)
    etat.write_text(json.dumps({"url": "https://an/a.zip", "last_modified": "autre", "taille": len(DONNEES)}))
    transport, _ = serveur(len(DONNEES), [])
    with httpx.Client(transport=transport) as c:
        sources.telecharger(c, "https://an/a.zip", cible)
    assert cible.read_bytes() == DONNEES


def test_abandon_sans_progres(tmp_path, monkeypatch):
    transport, _ = serveur(100, [0] * 10_000)
    t = iter(range(0, 10**9, 1000))
    monkeypatch.setattr(sources.time, "monotonic", lambda: next(t))
    with httpx.Client(transport=transport) as c, pytest.raises(SystemExit, match="aucun octet"):
        sources.telecharger(c, "https://an/a.zip", tmp_path / "a.zip", patience=3600)
    assert sources._etat(tmp_path / "a.zip")[0].stat().st_size == 100  # gardé pour la reprise

"""Téléchargement robuste aux coupures du serveur de l'AN (sources.telecharger)."""

import json
import shutil
import zipfile

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


def test_partiel_trop_long_repart_de_zero(tmp_path):
    """Même date, même taille annoncée, mais un partiel plus long : il ne peut venir que d'une autre version."""
    cible = tmp_path / "a.zip"
    part, etat = sources._etat(cible)
    part.write_bytes(b"x" * (len(DONNEES) + 10))
    etat.write_text(json.dumps({"url": "https://an/a.zip", "last_modified": LM, "taille": len(DONNEES)}))
    transport, _ = serveur(len(DONNEES), [])
    with httpx.Client(transport=transport) as c:
        sources.telecharger(c, "https://an/a.zip", cible)
    assert cible.read_bytes() == DONNEES


def test_taille_inattendue_purge_le_partiel(tmp_path):
    """Le GET livre une autre version que celle annoncée par le HEAD : erreur, et rien à supprimer à la main."""
    def gerer(req):
        h = {"last-modified": LM, "content-length": "10"}
        return httpx.Response(200, headers=h, content=b"" if req.method == "HEAD" else b"y" * 25)

    cible = tmp_path / "a.zip"
    with httpx.Client(transport=httpx.MockTransport(gerer)) as c, pytest.raises(SystemExit, match="attendu 10"):
        sources.telecharger(c, "https://an/a.zip", cible)
    part, etat = sources._etat(cible)
    assert not part.exists() and not etat.exists() and not cible.exists()


def test_abandon_sans_progres(tmp_path, monkeypatch):
    transport, _ = serveur(100, [0] * 10_000)
    t = iter(range(0, 10**9, 1000))
    monkeypatch.setattr(sources.time, "monotonic", lambda: next(t))
    with httpx.Client(transport=transport) as c, pytest.raises(SystemExit, match="aucun octet"):
        sources.telecharger(c, "https://an/a.zip", tmp_path / "a.zip", patience=3600)
    assert sources._etat(tmp_path / "a.zip")[0].stat().st_size == 100  # gardé pour la reprise


class Goutte(httpx.SyncByteStream):
    """Flux qui livre un octet à la fois, sans jamais couper : le délai de lecture du client ne se déclenche pas."""

    def __iter__(self):
        while True:
            yield b"x"


def _goutte(req: httpx.Request) -> httpx.Response:
    h = {"last-modified": LM, "content-length": str(len(DONNEES))}
    return httpx.Response(200, headers=h) if req.method == "HEAD" else httpx.Response(200, headers=h, stream=Goutte())


def test_debit_minimal_arrete_un_flux_au_goutte_a_goutte(tmp_path, monkeypatch):
    t = iter(range(0, 10**9, 10))  # 10 s entre deux octets
    monkeypatch.setattr(sources.time, "monotonic", lambda: next(t))
    with httpx.Client(transport=httpx.MockTransport(_goutte)) as c, pytest.raises(sources.Injoignable, match="débit minimal"):
        sources.telecharger(c, "https://an/a.zip", tmp_path / "a.zip", patience=1200, debit_minimal=20_000)
    assert sources._etat(tmp_path / "a.zip")[0].stat().st_size > 0  # gardé pour la reprise


def test_debit_minimal_arrete_des_plages_au_goutte_a_goutte(tmp_path, monkeypatch):
    transport, _ = serveur(100, [1] * 10_000)
    t = iter(range(0, 10**9, 100))
    monkeypatch.setattr(sources.time, "monotonic", lambda: next(t))
    with httpx.Client(transport=transport) as c, pytest.raises(sources.Injoignable, match="débit minimal"):
        sources.telecharger(c, "https://an/a.zip", tmp_path / "a.zip", patience=3600, debit_minimal=20_000)


def test_sans_debit_minimal_un_flux_lent_continue(tmp_path, monkeypatch):
    """Une source sans plan B n'a rien de mieux à faire que d'attendre."""
    transport, _ = serveur(len(DONNEES), [])
    t = iter(range(0, 10**12, 10**6))  # le téléchargement paraît très lent
    monkeypatch.setattr(sources.time, "monotonic", lambda: next(t))
    with httpx.Client(transport=transport) as c:
        sources.telecharger(c, "https://an/a.zip", tmp_path / "a.zip", patience=3600)
    assert (tmp_path / "a.zip").read_bytes() == DONNEES


def test_debit_suffisant_ne_declenche_rien(tmp_path, monkeypatch):
    transport, _ = serveur(len(DONNEES), [])
    t = iter(range(0, 10**6))  # 1 Mio en quelques secondes factices
    monkeypatch.setattr(sources.time, "monotonic", lambda: next(t))
    with httpx.Client(transport=transport) as c:
        sources.telecharger(c, "https://an/a.zip", tmp_path / "a.zip", patience=1, debit_minimal=20_000)
    assert (tmp_path / "a.zip").read_bytes() == DONNEES


def test_goutte_a_goutte_bascule_sur_le_plan_b(tmp_path, monkeypatch):
    from lvnd import secours
    monkeypatch.setattr(sources, "SOURCES", {"am": {"url": "https://an/am.zip", "secours": {"legislature": 15, "organe": "1"}}})
    monkeypatch.setattr(sources, "PATIENCE_AVANT_SECOURS", 1200)
    t = iter(range(0, 10**9, 10))
    monkeypatch.setattr(sources.time, "monotonic", lambda: next(t))
    monkeypatch.setattr(secours, "recuperer", lambda *a, **k: {"amendements_trouves": 1})
    _client_factice(monkeypatch, _goutte)
    sources.download(tmp_path, ["am"])
    assert json.loads((tmp_path / "manifeste.json").read_text())["am"]["mode"] == "secours"


def _zip(chemin, nom="json/a/b/c.json", contenu=b"{}"):
    chemin.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(chemin, "w") as z:
        z.writestr(nom, contenu)


def _sources(monkeypatch):
    """Deux sources, l'une rafraîchie par la passe légère, l'autre non (avec plan B)."""
    monkeypatch.setattr(sources, "SOURCES", {
        "legere": {"url": "https://an/legere.zip"},
        "lourde": {"url": "https://an/lourde.zip", "secours": {"legislature": 16, "organe": "1"}}})
    monkeypatch.setattr(sources, "LEGERES", ("legere",))


def _client_factice(monkeypatch, gerer):
    vrai = httpx.Client
    monkeypatch.setattr(sources.httpx, "Client", lambda **kw: vrai(transport=httpx.MockTransport(gerer)))


def test_leger_ne_touche_pas_aux_archives_lourdes(tmp_path, monkeypatch):
    _sources(monkeypatch)
    _zip(tmp_path / "lourde/lourde.zip")
    corps = tmp_path / "legere.zip"
    _zip(corps)
    appels = []

    def gerer(req):
        appels.append(str(req.url))
        return httpx.Response(200, headers={"last-modified": LM, "content-length": str(corps.stat().st_size)},
                              content=b"" if req.method == "HEAD" else corps.read_bytes())

    _client_factice(monkeypatch, gerer)
    sources.download(tmp_path, leger=True)
    assert set(appels) == {"https://an/legere.zip"}  # rien vers l'archive lourde
    assert (tmp_path / "lourde/x/json/a/b/c.json").exists()  # mais elle est extraite
    assert "lourde" not in json.loads((tmp_path / "manifeste.json").read_text())


def test_leger_sans_archive_ne_lance_pas_le_plan_b(tmp_path, monkeypatch):
    _sources(monkeypatch)
    monkeypatch.setattr(sources, "LEGERES", ())
    _client_factice(monkeypatch, lambda req: httpx.Response(404))
    with pytest.raises(httpx.HTTPStatusError):
        sources.download(tmp_path, leger=True)
    assert not (tmp_path / "legere/x").exists()


def test_dump_injoignable_garde_l_archive_precedente(tmp_path, monkeypatch):
    _sources(monkeypatch)
    monkeypatch.setitem(sources.SOURCES, "legere", {"url": "https://an/lourde2.zip", "secours": {"legislature": 16, "organe": "1"}})
    _zip(tmp_path / "legere/lourde2.zip")
    _zip(tmp_path / "lourde/lourde.zip")
    _client_factice(monkeypatch, lambda req: httpx.Response(503))
    sources.download(tmp_path)  # aucun plan B, aucun échec
    assert (tmp_path / "legere/x/json/a/b/c.json").exists() and (tmp_path / "lourde/x/json/a/b/c.json").exists()
    assert not (tmp_path / "lourde/unitaire").exists()


def test_archiver_refuse_un_plan_b_inacheve_puis_ecrit_les_memes_octets(tmp_path, monkeypatch):
    _sources(monkeypatch)
    f = tmp_path / "lourde/unitaire/json/d/t/a.json"
    f.parent.mkdir(parents=True)
    f.write_text('{"amendement": {}}')
    (tmp_path / "lourde/unitaire/etat.json").write_text("{}")
    with pytest.raises(SystemExit, match="pas terminé"):
        sources.archiver(tmp_path, "lourde", tmp_path / "s.zip")
    (tmp_path / "manifeste.json").write_text(json.dumps({"lourde": {"mode": "secours"}}))
    n, sha = sources.archiver(tmp_path, "lourde", tmp_path / "s.zip")
    assert n == 1
    assert sources.archiver(tmp_path, "lourde", tmp_path / "s2.zip")[1] == sha
    # Même arborescence que le dump : extraite, elle se lit comme lui, sans l'état du plan B.
    assert zipfile.ZipFile(tmp_path / "s.zip").namelist() == ["json/d/t/a.json"]


def test_archive_inchangee_non_retelechargee(tmp_path):
    cible = tmp_path / "a.zip"
    cible.write_bytes(b"x" * 10)
    appels = []

    def serveur(req):
        appels.append(req.method)
        return httpx.Response(200, headers={"last-modified": "Fri, 28 Jun 2024", "content-length": "10"})

    with httpx.Client(transport=httpx.MockTransport(serveur)) as client:
        connu = {"last_modified": "Fri, 28 Jun 2024", "taille": 10}
        assert sources.telecharger(client, "https://an/a.zip", cible, connu=connu) == "Fri, 28 Jun 2024"
    assert appels == ["HEAD"]


def _chaine(tmp_path, monkeypatch, an=503, release=None):
    """Une source avec dump (`an`), copie dans la release (`release`, chemin d'un zip ou None) et plan B."""
    monkeypatch.setattr(sources, "SOURCES", {"am": {"url": "https://an/a.zip", "figee": "https://gh/am.zip",
                                                     "secours": {"legislature": 16, "organe": "1"}}})
    appels = []

    def gerer(req):
        appels.append(str(req.url))
        if "gh" in str(req.url):
            if release is None:
                return httpx.Response(404)
            return httpx.Response(200, headers={"last-modified": LM, "content-length": str(release.stat().st_size)},
                                  content=b"" if req.method == "HEAD" else release.read_bytes())
        r = an["reponse"] if isinstance(an, dict) else an
        if isinstance(r, int):
            return httpx.Response(r)
        return httpx.Response(200, headers={"last-modified": "dump", "content-length": str(r.stat().st_size)},
                              content=b"" if req.method == "HEAD" else r.read_bytes())

    _client_factice(monkeypatch, gerer)
    return appels


def test_chaine_dump_injoignable_prend_la_copie_sans_plan_b(tmp_path, monkeypatch):
    from lvnd import secours
    copie = tmp_path / "copie.zip"
    _zip(copie)
    raw = tmp_path / "raw"
    appels = _chaine(tmp_path, monkeypatch, release=copie)
    monkeypatch.setattr(secours, "recuperer", lambda *a, **k: pytest.fail("plan B inutile"))
    sources.download(raw)
    m = json.loads((raw / "manifeste.json").read_text())["am"]
    assert appels[0] == "https://an/a.zip"  # le dump d'abord
    assert m["mode"] == "figee" and m["url"] == "https://gh/am.zip"
    assert (raw / "am/x/json/a/b/c.json").exists() and not (raw / "am/a.zip").exists()


def test_chaine_le_dump_revenu_remplace_la_copie(tmp_path, monkeypatch):
    copie, dump = tmp_path / "copie.zip", tmp_path / "dump.zip"
    _zip(copie)
    _zip(dump, "json/d/t/complet.json")
    raw = tmp_path / "raw"
    serveur_an = {"reponse": 503}
    _chaine(tmp_path, monkeypatch, an=serveur_an, release=copie)
    sources.download(raw)
    serveur_an["reponse"] = dump
    sources.download(raw)
    m = json.loads((raw / "manifeste.json").read_text())["am"]
    assert "mode" not in m and m["last_modified"] == "dump"
    assert (raw / "am/x/json/d/t/complet.json").exists() and not (raw / "am/x/json/a/b/c.json").exists()
    assert not (raw / "am" / sources.COPIE_FIGEE).exists()


def test_chaine_sans_release_lance_le_plan_b(tmp_path, monkeypatch):
    from lvnd import secours
    raw = tmp_path / "raw"
    _chaine(tmp_path, monkeypatch)
    monkeypatch.setattr(secours, "recuperer", lambda *a, **k: {"amendements_trouves": 1})
    sources.download(raw)
    assert json.loads((raw / "manifeste.json").read_text())["am"]["mode"] == "secours"


def test_chaine_leger_reutilise_la_copie_sans_tenter_le_dump(tmp_path, monkeypatch):
    copie = tmp_path / "copie.zip"
    _zip(copie)
    raw = tmp_path / "raw"
    appels = _chaine(tmp_path, monkeypatch, release=copie)
    monkeypatch.setattr(sources, "LEGERES", ())
    sources.download(raw)
    appels.clear()
    shutil.rmtree(raw / "am/x")
    sources.download(raw, leger=True)
    assert appels == [] and (raw / "am/x/json/a/b/c.json").exists()


def test_chaine_leger_sans_archive_prend_la_copie(tmp_path, monkeypatch):
    copie = tmp_path / "copie.zip"
    _zip(copie)
    raw = tmp_path / "raw"
    appels = _chaine(tmp_path, monkeypatch, release=copie)
    monkeypatch.setattr(sources, "LEGERES", ())
    sources.download(raw, leger=True)
    assert (raw / "am/x/json/a/b/c.json").exists()
    assert not any("an/" in a for a in appels)  # sans attendre le dump de l'AN


def test_chaine_leger_sans_copie_retente_le_dump(tmp_path, monkeypatch):
    dump = tmp_path / "dump.zip"
    _zip(dump)
    raw = tmp_path / "raw"
    _chaine(tmp_path, monkeypatch, an=dump)
    monkeypatch.setattr(sources, "LEGERES", ())
    sources.download(raw, leger=True)
    assert (raw / "am/x/json/a/b/c.json").exists()


def test_chaine_leger_reutilise_un_plan_b_acheve(tmp_path, monkeypatch):
    raw = tmp_path / "raw"
    fichier = raw / "am/unitaire/json/d/t/a.json"
    fichier.parent.mkdir(parents=True)
    fichier.write_text("{}")
    appels = _chaine(tmp_path, monkeypatch)
    monkeypatch.setattr(sources, "LEGERES", ())
    (raw / "manifeste.json").write_text(json.dumps({"am": {"mode": "secours"}}))
    sources.download(raw, leger=True)
    assert appels == [] and fichier.exists()


def test_chaine_leger_ne_prend_pas_un_plan_b_inacheve(tmp_path, monkeypatch):
    """Sans ligne au manifeste, le plan B est inachevé : la copie de la release le remplace."""
    copie = tmp_path / "copie.zip"
    _zip(copie)
    raw = tmp_path / "raw"
    (raw / "am/unitaire/json/d").mkdir(parents=True)
    appels = _chaine(tmp_path, monkeypatch, release=copie)
    monkeypatch.setattr(sources, "LEGERES", ())
    sources.download(raw, leger=True)
    assert any("gh" in a for a in appels) and (raw / "am/x/json/a/b/c.json").exists()


def test_url_decision_sans_prefixe_repete():
    from lvnd.textes import _url_decision
    base = "https://www.conseil-constitutionnel.fr/decision/"
    assert _url_decision({"urlConclusion": f"{base}{base}2019/2019790DC.htm", "dateActe": "2019-08-01"}) == f"{base}2019/2019790DC.htm"
    assert _url_decision({"urlConclusion": f"{base}2022/2022846DC.htm", "dateActe": "2023-01-19"}) == f"{base}2023/2022846DC.htm"

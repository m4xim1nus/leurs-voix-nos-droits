"""Plan B des amendements (secours.py) et bascule automatique depuis `download`."""

import json

import httpx
import pytest

from lvnd import secours, sources

ORGANE = "791932"


def uid(texte: str, n: int, partie: int = 0, division: int = 1) -> str:
    return f"AMANR5L16PO{ORGANE}{texte}P{partie}D{division}N{n:06d}"


def amendement(identifiant: str, seance=None, auteur="M. Dupont", depot="2023-01-10") -> dict:
    return {"uid": identifiant, "identification": {"numeroLong": str(int(identifiant[-6:]))},
            "texteLegislatifRef": "PRJLANR5L16BTC1010", "seanceDiscussionRef": seance or {},
            "signataires": {"libelle": f" {auteur}", "auteur": {"gouvernementRef": {}}},
            "cycleDeVie": {"dateDepot": depot}}


def scrutin(i: str = "V1", titre="l'amendement n° 7 de M. Dupont à l'article 2", seance="S1", d="2023-02-01") -> dict:
    return {"id": i, "titre": titre, "seance": seance, "date": d, "objet": "amendement"}


@pytest.fixture(autouse=True)
def sans_attente(monkeypatch):
    monkeypatch.setattr(secours.time, "sleep", lambda s: None)
    monkeypatch.setattr(sources.time, "sleep", lambda s: None)


def site(reponses: dict):
    """Site de l'AN : `reponses[uid]` est un amendement, un code HTTP, ou une liste de ceux-ci, servis dans l'ordre."""
    demandes = []

    def gerer(req: httpx.Request) -> httpx.Response:
        u = req.url.path.rsplit("/", 1)[1].removesuffix(".json")
        demandes.append(u)
        r = reponses.get(u, 404)
        if isinstance(r, list):
            r = r.pop(0)
        return httpx.Response(r) if isinstance(r, int) else httpx.Response(200, json=r)

    return httpx.MockTransport(gerer), demandes


def parcourir(transport, dossier, vises, bases=None, **k):
    with httpx.Client(transport=transport) as c:
        return secours.parcourir(c, dossier, 16, ORGANE, vises, {s["id"]: {"dossier_id": "D"} for s in vises}, {},
                                 {"PRJLANR5L16BTC1010": "D"}, {"D": bases or ["BTC1010"]}, **k)


def test_normaliser_comme_le_dump():
    a = secours.normaliser(amendement(uid("BTC1010", 7)))
    assert a["seanceDiscussionRef"] is None
    assert a["signataires"] == {"libelle": "M. Dupont", "auteur": {"gouvernementRef": None}}


def test_textes_du_dossier_du_plus_recent_au_plus_ancien():
    docs = {"PRJLANR5L16B0491": "D", "PRJLANR5L16BTC1010": "D", "PIONANR5L17B0001": "D", "RAPPANR5L16B1010": "D"}
    assert secours.textes_par_dossier(docs, 16) == {"D": ["BTC1010", "B1010", "B0491"]}


def test_ordre_des_candidats():
    assert secours.candidats(16, ORGANE, "I-7", ["BTC1", "B1"]) == [
        uid("BTC1", 7), uid("BTC1", 7, 1), uid("B1", 7), uid("B1", 7, 1),
        uid("BTC1", 7, 0, 2), uid("BTC1", 7, 1, 2), uid("B1", 7, 0, 2), uid("B1", 7, 1, 2)]


def test_trouve_et_range_comme_le_dump(tmp_path):
    u = uid("BTC1010", 7)
    transport, _ = site({u: amendement(u, "S1")})
    bilan = parcourir(transport, tmp_path, [scrutin()])
    assert bilan["amendements_trouves"] == 1
    lu = json.loads((tmp_path / f"json/D/PRJLANR5L16BTC1010/{u}.json").read_text())
    assert lu["amendement"]["uid"] == u


def test_meme_numero_sur_un_autre_texte_ecarte(tmp_path):
    """Autre auteur, autre séance : on continue jusqu'au bon texte (cas réel du dossier XVIe)."""
    faux, bon = uid("BTC2000", 7), uid("BTC1010", 7)
    transport, _ = site({faux: amendement(faux, "S9", "Mme Martin"), bon: amendement(bon, "S1")})
    parcourir(transport, tmp_path, [scrutin()], bases=["BTC2000", "BTC1010"])
    assert json.loads((tmp_path / "etat.json").read_text())["scrutins"]["V1"] == bon
    assert not list(tmp_path.glob(f"json/*/*/{faux}.json"))


def test_la_seance_prime_sur_l_auteur_et_la_date(tmp_path):
    """Cas réel XVIIe : même numéro, division 1 plausible par l'auteur, division 2 de la bonne séance."""
    d1, d2 = uid("BTC1010", 7), uid("BTC1010", 7, 0, 2)
    transport, _ = site({d1: amendement(d1, "S9"), d2: amendement(d2, "S1")})
    parcourir(transport, tmp_path, [scrutin()])
    assert json.loads((tmp_path / "etat.json").read_text())["scrutins"]["V1"] == d2
    assert not list(tmp_path.glob(f"json/*/*/{d1}.json"))


def test_numero_complet_exige(tmp_path):
    """Cas réel XVIIe (V1191) : même séance, mêmes chiffres, mais un autre numéro complet."""
    faux, bon = uid("BTC1010", 7), uid("BTC1010", 7, 0, 2)
    autre = amendement(faux, "S1")
    autre["identification"]["numeroLong"] = "DN7"
    transport, _ = site({faux: autre, bon: amendement(bon)})
    parcourir(transport, tmp_path, [scrutin()])
    assert json.loads((tmp_path / "etat.json").read_text())["scrutins"]["V1"] == bon


def test_repli_sur_le_depot_le_plus_recent(tmp_path):
    """Cas réel XVIIe (V4694) : deux amendements plausibles hors séance, comme dans `rattacher`."""
    vieux, recent = uid("BTC1010", 7), uid("BTC1010", 7, 0, 2)
    transport, _ = site({vieux: amendement(vieux, depot="2023-01-10"), recent: amendement(recent, depot="2023-01-30")})
    parcourir(transport, tmp_path, [scrutin()])
    assert json.loads((tmp_path / "etat.json").read_text())["scrutins"]["V1"] == recent


def test_meme_seance_mais_autre_auteur_ecarte(tmp_path):
    """Cas réel XVIIe (V1191) : l'amendement de M. Molac, même séance, n'est pas celui du Gouvernement."""
    faux, bon = uid("BTC1010", 7), uid("BTC1010", 7, 0, 2)
    transport, _ = site({faux: amendement(faux, "S1", "Mme Martin"), bon: amendement(bon)})
    parcourir(transport, tmp_path, [scrutin()])
    assert json.loads((tmp_path / "etat.json").read_text())["scrutins"]["V1"] == bon


def test_meme_seance_seule_en_dernier_recours(tmp_path):
    u = uid("BTC1010", 7)
    transport, _ = site({u: amendement(u, "S1", "Mme Martin")})
    parcourir(transport, tmp_path, [scrutin()])
    assert json.loads((tmp_path / "etat.json").read_text())["scrutins"]["V1"] == u


def test_sans_seance_auteur_et_date_de_depot(tmp_path):
    u = uid("BTC1010", 7)
    transport, _ = site({u: amendement(u, None, "M. Dupont", "2022-01-01")})  # hors fenêtre
    assert parcourir(transport, tmp_path, [scrutin()])["amendements_trouves"] == 0
    tmp = tmp_path / "b"
    transport, _ = site({u: amendement(u, None, "M. Dupont", "2023-01-10")})
    assert parcourir(transport, tmp, [scrutin()])["amendements_trouves"] == 1


def test_reprise_sans_redemander(tmp_path):
    u = uid("BTC1010", 7)
    transport, demandes = site({u: amendement(u, "S1")})
    parcourir(transport, tmp_path, [scrutin()])
    n = len(demandes)
    parcourir(transport, tmp_path, [scrutin()])
    assert len(demandes) == n


def test_le_texte_trouve_passe_en_tete_pour_le_scrutin_suivant(tmp_path):
    a, b = uid("BTC1010", 7), uid("BTC1010", 8)
    transport, demandes = site({a: amendement(a, "S1"), b: amendement(b, "S1")})
    parcourir(transport, tmp_path, [scrutin(), scrutin("V2", "l'amendement n° 8 de M. Dupont")],
              bases=["BTC2000", "BTC1010"])
    assert demandes[-1] == b and uid("BTC2000", 8) not in demandes


def test_erreur_passagere_reessayee(tmp_path):
    u = uid("BTC1010", 7)
    transport, _ = site({u: [500, 503, amendement(u, "S1")]})
    assert parcourir(transport, tmp_path, [scrutin()])["amendements_trouves"] == 1


def test_refus_du_serveur_arrete_sans_insister(tmp_path):
    u = uid("BTC1010", 7)
    transport, demandes = site({u: 403})
    with pytest.raises(SystemExit, match="refusé"):
        parcourir(transport, tmp_path, [scrutin()])
    assert len(demandes) == 1


def test_duree_maximale_garde_l_acquis(tmp_path, monkeypatch):
    a = uid("BTC1010", 7)
    transport, _ = site({a: amendement(a, "S1")})
    t = iter(range(0, 10**6, 100))
    monkeypatch.setattr(secours.time, "monotonic", lambda: next(t))
    with pytest.raises(SystemExit, match="durée maximale"):
        parcourir(transport, tmp_path, [scrutin(), scrutin("V2", "l'amendement n° 8 de M. Dupont")], duree_max=150)
    assert json.loads((tmp_path / "etat.json").read_text())["scrutins"] == {"V1": a}


def _sources(monkeypatch):
    monkeypatch.setitem(sources.SOURCES, "am", {"url": "https://an/a.zip", "secours": {"legislature": 16, "organe": ORGANE}})
    monkeypatch.setitem(sources.SOURCES, "autre", {"url": "https://an/b.zip"})


def _dump_coupe(monkeypatch):
    def coupe(*a, **k):
        raise sources.Injoignable("aucun octet")
    monkeypatch.setattr(sources, "telecharger", coupe)


def test_dump_injoignable_bascule_seul_sur_le_plan_b(tmp_path, monkeypatch):
    _sources(monkeypatch)
    _dump_coupe(monkeypatch)
    monkeypatch.setattr(secours, "recuperer", lambda *a, **k: {"amendements_trouves": 3})
    sources.download(tmp_path, ["am"])
    m = json.loads((tmp_path / "manifeste.json").read_text())["am"]
    assert m["mode"] == "secours" and m["amendements_trouves"] == 3


def test_source_sans_plan_b_echoue_comme_avant(tmp_path, monkeypatch):
    _sources(monkeypatch)
    _dump_coupe(monkeypatch)
    with pytest.raises(sources.Injoignable):
        sources.download(tmp_path, ["autre"])


def test_archive_ancienne_preferee_au_plan_b(tmp_path, monkeypatch):
    _sources(monkeypatch)
    _dump_coupe(monkeypatch)
    (tmp_path / "am").mkdir()
    (tmp_path / "am/a.zip").write_bytes(b"ancienne")
    with pytest.raises(sources.Injoignable):
        sources.download(tmp_path, ["am"])


def test_le_dump_revenu_remplace_le_plan_b(tmp_path, monkeypatch):
    import zipfile
    _sources(monkeypatch)
    (tmp_path / "am/unitaire/json/D/T").mkdir(parents=True)
    (tmp_path / "am/unitaire/json/D/T/A.json").write_text("{}")
    (tmp_path / "manifeste.json").write_text(json.dumps({"am": {"mode": "secours", "url": secours.URL}}))

    def ok(client, url, cible, **k):
        with zipfile.ZipFile(cible, "w") as z:
            z.writestr("json/D/T/A.json", "{}")
        return "lundi"

    monkeypatch.setattr(sources, "telecharger", ok)
    sources.download(tmp_path, ["am"])
    assert not (tmp_path / "am/unitaire").exists()
    assert sources.racine(tmp_path, "am") == sources.extraits(tmp_path, "am")
    m = json.loads((tmp_path / "manifeste.json").read_text())["am"]
    assert "mode" not in m and m["last_modified"] == "lundi"


def test_deux_download_simultanes_refuses(tmp_path):
    import fcntl
    with (tmp_path / ".download.lock").open("w") as v:
        fcntl.flock(v, fcntl.LOCK_EX)
        with pytest.raises(SystemExit, match="tourne déjà"):
            sources.download(tmp_path, [])

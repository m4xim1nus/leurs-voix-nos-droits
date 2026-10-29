import pytest

from lvnd import scores

TEMOINS = {"textes": [
    {"id": "t", "droits": [{"code": "etrangers", "role": "principal", "sens": "restreint"},
                           {"code": "enfants", "role": "secondaire", "sens": "etend"}],
     "scrutins": [{"id": "D", "role": "decisif", "pour": "texte"},
                  {"id": "A1", "role": "amendement", "pour": "contre-texte"},
                  {"id": "A2", "role": "amendement", "pour": "contre-texte"},
                  {"id": "M", "role": "motion", "pour": "contre-texte"},
                  {"id": "X", "role": "amendement", "pour": "a-trancher"}]},
]}


def v(scrutin, acteur, position, groupe="G"):
    return {"scrutin_id": scrutin, "acteur_id": acteur, "groupe_id": groupe, "position": position}


def test_sens_favorable():
    assert scores._favorable("restreint", "texte") == "contre"
    assert scores._favorable("restreint", "contre-texte") == "pour"
    assert scores._favorable("etend", "texte") == "pour"
    assert scores._favorable("etend", "a-trancher") is None


def test_motions_et_sens_non_fixe_non_comptes():
    ids = {c["scrutin_id"] for c in scores.scrutins_comptes(TEMOINS, scores.REGLES)}
    assert ids == {"D", "A1", "A2"}


def test_ponderation_par_texte():
    c = {(x["scrutin_id"], x["droit"]): x["poids"] for x in scores.scrutins_comptes(TEMOINS, scores.REGLES)}
    assert c[("D", "global")] == 0.5 and c[("A1", "global")] == 0.25


def test_score_depute():
    # contre le texte (favorable), pour la suppression A1 (favorable), contre A2 (défavorable)
    votes = [v("D", "PA1", "contre"), v("A1", "PA1", "pour"), v("A2", "PA1", "contre"), v("M", "PA1", "pour")]
    s = {(r["acteur_id"], r["droit"]): r for r in scores.calculer(TEMOINS, votes)["scores_deputes"]}
    assert s[("PA1", "global")]["score"] == 75.0  # 0,5 + 0,25 sur 1
    assert s[("PA1", "enfants")]["score"] == 25.0  # sur ce droit, le texte étend : sens inverse


def test_abstention_exclue_ou_demi():
    votes = [v("D", "PA1", "abstention")]
    assert scores.calculer(TEMOINS, votes)["scores_deputes"][0]["score"] is None
    s = scores.calculer(TEMOINS, votes, {"abstention": "demi"})["scores_deputes"]
    assert next(r for r in s if r["droit"] == "global")["score"] == 50.0


def test_groupes_depuis_ventilations():
    # Les ventilations donnent les mêmes scores de groupe que les votes nominatifs.
    votes = [v("D", "PA1", "contre"), v("D", "PA2", "pour"), v("D", "PA3", "abstention"),
             v("A1", "PA1", "pour"), v("A1", "PA2", "pour"), v("A2", "PA2", "non_votant")]
    ventil = [{"scrutin_id": "D", "groupe_id": "G", "pour": 1, "contre": 1, "abstention": 1, "non_votants": 0},
              {"scrutin_id": "A1", "groupe_id": "G", "pour": 2, "contre": 0, "abstention": 0, "non_votants": 0},
              {"scrutin_id": "A2", "groupe_id": "G", "pour": 0, "contre": 0, "abstention": 0, "non_votants": 1}]
    assert (scores.calculer(TEMOINS, votes, ventilations=ventil)["scores_groupes"]
            == scores.calculer(TEMOINS, votes)["scores_groupes"])


def test_participation():
    pl = pytest.importorskip("polars")
    comptes = scores.scrutins_comptes(TEMOINS, scores.REGLES)
    scrutins = pl.DataFrame({"id": ["D", "A1", "A2", "M"], "legislature": [17] * 4,
                             "date": ["2025-03-01", "2025-02-01", "2025-02-01", "2025-01-01"]})
    votes = pl.DataFrame({"scrutin_id": ["D", "A1", "M"], "acteur_id": ["PA1", "PA1", "PA1"],
                          "position": ["abstention", "non_votant", "pour"]})
    # PA1 en mandat jusqu'au 15/02 (D hors mandat), PA2 tout du long sans voter.
    mandats = pl.DataFrame({"acteur_id": ["PA1", "PA2"], "legislature": [17, 17],
                            "debut": ["2024-07-07", "2024-07-07"], "fin": ["2025-02-15", None]})
    p = {r["acteur_id"]: r for r in scores.participation(comptes, scrutins, votes, mandats)}
    assert (p["PA1"]["scrutins"], p["PA1"]["votes"], p["PA1"]["non_votants"]) == (2, 0, 1)
    assert (p["PA2"]["scrutins"], p["PA2"]["taux"]) == (3, 0.0)


def test_lvnd_scores_redonne_build(tmp_path):
    """`lvnd scores` (data/export/, ventilations) redonne à l'octet près les scores de `lvnd build`
    (dump, votes nominatifs), tant que la qualification n'a pas changé depuis le dernier build."""
    from lvnd import editorial
    from lvnd.cli import EXPORT

    sc = scores.depuis_export(EXPORT, editorial.charger())
    scores.ecrire(tmp_path, sc)
    if (tmp_path / "scores_scrutins.csv").read_bytes() != (EXPORT / "scores_scrutins.csv").read_bytes():
        pytest.skip("data/editorial.json publié depuis le dernier `lvnd build`")
    for nom in ("scores_deputes", "scores_groupes"):
        assert (tmp_path / f"{nom}.csv").read_bytes() == (EXPORT / f"{nom}.csv").read_bytes(), nom


def test_par_texte():
    votes = [v("D", "PA1", "contre"), v("A1", "PA1", "pour"), v("A2", "PA1", "contre")]
    r = scores.par_texte(TEMOINS, votes)["scores_deputes_textes"]
    assert r == [{"acteur_id": "PA1", "texte_id": "t", "votes_favorables": 2, "votes_defavorables": 1,
                  "abstentions": 0, "non_votants": 0, "score": 75.0}]

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

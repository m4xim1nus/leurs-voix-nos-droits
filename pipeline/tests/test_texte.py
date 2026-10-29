from lvnd.texte import objet_scrutin


def test_objet_scrutin():
    assert objet_scrutin("l'ensemble du projet de loi pour contrôler l'immigration (texte de la CMP).") == "ensemble"
    assert objet_scrutin("l'article unique de la proposition de loi constitutionnelle") == "article_unique"
    assert objet_scrutin("la motion de rejet préalable, déposée par M. X, du projet de loi") == "motion_rejet"


def test_ensemble_d_une_partie_n_est_pas_le_texte():
    # PLFSS 2025 (VTANR5L17V242) : ce vote ne peut pas être le décisif
    titre = ("l'ensemble de la deuxième partie du projet de loi de financement de la sécurité sociale "
             "pour 2025 (première lecture).")
    assert objet_scrutin(titre) == "partie"
    assert objet_scrutin("la première partie du projet de loi de finances pour 2024") == "partie"

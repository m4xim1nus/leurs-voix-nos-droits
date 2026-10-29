from lvnd.texte import objet_scrutin


def test_objet_scrutin():
    assert objet_scrutin("l'ensemble du projet de loi pour contrôler l'immigration (texte de la CMP).") == "ensemble"
    assert objet_scrutin("l'article unique de la proposition de loi constitutionnelle") == "article_unique"
    assert objet_scrutin("la motion de rejet préalable, déposée par M. X, du projet de loi") == "motion_rejet"
    # délit de séjour irrégulier (VTANR5L17V3261) et avenant chômage (VTANR5L17V6283)
    assert objet_scrutin("l'amendement de suppression n° 2 de M. Christophle et les amendements identiques "
                         "suivants à l'article unique de la proposition de loi") == "suppression_article_unique"
    assert objet_scrutin("l'amendement n° 1 de M. Monnet et les amendements identiques suivants de suppression "
                         "de l'article unique du projet de loi") == "suppression_article_unique"
    assert objet_scrutin("l'amendement de suppression n° 3 de M. X à l'article 2 de la proposition de loi") == "amendement"


def test_ensemble_d_une_partie_n_est_pas_le_texte():
    # PLFSS 2025 (VTANR5L17V242) : ce vote ne peut pas être le décisif
    titre = ("l'ensemble de la deuxième partie du projet de loi de financement de la sécurité sociale "
             "pour 2025 (première lecture).")
    assert objet_scrutin(titre) == "partie"
    assert objet_scrutin("la première partie du projet de loi de finances pour 2024") == "partie"

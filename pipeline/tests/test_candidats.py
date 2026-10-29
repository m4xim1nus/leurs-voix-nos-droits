from lvnd.candidats import nature, reperer


def test_reperer():
    r = reperer(["Proposition de loi visant à protéger les logements contre l'occupation illicite"])
    assert set(r) == {"logement"}
    r = reperer(["Projet de loi pour contrôler l'immigration, améliorer l'intégration"])
    assert set(r) == {"etrangers"}


def test_securite_sociale_n_est_pas_police():
    assert "police-justice" not in reperer(["Projet de loi de financement de la sécurité sociale pour 2025"])
    assert "police-justice" in reperer(["Proposition de loi relative à la sécurité globale"])


def test_nature():
    assert nature("Projet de ratification des traités", "autorisant l'approbation de l'accord") == "convention"
    assert nature("Projet de loi de finances de l'année", "de finances pour 2025") == "budget"
    assert nature("Proposition de loi organique", "relative au statut") == "organique"
    assert nature("Proposition de loi ordinaire", "visant à sortir la France du piège du narcotrafic") == "ordinaire"

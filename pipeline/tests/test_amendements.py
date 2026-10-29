from lvnd.amendements import analyser


def test_intitule_simple():
    assert analyser("l'amendement n° 1762 de M. Le Coq à l'article 2 du projet de loi de finances pour 2025") \
        == ("amendement", "1762", "le coq")


def test_suppression_et_rectifie():
    nature, num, nom = analyser("l'amendement de suppression n° 45 (2ème rect.) de Mme Panot à l'article 7")
    assert (nature, num, nom) == ("amendement", "45", "panot")


def test_sous_amendement_et_prefixe():
    assert analyser("le sous-amendement n° 3020 de M. Bernalicis à l'amendement n° 12")[:2] == ("sous amendement", "3020")
    assert analyser("l'amendement n° I-512 de M. Coquerel")[1] == "I-512"


def test_intitule_non_analyse():
    assert analyser("l'ensemble du projet de loi") == (None, None, None)

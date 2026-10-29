from lvnd.positions import position


def test_majorite_des_exprimes():
    assert position(6, 2, 2) == ("pour", 0.6)
    assert position(2, 6, 0) == ("contre", 0.75)


def test_abstention_l_emporte_sur_les_deux():
    # leurs-votes.fr et datan.fr diraient « abstention » dès que l'abstention est en tête
    assert position(4, 1, 5)[0] == "abstention"
    assert position(5, 1, 5)[0] == "pour"  # égalité avec les pour : la majorité des exprimés prime


def test_partage_et_absent():
    assert position(3, 3, 0) == ("partage", None)
    assert position(0, 0, 0) == ("absent", None)

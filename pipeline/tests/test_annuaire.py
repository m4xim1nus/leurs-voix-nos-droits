from lvnd import annuaire


def test_insee_des_bureaux():
    assert annuaire._insee("33063", "0101") == "33063"
    assert annuaire._insee("75056", "1503") == "75115"  # Paris 15e
    assert annuaire._insee("69123", "0712") == "69387"  # Lyon 7e
    assert annuaire._insee("13055", "1301") == "13213"  # Marseille 13e
    assert annuaire._insee("ZX701", "0001") == "97701"
    assert annuaire._insee("ZZ001", "0001") is None  # Français de l'étranger


def test_departements_an():
    assert [annuaire._dep_an(d) for d in ("1", "2A", "ZA", "ZZ")] == ["01", "2A", "971", "099"]

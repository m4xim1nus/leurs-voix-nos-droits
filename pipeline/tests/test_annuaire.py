import polars as pl

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


def test_departement_d_une_commune():
    cp = pl.DataFrame({"cp": ["20000", "20200", "97133", "97150", "33000", "33000"],
                       "insee": ["2A004", "2B033", "97701", "97801", "33063", "33063"]})
    assert annuaire.codes_postaux_departements(cp).rows() == [
        ("20000", "2A"), ("20200", "2B"), ("33000", "33"), ("97133", "977"), ("97150", "978")]

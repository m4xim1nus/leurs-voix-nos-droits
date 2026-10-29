"""Tests sur la base produite."""

import pytest

from lvnd import check

pytestmark = pytest.mark.donnees


def test_check_passe(base):
    ok, lignes = check.verifier(base)
    assert ok, "\n".join(l for l in lignes if l.startswith("ÉCHEC"))

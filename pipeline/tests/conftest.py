"""Fixtures : base produite (tests `donnees`, sautés si elle est absente)."""

import pytest

from lvnd.cli import SQLITE


@pytest.fixture(scope="session")
def base():
    if not SQLITE.exists():
        pytest.skip(f"base absente : {SQLITE} (lancer `lvnd build`)")
    return SQLITE

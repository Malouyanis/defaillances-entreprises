"""Tests du script get_data.py à la racine du dépôt."""

import pytest

import config
import get_data


def test_periode_par_defaut() -> None:
    """Sans arguments, toute la période de l'étude est téléchargée."""
    assert get_data.lire_periode([]) == (config.ANNEE_DEBUT, config.ANNEE_FIN)


def test_periode_choisie() -> None:
    """Deux années en arguments donnent une période plus courte."""
    assert get_data.lire_periode(["2024", "2025"]) == (2024, 2025)


def test_periode_hors_etude() -> None:
    """Une période en dehors de 2019-2025 est refusée avec un message clair."""
    with pytest.raises(ValueError, match="Période attendue"):
        get_data.lire_periode(["2010", "2012"])

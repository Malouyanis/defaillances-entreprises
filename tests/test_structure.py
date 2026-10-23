"""Tests de la structure du projet."""

import importlib
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent


def test_packages_importables() -> None:
    """Les packages du projet s'importent sans erreur."""
    for nom in ("src", "src.components", "src.pages", "src.utils"):
        assert importlib.import_module(nom) is not None


def test_donnees_brutes_ignorees_par_git() -> None:
    """Le dossier data/raw/ est ignoré par Git, car les données brutes sont trop lourdes."""
    contenu = (RACINE / ".gitignore").read_text(encoding="utf-8")
    assert "data/raw/" in contenu

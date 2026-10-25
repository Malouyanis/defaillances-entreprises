"""Tests de la création de l'application Dash."""

import dash

import config
from src.app import creer_application


def test_creer_application() -> None:
    """L'application porte le bon titre et la page d'accueil est enregistrée sur « / »."""
    application = creer_application()
    assert application.title == config.TITRE_APPLICATION
    chemins = [page["path"] for page in dash.page_registry.values()]
    assert "/" in chemins
    
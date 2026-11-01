"""Tests de la page Méthodologie."""

import dash

from src.app import creer_application


def page_methodologie() -> dict:
    """Crée l'application puis renvoie l'entrée de la page Méthodologie dans le registre."""
    creer_application()
    pages = [page for page in dash.page_registry.values() if page["path"] == "/methodologie"]
    assert len(pages) == 1
    return pages[0]


def test_page_enregistree() -> None:
    """La page est enregistrée sur /methodologie, après les pages d'analyse dans le menu."""
    page = page_methodologie()
    assert page["name"] == "Méthodologie"
    assert page["order"] == 90


def test_contenu() -> None:
    """La page présente les quatre parties, dont les limites de l'étude."""
    texte = str(page_methodologie()["layout"])
    for titre in ("Sources", "Ce qu'on appelle une défaillance", "Choix de nettoyage", "Limites"):
        assert titre in texte
    assert "biais de sélection" in texte


def test_texte_a_jour() -> None:
    """Le texte reflète les derniers choix : confidentiels gardés, biais du survivant."""
    texte = str(page_methodologie()["layout"])
    assert "laissés vides" in texte
    assert "biais du survivant" in texte
    assert "un tiers" not in texte

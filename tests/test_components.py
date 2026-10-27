"""Tests des composants communs : barre de navigation et pied de page."""

from src.app import creer_application
from src.components import footer
from src.components.navbar import creer_navbar


def test_navbar_contient_lien_accueil() -> None:
    """La barre de navigation contient un lien vers la page d'accueil « / »."""
    creer_application()
    navbar = creer_navbar()
    liens = [element.children.href for element in navbar.children]
    assert "/" in liens


def test_footer_cite_les_sources() -> None:
    """Le pied de page cite les trois sources de données."""
    for source in ("BODACC", "BCE/INPI", "Sirene"):
        assert source in footer.TEXTE_SOURCES
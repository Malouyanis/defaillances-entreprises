"""Tests des composants communs : barre latérale et pied de page."""

from src.app import creer_application
from src.components import footer, navbar


def test_navbar_contient_lien_accueil() -> None:
    """La barre latérale a un lien par page, dont l'accueil « / »."""
    creer_application()
    liens = navbar.creer_liens()
    assert "/" in [lien.to_plotly_json()["props"]["href"] for lien in liens]
    assert "Carte des défaillances" not in [
        lien.to_plotly_json()["props"]["children"] for lien in liens
    ]


def test_page_ouverte_mise_en_avant() -> None:
    """Seul le lien de la page ouverte reçoit la classe active."""
    creer_application()
    liens = navbar.mettre_en_avant("/carte")
    proprietes = [lien.to_plotly_json()["props"] for lien in liens]
    actifs = [p["href"] for p in proprietes if p["className"] == "active"]
    assert actifs == ["/carte"]


def test_footer_cite_les_sources() -> None:
    """Le pied de page cite les trois sources de données."""
    for source in ("BODACC", "BCE/INPI", "Sirene"):
        assert source in footer.TEXTE_SOURCES

"""Tests des composants communs : barre latérale, pied de page, chiffres et graphiques."""

from src.app import creer_application
from src.components import chiffres, footer, graphique, navbar


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


def test_carte_chiffres_nommee() -> None:
    """La carte des chiffres a une colonne par chiffre et un nom pour les lecteurs d'écran."""
    carte = chiffres.creer_carte_chiffres([("AUC", "0,755", "test"), ("Sociétés", "12", "")], "Q")
    proprietes = carte.to_plotly_json()["props"]
    assert proprietes["aria-label"] == "Q"
    assert len(proprietes["children"]) == 2
    assert "0,755" in str(carte)


def test_graphique_avec_description() -> None:
    """Le graphique est suivi d'une description en texte, cachée à l'écran."""
    figure = graphique.creer_graphique("Deux barres : 3 et 5.", id="essai")
    enfants = figure.to_plotly_json()["props"]["children"]
    assert enfants[0].to_plotly_json()["props"]["id"] == "essai"
    legende = enfants[1].to_plotly_json()["props"]
    assert legende["children"] == "Deux barres : 3 et 5."
    assert legende["className"] == "lecteur-ecran"

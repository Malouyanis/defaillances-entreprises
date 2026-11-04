"""Tests du style commun des graphiques et de la mise en forme des nombres."""

import plotly.graph_objects as go

from src.utils import figures, formatage


def test_appliquer_style() -> None:
    """La figure reçoit le template du projet (police, palette, séparateurs) et le titre."""
    figure = figures.appliquer_style(go.Figure(go.Bar(x=["a", "b"], y=[1, 2])), "Essai")
    template = figure.layout.template.layout
    assert template.font.family == figures.POLICE
    assert list(template.colorway) == list(figures.PALETTE)
    assert template.separators == figures.SEPARATEURS_FR
    assert figure.layout.title.text == "Essai"
    assert figure.layout.showlegend is False


def test_figure_vide() -> None:
    """La figure vide n'a ni données ni axes, seulement le message."""
    figure = figures.figure_vide("Rien à afficher")
    assert len(figure.data) == 0
    assert figure.layout.annotations[0].text == "Rien à afficher"
    assert figure.layout.xaxis.visible is False


def test_couleurs_procedures() -> None:
    """Chaque procédure a sa couleur ; la liquidation porte la teinte du projet."""
    couleurs = list(figures.COULEURS_PROCEDURES.values())
    assert len(set(couleurs)) == len(couleurs) == 3
    assert figures.COULEURS_PROCEDURES["Liquidation judiciaire"] == figures.TEINTE


def test_formatage_francais() -> None:
    """Espace fine pour les milliers, virgule décimale, pourcentage à la française."""
    assert formatage.entier(272219) == "272 219"
    assert formatage.decimal(5.66) == "5,7"
    assert formatage.pourcentage(0.7015) == "70 %"
    assert formatage.pourcentage(0.184, 1) == "18,4 %"

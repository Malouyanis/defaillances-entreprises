"""Tests du style commun des graphiques."""

import plotly.graph_objects as go

from src.utils import figures


def test_appliquer_style() -> None:
    """La figure reçoit la police, la palette et le titre du projet."""
    figure = figures.appliquer_style(go.Figure(go.Bar(x=["a", "b"], y=[1, 2])), "Essai")
    assert figure.layout.font.family == figures.POLICE
    assert list(figure.layout.colorway) == list(figures.PALETTE)
    assert figure.layout.title.text == "Essai"


def test_figure_vide() -> None:
    """La figure vide n'a ni données ni axes, seulement le message."""
    figure = figures.figure_vide("Rien à afficher")
    assert len(figure.data) == 0
    assert figure.layout.annotations[0].text == "Rien à afficher"
    assert figure.layout.xaxis.visible is False


def test_couleurs_procedures() -> None:
    """Chaque procédure a sa propre couleur."""
    couleurs = list(figures.COULEURS_PROCEDURES.values())
    assert len(set(couleurs)) == len(couleurs) == 3

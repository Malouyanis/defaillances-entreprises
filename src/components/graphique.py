"""Graphique accessible : un dcc.Graph accompagné d'une description en texte.

Un graphique Plotly est une image pour un lecteur d'écran. La description, invisible à
l'écran mais lue à voix haute, donne les mêmes informations en mots et en chiffres.
"""

from typing import Any

from dash import dcc, html


def creer_graphique(description: str, **proprietes: Any) -> html.Figure:
    """Un graphique sans barre d'outils, suivi de sa description pour les lecteurs d'écran."""
    return html.Figure(
        [
            dcc.Graph(config={"displayModeBar": False}, className="graphique", **proprietes),
            html.Figcaption(description, className="lecteur-ecran"),
        ],
        className="figure-graphique",
    )

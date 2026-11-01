"""Bouton « Mettre à jour les données » : vide le cache pour relire la base SQLite."""

from datetime import datetime

import dash_bootstrap_components as dbc
from dash import Input, Output, callback, html

from src.utils import cache

ID_BOUTON_MISE_A_JOUR = "bouton-mise-a-jour"
ID_MESSAGE_MISE_A_JOUR = "message-mise-a-jour"


def creer_bouton_mise_a_jour() -> html.Div:
    """Crée le bouton et la zone de message qui confirme la mise à jour."""
    return html.Div(
        [
            dbc.Button(
                "Mettre à jour les données",
                id=ID_BOUTON_MISE_A_JOUR,
                color="secondary",
                outline=True,
                size="sm",
            ),
            html.Span(id=ID_MESSAGE_MISE_A_JOUR, className="small text-muted ms-2"),
        ],
        className="mb-3",
    )


@callback(
    Output(ID_MESSAGE_MISE_A_JOUR, "children"),
    Input(ID_BOUTON_MISE_A_JOUR, "n_clicks"),
    prevent_initial_call=True,
)
def mettre_a_jour(_n_clics: int | None) -> str:
    """Vide le cache des tables et renvoie un message avec l'heure de la mise à jour."""
    cache.vider_cache()
    return f"Données rechargées depuis la base à {datetime.now():%H:%M}."

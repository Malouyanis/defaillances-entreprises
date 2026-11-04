"""Bouton « Mettre à jour les données » : vide le cache pour relire la base SQLite."""

from datetime import datetime
from typing import Any

from dash import Input, Output, callback, html

from src.utils import cache

ID_BOUTON_MISE_A_JOUR = "bouton-mise-a-jour"
ID_MESSAGE_MISE_A_JOUR = "message-mise-a-jour"
ANNONCE_POLIE: dict[str, Any] = {"aria-live": "polite"}


def creer_bouton_mise_a_jour() -> html.Div:
    """Crée le bouton et la zone de message qui confirme la mise à jour."""
    return html.Div(
        [
            html.Button(
                "Mettre à jour les données",
                id=ID_BOUTON_MISE_A_JOUR,
                className="bouton-discret",
                type="button",
            ),
            html.Span(id=ID_MESSAGE_MISE_A_JOUR, className="message-maj", **ANNONCE_POLIE),
        ],
        style={"display": "flex", "flexDirection": "column", "gap": "6px"},
    )


@callback(
    Output(ID_MESSAGE_MISE_A_JOUR, "children"),
    Input(ID_BOUTON_MISE_A_JOUR, "n_clicks"),
    prevent_initial_call=True,
)
def mettre_a_jour(_n_clics: int | None) -> str:
    """Vide le cache des tables et renvoie un message avec l'heure de la mise à jour."""
    cache.vider_cache()
    return f"Données rechargées à {datetime.now():%H:%M}."

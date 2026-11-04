"""Barre latérale : la marque du projet, son périmètre et un lien vers chaque page."""

from typing import Any

import dash
from dash import Input, Output, callback, dcc, html

import config
from src.components.mise_a_jour import creer_bouton_mise_a_jour

PERIMETRE = f"France métropolitaine · {config.ANNEE_DEBUT}-{config.ANNEE_FIN}"
NOM_COURT = "Défaillances"
ID_URL = "url"
ID_NAV = "nav-liens"
CACHE_AUX_LECTEURS: dict[str, Any] = {"aria-hidden": "true"}
NOM_ACCESSIBLE: dict[str, Any] = {"aria-label": "Pages du tableau de bord"}


def creer_marque() -> html.Div:
    """Marque du projet : trois barres descendantes (des défaillances qui tombent) et le nom."""
    barres = [
        html.Div(style={"width": "4px", "height": f"{hauteur}px", "background": "currentColor"})
        for hauteur in (14, 10, 6)
    ]
    symbole = html.Div(
        barres,
        style={"display": "flex", "alignItems": "flex-end", "gap": "2px"},
        **CACHE_AUX_LECTEURS,
    )
    return html.Div([symbole, html.Span(NOM_COURT)], className="marque")


def creer_liens(chemin: str | None = "/") -> list[dcc.Link]:
    """Un lien par page enregistrée, dans l'ordre du menu ; la page ouverte est mise en avant.

    Les liens sont lus dans dash.page_registry : une nouvelle page apparaît
    automatiquement dans le menu, dans l'ordre donné par son paramètre order.
    """
    pages = sorted(dash.page_registry.values(), key=lambda page: page["order"])
    return [
        dcc.Link(
            page["name"],
            href=page["relative_path"],
            className="active" if page["relative_path"] == chemin else "",
        )
        for page in pages
    ]


def creer_navbar() -> html.Nav:
    """Crée la barre latérale : marque, périmètre, liens des pages et bouton de mise à jour."""
    return html.Nav(
        [
            dcc.Location(id=ID_URL),
            creer_marque(),
            html.Div(PERIMETRE, className="perimetre"),
            html.Div(creer_liens(), className="nav", id=ID_NAV),
            html.Div(creer_bouton_mise_a_jour(), className="outils"),
        ],
        className="sidebar",
        **NOM_ACCESSIBLE,
    )


@callback(Output(ID_NAV, "children"), Input(ID_URL, "pathname"))
def mettre_en_avant(chemin: str | None) -> list[dcc.Link]:
    """Redessine les liens à chaque changement de page pour marquer la page ouverte."""
    return creer_liens(chemin)

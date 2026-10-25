"""Création de l'application Dash : thème, pages et mise en page générale."""

import dash
import dash_bootstrap_components as dbc
from dash import Dash, html

import config

THEME = dbc.themes.FLATLY


def creer_application() -> Dash:
    """Crée l'application Dash multipage avec le thème Bootstrap clair du projet.

    Chaque fichier de src/pages/ qui appelle dash.register_page devient une page :
    pour ajouter une page, il suffit d'y créer un nouveau fichier.
    """
    application = Dash(
        __name__,
        use_pages=True,
        pages_folder=str(config.DOSSIER_PAGES),
        external_stylesheets=[THEME],
        title=config.TITRE_APPLICATION,
        suppress_callback_exceptions=True,
    )
    application.layout = dbc.Container(
        [
            html.H1(config.TITRE_APPLICATION, className="my-4"),
            dash.page_container,
        ],
        fluid=True,
    )
    return application
"""Création de l'application Dash : thème, pages et mise en page générale."""

import dash
import dash_bootstrap_components as dbc
from dash import Dash, html

import config
from src.components.footer import creer_footer
from src.components.navbar import creer_navbar

THEME = dbc.themes.FLATLY


def creer_application() -> Dash:
    """Crée l'application Dash multipage avec le thème Bootstrap clair du projet.

    Chaque fichier de src/pages/ qui appelle dash.register_page devient une page :
    pour ajouter une page, il suffit d'y créer un nouveau fichier. La barre de
    navigation est construite après la création de l'application, quand Dash a
    enregistré toutes les pages.
    """
    application = Dash(
        __name__,
        use_pages=True,
        pages_folder=str(config.DOSSIER_PAGES),
        external_stylesheets=[THEME],
        title=config.TITRE_APPLICATION,
        suppress_callback_exceptions=True,
    )
    application.layout = html.Div(
        [
            creer_navbar(),
            dbc.Container([dash.page_container, creer_footer()], fluid=True),
        ]
    )
    return application
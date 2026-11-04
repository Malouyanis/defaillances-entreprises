"""Création de l'application Dash : pages, barre latérale et thème « Registre »."""

import dash
from dash import Dash, html

import config
from src.components.footer import creer_footer
from src.components.navbar import creer_navbar


def creer_application() -> Dash:
    """Crée l'application Dash multipage avec le thème du projet.

    Chaque fichier de src/pages/ qui appelle dash.register_page devient une page :
    pour ajouter une page, il suffit d'y créer un nouveau fichier. Le thème (couleurs,
    police, mise en page) vient de src/assets/theme.css, que Dash charge tout seul ;
    aucune feuille de style n'est téléchargée depuis internet. La barre latérale est
    construite après la création de l'application, quand Dash a enregistré les pages.
    """
    application = Dash(
        __name__,
        use_pages=True,
        pages_folder=str(config.DOSSIER_PAGES),
        title=config.TITRE_APPLICATION,
        suppress_callback_exceptions=True,
    )
    application.layout = html.Div(
        [
            creer_navbar(),
            html.Main([dash.page_container, creer_footer()], className="contenu"),
        ],
        className="app",
    )
    return application

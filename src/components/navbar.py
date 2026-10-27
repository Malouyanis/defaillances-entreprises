"""Barre de navigation : le titre du dashboard et un lien vers chaque page."""

import dash
import dash_bootstrap_components as dbc

import config


def creer_navbar() -> dbc.NavbarSimple:
    """Crée la barre de navigation à partir des pages enregistrées dans Dash.

    Les liens sont lus dans dash.page_registry : une nouvelle page apparaît
    automatiquement dans le menu, dans l'ordre donné par son paramètre order.
    """
    pages = sorted(dash.page_registry.values(), key=lambda page: page["order"])
    liens = [
        dbc.NavItem(dbc.NavLink(page["name"], href=page["relative_path"], active="exact"))
        for page in pages
    ]
    return dbc.NavbarSimple(
        children=liens,
        brand=config.TITRE_APPLICATION,
        brand_href="/",
        color="primary",
        dark=True,
        className="mb-4",
    )
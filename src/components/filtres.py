"""Barre de filtres commune aux pages : période, procédure et région.

Chaque filtre a un identifiant constant : les callbacks des pages s'y brancheront
en important ces constantes, sans recopier les identifiants à la main.
"""

from dash import dcc, html

import config
from src.utils.figures import COULEURS_PROCEDURES

ID_FILTRE_ANNEES = "filtre-annees"
ID_FILTRE_PROCEDURES = "filtre-procedures"
ID_FILTRE_REGIONS = "filtre-regions"
LIBELLES_LISTES = {
    "select_all": "Tout sélectionner",
    "deselect_all": "Tout désélectionner",
    "selected_count": "{num_selected} choisies",
    "search": "Rechercher",
    "clear_search": "Effacer la recherche",
    "clear_selection": "Effacer la sélection",
    "no_options_found": "Aucun résultat",
}
REGIONS_METROPOLE = (
    "Auvergne-Rhône-Alpes",
    "Bourgogne-Franche-Comté",
    "Bretagne",
    "Centre-Val de Loire",
    "Corse",
    "Grand Est",
    "Hauts-de-France",
    "Île-de-France",
    "Normandie",
    "Nouvelle-Aquitaine",
    "Occitanie",
    "Pays de la Loire",
    "Provence-Alpes-Côte d'Azur",
)


def creer_filtre_annees() -> dcc.RangeSlider:
    """Curseur à deux poignées pour choisir la période étudiée."""
    annees = range(config.ANNEE_DEBUT, config.ANNEE_FIN + 1)
    return dcc.RangeSlider(
        id=ID_FILTRE_ANNEES,
        min=config.ANNEE_DEBUT,
        max=config.ANNEE_FIN,
        step=1,
        value=[config.ANNEE_DEBUT, config.ANNEE_FIN],
        marks={annee: str(annee) for annee in annees},
    )


def creer_filtre_procedures() -> dcc.Dropdown:
    """Liste déroulante à choix multiple des procédures (toutes cochées par défaut)."""
    procedures = list(COULEURS_PROCEDURES)
    return dcc.Dropdown(
        id=ID_FILTRE_PROCEDURES,
        options=procedures,
        value=procedures,
        multi=True,
        clearable=False,
        labels=LIBELLES_LISTES,
    )


def creer_filtre_regions() -> dcc.Dropdown:
    """Liste déroulante des régions ; vide = toute la France métropolitaine."""
    return dcc.Dropdown(
        id=ID_FILTRE_REGIONS,
        options=list(REGIONS_METROPOLE),
        value=[],
        multi=True,
        placeholder="Toute la France métropolitaine",
        labels=LIBELLES_LISTES,
    )


def creer_barre_filtres() -> html.Div:
    """Assemble les trois filtres sur une ligne, au-dessus des graphiques."""
    filtres = [
        ("Période", ID_FILTRE_ANNEES, creer_filtre_annees()),
        ("Procédure", ID_FILTRE_PROCEDURES, creer_filtre_procedures()),
        ("Région", ID_FILTRE_REGIONS, creer_filtre_regions()),
    ]
    return html.Div(
        [
            html.Div([html.Label(titre, htmlFor=ident), composant])
            for titre, ident, composant in filtres
        ],
        className="filtres",
    )

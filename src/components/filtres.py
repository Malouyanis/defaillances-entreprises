"""Barre de filtres commune aux pages : période, procédure et région.

Chaque filtre a un identifiant constant : les callbacks des pages s'y brancheront
en important ces constantes, sans recopier les identifiants à la main.
"""

import dash_bootstrap_components as dbc
from dash import dcc, html

import config
from src.utils.figures import COULEURS_PROCEDURES

ID_FILTRE_ANNEES = "filtre-annees"
ID_FILTRE_PROCEDURES = "filtre-procedures"
ID_FILTRE_REGIONS = "filtre-regions"
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
    )


def creer_filtre_regions() -> dcc.Dropdown:
    """Liste déroulante des régions ; vide = toute la France métropolitaine."""
    return dcc.Dropdown(
        id=ID_FILTRE_REGIONS,
        options=list(REGIONS_METROPOLE),
        value=[],
        multi=True,
        placeholder="Toute la France métropolitaine",
    )


def creer_barre_filtres() -> dbc.Card:
    """Assemble les trois filtres sur une ligne, au-dessus des graphiques."""
    filtres = [
        ("Période", creer_filtre_annees(), 5),
        ("Procédure", creer_filtre_procedures(), 4),
        ("Région", creer_filtre_regions(), 3),
    ]
    colonnes = [
        dbc.Col([html.Label(titre, className="fw-bold small mb-1"), composant], md=largeur)
        for titre, composant, largeur in filtres
    ]
    return dbc.Card(dbc.CardBody(dbc.Row(colonnes, className="g-3")), className="mb-4")

"""Page Carte : les défaillances par département, selon la période, la procédure et la région."""

import json
from functools import cache as memoriser
from pathlib import Path

import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, callback, dcc, html

import config
from src.components.filtres import (
    ID_FILTRE_ANNEES,
    ID_FILTRE_PROCEDURES,
    ID_FILTRE_REGIONS,
    creer_barre_filtres,
)
from src.utils import cache, database, filtrage
from src.utils.figures import ECHELLE_CONTINUE, appliquer_style, figure_vide

dash.register_page(__name__, path="/carte", name="Carte", order=10)

NOM_TABLE_CLEANED = "cleaned"
NOM_FICHIER_GEOJSON = "departements.geojson"
ID_INDICATEUR = "carte-indicateur"
ID_GRAPHIQUE = "carte-graphique"
CENTRE_FRANCE = {"lat": 46.6, "lon": 2.5}
INDICATEURS = (
    "Nombre de défaillances",
    "Part de liquidations (%)",
    "Âge médian à la défaillance (ans)",
)
MESSAGE_SANS_DONNEES = (
    "Les données ne sont pas encore disponibles : lancez get_data.py puis clean_data.py."
)
MESSAGE_SANS_CONTOURS = f"Le fichier des contours data/{NOM_FICHIER_GEOJSON} est introuvable."


def chemin_geojson() -> Path:
    """Chemin du fichier des contours des départements (dans le dossier data)."""
    return Path(config.CHEMIN_BASE).parent / NOM_FICHIER_GEOJSON


@memoriser
def charger_geojson(chemin: Path) -> dict:
    """Lit une seule fois le fichier des contours des départements."""
    with open(chemin, encoding="utf-8") as fichier:
        return json.load(fichier)


def calculer_par_departement(defaillances: pd.DataFrame, indicateur: str) -> pd.DataFrame:
    """Calcule l'indicateur choisi pour chaque département (colonnes departement, valeur)."""
    groupes = defaillances.groupby("departement")
    if indicateur == INDICATEURS[1]:
        valeurs = groupes["procedure"].agg(lambda p: (p == "Liquidation judiciaire").mean() * 100)
    elif indicateur == INDICATEURS[2]:
        valeurs = groupes["age_defaillance"].median()
    else:
        valeurs = groupes.size()
    return valeurs.round(1).rename("valeur").reset_index()


def creer_carte(par_departement: pd.DataFrame, geojson: dict, indicateur: str) -> go.Figure:
    """Dessine la carte des départements, colorés selon l'indicateur."""
    noms = {f["properties"]["code"]: f["properties"]["nom"] for f in geojson["features"]}
    figure = go.Figure(
        go.Choroplethmap(
            geojson=geojson,
            featureidkey="properties.code",
            locations=par_departement["departement"],
            z=par_departement["valeur"],
            text=par_departement["departement"].map(noms),
            colorscale=list(ECHELLE_CONTINUE),
            marker_line_color="white",
            marker_line_width=0.5,
            hovertemplate="%{text} (%{location})<br>%{z}<extra></extra>",
        )
    )
    appliquer_style(figure, indicateur)
    figure.update_layout(
        map={"style": "white-bg", "center": CENTRE_FRANCE, "zoom": 4.6},
        height=600,
        margin={"l": 0, "r": 0, "t": 50, "b": 0},
    )
    return figure


def layout() -> html.Div:
    """Construit la page : filtres, choix de l'indicateur et carte."""
    contenu: list = [
        html.H2("Carte des défaillances"),
        html.P("Où les sociétés font-elles défaut ? Survolez un département pour le détail."),
    ]
    if not database.table_existe(NOM_TABLE_CLEANED, config.CHEMIN_BASE):
        contenu.append(dbc.Alert(MESSAGE_SANS_DONNEES, color="warning"))
        return html.Div(contenu)
    if not chemin_geojson().exists():
        contenu.append(dbc.Alert(MESSAGE_SANS_CONTOURS, color="warning"))
        return html.Div(contenu)
    choix = dcc.RadioItems(
        id=ID_INDICATEUR, options=list(INDICATEURS), value=INDICATEURS[0], inline=True
    )
    contenu.extend(
        [
            creer_barre_filtres(),
            html.Div(choix, className="mb-2"),
            dcc.Loading(dcc.Graph(id=ID_GRAPHIQUE)),
        ]
    )
    return html.Div(contenu)


@callback(
    Output(ID_GRAPHIQUE, "figure"),
    Input(ID_FILTRE_ANNEES, "value"),
    Input(ID_FILTRE_PROCEDURES, "value"),
    Input(ID_FILTRE_REGIONS, "value"),
    Input(ID_INDICATEUR, "value"),
)
def mettre_a_jour_carte(
    annees: list[int], procedures: list[str], regions: list[str], indicateur: str
) -> go.Figure:
    """Redessine la carte à chaque changement de filtre ou d'indicateur."""
    cleaned = cache.charger_table(NOM_TABLE_CLEANED, config.CHEMIN_BASE)
    filtrees = filtrage.appliquer_filtres(cleaned, annees, procedures, regions)
    if filtrees.empty:
        return figure_vide()
    par_departement = calculer_par_departement(filtrees, indicateur)
    return creer_carte(par_departement, charger_geojson(chemin_geojson()), indicateur)

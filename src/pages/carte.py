"""Page Carte : les défaillances par département, selon la période, la procédure et la région."""

import dash
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
from src.utils import cache, database, filtrage, formatage, geographie
from src.utils.figures import (
    ECHELLE_CONTINUE,
    FOND_CARTE,
    FORMAT_NOMBRES,
    TEINTE,
    appliquer_style,
    figure_vide,
)

dash.register_page(__name__, path="/carte", name="Carte", order=10)

NOM_TABLE_CLEANED = "cleaned"
ID_INDICATEUR = "carte-indicateur"
ID_GRAPHIQUE = "carte-graphique"
ID_CLASSEMENT = "carte-classement"
CENTRE_FRANCE = {"lat": 46.6, "lon": 2.5}
NOMBRE_LIGNES = 11
INDICATEURS = (
    "Nombre de défaillances",
    "Part de liquidations (%)",
    "Âge médian à la défaillance (ans)",
)
MESSAGE_SANS_DONNEES = (
    "Les données ne sont pas encore disponibles : lancez get_data.py puis clean_data.py."
)
MESSAGE_SANS_CONTOURS = (
    f"Le fichier des contours data/{geographie.NOM_FICHIER_GEOJSON} est introuvable."
)


def calculer_par_departement(defaillances: pd.DataFrame, indicateur: str) -> pd.DataFrame:
    """Calcule l'indicateur choisi pour chaque département (colonnes departement, valeur)."""
    groupes = defaillances.groupby("departement")
    valeurs: pd.Series
    if indicateur == INDICATEURS[1]:
        valeurs = groupes["procedure"].agg(lambda p: (p == "Liquidation judiciaire").mean() * 100)
    elif indicateur == INDICATEURS[2]:
        valeurs = groupes["age_defaillance"].median()
    else:
        valeurs = groupes.size()
    return valeurs.round(1).rename("valeur").reset_index()


def creer_carte(par_departement: pd.DataFrame, geojson: dict, indicateur: str) -> go.Figure:
    """Dessine la carte des départements, colorés selon l'indicateur, sans fond réseau."""
    noms = geographie.noms_departements(geojson)
    figure = go.Figure(
        go.Choroplethmap(
            geojson=geojson,
            featureidkey="properties.code",
            locations=par_departement["departement"],
            z=par_departement["valeur"],
            text=par_departement["departement"].map(noms),
            colorscale=list(ECHELLE_CONTINUE),
            marker_line_color="white",
            marker_line_width=0.6,
            colorbar={
                "thickness": 8,
                "len": 0.6,
                "outlinewidth": 0,
                "x": 0.98,
                "tickformat": FORMAT_NOMBRES,
            },
            hovertemplate="%{text} (%{location}) : %{z}<extra></extra>",
        )
    )
    appliquer_style(figure)
    figure.update_layout(
        map={"style": FOND_CARTE, "center": CENTRE_FRANCE, "zoom": 4.4},
        height=520,
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
    )
    return figure


def valeur_affichee(valeur: float, indicateur: str) -> str:
    """Met en forme la valeur d'un département selon l'indicateur choisi."""
    if indicateur == INDICATEURS[0]:
        return formatage.entier(valeur)
    suffixe = " %" if indicateur == INDICATEURS[1] else " ans"
    return formatage.decimal(valeur) + suffixe


def creer_classement(par_departement: pd.DataFrame, geojson: dict, indicateur: str) -> html.Table:
    """La liste qui accompagne la carte : les départements en tête pour l'indicateur."""
    noms = geographie.noms_departements(geojson)
    tete = par_departement.sort_values("valeur", ascending=False).head(NOMBRE_LIGNES)
    lignes = [
        html.Tr(
            [
                html.Td(noms.get(code, code)),
                html.Td(code, className="num muted"),
                html.Td(valeur_affichee(valeur, indicateur), className="num"),
            ]
        )
        for code, valeur in zip(tete["departement"], tete["valeur"], strict=True)
    ]
    entete = html.Tr(
        [
            html.Th("Département"),
            html.Th("Code", className="num"),
            html.Th("Valeur", className="num"),
        ]
    )
    return html.Table([html.Thead(entete), html.Tbody(lignes)], className="tableau")


def layout() -> html.Div:
    """Construit la page : filtres, choix de l'indicateur, carte et classement."""
    contenu: list = [
        html.Div(
            [
                html.H1("Carte des défaillances"),
                html.P(
                    "Où les sociétés font-elles défaut ? Survolez un département pour le détail.",
                    className="constat",
                ),
            ]
        )
    ]
    if not database.table_existe(NOM_TABLE_CLEANED, config.CHEMIN_BASE):
        contenu.append(html.P(MESSAGE_SANS_DONNEES, className="avis"))
        return html.Div(contenu)
    if not geographie.chemin_geojson().exists():
        contenu.append(html.P(MESSAGE_SANS_CONTOURS, className="avis"))
        return html.Div(contenu)
    choix = dcc.RadioItems(
        id=ID_INDICATEUR,
        options=list(INDICATEURS),
        value=INDICATEURS[0],
        className="choix-indicateur",
    )
    contenu.extend(
        [
            creer_barre_filtres(),
            html.Div(
                [
                    html.Section(
                        [
                            html.H2("Indicateur par département"),
                            choix,
                            dcc.Loading(
                                dcc.Graph(
                                    id=ID_GRAPHIQUE,
                                    config={"displayModeBar": False},
                                    className="graphique",
                                ),
                                color=TEINTE,
                            ),
                        ],
                        className="carte-bloc col-8",
                    ),
                    html.Section(
                        [
                            html.H2("En tête"),
                            html.P(
                                "Le nombre brut suit aussi le nombre de sociétés installées : "
                                "la part de liquidations et l'âge médian se comparent mieux.",
                                className="note",
                            ),
                            html.Div(id=ID_CLASSEMENT),
                        ],
                        className="carte-bloc col-4",
                    ),
                ],
                className="grille",
            ),
        ]
    )
    return html.Div(contenu, style={"display": "flex", "flexDirection": "column", "gap": "20px"})


@callback(
    Output(ID_GRAPHIQUE, "figure"),
    Output(ID_CLASSEMENT, "children"),
    Input(ID_FILTRE_ANNEES, "value"),
    Input(ID_FILTRE_PROCEDURES, "value"),
    Input(ID_FILTRE_REGIONS, "value"),
    Input(ID_INDICATEUR, "value"),
)
def mettre_a_jour_carte(
    annees: list[int], procedures: list[str], regions: list[str], indicateur: str
) -> tuple[go.Figure, html.Table | html.P]:
    """Redessine la carte et le classement à chaque changement de filtre ou d'indicateur."""
    cleaned = cache.charger_table(NOM_TABLE_CLEANED, config.CHEMIN_BASE)
    filtrees = filtrage.appliquer_filtres(cleaned, annees, procedures, regions)
    if filtrees.empty:
        message = html.P("Aucune défaillance pour ces filtres.", className="note")
        return figure_vide(), message
    geojson = geographie.charger_geojson(geographie.chemin_geojson())
    par_departement = calculer_par_departement(filtrees, indicateur)
    return (
        creer_carte(par_departement, geojson, indicateur),
        creer_classement(par_departement, geojson, indicateur),
    )

"""Page Finances : le chiffre d'affaires des sociétés défaillantes comparé à celui des saines."""

import dash
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, callback, dcc, html

import config
from src.utils import cache, database, finances, formatage
from src.utils.figures import NEUTRE, TEINTE, appliquer_style, figure_vide
from src.utils.nettoyage_sirene import SECTIONS_NAF

dash.register_page(__name__, path="/finances", name="Finances", order=30)

ID_SECTEUR = "finances-secteur"
ID_GRAPHIQUE = "finances-graphique"
ID_TABLEAU = "finances-tableau"
ID_CONSTAT = "finances-constat"
SEUIL_GRAND_CA = 10_000_000
EFFECTIF_MINIMUM = 30
COULEURS_GROUPES = {"Défaillantes": TEINTE, "Saines": NEUTRE}
GRADUATIONS = {3: "1 k€", 4: "10 k€", 5: "100 k€", 6: "1 M€", 7: "10 M€", 8: "100 M€"}
LIGNES_STATISTIQUES = (
    ("effectif", "Sociétés"),
    ("q1", "Premier quartile"),
    ("mediane", "Médiane"),
    ("q3", "Troisième quartile"),
    ("moyenne", "Moyenne"),
)
MESSAGE_SANS_DONNEES = (
    "Les données ne sont pas encore disponibles : lancez get_data.py puis clean_data.py."
)
MESSAGE_TROP_PEU = "Trop peu de sociétés dans ce secteur pour comparer les deux groupes."


def filtrer_secteur(table: pd.DataFrame, secteur: str | None) -> pd.DataFrame:
    """Garde les sociétés du secteur choisi ; aucun secteur choisi = tous les secteurs."""
    if not secteur:
        return table
    return table.loc[table["section_naf"] == secteur]


def assez_de_societes(table: pd.DataFrame) -> bool:
    """Vrai si chaque groupe (saines, défaillantes) compte assez de CA positifs pour comparer."""
    effectifs = finances.preparer_ca(table)["groupe"].value_counts()
    return all(effectifs.get(groupe, 0) >= EFFECTIF_MINIMUM for groupe in COULEURS_GROUPES)


def constat(table: pd.DataFrame) -> str:
    """La phrase sous le titre : les médianes, puis la part des grandes sociétés par groupe."""
    donnees = finances.preparer_ca(table)
    medianes = donnees.groupby("groupe")["chiffre_d_affaires"].median()
    grandes = (donnees["chiffre_d_affaires"] >= SEUIL_GRAND_CA).groupby(donnees["groupe"]).mean()
    return (
        f"La moitié des défaillantes réalisaient moins de "
        f"{formatage.entier(medianes['Défaillantes'])} € de chiffre d'affaires, contre "
        f"{formatage.entier(medianes['Saines'])} € pour les saines : l'écart se joue aux extrêmes, "
        f"{formatage.pourcentage(grandes['Saines'], 1)} des saines dépassent 10 M€, contre "
        f"{formatage.pourcentage(grandes['Défaillantes'], 1)} des défaillantes."
    )


def creer_histogramme(histo: pd.DataFrame) -> go.Figure:
    """Barres côte à côte : la part de chaque groupe dans chaque tranche de CA (échelle log).

    L'axe horizontal est en log10 du CA : chaque tranche a la même largeur, et les
    graduations affichent les montants en euros (1 k€, 10 k€… 100 M€).
    """
    centres = np.log10(histo["debut"].to_numpy()) + finances.PAS_LOG / 2
    tranches = [
        f"{formatage.entier(debut)} à {formatage.entier(fin)} €"
        for debut, fin in zip(histo["debut"], histo["fin"], strict=True)
    ]
    figure = go.Figure(
        [
            go.Bar(
                x=centres,
                y=histo[f"part_{groupe.lower()}"] * 100,
                name=groupe,
                marker={"color": couleur},
                customdata=tranches,
                hovertemplate=f"%{{customdata}} : %{{y:.1f}} % des {groupe.lower()}<extra></extra>",
            )
            for groupe, couleur in COULEURS_GROUPES.items()
        ]
    )
    appliquer_style(figure)
    figure.update_layout(barmode="group", bargap=0.15, bargroupgap=0)
    figure.update_xaxes(
        range=[finances.LOG_MIN - 0.1, finances.LOG_MAX + 0.1],
        tickvals=list(GRADUATIONS),
        ticktext=list(GRADUATIONS.values()),
        title={"text": "Chiffre d'affaires du dernier exercice"},
    )
    figure.update_yaxes(ticksuffix=" %", rangemode="tozero")
    return figure


def tableau_statistiques(stats: pd.DataFrame) -> html.Table:
    """Tableau des statistiques du CA : une ligne par indicateur, une colonne par groupe."""
    groupes = list(COULEURS_GROUPES)
    valeurs = stats.to_dict(orient="index")
    entete = html.Tr(
        [html.Th("Chiffre d'affaires")] + [html.Th(g, className="num") for g in groupes]
    )
    lignes = [
        html.Tr(
            [html.Td(libelle)]
            + [
                html.Td(
                    formatage.entier(valeurs[groupe][colonne])
                    + ("" if colonne == "effectif" else " €"),
                    className="num",
                )
                for groupe in groupes
            ]
        )
        for colonne, libelle in LIGNES_STATISTIQUES
    ]
    return html.Table([html.Thead(entete), html.Tbody(lignes)], className="tableau")


def options_secteurs(table: pd.DataFrame) -> list[dict[str, str]]:
    """Les secteurs présents dans la table, avec leur libellé, du plus au moins représenté."""
    libelles = {lettre: libelle for lettre, _, _, libelle in SECTIONS_NAF}
    presents = table["section_naf"].value_counts().index
    return [{"label": libelles.get(lettre, lettre), "value": lettre} for lettre in presents]


def layout() -> html.Div:
    """Construit la page : choix du secteur, histogramme du CA et statistiques par groupe."""
    entete = html.Div([html.H1("Chiffre d'affaires"), html.P(id=ID_CONSTAT, className="constat")])
    if not database.table_existe(finances.NOM_TABLE_SCORING, config.CHEMIN_BASE):
        return html.Div(
            [html.H1("Chiffre d'affaires"), html.P(MESSAGE_SANS_DONNEES, className="avis")]
        )
    table = cache.charger_table(finances.NOM_TABLE_SCORING, config.CHEMIN_BASE)
    filtre = html.Div(
        [
            html.Div(
                [
                    html.Label("Secteur", htmlFor=ID_SECTEUR),
                    dcc.Dropdown(
                        id=ID_SECTEUR,
                        options=options_secteurs(table),
                        value=None,
                        placeholder="Tous les secteurs",
                    ),
                ]
            )
        ],
        className="filtres",
    )
    return html.Div(
        [
            entete,
            filtre,
            html.Div(
                [
                    html.Section(
                        [
                            html.H2("Répartition du chiffre d'affaires"),
                            html.P(
                                "Part de chaque groupe par tranche de CA, sur une échelle"
                                " logarithmique : chaque tranche est 1,8 fois plus large que"
                                " la précédente.",
                                className="note",
                            ),
                            dcc.Graph(
                                id=ID_GRAPHIQUE,
                                config={"displayModeBar": False},
                                className="graphique",
                            ),
                        ],
                        className="carte-bloc col-8",
                    ),
                    html.Section(
                        [
                            html.H2("Statistiques par groupe"),
                            html.P(
                                "En euros, CA du dernier exercice publié. La moyenne est tirée"
                                " vers le haut par quelques grandes sociétés : la médiane est"
                                " plus fiable.",
                                className="note",
                            ),
                            html.Div(id=ID_TABLEAU),
                        ],
                        className="carte-bloc col-4",
                    ),
                ],
                className="grille",
            ),
        ],
        style={"display": "flex", "flexDirection": "column", "gap": "20px"},
    )


@callback(
    Output(ID_GRAPHIQUE, "figure"),
    Output(ID_TABLEAU, "children"),
    Output(ID_CONSTAT, "children"),
    Input(ID_SECTEUR, "value"),
)
def mettre_a_jour_finances(secteur: str | None) -> tuple[go.Figure, html.Table | html.P, str]:
    """Recalcule l'histogramme, les statistiques et le constat pour le secteur choisi."""
    table = cache.charger_table(finances.NOM_TABLE_SCORING, config.CHEMIN_BASE)
    choisies = filtrer_secteur(table, secteur)
    if not assez_de_societes(choisies):
        return figure_vide(MESSAGE_TROP_PEU), html.P(MESSAGE_TROP_PEU, className="note"), ""
    return (
        creer_histogramme(finances.histogramme_ca(choisies)),
        tableau_statistiques(finances.statistiques_ca(choisies)),
        constat(choisies),
    )

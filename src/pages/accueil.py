"""Page d'accueil : combien de sociétés font défaut, quand et où (2019-2025)."""

from typing import Any

import dash
import pandas as pd
import plotly.graph_objects as go
from dash import dcc, html

import config
from src.utils import cache, database, formatage, geographie
from src.utils.figures import NEUTRE, TEINTE, appliquer_style
from src.utils.nettoyage_sirene import SECTIONS_NAF

dash.register_page(__name__, path="/", name="Accueil", order=0)

NOM_TABLE_CLEANED = "cleaned"
NOMBRE_DEPARTEMENTS = 6
NOM_CHIFFRES: dict[str, Any] = {"aria-label": "Chiffres clés"}
MESSAGE_SANS_DONNEES = (
    "Les données ne sont pas encore disponibles : lancez get_data.py puis clean_data.py."
)


def calculer_chiffres_cles(cleaned: pd.DataFrame) -> list[tuple[str, str, str]]:
    """Les quatre chiffres clés : (libellé, valeur mise en forme, unité ou précision)."""
    libelles = {lettre: libelle for lettre, _, _, libelle in SECTIONS_NAF}
    part_liquidations = (cleaned["procedure"] == "Liquidation judiciaire").mean()
    sections = cleaned["section_naf"].value_counts()
    return [
        ("Ouvertures de procédure", formatage.entier(len(cleaned)), "sociétés"),
        ("Part de liquidations", formatage.pourcentage(part_liquidations), "des ouvertures"),
        ("Âge médian au jugement", formatage.decimal(cleaned["age_defaillance"].median()), "ans"),
        (
            "Secteur le plus touché",
            libelles.get(sections.index[0], sections.index[0]),
            f"{formatage.pourcentage(sections.iloc[0] / len(cleaned))} des ouvertures",
        ),
    ]


def ouvertures_par_annee(cleaned: pd.DataFrame) -> pd.Series:
    """Nombre d'ouvertures de procédure par année, dans l'ordre chronologique."""
    return cleaned["annee"].value_counts().sort_index()


def constat(par_annee: pd.Series) -> str:
    """La phrase sous le titre : l'année record et son écart avec l'année d'avant."""
    record = int(par_annee.index.to_list()[int(par_annee.argmax())])
    phrase = (
        f"{record} est l'année record de la période : "
        f"{formatage.entier(par_annee.max())} ouvertures de procédure"
    )
    if record - 1 in par_annee.index:
        evolution = par_annee[record] / par_annee[record - 1] - 1
        signe = "+" if evolution >= 0 else "−"
        phrase += f", {signe}{formatage.pourcentage(abs(evolution), 1)} sur {record - 1}"
    return phrase + "."


def creer_graphique_annees(par_annee: pd.Series) -> go.Figure:
    """Barres par année : grises, l'année record dans la teinte du projet, annotée."""
    annees = [str(annee) for annee in par_annee.index]
    position_record = list(par_annee.index).index(par_annee.idxmax())
    figure = go.Figure(
        go.Bar(
            x=annees,
            y=par_annee.to_list(),
            marker={
                "color": [TEINTE if i == position_record else NEUTRE for i in range(len(annees))]
            },
            hovertemplate="%{x} : %{y:,} ouvertures<extra></extra>",
        )
    )
    appliquer_style(figure)
    figure.update_xaxes(type="category")
    figure.update_yaxes(rangemode="tozero")
    figure.add_annotation(
        x=position_record,
        y=par_annee.max(),
        text=f"Record : {formatage.entier(par_annee.max())}",
        showarrow=False,
        yshift=12,
    )
    return figure


def tableau_departements(cleaned: pd.DataFrame) -> html.Table:
    """Les départements qui comptent le plus d'ouvertures, avec leur part du total."""
    comptes = cleaned["departement"].value_counts().head(NOMBRE_DEPARTEMENTS)
    chemin = geographie.chemin_geojson()
    noms = (
        geographie.noms_departements(geographie.charger_geojson(chemin)) if chemin.exists() else {}
    )
    lignes = [
        html.Tr(
            [
                html.Td(noms.get(str(code), str(code))),
                html.Td(str(code), className="num"),
                html.Td(formatage.entier(nombre), className="num"),
                html.Td(formatage.pourcentage(nombre / len(cleaned), 1), className="num muted"),
            ]
        )
        for code, nombre in comptes.items()
    ]
    entete = html.Tr(
        [
            html.Th("Département"),
            html.Th("Code", className="num"),
            html.Th("Ouvertures", className="num"),
            html.Th("Part", className="num"),
        ]
    )
    return html.Table([html.Thead(entete), html.Tbody(lignes)], className="tableau")


def creer_chiffre(libelle: str, valeur: str, unite: str) -> html.Div:
    """Une colonne de la carte des chiffres clés : libellé, valeur, unité."""
    return html.Div(
        [
            html.Div(libelle, className="libelle"),
            html.Div(valeur, className="valeur"),
            html.Div(unite, className="unite"),
        ],
        className="chiffre",
    )


def layout() -> html.Div:
    """Construit la page à chaque visite, à partir de la table cleaned (mise en cache)."""
    titre = html.H1("Défaillances de sociétés en France")
    if not database.table_existe(NOM_TABLE_CLEANED, config.CHEMIN_BASE):
        return html.Div([titre, html.P(MESSAGE_SANS_DONNEES, className="avis")])
    cleaned = cache.charger_table(NOM_TABLE_CLEANED, config.CHEMIN_BASE)
    par_annee = ouvertures_par_annee(cleaned)
    chiffres = [creer_chiffre(*chiffre) for chiffre in calculer_chiffres_cles(cleaned)]
    total = formatage.entier(len(cleaned))
    return html.Div(
        [
            html.Div(
                [
                    html.Div([titre, html.P(constat(par_annee), className="constat")]),
                    dcc.Link("Explorer la carte", href="/carte", className="bouton"),
                ],
                className="ligne-titre",
            ),
            html.Div(
                [
                    html.Section(
                        chiffres,
                        className="carte-bloc chiffres col-12",
                        **NOM_CHIFFRES,
                    ),
                    html.Section(
                        [
                            html.H2("Ouvertures de procédure par année"),
                            html.P(
                                "Le creux des années d'aides publiques (2020-2021), puis un"
                                " rattrapage au-dessus du niveau de 2019.",
                                className="note",
                            ),
                            dcc.Graph(
                                figure=creer_graphique_annees(par_annee),
                                config={"displayModeBar": False},
                                className="graphique",
                            ),
                        ],
                        className="carte-bloc col-8",
                    ),
                    html.Section(
                        [
                            html.H2("Départements les plus touchés"),
                            html.P(f"Part du total de {total} ouvertures", className="note"),
                            tableau_departements(cleaned),
                        ],
                        className="carte-bloc col-4",
                    ),
                ],
                className="grille",
            ),
        ],
        style={"display": "flex", "flexDirection": "column", "gap": "20px"},
    )

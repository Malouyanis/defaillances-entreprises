"""Page Évolution : les ouvertures de procédure mois par mois et année par année (2019-2025)."""

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
from src.utils import cache, database, filtrage, formatage
from src.utils.figures import (
    COULEUR_TEXTE_SECONDAIRE,
    COULEURS_PROCEDURES,
    appliquer_style,
    figure_vide,
)

dash.register_page(__name__, path="/evolution", name="Évolution", order=20)

NOM_TABLE_CLEANED = "cleaned"
COULEUR_BANDE = "#eef0f3"
CHIFFRES_ALIGNES = {"fontVariantNumeric": "tabular-nums"}
ID_GRAPHIQUE = "evolution-graphique"
ID_TABLEAU = "evolution-tableau"
ID_CONSTAT = "evolution-constat"
EVENEMENTS = ((("2020-03", "2020-05"), "1er confinement"),)
MOIS = (
    "janv.",
    "févr.",
    "mars",
    "avr.",
    "mai",
    "juin",
    "juil.",
    "août",
    "sept.",
    "oct.",
    "nov.",
    "déc.",
)
MESSAGE_SANS_DONNEES = (
    "Les données ne sont pas encore disponibles : lancez get_data.py puis clean_data.py."
)


def ouvertures_par_mois(defaillances: pd.DataFrame) -> pd.DataFrame:
    """Ouvertures par mois (AAAA-MM) et par procédure ; 0 pour une procédure absente ce mois-là."""
    mois = defaillances["date_jugement"].str[:7].rename("mois")
    table = defaillances.groupby([mois, defaillances["procedure"]]).size().unstack(fill_value=0)
    return table.sort_index()


def ouvertures_par_annee(defaillances: pd.DataFrame) -> pd.DataFrame:
    """Ouvertures par année et évolution par rapport à l'année précédente (part, ex. 0,18)."""
    comptes = defaillances["annee"].value_counts().sort_index()
    return pd.DataFrame({"ouvertures": comptes, "evolution": comptes.pct_change()})


def libelle_mois(mois: str) -> str:
    """« 2020-04 » → « avr. 2020 »."""
    annee, numero = mois.split("-")
    return f"{MOIS[int(numero) - 1]} {annee}"


def constat(par_annee: pd.DataFrame) -> str:
    """La phrase sous le titre : l'année la plus basse, la plus haute et l'écart sur la période."""
    comptes = par_annee["ouvertures"]
    debut, fin = int(comptes.index.min()), int(comptes.index.max())
    if debut == fin:
        return f"{debut} : {formatage.entier(comptes.iloc[0])} ouvertures de procédure."
    annees = comptes.index.to_list()
    bas, haut = int(annees[int(comptes.argmin())]), int(annees[int(comptes.argmax())])
    ecart = comptes[fin] / comptes[debut] - 1
    signe = "+" if ecart >= 0 else "−"
    return (
        f"L'année la plus basse est {bas} ({formatage.entier(comptes[bas])} ouvertures), la plus"
        f" haute {haut} ({formatage.entier(comptes[haut])}) ; {fin} est à {signe}"
        f"{formatage.pourcentage(abs(ecart), 1)} de {debut}."
    )


def creer_graphique_mois(par_mois: pd.DataFrame) -> go.Figure:
    """Une ligne par procédure, toujours dans sa couleur, et une bande grise sur les événements.

    La légende garde le premier mot de la procédure (« Liquidation ») pour tenir sur une ligne,
    même sur un téléphone.
    """
    mois = list(par_mois.index)
    figure = go.Figure(
        [
            go.Scatter(
                x=mois,
                y=par_mois[procedure],
                name=procedure.split()[0],
                mode="lines",
                line={"color": couleur, "width": 2},
                customdata=[libelle_mois(m) for m in mois],
                hovertemplate=f"%{{customdata}} : %{{y:,}} ({procedure.lower()})<extra></extra>",
            )
            for procedure, couleur in COULEURS_PROCEDURES.items()
            if procedure in par_mois
        ]
    )
    appliquer_style(figure)
    figure.update_layout(legend={"yanchor": "bottom", "y": 1.02, "itemwidth": 30})
    figure.update_xaxes(
        type="category",
        tickvals=[m for m in mois if m.endswith("-01")],
        ticktext=[m[:4] for m in mois if m.endswith("-01")],
    )
    figure.update_yaxes(rangemode="tozero")
    for (premier, dernier), texte in EVENEMENTS:
        pendant = [m for m in mois if premier <= m <= dernier]
        if pendant:
            figure.add_vrect(
                x0=mois.index(pendant[0]) - 0.5,
                x1=mois.index(pendant[-1]) + 0.5,
                fillcolor=COULEUR_BANDE,
                line_width=0,
                layer="below",
                annotation_text=texte,
                annotation_position="inside top left",
                annotation_font={"size": 12, "color": COULEUR_TEXTE_SECONDAIRE},
            )
    return figure


def tableau_annees(par_annee: pd.DataFrame) -> html.Table:
    """Tableau année par année : ouvertures et évolution sur l'année précédente."""
    lignes = []
    for annee, ligne in par_annee.iterrows():
        evolution = ligne["evolution"]
        if pd.isna(evolution):
            texte, classe = "—", "num muted"
        else:
            signe = "+" if evolution >= 0 else "−"
            texte, classe = f"{signe}{formatage.pourcentage(abs(evolution), 1)}", "num"
        lignes.append(
            html.Tr(
                [
                    html.Td(str(annee), style=CHIFFRES_ALIGNES),
                    html.Td(formatage.entier(ligne["ouvertures"]), className="num"),
                    html.Td(texte, className=classe),
                ]
            )
        )
    entete = html.Tr(
        [
            html.Th("Année"),
            html.Th("Ouvertures", className="num"),
            html.Th("Sur un an", className="num"),
        ]
    )
    return html.Table([html.Thead(entete), html.Tbody(lignes)], className="tableau")


def layout() -> html.Div:
    """Construit la page : filtres, courbes mensuelles par procédure et tableau par année."""
    titre = html.H1("Évolution des défaillances")
    if not database.table_existe(NOM_TABLE_CLEANED, config.CHEMIN_BASE):
        return html.Div([titre, html.P(MESSAGE_SANS_DONNEES, className="avis")])
    return html.Div(
        [
            html.Div([titre, html.P(id=ID_CONSTAT, className="constat")]),
            creer_barre_filtres(),
            html.Div(
                [
                    html.Section(
                        [
                            html.H2("Ouvertures de procédure par mois"),
                            html.P(
                                "Chaque mois d'août plonge : les tribunaux tournent au ralenti"
                                " pendant les vacances judiciaires.",
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
                            html.H2("Par année"),
                            html.P("Selon les filtres choisis", className="note"),
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
    Input(ID_FILTRE_ANNEES, "value"),
    Input(ID_FILTRE_PROCEDURES, "value"),
    Input(ID_FILTRE_REGIONS, "value"),
)
def mettre_a_jour_evolution(
    annees: list[int], procedures: list[str], regions: list[str]
) -> tuple[go.Figure, html.Table | html.P, str]:
    """Recalcule les courbes, le tableau et le constat à chaque changement de filtre."""
    cleaned = cache.charger_table(NOM_TABLE_CLEANED, config.CHEMIN_BASE)
    filtrees = filtrage.appliquer_filtres(cleaned, annees, procedures, regions)
    if filtrees.empty:
        return figure_vide(), html.P("Aucune défaillance pour ces filtres.", className="note"), ""
    par_annee = ouvertures_par_annee(filtrees)
    return (
        creer_graphique_mois(ouvertures_par_mois(filtrees)),
        tableau_annees(par_annee),
        constat(par_annee),
    )

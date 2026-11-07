"""Page Scoring : le modèle de risque, la note de A à E et ce qui pèse dans le score."""

from dataclasses import dataclass
from functools import cache
from pathlib import Path

import dash
import pandas as pd
import plotly.graph_objects as go
from dash import html

import config
from src.components.chiffres import creer_carte_chiffres
from src.components.graphique import creer_graphique
from src.utils import database, formatage, notation, scoring
from src.utils.figures import NEUTRE_FONCE, TEINTE, appliquer_style

dash.register_page(__name__, path="/scoring", name="Scoring", order=40)

NOMBRE_COEFFICIENTS = 8
LIBELLES_VARIABLES = {
    "ratio_de_liquidite": "Liquidité",
    "autonomie_financiere": "Autonomie financière",
    "fonds_propres_negatifs": "Fonds propres négatifs",
    "endettement_fonds_propres_positifs": "Endettement",
    "marge_ebe": "Marge d'EBE",
    "resultat_negatif": "Résultat négatif",
    "capacite_de_remboursement": "Capacité de remboursement",
    "age_defaillance": "Âge de la société",
    "missingindicator_marge_ebe": "Marge d'EBE non publiée",
    "missingindicator_resultat_negatif": "Résultat non publié",
    "missingindicator_capacite_de_remboursement": "Capacité non publiée",
}
MESSAGE_SANS_DONNEES = (
    "Les données ne sont pas encore disponibles : lancez get_data.py puis clean_data.py."
)


@dataclass(frozen=True)
class Resultats:
    """Ce que la page affiche : grille de notation, AUC, coefficients et effectif du test."""

    grille: pd.DataFrame
    auc_entrainement: float
    auc_test: float
    coefficients: pd.DataFrame
    societes_test: int


@cache
def calculer_resultats(chemin: Path) -> Resultats:
    """Entraîne le modèle UNE SEULE FOIS et garde les résultats en mémoire (functools.cache).

    L'entraînement prend quelques secondes : le refaire à chaque visite rendrait la page lente.
    """
    table = scoring.ajouter_variables(database.lire_table(scoring.NOM_TABLE_SCORING, chemin))
    entrainement, test = scoring.decouper_par_annee(table)
    modele = scoring.entrainer(entrainement)
    return Resultats(
        grille=notation.noter_test(modele, entrainement, test),
        auc_entrainement=scoring.auc(modele, entrainement),
        auc_test=scoring.auc(modele, test),
        coefficients=scoring.coefficients(modele),
        societes_test=len(test),
    )


def coefficients_financiers(coefficients: pd.DataFrame) -> pd.DataFrame:
    """Les variables financières les plus influentes (sans les secteurs), avec leur libellé."""
    financiers = coefficients.loc[~coefficients["variable"].str.startswith("section_naf_")]
    tete = financiers.head(NOMBRE_COEFFICIENTS)
    return tete.assign(libelle=tete["variable"].map(LIBELLES_VARIABLES).fillna(tete["variable"]))


def constat(resultats: Resultats) -> str:
    """La phrase sous le titre : le taux de défaut observé en note A et en note E."""
    taux = resultats.grille["taux_defaut_observe"]
    return (
        f"Sur 2024-2025, des années que le modèle n'a jamais vues, "
        f"{formatage.pourcentage(taux['E'])} des sociétés notées E ont fait défaut, contre "
        f"{formatage.pourcentage(taux['A'])} des sociétés notées A."
    )


def creer_graphique_notes(grille: pd.DataFrame) -> go.Figure:
    """Barres du taux de défaut observé par note, de A à E, avec la valeur au-dessus."""
    taux = grille["taux_defaut_observe"] * 100
    figure = go.Figure(
        go.Bar(
            x=list(grille.index.astype(str)),
            y=taux,
            marker={"color": TEINTE},
            text=[formatage.pourcentage(t / 100) for t in taux],
            textposition="outside",
            cliponaxis=False,
            hovertemplate="Note %{x} : %{y:.1f} % de défaillantes<extra></extra>",
        )
    )
    appliquer_style(figure)
    figure.update_xaxes(type="category")
    figure.update_yaxes(ticksuffix=" %", range=[0, 100])
    return figure


def creer_graphique_coefficients(financiers: pd.DataFrame) -> go.Figure:
    """Barres horizontales : en bleu ce qui augmente le risque, en gris ce qui le diminue."""
    ordre = financiers.iloc[::-1]
    figure = go.Figure(
        go.Bar(
            x=ordre["coefficient"],
            y=ordre["libelle"],
            orientation="h",
            marker={"color": [TEINTE if c > 0 else NEUTRE_FONCE for c in ordre["coefficient"]]},
            hovertemplate="%{y} : %{x:.3f}<extra></extra>",
        )
    )
    appliquer_style(figure)
    figure.update_xaxes(showgrid=True, zeroline=True, zerolinecolor=NEUTRE_FONCE, tickformat=".1f")
    figure.update_yaxes(showgrid=False)
    return figure


def tableau_grille(grille: pd.DataFrame) -> html.Table:
    """La grille de notation : effectif, part, défaut observé et probabilité recalée par note."""
    entete = html.Tr(
        [
            html.Th("Note"),
            html.Th("Sociétés", className="num"),
            html.Th("Part", className="num"),
            html.Th("Défaut observé", className="num"),
            html.Th("Probabilité à 1 an", className="num"),
        ]
    )
    lignes = [
        html.Tr(
            [
                html.Td(str(note)),
                html.Td(formatage.entier(ligne["effectif"]), className="num"),
                html.Td(formatage.pourcentage(ligne["part"]), className="num muted"),
                html.Td(formatage.pourcentage(ligne["taux_defaut_observe"], 1), className="num"),
                html.Td(formatage.pourcentage(ligne["pd_recalee_moyenne"], 2), className="num"),
            ]
        )
        for note, ligne in grille.iterrows()
    ]
    return html.Table([html.Thead(entete), html.Tbody(lignes)], className="tableau")


def description_notes(grille: pd.DataFrame) -> str:
    """Le graphique des notes en mots, pour les lecteurs d'écran."""
    valeurs = " ; ".join(
        f"note {note} : {formatage.pourcentage(taux, 1)}"
        for note, taux in grille["taux_defaut_observe"].items()
    )
    return f"Taux de défaut observé par note. {valeurs}."


def description_coefficients(financiers: pd.DataFrame) -> str:
    """Le graphique des coefficients en mots, pour les lecteurs d'écran."""
    valeurs = " ; ".join(
        f"{libelle} : {formatage.decimal(coefficient, 2)}"
        for libelle, coefficient in zip(
            financiers["libelle"], financiers["coefficient"], strict=True
        )
    )
    return f"Coefficients de la régression, positif = plus de risque. {valeurs}."


def layout() -> html.Div:
    """Construit la page à partir des résultats mémorisés (le modèle n'est entraîné qu'une fois)."""
    titre = html.H1("Scoring du risque de défaillance")
    if not database.table_existe(scoring.NOM_TABLE_SCORING, config.CHEMIN_BASE):
        return html.Div([titre, html.P(MESSAGE_SANS_DONNEES, className="avis")])
    resultats = calculer_resultats(config.CHEMIN_BASE)
    chiffres = [
        ("AUC sur 2024-2025", formatage.decimal(resultats.auc_test, 3), "années de test"),
        ("AUC sur 2019-2023", formatage.decimal(resultats.auc_entrainement, 3), "entraînement"),
        ("Sociétés notées", formatage.entier(resultats.societes_test), "en 2024-2025"),
        (
            "Taux de référence",
            formatage.pourcentage(notation.TAUX_DEFAUT_REFERENCE),
            "par an, hypothèse",
        ),
    ]
    financiers = coefficients_financiers(resultats.coefficients)
    return html.Div(
        [
            html.Div([titre, html.P(constat(resultats), className="constat")]),
            html.Div(
                [
                    creer_carte_chiffres(chiffres, "Qualité du modèle"),
                    html.Section(
                        [
                            html.H2("Taux de défaut observé par note"),
                            html.P(
                                "De A (risque le plus faible) à E : le taux doit monter de note en"
                                " note pour que la notation soit utile.",
                                className="note",
                            ),
                            creer_graphique(
                                description_notes(resultats.grille),
                                figure=creer_graphique_notes(resultats.grille),
                            ),
                        ],
                        className="carte-bloc col-6",
                    ),
                    html.Section(
                        [
                            html.H2("Ce qui pèse dans le score"),
                            html.P(
                                "Coefficients de la régression, variables à la même échelle : en"
                                " bleu ce qui augmente le risque, en gris ce qui le diminue.",
                                className="note",
                            ),
                            creer_graphique(
                                description_coefficients(financiers),
                                figure=creer_graphique_coefficients(financiers),
                            ),
                        ],
                        className="carte-bloc col-6",
                    ),
                    html.Section(
                        [
                            html.H2("Grille de notation"),
                            html.P(notation.EXPLICATION_TAUX, className="note"),
                            tableau_grille(resultats.grille),
                        ],
                        className="carte-bloc col-12",
                    ),
                ],
                className="grille",
            ),
        ],
        style={"display": "flex", "flexDirection": "column", "gap": "20px"},
    )

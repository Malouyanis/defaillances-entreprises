"""Page d'accueil : le sujet en une phrase et les chiffres clés des défaillances 2019-2025."""

import dash
import dash_bootstrap_components as dbc
import pandas as pd
from dash import dcc, html

import config
from src.utils import cache, database
from src.utils.nettoyage_sirene import SECTIONS_NAF

dash.register_page(__name__, path="/", name="Accueil", order=0)

NOM_TABLE_CLEANED = "cleaned"
INTRODUCTION = (
    "Ce tableau de bord étudie les défaillances d'entreprises en France métropolitaine"
    " de 2019 à 2025 : combien, où, dans quels secteurs, et quels signaux financiers"
    " les annonçaient dans les derniers comptes publiés."
)
MESSAGE_SANS_DONNEES = (
    "Les données ne sont pas encore disponibles : lancez get_data.py puis clean_data.py."
)


def calculer_chiffres_cles(cleaned: pd.DataFrame) -> dict[str, str]:
    """Calcule les chiffres clés affichés sur l'accueil, déjà mis en forme en texte."""
    libelles = {lettre: libelle for lettre, _, _, libelle in SECTIONS_NAF}
    part_liquidations = (cleaned["procedure"] == "Liquidation judiciaire").mean()
    section_principale = cleaned["section_naf"].mode().iloc[0]
    return {
        "Défaillances de sociétés": f"{len(cleaned):,}".replace(",", " "),
        "Part de liquidations": f"{round(part_liquidations * 100)} %",
        "Âge médian à la défaillance": f"{cleaned['age_defaillance'].median():.1f} ans".replace(
            ".", ","
        ),
        "Secteur le plus touché": libelles.get(section_principale, section_principale),
    }


def creer_carte(titre: str, valeur: str) -> dbc.Col:
    """Crée une carte qui met en valeur un chiffre clé."""
    return dbc.Col(
        dbc.Card(
            dbc.CardBody(
                [
                    html.P(titre, className="text-muted small mb-1"),
                    html.H3(valeur, className="mb-0"),
                ]
            )
        ),
        md=3,
        className="mb-3",
    )


def creer_liens() -> html.Ul:
    """Liste des autres pages du tableau de bord, construite depuis le registre de Dash."""
    pages = sorted(dash.page_registry.values(), key=lambda page: page["order"])
    return html.Ul(
        [
            html.Li(dcc.Link(page["name"], href=page["relative_path"]))
            for page in pages
            if page["path"] != "/"
        ]
    )


def layout() -> html.Div:
    """Construit la page à chaque visite, à partir de la table cleaned (mise en cache)."""
    contenu: list = [html.H2("Défaillances d'entreprises en France"), html.P(INTRODUCTION)]
    if not database.table_existe(NOM_TABLE_CLEANED, config.CHEMIN_BASE):
        contenu.append(dbc.Alert(MESSAGE_SANS_DONNEES, color="warning"))
        return html.Div(contenu)
    cleaned = cache.charger_table(NOM_TABLE_CLEANED, config.CHEMIN_BASE)
    chiffres = calculer_chiffres_cles(cleaned)
    contenu.append(dbc.Row([creer_carte(titre, valeur) for titre, valeur in chiffres.items()]))
    contenu.extend([html.H4("Explorer", className="h5 mt-3"), creer_liens()])
    return html.Div(contenu)

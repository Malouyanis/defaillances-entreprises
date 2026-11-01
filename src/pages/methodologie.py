"""Page Méthodologie : sources, définitions, choix de nettoyage et limites de l'étude."""

import dash
import dash_bootstrap_components as dbc
from dash import html

dash.register_page(__name__, path="/methodologie", name="Méthodologie", order=90)

SECTIONS = (
    (
        "Sources",
        (
            "BODACC (DILA) : annonces de procédures collectives publiées de 2019 à 2025.",
            "Ratios financiers BCE/INPI (DGE) : comptes annuels déposés par les sociétés.",
            "Répertoire Sirene (INSEE) : date de création, secteur et taille des sociétés.",
            "Toutes les données sont ouvertes, sous Licence Ouverte Etalab 2.0.",
        ),
    ),
    (
        "Ce qu'on appelle une défaillance",
        (
            "L'ouverture d'une procédure collective : liquidation judiciaire, redressement"
            " judiciaire ou sauvegarde, d'après le jugement publié au BODACC.",
            "Une seule défaillance par société : la première ouverture entre 2019 et 2025.",
            "Périmètre : France métropolitaine (Corse comprise), sociétés uniquement ;"
            " les entrepreneurs individuels sont exclus.",
        ),
    ),
    (
        "Choix de nettoyage",
        (
            "Les avis rectificatifs et les annulations sont retirés : ils répètent une annonce.",
            "Une date de jugement absente ou impossible est remplacée par la date de parution.",
            "Seuls les bilans complets et simplifiés sont gardés. Les comptes déposés en mode"
            " confidentiel sont gardés pour leurs ratios de bilan (endettement, liquidité,"
            " autonomie financière) ; leur chiffre d'affaires, leur résultat et leur EBE,"
            " non publiés, sont laissés vides.",
            "Les ratios financiers sont ramenés entre leurs percentiles 1 et 99 pour limiter"
            " l'effet des valeurs extrêmes.",
            "Les comptes d'une défaillante sont ceux du dernier exercice clos avant le jugement,"
            " et au plus deux ans avant.",
        ),
    ),
    (
        "Limites",
        (
            "Une minorité des sociétés défaillantes (environ 15 %) ont des comptes clos dans les"
            " deux ans avant le jugement : l'analyse financière porte sur les sociétés qui"
            " publient leurs comptes (biais de sélection).",
            "Les sociétés saines de comparaison sont des sociétés encore actives aujourd'hui :"
            " elles ont forcément survécu, ce qui rend la comparaison un peu optimiste"
            " (biais du survivant).",
            "Le secteur est déduit du code d'activité ; quelques sociétés anciennes ont encore"
            " un code d'une ancienne nomenclature (NAF rév. 1).",
            "L'âge à la défaillance n'est calculé que si la date de création est plausible.",
        ),
    ),
)


def creer_section(titre: str, points: tuple[str, ...]) -> dbc.Card:
    """Crée une carte avec un titre et une liste de points."""
    return dbc.Card(
        dbc.CardBody([html.H4(titre, className="h5"), html.Ul([html.Li(p) for p in points])]),
        className="mb-3",
    )


layout = html.Div(
    [
        html.H2("Méthodologie"),
        html.P(
            "Comment les données ont été choisies, nettoyées et croisées.",
            className="text-muted",
        ),
        *[creer_section(titre, points) for titre, points in SECTIONS],
    ]
)

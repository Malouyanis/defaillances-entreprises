"""Page Méthodologie : sources, définitions, choix de nettoyage et limites de l'étude."""

import dash
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
        "Modèle de scoring",
        (
            "Une régression logistique estime la probabilité de défaillance d'une société à partir"
            " de ses derniers comptes : liquidité, autonomie financière, fonds propres négatifs,"
            " endettement, marge d'EBE, résultat négatif, capacité de remboursement, âge et"
            " secteur.",
            "Le modèle apprend sur les années 2019 à 2023 et il est jugé sur 2024-2025, des années"
            " qu'il n'a jamais vues, comme une banque qui note avec un modèle construit sur le"
            " passé.",
            "Les effectifs et la catégorie d'entreprise sont exclus : Sirene donne leur état"
            " actuel, mis à jour après la défaillance (fuite d'information).",
            "La qualité du classement est mesurée par l'AUC : 0,5 pour un tirage au hasard,"
            " 1 pour un classement parfait.",
        ),
    ),
    (
        "Notation de A à E",
        (
            "Les seuils entre les notes sont les quintiles des probabilités sur les années"
            " d'entraînement : chaque note y regroupe un cinquième des sociétés.",
            "Le modèle apprend sur un échantillon où près d'une société sur deux fait défaut :"
            " ses probabilités sont recalées sur un taux de défaut annuel de référence de 1 %.",
            "Ce 1 % est une hypothèse d'ordre de grandeur, pas un chiffre officiel : la Banque de"
            " France publie des nombres de défaillances, pas un taux. Il change le niveau des"
            " probabilités, pas l'ordre des notes.",
            "Une notation est utile si le taux de défaut observé augmente de note en note :"
            " c'est vérifié sur 2024-2025.",
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


def creer_section(titre: str, points: tuple[str, ...]) -> html.Section:
    """Crée un bloc avec un titre et une liste de points."""
    return html.Section(
        [html.H2(titre), html.Ul([html.Li(p) for p in points])],
        className="carte-bloc section-texte col-6",
    )


layout = html.Div(
    [
        html.Div(
            [
                html.H1("Méthodologie"),
                html.P(
                    "Comment les données ont été choisies, nettoyées et croisées.",
                    className="constat",
                ),
            ]
        ),
        html.Div(
            [creer_section(titre, points) for titre, points in SECTIONS],
            className="grille",
        ),
    ],
    style={"display": "flex", "flexDirection": "column", "gap": "20px"},
)

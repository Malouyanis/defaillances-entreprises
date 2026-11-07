"""Carte des chiffres clés : une rangée de chiffres séparés par de fins traits verticaux."""

from typing import Any

from dash import html


def creer_chiffre(libelle: str, valeur: str, unite: str) -> html.Div:
    """Une colonne de la carte des chiffres : libellé, valeur en grand, précision dessous."""
    return html.Div(
        [
            html.Div(libelle, className="libelle"),
            html.Div(valeur, className="valeur"),
            html.Div(unite, className="unite"),
        ],
        className="chiffre",
    )


def creer_carte_chiffres(chiffres: list[tuple[str, str, str]], nom: str) -> html.Section:
    """La carte entière, sur toute la largeur ; nom est lu par les lecteurs d'écran."""
    accessibilite: dict[str, Any] = {"aria-label": nom}
    return html.Section(
        [creer_chiffre(*chiffre) for chiffre in chiffres],
        className="carte-bloc chiffres col-12",
        **accessibilite,
    )

"""Pied de page : sources des données et auteurs du projet."""

from dash import html

TEXTE_SOURCES = (
    "Sources : BODACC (DILA), ratios financiers BCE/INPI (DGE), répertoire Sirene (INSEE)"
    " — données ouvertes, Licence Ouverte Etalab."
)
TEXTE_AUTEURS = "Projet data — E4 DSIA, ESIEE Paris — Yanis Malou et Maxime Pierrard"


def creer_footer() -> html.Footer:
    """Crée le pied de page commun à toutes les pages."""
    return html.Footer(
        [
            html.Hr(),
            html.P(TEXTE_SOURCES, className="small text-muted mb-1"),
            html.P(TEXTE_AUTEURS, className="small text-muted"),
        ],
        className="mt-5",
    )
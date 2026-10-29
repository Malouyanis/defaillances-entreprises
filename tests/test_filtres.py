"""Tests de la barre de filtres."""

import config
from src.components import filtres


def test_filtre_annees_couvre_la_periode() -> None:
    """Le curseur va de la première à la dernière année étudiée, tout sélectionné."""
    curseur = filtres.creer_filtre_annees()
    assert curseur.id == filtres.ID_FILTRE_ANNEES
    assert curseur.value == [config.ANNEE_DEBUT, config.ANNEE_FIN]


def test_filtre_procedures_tout_coche() -> None:
    """Les trois procédures sont proposées et cochées au départ."""
    liste = filtres.creer_filtre_procedures()
    assert liste.value == ["Liquidation judiciaire", "Redressement judiciaire", "Sauvegarde"]


def test_barre_filtres_contient_les_trois_filtres() -> None:
    """La barre affiche bien les trois filtres, chacun avec son identifiant."""
    texte = str(filtres.creer_barre_filtres())
    for identifiant in (
        filtres.ID_FILTRE_ANNEES,
        filtres.ID_FILTRE_PROCEDURES,
        filtres.ID_FILTRE_REGIONS,
    ):
        assert identifiant in texte
    assert len(filtres.REGIONS_METROPOLE) == 13

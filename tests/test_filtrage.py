"""Tests de l'application des filtres."""

import pandas as pd

from src.components.filtres import REGIONS_METROPOLE
from src.utils import filtrage


def defaillances_exemple() -> pd.DataFrame:
    """Fabrique quatre défaillances dans trois régions et sur trois années."""
    return pd.DataFrame(
        {
            "annee": [2019, 2021, 2024, 2025],
            "procedure": [
                "Liquidation judiciaire",
                "Redressement judiciaire",
                "Liquidation judiciaire",
                "Sauvegarde",
            ],
            "departement": ["75", "2A", "1", "59"],
        }
    )


def test_correspondance_complete() -> None:
    """Les 96 départements de métropole sont rangés dans les 13 régions du filtre."""
    assert len(filtrage.REGION_DU_DEPARTEMENT) == 96
    assert set(filtrage.DEPARTEMENTS_PAR_REGION) == set(REGIONS_METROPOLE)


def test_region_des_departements() -> None:
    """Un code sans zéro de tête ou en minuscules est reconnu."""
    regions = filtrage.region_des_departements(pd.Series(["1", "2a", "93"]))
    assert list(regions) == ["Auvergne-Rhône-Alpes", "Corse", "Île-de-France"]


def test_appliquer_filtres() -> None:
    """Période, procédure et région sont appliquées ensemble ; aucune région = tout."""
    donnees = defaillances_exemple()
    toutes = ["Liquidation judiciaire", "Redressement judiciaire", "Sauvegarde"]
    assert len(filtrage.appliquer_filtres(donnees, [2019, 2025], toutes, [])) == 4
    liquidations = filtrage.appliquer_filtres(donnees, [2020, 2025], ["Liquidation judiciaire"], [])
    assert list(liquidations["annee"]) == [2024]
    corse = filtrage.appliquer_filtres(donnees, [2019, 2025], toutes, ["Corse"])
    assert list(corse["departement"]) == ["2A"]

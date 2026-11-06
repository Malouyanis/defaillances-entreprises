"""Tests de la page Évolution."""

import sys
from pathlib import Path
from types import ModuleType

import dash
import pandas as pd
import pytest

import config
from src.app import creer_application
from src.utils import cache, database, formatage

PROCEDURES = ["Liquidation judiciaire", "Redressement judiciaire", "Sauvegarde"]


def cleaned_exemple() -> pd.DataFrame:
    """Sept défaillances de 2019 à 2021, dont deux en avril 2020 (1er confinement)."""
    return pd.DataFrame(
        {
            "date_jugement": [
                "2019-03-04",
                "2019-03-20",
                "2020-04-02",
                "2020-04-15",
                "2021-01-10",
                "2021-06-30",
                "2021-06-30",
            ],
            "annee": [2019, 2019, 2020, 2020, 2021, 2021, 2021],
            "departement": ["75", "13", "75", "75", "59", "2A", "69"],
            "procedure": [PROCEDURES[0], PROCEDURES[1], PROCEDURES[0], PROCEDURES[2]]
            + [PROCEDURES[0]] * 3,
        }
    )


def module_evolution() -> ModuleType:
    """Crée l'application (qui charge les pages) et renvoie le module de la page Évolution."""
    creer_application()
    page = next(page for page in dash.page_registry.values() if page["path"] == "/evolution")
    return sys.modules[page["module"]]


def test_calculs() -> None:
    """Comptes par mois et par procédure, évolution annuelle, libellé du mois en français."""
    evolution = module_evolution()
    par_mois = evolution.ouvertures_par_mois(cleaned_exemple())
    assert list(par_mois.index) == ["2019-03", "2020-04", "2021-01", "2021-06"]
    assert par_mois.loc["2020-04", "Sauvegarde"] == 1
    assert par_mois.loc["2021-01", "Sauvegarde"] == 0
    par_annee = evolution.ouvertures_par_annee(cleaned_exemple())
    assert list(par_annee["ouvertures"]) == [2, 2, 3]
    assert par_annee.loc[2020, "evolution"] == 0
    assert evolution.libelle_mois("2020-04") == "avr. 2020"


def test_page_et_callback(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """La page s'affiche ; le callback filtre, colore chaque procédure et annote le confinement."""
    chemin = tmp_path / "essai.sqlite"
    database.ecrire_table(cleaned_exemple(), "cleaned", chemin)
    monkeypatch.setattr(config, "CHEMIN_BASE", chemin)
    cache.vider_cache()
    evolution = module_evolution()
    assert "evolution-graphique" in str(evolution.layout())
    figure, tableau, constat = evolution.mettre_a_jour_evolution([2019, 2021], PROCEDURES, [])
    couleurs = [trace.line.color for trace in figure.data]
    assert couleurs == list(evolution.COULEURS_PROCEDURES.values())
    assert figure.data[0].name == "Liquidation"
    assert figure.layout.annotations[0].text == "1er confinement"
    assert "2021" in str(tableau)
    assert constat.startswith("L'année la plus basse est 2019")
    assert constat.endswith(f"2021 est à +{formatage.pourcentage(0.5, 1)} de 2019.")
    vide, message, _ = evolution.mettre_a_jour_evolution([2019, 2019], ["Sauvegarde"], [])
    assert "Aucune défaillance" in str(message)


def test_sans_base(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Sans table cleaned, la page affiche un avis au lieu de planter."""
    monkeypatch.setattr(config, "CHEMIN_BASE", tmp_path / "vide.sqlite")
    cache.vider_cache()
    assert "pas encore disponibles" in str(module_evolution().layout())

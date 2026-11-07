"""Tests de la page d'accueil."""

import sys
from pathlib import Path
from types import ModuleType

import dash
import pandas as pd
import pytest

import config
from src.app import creer_application
from src.utils import cache, database


def cleaned_exemple() -> pd.DataFrame:
    """Cinq défaillances : quatre liquidations, surtout dans la construction (F), record en 2024."""
    return pd.DataFrame(
        {
            "annee": [2023, 2024, 2024, 2024, 2025],
            "departement": ["75", "75", "13", "75", "59"],
            "procedure": ["Liquidation judiciaire"] * 4 + ["Redressement judiciaire"],
            "section_naf": ["F", "F", "I", "F", "G"],
            "age_defaillance": [2.0, 4.0, 5.0, 6.0, 8.0],
        }
    )


def module_accueil() -> ModuleType:
    """Crée l'application (qui charge les pages) et renvoie le module de la page d'accueil."""
    creer_application()
    page = next(page for page in dash.page_registry.values() if page["path"] == "/")
    return sys.modules[page["module"]]


def contenu_accueil(chemin: Path, monkeypatch: pytest.MonkeyPatch) -> str:
    """Pointe le projet vers une base de test et renvoie le texte de la page d'accueil."""
    monkeypatch.setattr(config, "CHEMIN_BASE", chemin)
    cache.vider_cache()
    creer_application()
    page = next(page for page in dash.page_registry.values() if page["path"] == "/")
    return str(page["layout"]())


def test_chiffres_cles() -> None:
    """Nombre, part de liquidations, âge médian et secteur, mis en forme à la française."""
    chiffres = module_accueil().calculer_chiffres_cles(cleaned_exemple())
    valeurs = {libelle: valeur for libelle, valeur, _ in chiffres}
    assert valeurs["Ouvertures de procédure"] == "5"
    assert valeurs["Part de liquidations"] == "80 %"
    assert valeurs["Âge médian au jugement"] == "5,0"
    assert valeurs["Secteur le plus touché"] == "Construction"


def test_constat_et_graphique() -> None:
    """Phrase de l'année record, barre du record dans la teinte, description en texte."""
    accueil = module_accueil()
    par_annee = accueil.ouvertures_par_annee(cleaned_exemple())
    assert accueil.constat(par_annee).startswith("2024 est l'année record")
    assert "+200,0 % sur 2023" in accueil.constat(par_annee)
    figure = accueil.creer_graphique_annees(par_annee)
    assert list(figure.data[0].marker.color).count(accueil.TEINTE) == 1
    description = accueil.description_annees(par_annee)
    assert description.startswith("Ouvertures de procédure par année.")
    assert "2024 : 3" in description


def test_page_complete(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """La page affiche le titre, les chiffres, le graphique et le classement des départements."""
    chemin = tmp_path / "essai.sqlite"
    database.ecrire_table(cleaned_exemple(), "cleaned", chemin)
    texte = contenu_accueil(chemin, monkeypatch)
    for attendu in (
        "Défaillances de sociétés en France",
        "Chiffres clés",
        "75",
        "Explorer la carte",
    ):
        assert attendu in texte


def test_sans_base(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Sans table cleaned, la page affiche un message au lieu de planter."""
    texte = contenu_accueil(tmp_path / "vide.sqlite", monkeypatch)
    assert "pas encore disponibles" in texte

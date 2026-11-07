"""Tests de la page Scoring."""

import sys
from pathlib import Path
from types import ModuleType

import dash
import pytest

import config
from src.app import creer_application
from src.utils import database
from tests.test_scoring import scoring_exemple


def module_scoring() -> ModuleType:
    """Crée l'application (qui charge les pages) et renvoie le module de la page Scoring."""
    creer_application()
    page = next(page for page in dash.page_registry.values() if page["path"] == "/scoring")
    return sys.modules[page["module"]]


def test_resultats_memorises(tmp_path: Path) -> None:
    """Le modèle n'est entraîné qu'une fois par base : le second appel renvoie le même objet."""
    chemin = tmp_path / "essai.sqlite"
    database.ecrire_table(scoring_exemple(), "scoring", chemin)
    page = module_scoring()
    page.calculer_resultats.cache_clear()
    premier = page.calculer_resultats(chemin)
    assert page.calculer_resultats(chemin) is premier
    assert page.calculer_resultats.cache_info().misses == 1
    assert list(premier.grille.index) == ["A", "B", "C", "D", "E"]
    assert premier.auc_test > 0.8
    assert premier.societes_test == 100


def test_page_complete(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """La page affiche le constat, les AUC, la grille, et dit que le 1 % est une hypothèse."""
    chemin = tmp_path / "essai.sqlite"
    database.ecrire_table(scoring_exemple(), "scoring", chemin)
    monkeypatch.setattr(config, "CHEMIN_BASE", chemin)
    page = module_scoring()
    page.calculer_resultats.cache_clear()
    texte = str(page.layout())
    for attendu in ("AUC sur 2024-2025", "Grille de notation", "hypothèse", "notées E"):
        assert attendu in texte
    financiers = page.coefficients_financiers(page.calculer_resultats(chemin).coefficients)
    assert not financiers["variable"].str.startswith("section_naf_").any()
    assert "Liquidité" in set(financiers["libelle"])
    assert page.description_notes(page.calculer_resultats(chemin).grille).count("note ") == 5
    assert page.description_coefficients(financiers).startswith("Coefficients de la régression")


def test_sans_base(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Sans table scoring, la page affiche un avis au lieu de planter."""
    monkeypatch.setattr(config, "CHEMIN_BASE", tmp_path / "vide.sqlite")
    assert "pas encore disponibles" in str(module_scoring().layout())

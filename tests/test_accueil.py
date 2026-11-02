"""Tests de la page d'accueil."""

from pathlib import Path

import dash
import pandas as pd
import pytest

import config
from src.app import creer_application
from src.utils import cache, database


def cleaned_exemple() -> pd.DataFrame:
    """Quatre défaillances : trois liquidations, surtout dans la construction (section F)."""
    return pd.DataFrame(
        {
            "procedure": ["Liquidation judiciaire"] * 3 + ["Redressement judiciaire"],
            "section_naf": ["F", "F", "I", "F"],
            "age_defaillance": [2.0, 4.0, 6.0, 8.0],
        }
    )


def contenu_accueil(chemin: Path, monkeypatch: pytest.MonkeyPatch) -> str:
    """Pointe le projet vers une base de test et renvoie le texte de la page d'accueil."""
    monkeypatch.setattr(config, "CHEMIN_BASE", chemin)
    cache.vider_cache()
    creer_application()
    page = next(page for page in dash.page_registry.values() if page["path"] == "/")
    return str(page["layout"]())


def test_chiffres_cles(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Les cartes affichent le nombre, la part de liquidations, l'âge et le secteur."""
    chemin = tmp_path / "essai.sqlite"
    database.ecrire_table(cleaned_exemple(), "cleaned", chemin)
    texte = contenu_accueil(chemin, monkeypatch)
    assert "75 %" in texte
    assert "5,0 ans" in texte
    assert "Construction" in texte


def test_sans_base(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Sans table cleaned, la page affiche un message au lieu de planter."""
    texte = contenu_accueil(tmp_path / "vide.sqlite", monkeypatch)
    assert "pas encore disponibles" in texte

"""Tests de la page Finances."""

import sys
from pathlib import Path
from types import ModuleType

import dash
import numpy as np
import pandas as pd
import pytest

import config
from src.app import creer_application
from src.utils import cache, database, formatage


def scoring_exemple() -> pd.DataFrame:
    """120 sociétés de la construction (F), moitié saines ; trois du commerce (G)."""
    generateur = np.random.default_rng(0)
    defaut = np.tile([0, 1], 60)
    chiffre = 10 ** generateur.uniform(4, 7, 120) * (1 + defaut)
    construction = pd.DataFrame(
        {"defaut": defaut, "section_naf": "F", "chiffre_d_affaires": chiffre}
    )
    commerce = pd.DataFrame(
        {"defaut": [0, 1, 1], "section_naf": "G", "chiffre_d_affaires": [5e4, 2e5, 2e7]}
    )
    return pd.concat([construction, commerce], ignore_index=True)


def module_finances() -> ModuleType:
    """Crée l'application (qui charge les pages) et renvoie le module de la page Finances."""
    creer_application()
    page = next(page for page in dash.page_registry.values() if page["path"] == "/finances")
    return sys.modules[page["module"]]


def preparer_base(chemin: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Pointe le projet vers une base de test qui contient (ou non) la table scoring."""
    monkeypatch.setattr(config, "CHEMIN_BASE", chemin)
    cache.vider_cache()


def test_page_et_callback(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """La page s'affiche ; le callback renvoie deux séries de barres, le tableau et le constat."""
    chemin = tmp_path / "essai.sqlite"
    database.ecrire_table(scoring_exemple(), "scoring", chemin)
    preparer_base(chemin, monkeypatch)
    finances = module_finances()
    texte = str(finances.layout())
    assert "Chiffre d'affaires" in texte
    assert "Construction" in texte
    assert "lecteur-ecran" in texte
    figure, tableau, constat = finances.mettre_a_jour_finances(None)
    assert [trace.name for trace in figure.data] == ["Défaillantes", "Saines"]
    assert figure.data[0].marker.color == finances.TEINTE
    assert sum(figure.data[1].y) == pytest.approx(100, abs=0.1)
    assert "Médiane" in str(tableau)
    assert constat.startswith("La moitié des défaillantes")


def test_secteur_trop_petit_et_sans_base(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Un secteur avec trop peu de sociétés donne un message ; sans base, un avis."""
    chemin = tmp_path / "essai.sqlite"
    database.ecrire_table(scoring_exemple(), "scoring", chemin)
    preparer_base(chemin, monkeypatch)
    finances = module_finances()
    figure, message, constat = finances.mettre_a_jour_finances("G")
    assert "Trop peu" in str(figure.layout.annotations[0].text)
    assert "Trop peu" in str(message)
    assert constat == ""
    preparer_base(tmp_path / "vide.sqlite", monkeypatch)
    assert "pas encore disponibles" in str(finances.layout())


def test_constat() -> None:
    """Médianes en euros et part des sociétés au-delà de 10 M€, mises en forme à la française."""
    table = pd.DataFrame({"defaut": [0, 0, 1, 1], "chiffre_d_affaires": [1e5, 2e7, 1e5, 3e5]})
    phrase = module_finances().constat(table)
    assert f"{formatage.entier(200_000)} €" in phrase
    assert f"{formatage.pourcentage(0.5, 1)} des saines" in phrase

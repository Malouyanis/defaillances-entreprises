"""Tests de la page Carte."""

import json
import sys
from pathlib import Path
from types import ModuleType

import dash
import pandas as pd
import pytest
from dash import Patch

import config
from src.app import creer_application
from src.utils import cache, database

GEOJSON_EXEMPLE = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {"code": code, "nom": nom},
            "geometry": {"type": "Polygon", "coordinates": [[[x, 45], [x + 1, 45], [x, 46]]]},
        }
        for code, nom, x in (("75", "Paris", 2), ("2A", "Corse-du-Sud", 8))
    ],
}


def cleaned_exemple() -> pd.DataFrame:
    """Quatre défaillances : trois à Paris (dont deux liquidations), une en Corse-du-Sud."""
    return pd.DataFrame(
        {
            "annee": [2020, 2021, 2024, 2025],
            "departement": ["75", "75", "75", "2A"],
            "procedure": [
                "Liquidation judiciaire",
                "Redressement judiciaire",
                "Liquidation judiciaire",
                "Sauvegarde",
            ],
            "age_defaillance": [2.0, 4.0, 9.0, 12.0],
        }
    )


def module_carte() -> ModuleType:
    """Crée l'application (qui charge les pages) et renvoie le module de la page Carte."""
    creer_application()
    page = next(page for page in dash.page_registry.values() if page["path"] == "/carte")
    return sys.modules[page["module"]]


def page_carte(dossier: Path, monkeypatch: pytest.MonkeyPatch) -> dict:
    """Prépare une base et des contours de test, puis renvoie la page Carte du registre."""
    chemin = dossier / "essai.sqlite"
    database.ecrire_table(cleaned_exemple(), "cleaned", chemin)
    (dossier / "departements.geojson").write_text(json.dumps(GEOJSON_EXEMPLE), encoding="utf-8")
    monkeypatch.setattr(config, "CHEMIN_BASE", chemin)
    cache.vider_cache()
    creer_application()
    return next(page for page in dash.page_registry.values() if page["path"] == "/carte")


def valeurs_modifiees(modification: Patch) -> dict[tuple, list]:
    """Ce que la modification partielle change dans la figure : emplacement → nouvelle valeur."""
    operations = modification.to_plotly_json()["operations"]
    return {tuple(op["location"]): op["params"]["value"] for op in operations}


def test_calculer_par_departement() -> None:
    """Nombre, part de liquidations et âge médian calculés par département."""
    carte = module_carte()
    donnees = cleaned_exemple()
    nombre = carte.calculer_par_departement(donnees, carte.INDICATEURS[0])
    assert dict(zip(nombre["departement"], nombre["valeur"], strict=True)) == {"2A": 1, "75": 3}
    part = carte.calculer_par_departement(donnees, carte.INDICATEURS[1]).set_index("departement")
    assert part.loc["75", "valeur"] == round(200 / 3, 1)
    age = carte.calculer_par_departement(donnees, carte.INDICATEURS[2]).set_index("departement")
    assert age.loc["75", "valeur"] == 4.0


def test_page_et_carte(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """La page dessine la carte une fois ; le callback ne change ensuite que les valeurs."""
    page = page_carte(tmp_path, monkeypatch)
    assert page["name"] == "Carte"
    texte = str(page["layout"]())
    assert "carte-graphique" in texte
    assert "Corse-du-Sud" in texte
    carte = module_carte()
    modification, classement = carte.mettre_a_jour_carte(
        [2019, 2023], ["Liquidation judiciaire"], [], "Nombre de défaillances"
    )
    valeurs = valeurs_modifiees(modification)
    assert valeurs[("data", 0, "locations")] == ["75"]
    assert valeurs[("data", 0, "z")] == [1]
    assert valeurs[("data", 0, "text")] == ["Paris"]
    assert "geojson" not in str(modification.to_plotly_json())
    assert "Paris" in str(classement)


def test_sans_resultat_et_sans_contours(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Filtres sans résultat : carte sans valeurs ; fichier des contours absent : message."""
    page_carte(tmp_path, monkeypatch)
    carte = module_carte()
    vide, message = carte.mettre_a_jour_carte(
        [2019, 2019], ["Sauvegarde"], [], carte.INDICATEURS[0]
    )
    assert valeurs_modifiees(vide)[("data", 0, "z")] == []
    assert "Aucune défaillance" in str(message)
    (tmp_path / "departements.geojson").unlink()
    page = next(p for p in dash.page_registry.values() if p["path"] == "/carte")
    assert "introuvable" in str(page["layout"]())

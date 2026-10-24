"""Tests du module d'accès à la base SQLite."""

from pathlib import Path

import pandas as pd
import pytest

from src.utils import database


def test_ecrire_puis_lire_table(tmp_path: Path) -> None:
    """Une table écrite puis relue redonne les mêmes données."""
    chemin = tmp_path / "essai.sqlite"
    donnees = pd.DataFrame({"siren": ["123456789", "987654321"], "montant": [10.5, 20.0]})
    database.ecrire_table(donnees, "essai", chemin)
    relu = database.lire_table("essai", chemin)
    pd.testing.assert_frame_equal(relu, donnees, check_dtype=False)


def test_lister_tables(tmp_path: Path) -> None:
    """Les tables écrites apparaissent dans la liste, par ordre alphabétique."""
    chemin = tmp_path / "essai.sqlite"
    database.ecrire_table(pd.DataFrame({"a": [1]}), "raw", chemin)
    database.ecrire_table(pd.DataFrame({"a": [2]}), "cleaned", chemin)
    assert database.lister_tables(chemin) == ["cleaned", "raw"]
    assert database.table_existe("raw", chemin)


def test_lire_requete_avec_parametre(tmp_path: Path) -> None:
    """Une requête paramétrée ne renvoie que les lignes demandées."""
    chemin = tmp_path / "essai.sqlite"
    database.ecrire_table(pd.DataFrame({"annee": [2019, 2020, 2021]}), "raw", chemin)
    resultat = database.lire_requete("SELECT * FROM raw WHERE annee >= ?", (2020,), chemin)
    assert len(resultat) == 2


def test_nom_de_table_invalide_refuse(tmp_path: Path) -> None:
    """Un nom de table qui contient du SQL est refusé."""
    with pytest.raises(ValueError):
        database.lire_table("raw; DROP TABLE raw", tmp_path / "essai.sqlite")
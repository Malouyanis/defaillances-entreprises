"""Tests de la préparation des tables cleaned et scoring."""

from pathlib import Path

import pandas as pd

import clean_data
from src.utils import database, nettoyage_comptes


def table_exemple() -> pd.DataFrame:
    """Deux sociétés : une avec des capitaux propres négatifs, une sans comptes."""
    lignes: dict[str, object] = {
        "siren": ["012345678", "523456789"],
        "date_jugement": pd.to_datetime(["2024-03-15", "2023-06-01"]),
        "annee": [2024, 2023],
        "defaut": [1, 0],
        "departement": ["75", "59"],
        "procedure": ["Liquidation judiciaire", None],
        "section_naf": ["F", "G"],
        "tranche_effectifs": ["1 à 2", "Non employeur"],
        "categorie_entreprise": ["PME", None],
        "age_defaillance": [5.04, 12.36],
        "a_des_comptes": [True, False],
        "compte_resultat_publie": [True, None],
    }
    for colonne in clean_data.VARIABLES_FINANCIERES:
        lignes[colonne] = [1234.56, None]
    lignes["autonomie_financiere"] = [-12.34, None]
    return pd.DataFrame(lignes)


def test_ajouter_fonds_propres_negatifs() -> None:
    """1 si l'autonomie financière est négative, 0 si elle est positive, vide sans comptes."""
    table = pd.DataFrame({"autonomie_financiere": [-5.0, 10.0, None]})
    resultat = clean_data.ajouter_fonds_propres_negatifs(table)["fonds_propres_negatifs"]
    assert resultat.iloc[0] == 1.0
    assert resultat.iloc[1] == 0.0
    assert pd.isna(resultat.iloc[2])


def test_preparer_table() -> None:
    """Colonnes dans l'ordre voulu, date en texte, montants entiers, ratios arrondis."""
    cleaned = clean_data.preparer_table(table_exemple(), clean_data.COLONNES_CLEANED)
    assert list(cleaned.columns) == list(clean_data.COLONNES_CLEANED)
    assert cleaned.loc[0, "date_jugement"] == "2024-03-15"
    assert cleaned.loc[0, "chiffre_d_affaires"] == 1235
    assert cleaned.loc[0, "autonomie_financiere"] == -12.3
    assert cleaned.loc[0, "fonds_propres_negatifs"] == 1.0
    assert list(cleaned["a_des_comptes"]) == [1, 0]
    scoring = clean_data.preparer_table(table_exemple(), clean_data.COLONNES_SCORING)
    assert list(scoring.columns) == list(clean_data.COLONNES_SCORING)
    assert set(nettoyage_comptes.RATIOS) <= set(scoring.columns)


def test_ecriture_et_compactage(tmp_path: Path) -> None:
    """Les tables s'écrivent dans la base ; VACUUM rend la place d'une table remplacée."""
    chemin = tmp_path / "essai.sqlite"
    grande = pd.DataFrame({"texte": ["x" * 200] * 5_000})
    database.ecrire_table(grande, "cleaned", chemin)
    taille_avant = clean_data.taille_mo(chemin)
    database.ecrire_table(grande.head(10), "cleaned", chemin)
    clean_data.compacter_base(chemin)
    assert clean_data.taille_mo(chemin) < taille_avant
    assert database.lister_tables(chemin) == ["cleaned"]

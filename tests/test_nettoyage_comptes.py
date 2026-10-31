"""Tests du nettoyage des comptes annuels (ratios BCE/INPI)."""

from pathlib import Path

import pandas as pd

from src.utils import nettoyage_comptes


def comptes_exemple() -> pd.DataFrame:
    """Fabrique quatre exercices, dont un doublon et un compte confidentiel."""
    lignes = {
        "siren": ["012345678", "012345678", "523456789", "434567890"],
        "date_cloture_exercice": ["2023-12-31", "2023-12-31", "2023-06-30", "2023-12-31"],
        "chiffre_d_affaires": [250_000.0, 240_000.0, 0.0, 90_000.0],
        "resultat_net": [10_000.0, 9_000.0, -5_000.0, 1_000.0],
        "ebe": [20_000.0, 19_000.0, -2_000.0, 3_000.0],
        "type_bilan": ["S", "C", "S", "S"],
        "confidentiality": ["Public", "Public", "Public", "Confidentiel"],
    }
    for colonne in nettoyage_comptes.RATIOS:
        lignes[colonne] = [1.0, 1.0, 2.0, 3.0]
    return pd.DataFrame(lignes)


def test_normaliser_siren() -> None:
    """Les zéros de tête perdus sont rétablis ; un numéro trop long est rejeté."""
    resultat = nettoyage_comptes.normaliser_siren(pd.Series([12345678, 523456789]))
    assert list(resultat) == ["012345678", "523456789"]
    texte = nettoyage_comptes.normaliser_siren(pd.Series(["523 456 789", "1234567890"]))
    assert texte.iloc[0] == "523456789"
    assert pd.isna(texte.iloc[1])


def test_plafonner_ratios() -> None:
    """Une valeur extrême est ramenée près des autres ; l'ordre des valeurs est gardé."""
    comptes = pd.DataFrame(
        {colonne: [1.0] * 99 + [1_000.0] for colonne in nettoyage_comptes.RATIOS}
    )
    resultat = nettoyage_comptes.plafonner_ratios(comptes)
    assert resultat["taux_d_endettement"].max() < 1_000.0
    assert resultat["taux_d_endettement"].min() == 1.0


def test_nettoyer_comptes() -> None:
    """Les doublons sont retirés et le bilan complet est préféré ; le confidentiel reste."""
    resultat = nettoyage_comptes.nettoyer_comptes(comptes_exemple())
    assert list(resultat.columns) == list(nettoyage_comptes.COLONNES_NETTOYEES)
    assert list(resultat["siren"]) == ["012345678", "434567890", "523456789"]
    assert resultat.loc[0, "type_bilan"] == "C"
    assert resultat.loc[0, "chiffre_d_affaires"] == 240_000.0
    assert len(nettoyage_comptes.garder_ca_positif(resultat)) == 1


def test_masquer_compte_resultat() -> None:
    """Un dépôt confidentiel garde ses ratios de bilan mais perd son CA, son résultat, son EBE."""
    resultat = nettoyage_comptes.masquer_compte_resultat(comptes_exemple())
    confidentiel = resultat.iloc[3]
    assert pd.isna(confidentiel["chiffre_d_affaires"])
    assert pd.isna(confidentiel["marge_ebe"])
    assert confidentiel["taux_d_endettement"] == 3.0
    assert list(resultat["compte_resultat_publie"]) == [True, True, True, False]
    assert nettoyage_comptes.part_ca_nul_confidentiels(comptes_exemple()) == 0.0


def test_lire_comptes(tmp_path: Path) -> None:
    """La lecture ne garde que les bilans complets et simplifiés."""
    comptes = comptes_exemple().assign(type_bilan=["C", "S", "K", "S"])
    chemin = tmp_path / "ratios.parquet"
    comptes.to_parquet(chemin)
    resultat = nettoyage_comptes.lire_comptes(chemin)
    assert sorted(resultat["type_bilan"]) == ["C", "S", "S"]
    assert list(resultat.columns) == list(nettoyage_comptes.COLONNES_LUES)

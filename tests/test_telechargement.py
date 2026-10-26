"""Tests des outils de téléchargement et du contrôle des colonnes Sirene."""

from pathlib import Path

import pandas as pd

from src.utils import sirene, telechargement


def test_decrire_parquet(tmp_path: Path) -> None:
    """La description donne le bon nombre de lignes et les bonnes colonnes."""
    chemin = tmp_path / "essai.parquet"
    pd.DataFrame({"siren": ["123456789", "987654321"], "ca": [1.0, 2.0]}).to_parquet(chemin)
    description = telechargement.decrire_parquet(chemin)
    assert description.lignes == 2
    assert description.colonnes == ["siren", "ca"]


def test_fichier_present_non_retelecharge(tmp_path: Path) -> None:
    """Un fichier déjà présent est renvoyé tel quel, sans appel réseau."""
    chemin = tmp_path / "deja_la.parquet"
    chemin.write_bytes(b"contenu")
    assert telechargement.telecharger_fichier("https://exemple.invalid", chemin) == chemin
    assert chemin.read_bytes() == b"contenu"


def test_colonnes_manquantes() -> None:
    """Seules les colonnes utiles absentes sont signalées."""
    presentes = [colonne for colonne in sirene.COLONNES_SIRENE_UTILES if colonne != "siren"]
    assert sirene.colonnes_manquantes(presentes) == ["siren"]

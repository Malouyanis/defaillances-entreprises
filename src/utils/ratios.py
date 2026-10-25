"""Téléchargement des comptes annuels des sociétés (ratios financiers BCE/INPI)."""

import sys
from pathlib import Path

import config
from src.utils.telechargement import decrire_parquet, telecharger_fichier


def chemin_fichier_ratios() -> Path:
    """Chemin du fichier brut des ratios dans data/raw/ratios/."""
    return config.DOSSIER_RAW / "ratios" / "ratios_inpi_bce.parquet"


def telecharger_ratios(forcer: bool = False) -> Path:
    """Télécharge le jeu complet des ratios BCE/INPI au format Parquet, sans le modifier."""
    return telecharger_fichier(config.RATIOS_URL_EXPORT, chemin_fichier_ratios(), forcer)


if __name__ == "__main__":
    fichier_ratios = telecharger_ratios(forcer="--forcer" in sys.argv)
    description = decrire_parquet(fichier_ratios)
    print(f"{description.lignes} lignes, {description.taille_mo} Mo : {fichier_ratios}")
    print("Colonnes :", ", ".join(description.colonnes))
"""Téléchargement du répertoire Sirene des entreprises (fichier stock des unités légales)."""

import sys
from pathlib import Path

import config
from src.utils.telechargement import decrire_parquet, telecharger_fichier

COLONNES_SIRENE_UTILES = (
    "siren",
    "dateCreationUniteLegale",
    "categorieJuridiqueUniteLegale",
    "activitePrincipaleUniteLegale",
    "trancheEffectifsUniteLegale",
    "categorieEntreprise",
    "etatAdministratifUniteLegale",
)


def chemin_fichier_sirene() -> Path:
    """Chemin du fichier brut Sirene dans data/raw/sirene/."""
    return config.DOSSIER_RAW / "sirene" / "stock_unite_legale.parquet"


def telecharger_sirene(forcer: bool = False) -> Path:
    """Télécharge le stock Sirene des unités légales au format Parquet, sans le modifier."""
    return telecharger_fichier(
        config.SIRENE_URL_STOCK_UNITE_LEGALE, chemin_fichier_sirene(), forcer
    )


def colonnes_manquantes(colonnes_presentes: list[str]) -> list[str]:
    """Liste les colonnes utiles au projet qui seraient absentes du fichier téléchargé."""
    return [colonne for colonne in COLONNES_SIRENE_UTILES if colonne not in colonnes_presentes]


if __name__ == "__main__":
    fichier_sirene = telecharger_sirene(forcer="--forcer" in sys.argv)
    description = decrire_parquet(fichier_sirene)
    manquantes = colonnes_manquantes(description.colonnes)
    print(f"{description.lignes} lignes, {description.taille_mo} Mo : {fichier_sirene}")
    print("Colonnes :", ", ".join(description.colonnes))
    print("Colonnes utiles manquantes :", ", ".join(manquantes) if manquantes else "aucune")
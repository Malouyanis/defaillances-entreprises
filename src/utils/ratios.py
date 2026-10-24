"""Téléchargement des comptes annuels des sociétés (ratios financiers BCE/INPI)."""

import sys
from pathlib import Path
from typing import NamedTuple

import pyarrow.parquet as pq
import requests

import config

TAILLE_BLOC = 1024 * 1024


class DescriptionFichier(NamedTuple):
    """Résumé d'un fichier Parquet : volume, colonnes et taille sur le disque."""

    lignes: int
    colonnes: list[str]
    taille_mo: float


def chemin_fichier_ratios() -> Path:
    """Chemin du fichier brut des ratios dans data/raw/ratios/."""
    return config.DOSSIER_RAW / "ratios" / "ratios_inpi_bce.parquet"


def telecharger_ratios(forcer: bool = False) -> Path:
    """Télécharge le jeu complet des ratios BCE/INPI au format Parquet, sans le modifier.

    Le fichier pèse plusieurs centaines de Mo : il est écrit bloc par bloc pour ne pas
    saturer la mémoire, d'abord sous un nom temporaire. Il n'est pas retéléchargé s'il
    existe déjà, sauf si forcer=True.
    """
    chemin = chemin_fichier_ratios()
    if chemin.exists() and not forcer:
        return chemin
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin_temporaire = chemin.with_suffix(".tmp")
    with requests.get(
        config.RATIOS_URL_EXPORT, stream=True, timeout=config.TIMEOUT_HTTP
    ) as reponse:
        reponse.raise_for_status()
        with chemin_temporaire.open("wb") as fichier:
            for bloc in reponse.iter_content(chunk_size=TAILLE_BLOC):
                fichier.write(bloc)
    chemin_temporaire.replace(chemin)
    return chemin


def decrire_fichier(chemin: Path) -> DescriptionFichier:
    """Lit seulement les métadonnées du Parquet : nombre de lignes et noms de colonnes."""
    fichier = pq.ParquetFile(chemin)
    return DescriptionFichier(
        lignes=fichier.metadata.num_rows,
        colonnes=list(fichier.schema_arrow.names),
        taille_mo=round(chemin.stat().st_size / 1e6, 1),
    )


if __name__ == "__main__":
    fichier_ratios = telecharger_ratios(forcer="--forcer" in sys.argv)
    description = decrire_fichier(fichier_ratios)
    print(f"{description.lignes} lignes, {description.taille_mo} Mo : {fichier_ratios}")
    print("Colonnes :", ", ".join(description.colonnes))
    
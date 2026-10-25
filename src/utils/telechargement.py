"""Outils communs de téléchargement : fichiers volumineux en flux et description Parquet."""

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


def telecharger_fichier(url: str, chemin: Path, forcer: bool = False) -> Path:
    """Télécharge un fichier volumineux bloc par bloc et l'enregistre sans le modifier.

    Le fichier est d'abord écrit sous un nom temporaire, puis renommé : un téléchargement
    interrompu ne laisse jamais de fichier incomplet. Un fichier déjà présent n'est pas
    retéléchargé, sauf si forcer=True.
    """
    if chemin.exists() and not forcer:
        return chemin
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin_temporaire = chemin.with_suffix(".tmp")
    with requests.get(url, stream=True, timeout=config.TIMEOUT_HTTP) as reponse:
        reponse.raise_for_status()
        with chemin_temporaire.open("wb") as fichier:
            for bloc in reponse.iter_content(chunk_size=TAILLE_BLOC):
                fichier.write(bloc)
    chemin_temporaire.replace(chemin)
    return chemin


def decrire_parquet(chemin: Path) -> DescriptionFichier:
    """Lit seulement les métadonnées d'un Parquet : nombre de lignes et noms de colonnes."""
    fichier = pq.ParquetFile(chemin)
    return DescriptionFichier(
        lignes=fichier.metadata.num_rows,
        colonnes=list(fichier.schema_arrow.names),
        taille_mo=round(chemin.stat().st_size / 1e6, 1),
    )
    
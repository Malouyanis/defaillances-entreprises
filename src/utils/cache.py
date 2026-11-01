"""Cache des tables de la base : chaque table n'est lue qu'une fois, puis gardée en mémoire.

Les pages relisent souvent les mêmes données ; les garder en mémoire rend les filtres
instantanés. vider_cache() force une nouvelle lecture (bouton « Mettre à jour »).
"""

from functools import lru_cache
from pathlib import Path

import pandas as pd

import config
from src.utils import database


@lru_cache(maxsize=8)
def _lire_table_memorisee(nom_table: str, chemin: Path) -> pd.DataFrame:
    """Lit une table dans la base ; le résultat est mémorisé par lru_cache."""
    return database.lire_table(nom_table, chemin)


def charger_table(nom_table: str, chemin: Path = config.CHEMIN_BASE) -> pd.DataFrame:
    """Renvoie une copie de la table mise en cache, pour que les pages ne la modifient pas."""
    return _lire_table_memorisee(nom_table, chemin).copy()


def vider_cache() -> None:
    """Oublie toutes les tables gardées en mémoire : la prochaine lecture repart de la base."""
    _lire_table_memorisee.cache_clear()


def tables_en_cache() -> int:
    """Nombre de tables actuellement gardées en mémoire."""
    return _lire_table_memorisee.cache_info().currsize

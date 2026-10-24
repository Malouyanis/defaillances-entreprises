"""Accès à la base SQLite du projet : connexion, écriture et lecture de tables."""

import sqlite3
from contextlib import closing
from pathlib import Path

import pandas as pd

import config

REQUETE_LISTE_TABLES = "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"


def verifier_nom_table(nom_table: str) -> None:
    """Refuse un nom de table qui ne soit pas un identifiant simple (protège le SQL)."""
    if not nom_table.isidentifier():
        raise ValueError(f"Nom de table invalide : {nom_table!r}")


def connexion(chemin: Path = config.CHEMIN_BASE) -> sqlite3.Connection:
    """Ouvre une connexion à la base SQLite, en créant le dossier data/ si besoin."""
    chemin.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(chemin)


def ecrire_table(
    donnees: pd.DataFrame, nom_table: str, chemin: Path = config.CHEMIN_BASE
) -> None:
    """Écrit un DataFrame dans une table, en remplaçant la table si elle existe déjà."""
    verifier_nom_table(nom_table)
    with closing(connexion(chemin)) as conn:
        donnees.to_sql(nom_table, conn, if_exists="replace", index=False)
        conn.commit()


def lire_table(nom_table: str, chemin: Path = config.CHEMIN_BASE) -> pd.DataFrame:
    """Lit une table entière et la renvoie sous forme de DataFrame."""
    verifier_nom_table(nom_table)
    with closing(connexion(chemin)) as conn:
        return pd.read_sql_query(f'SELECT * FROM "{nom_table}"', conn)


def lire_requete(
    requete: str, parametres: tuple[object, ...] = (), chemin: Path = config.CHEMIN_BASE
) -> pd.DataFrame:
    """Exécute une requête SQL de lecture (avec paramètres ?) et renvoie le résultat."""
    with closing(connexion(chemin)) as conn:
        return pd.read_sql_query(requete, conn, params=parametres)


def lister_tables(chemin: Path = config.CHEMIN_BASE) -> list[str]:
    """Renvoie le nom des tables présentes dans la base, par ordre alphabétique."""
    with closing(connexion(chemin)) as conn:
        lignes = conn.execute(REQUETE_LISTE_TABLES).fetchall()
    return [ligne[0] for ligne in lignes]


def table_existe(nom_table: str, chemin: Path = config.CHEMIN_BASE) -> bool:
    """Indique si une table existe dans la base."""
    return nom_table in lister_tables(chemin)
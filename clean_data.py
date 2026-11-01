"""Nettoyage complet : construit les tables cleaned et scoring de data/db.sqlite.

Point d'entrée exigé par le projet. Il part de la table raw (écrite par get_data.py)
et des fichiers bruts de data/raw/, enchaîne le nettoyage des trois sources, la
jointure point-in-time et l'échantillon de sociétés saines, puis écrit deux tables :
- cleaned : une ligne par société défaillante, pour le tableau de bord ;
- scoring : défaillantes et sociétés saines avec comptes, pour le modèle de scoring.
"""

import gc
import sqlite3
from contextlib import closing
from pathlib import Path

import pandas as pd

import config
from src.utils import (
    database,
    echantillon_sain,
    jointure,
    nettoyage_bodacc,
    nettoyage_comptes,
    nettoyage_sirene,
    ratios,
    sirene,
)
from src.utils.get_data import NOM_TABLE_RAW

NOM_TABLE_CLEANED = "cleaned"
NOM_TABLE_SCORING = "scoring"
TAILLE_MAX_MO = 90
VARIABLES_FINANCIERES = (*nettoyage_comptes.MONTANTS, *nettoyage_comptes.RATIOS)
COLONNES_CLEANED = (
    "siren",
    "date_jugement",
    "annee",
    "departement",
    "procedure",
    "section_naf",
    "tranche_effectifs",
    "categorie_entreprise",
    "age_defaillance",
    "a_des_comptes",
    "compte_resultat_publie",
    *VARIABLES_FINANCIERES,
    "fonds_propres_negatifs",
)
COLONNES_SCORING = (
    "siren",
    "annee",
    "defaut",
    "section_naf",
    "tranche_effectifs",
    "categorie_entreprise",
    "age_defaillance",
    "compte_resultat_publie",
    *VARIABLES_FINANCIERES,
    "fonds_propres_negatifs",
)


def ajouter_fonds_propres_negatifs(table: pd.DataFrame) -> pd.DataFrame:
    """Ajoute 1 si les capitaux propres sont négatifs (autonomie financière < 0), 0 sinon.

    Le taux d'endettement devient négatif dans ce cas : cet indicateur rend le signal lisible.
    Sans comptes, la valeur reste vide.
    """
    autonomie = table["autonomie_financiere"]
    negatifs = (autonomie < 0).astype(float).where(autonomie.notna())
    return table.assign(fonds_propres_negatifs=negatifs)


def simplifier_types(table: pd.DataFrame) -> pd.DataFrame:
    """Rend la table légère pour SQLite : dates en texte, montants entiers, ratios arrondis."""
    simple = table.copy()
    if "date_jugement" in simple:
        simple["date_jugement"] = simple["date_jugement"].dt.strftime("%Y-%m-%d")
    for colonne in nettoyage_comptes.MONTANTS:
        simple[colonne] = simple[colonne].round().astype("Int64")
    for colonne in (*nettoyage_comptes.RATIOS, "age_defaillance"):
        simple[colonne] = simple[colonne].round(1)
    for colonne in ("a_des_comptes", "compte_resultat_publie"):
        if colonne in simple:
            simple[colonne] = simple[colonne].astype("boolean").astype("Int64")
    return simple


def preparer_table(table: pd.DataFrame, colonnes: tuple[str, ...]) -> pd.DataFrame:
    """Ajoute l'indicateur de fonds propres négatifs, garde les colonnes voulues, simplifie."""
    avec_indicateur = ajouter_fonds_propres_negatifs(table)
    return simplifier_types(avec_indicateur.loc[:, list(colonnes)])


def compacter_base(chemin: Path = config.CHEMIN_BASE) -> None:
    """Récupère la place laissée par les tables remplacées (commande SQLite VACUUM)."""
    with closing(sqlite3.connect(chemin)) as conn:
        conn.execute("VACUUM")


def taille_mo(chemin: Path = config.CHEMIN_BASE) -> float:
    """Taille du fichier de la base, en mégaoctets."""
    return round(chemin.stat().st_size / 1e6, 1)


def construire_tables() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Enchaîne nettoyage, jointure et échantillon ; renvoie les tables cleaned et scoring."""
    defaillances = nettoyage_bodacc.nettoyer_bodacc(database.lire_table(NOM_TABLE_RAW))
    sirens_defaillants = set(defaillances["siren"])

    societes = nettoyage_sirene.nettoyer_sirene(
        nettoyage_sirene.lire_societes(sirene.chemin_fichier_sirene())
    )
    candidats = echantillon_sain.candidats_sains(societes, sirens_defaillants)
    taille = echantillon_sain.NOMBRE_SAINS_PAR_DEFAILLANTE * len(defaillances)
    sains = echantillon_sain.tirer_sains(candidats, defaillances["date_jugement"], taille)
    sirens_utiles = sirens_defaillants | set(sains["siren"])
    societes_utiles = societes.loc[societes["siren"].isin(sirens_utiles)]
    del societes, candidats
    gc.collect()

    comptes = nettoyage_comptes.nettoyer_comptes(
        nettoyage_comptes.lire_comptes(ratios.chemin_fichier_ratios())
    )
    comptes_utiles = comptes.loc[comptes["siren"].isin(sirens_utiles)]
    del comptes
    gc.collect()

    defaillantes = jointure.joindre_sources(defaillances, comptes_utiles, societes_utiles)
    sains_joints = jointure.joindre_sources(sains, comptes_utiles, societes_utiles)
    echantillon = echantillon_sain.assembler(defaillantes, sains_joints)
    scoring = echantillon_sain.garder_pour_scoring(echantillon)
    return (
        preparer_table(defaillantes, COLONNES_CLEANED),
        preparer_table(scoring, COLONNES_SCORING),
    )


if __name__ == "__main__":
    table_cleaned, table_scoring = construire_tables()
    database.ecrire_table(table_cleaned, NOM_TABLE_CLEANED)
    database.ecrire_table(table_scoring, NOM_TABLE_SCORING)
    compacter_base()
    print(f"Table {NOM_TABLE_CLEANED} : {len(table_cleaned)} lignes")
    print(f"Table {NOM_TABLE_SCORING} : {len(table_scoring)} lignes")
    print(f"Tables de la base : {', '.join(database.lister_tables())}")
    taille = taille_mo()
    print(f"Taille de {config.CHEMIN_BASE.name} : {taille} Mo (limite {TAILLE_MAX_MO} Mo)")
    if taille > TAILLE_MAX_MO:
        print("ATTENTION : base trop lourde pour GitHub, ne pas la commiter")

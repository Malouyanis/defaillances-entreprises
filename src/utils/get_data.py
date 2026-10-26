"""Récupération des trois sources et construction de la table raw de la base SQLite.

Les fichiers bruts complets restent dans data/raw/ (BODACC, ratios BCE/INPI, Sirene).
La table raw de data/db.sqlite contient les jugements d'ouverture publiés au BODACC,
avec leurs valeurs d'origine : seules les lignes et les colonnes utiles sont retenues.
"""

import json
import sys
from pathlib import Path

import pandas as pd

import config
from src.utils import bodacc, database, ratios, sirene

NOM_TABLE_RAW = "raw"
DEBUT_NATURE_OUVERTURE = "jugement d'ouverture"
COLONNES_RAW = (
    "id",
    "dateparution",
    "typeavis",
    "numerodepartement",
    "registre",
    "jugement_nature",
    "jugement_date",
)


def extraire_jugement(valeur: object) -> tuple[str | None, str | None]:
    """Extrait la nature et la date du jugement depuis le champ « jugement ».

    Selon l'API, ce champ arrive sous forme de texte JSON ou de dictionnaire déjà lu.
    """
    jugement = valeur
    if isinstance(valeur, str):
        try:
            jugement = json.loads(valeur)
        except json.JSONDecodeError:
            return None, None
    if not isinstance(jugement, dict):
        return None, None
    return jugement.get("nature"), jugement.get("date")


def liste_en_texte(valeur: object) -> object:
    """Transforme une liste (ex. plusieurs numéros au registre) en texte, sans la modifier.

    SQLite ne sait pas stocker une liste Python : on joint ses éléments par « , ».
    """
    if isinstance(valeur, list):
        return ", ".join(str(element) for element in valeur)
    return valeur


def lire_annonces(chemin: Path) -> pd.DataFrame:
    """Lit un fichier brut mensuel du BODACC et renvoie ses annonces."""
    return pd.DataFrame(json.loads(chemin.read_text(encoding="utf-8")))


def garder_jugements_ouverture(annonces: pd.DataFrame) -> pd.DataFrame:
    """Ne garde que les jugements d'ouverture et les colonnes utiles de la table raw.

    Les autres annonces d'une même procédure (clôture, état des créances, conversion...)
    ne sont pas de nouvelles défaillances : elles ne servent pas au projet.
    """
    if annonces.empty:
        return pd.DataFrame(columns=list(COLONNES_RAW))
    natures_dates = annonces["jugement"].map(extraire_jugement)
    annonces = annonces.assign(
        jugement_nature=natures_dates.str[0], jugement_date=natures_dates.str[1]
    )
    est_ouverture = annonces["jugement_nature"].str.lower().str.startswith(
        DEBUT_NATURE_OUVERTURE, na=False
    )
    table = annonces.loc[est_ouverture, list(COLONNES_RAW)].reset_index(drop=True)
    return table.map(liste_en_texte)


def construire_table_raw(chemins: list[Path]) -> pd.DataFrame:
    """Assemble les jugements d'ouverture de tous les mois téléchargés."""
    tables = [garder_jugements_ouverture(lire_annonces(chemin)) for chemin in chemins]
    return pd.concat(tables, ignore_index=True)


def recuperer_donnees(
    annee_debut: int = config.ANNEE_DEBUT, annee_fin: int = config.ANNEE_FIN
) -> pd.DataFrame:
    """Télécharge les trois sources, puis écrit la table raw dans data/db.sqlite."""
    chemins_bodacc = bodacc.telecharger_periode(annee_debut, annee_fin)
    print("Ratios BCE/INPI :", ratios.telecharger_ratios())
    print("Sirene :", sirene.telecharger_sirene())
    table_raw = construire_table_raw(chemins_bodacc)
    database.ecrire_table(table_raw, NOM_TABLE_RAW)
    return table_raw


if __name__ == "__main__":
    if len(sys.argv) == 3:
        debut, fin = int(sys.argv[1]), int(sys.argv[2])
    else:
        debut, fin = config.ANNEE_DEBUT, config.ANNEE_FIN
    table = recuperer_donnees(debut, fin)
    taille_mo = round(config.CHEMIN_BASE.stat().st_size / 1e6, 1)
    print(f"Table raw : {len(table)} jugements d'ouverture ({debut}-{fin})")
    print(f"Base {config.CHEMIN_BASE.name} : {taille_mo} Mo")
    print(table["jugement_nature"].value_counts().head(5).to_string())

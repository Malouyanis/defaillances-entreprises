"""Nettoyage des jugements d'ouverture du BODACC (table raw).

Le résultat contient une ligne par entreprise défaillante : son SIREN, la date du
jugement d'ouverture, le département (métropole uniquement) et la procédure.
"""

import re

import pandas as pd

import config
from src.utils import database
from src.utils.get_data import NOM_TABLE_RAW

MOTS_AVIS_ECARTES = ("rectif", "annul")
PROCEDURES = (
    ("liquidation", "Liquidation judiciaire"),
    ("sauvegarde", "Sauvegarde"),
    ("redressement", "Redressement judiciaire"),
    ("sortie de crise", "Redressement judiciaire"),
)
ECART_MAX_JOURS = 365
COLONNES_NETTOYEES = (
    "siren",
    "date_jugement",
    "annee",
    "departement",
    "procedure",
    "id_annonce",
)


def extraire_siren(registre: object) -> str | None:
    """Renvoie le SIREN (9 chiffres) du premier numéro inscrit au registre, sinon None."""
    if not isinstance(registre, str):
        return None
    premier_numero = registre.split(",")[0]
    chiffres = re.sub(r"\D", "", premier_numero)
    return chiffres if len(chiffres) == 9 else None


def categoriser_procedure(nature: object) -> str | None:
    """Range la nature du jugement dans une des trois procédures collectives."""
    if not isinstance(nature, str):
        return None
    nature_minuscule = nature.lower()
    for mot_cle, procedure in PROCEDURES:
        if mot_cle in nature_minuscule:
            return procedure
    return None


def garder_avis_initiaux(raw: pd.DataFrame) -> pd.DataFrame:
    """Écarte les avis rectificatifs et les annulations, qui répètent un avis déjà publié."""
    type_avis = raw["typeavis"].fillna("").str.lower()
    est_ecarte = type_avis.str.contains("|".join(MOTS_AVIS_ECARTES))
    return raw.loc[~est_ecarte]


def garder_metropole(raw: pd.DataFrame) -> pd.DataFrame:
    """Retire les départements et collectivités d'outre-mer."""
    departement = raw["numerodepartement"].astype("string").str.strip()
    return raw.loc[~departement.isin(config.DEPARTEMENTS_OUTRE_MER)]


def corriger_date_jugement(date_jugement: pd.Series, date_parution: pd.Series) -> pd.Series:
    """Remplace une date de jugement absente ou impossible par la date de parution.

    Le jugement précède sa parution au BODACC de quelques jours ou semaines : une date
    postérieure à la parution, ou antérieure de plus d'un an, est une erreur de saisie.
    """
    ecart = date_parution - date_jugement
    aberrante = (
        date_jugement.isna()
        | (ecart < pd.Timedelta(0))
        | (ecart > pd.Timedelta(days=ECART_MAX_JOURS))
    )
    return date_jugement.mask(aberrante, date_parution)


def preparer_colonnes(raw: pd.DataFrame) -> pd.DataFrame:
    """Calcule SIREN, procédure et dates, puis garde les colonnes du résultat."""
    date_jugement = pd.to_datetime(raw["jugement_date"], errors="coerce")
    date_parution = pd.to_datetime(raw["dateparution"], errors="coerce")
    resultat = pd.DataFrame(
        {
            "siren": raw["registre"].map(extraire_siren),
            "date_jugement": corriger_date_jugement(date_jugement, date_parution),
            "departement": raw["numerodepartement"].astype("string").str.strip(),
            "procedure": raw["jugement_nature"].map(categoriser_procedure),
            "id_annonce": raw["id"],
        }
    )
    resultat["annee"] = resultat["date_jugement"].dt.year
    return resultat.loc[:, list(COLONNES_NETTOYEES)]


def garder_periode(jugements: pd.DataFrame) -> pd.DataFrame:
    """Garde les jugements rendus pendant la période étudiée (2019-2025)."""
    dans_periode = jugements["annee"].between(config.ANNEE_DEBUT, config.ANNEE_FIN)
    return jugements.loc[dans_periode]


def une_ouverture_par_entreprise(jugements: pd.DataFrame) -> pd.DataFrame:
    """Garde la première ouverture de chaque entreprise sur la période."""
    tries = jugements.sort_values(["date_jugement", "id_annonce"])
    return tries.drop_duplicates(subset="siren", keep="first").reset_index(drop=True)


def nettoyer_bodacc(raw: pd.DataFrame) -> pd.DataFrame:
    """Enchaîne les étapes de nettoyage et renvoie une ligne par entreprise défaillante."""
    jugements = preparer_colonnes(garder_metropole(garder_avis_initiaux(raw)))
    complets = jugements.dropna(subset=["siren", "procedure", "date_jugement"])
    return une_ouverture_par_entreprise(garder_periode(complets))


if __name__ == "__main__":
    table_raw = database.lire_table(NOM_TABLE_RAW)
    print(f"Table raw : {len(table_raw)} lignes")
    print(table_raw["typeavis"].value_counts(dropna=False).to_string())
    defaillances = nettoyer_bodacc(table_raw)
    print(f"Après nettoyage : {len(defaillances)} entreprises défaillantes")
    print(defaillances["procedure"].value_counts().to_string())
    print(defaillances["annee"].value_counts().sort_index().to_string())

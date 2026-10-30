"""Jointure des trois sources : chaque défaillante reçoit son profil Sirene et ses comptes.

Les comptes retenus sont ceux du dernier exercice clos AVANT le jugement (jointure
« point-in-time ») : on ne regarde que ce qu'un prêteur aurait pu voir à ce moment-là.
"""

import gc

import pandas as pd

from src.utils import (
    database,
    nettoyage_bodacc,
    nettoyage_comptes,
    nettoyage_sirene,
    ratios,
    sirene,
)
from src.utils.get_data import NOM_TABLE_RAW

DATE_CREATION_MIN = pd.Timestamp("1900-01-01")
ANCIENNETE_MAX_COMPTES = pd.Timedelta(days=730)
JOURS_PAR_AN = 365.25


def calculer_age(date_jugement: pd.Series, date_creation: pd.Series) -> pd.Series:
    """Renvoie l'âge en années au jour du jugement ; vide si la date de création est impossible."""
    age = (date_jugement - date_creation).dt.days / JOURS_PAR_AN
    plausible = (date_creation >= DATE_CREATION_MIN) & (date_creation <= date_jugement)
    return age.where(plausible).round(1)


def ajouter_profil(defaillances: pd.DataFrame, societes: pd.DataFrame) -> pd.DataFrame:
    """Garde les défaillantes qui sont des sociétés Sirene et ajoute leur profil et leur âge."""
    jointes = defaillances.merge(societes, on="siren", how="inner")
    jointes["age_defaillance"] = calculer_age(jointes["date_jugement"], jointes["date_creation"])
    return jointes


def ajouter_derniers_comptes(defaillances: pd.DataFrame, comptes: pd.DataFrame) -> pd.DataFrame:
    """Associe à chaque défaillante son dernier exercice clos avant le jugement (24 mois max)."""
    gauche = defaillances.assign(
        siren=defaillances["siren"].astype("string"),
        date_jugement=defaillances["date_jugement"].astype("datetime64[ns]"),
    ).sort_values("date_jugement")
    droite = comptes.assign(
        siren=comptes["siren"].astype("string"),
        date_cloture_exercice=comptes["date_cloture_exercice"].astype("datetime64[ns]"),
    ).sort_values("date_cloture_exercice")
    jointes = pd.merge_asof(
        gauche,
        droite.drop(columns="type_bilan"),
        left_on="date_jugement",
        right_on="date_cloture_exercice",
        by="siren",
        direction="backward",
        allow_exact_matches=False,
        tolerance=ANCIENNETE_MAX_COMPTES,
    )
    jointes["a_des_comptes"] = jointes["date_cloture_exercice"].notna()
    return jointes.sort_values(["date_jugement", "siren"]).reset_index(drop=True)


def joindre_sources(
    defaillances: pd.DataFrame, comptes: pd.DataFrame, societes: pd.DataFrame
) -> pd.DataFrame:
    """Enchaîne profil Sirene, âge et derniers comptes : une ligne par société défaillante."""
    return ajouter_derniers_comptes(ajouter_profil(defaillances, societes), comptes)


def taux_renseignes(comptes_bruts: pd.DataFrame) -> pd.DataFrame:
    """Part des montants et ratios renseignés, selon le niveau de confidentialité du dépôt."""
    colonnes = list(nettoyage_comptes.MONTANTS + nettoyage_comptes.RATIOS)
    renseignes = comptes_bruts[colonnes].notna()
    renseignes["confidentiality"] = comptes_bruts["confidentiality"]
    return renseignes.groupby("confidentiality").mean().round(2)


if __name__ == "__main__":
    defaillantes = nettoyage_bodacc.nettoyer_bodacc(database.lire_table(NOM_TABLE_RAW))
    sirens_defaillants = set(defaillantes["siren"])
    print(f"Défaillantes BODACC : {len(defaillantes)}")

    bruts = nettoyage_comptes.lire_comptes(ratios.chemin_fichier_ratios())
    print("Part renseignée selon la confidentialité :")
    print(taux_renseignes(bruts).to_string())
    comptes_propres = nettoyage_comptes.nettoyer_comptes(bruts)
    comptes_utiles = comptes_propres.loc[comptes_propres["siren"].isin(sirens_defaillants)]
    del bruts, comptes_propres
    gc.collect()

    societes_propres = nettoyage_sirene.nettoyer_sirene(
        nettoyage_sirene.lire_societes(sirene.chemin_fichier_sirene())
    )
    societes_utiles = societes_propres.loc[societes_propres["siren"].isin(sirens_defaillants)]
    del societes_propres
    gc.collect()

    jointes = joindre_sources(defaillantes, comptes_utiles, societes_utiles)
    print(f"Défaillantes qui sont des sociétés Sirene : {len(jointes)}")
    print(f"Part avec des comptes de moins de 2 ans : {jointes['a_des_comptes'].mean():.1%}")
    print(f"Âge médian à la défaillance : {jointes['age_defaillance'].median():.1f} ans")
    print(jointes.groupby("annee")["a_des_comptes"].mean().round(3).to_string())
    print(jointes["secteur"].value_counts().head(10).to_string())

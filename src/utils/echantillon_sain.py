"""Échantillon de sociétés saines et table d'apprentissage du scoring.

Pour apprendre à reconnaître une défaillance, le modèle doit voir aussi des sociétés
qui n'ont pas fait défaut, décrites de la même façon et à la même époque : chaque
société saine reçoit une date de référence tirée parmi les dates de jugement.
"""

import gc

import pandas as pd

from src.utils import (
    database,
    jointure,
    nettoyage_bodacc,
    nettoyage_comptes,
    nettoyage_sirene,
    ratios,
    sirene,
)
from src.utils.get_data import NOM_TABLE_RAW

PREFIXE_SOCIETE_COMMERCIALE = "5"
NOMBRE_SAINS_PAR_DEFAILLANTE = 1
GRAINE = 42


def candidats_sains(societes: pd.DataFrame, sirens_defaillants: set[str]) -> pd.DataFrame:
    """Sociétés commerciales actives qui n'ont connu aucune défaillance sur la période."""
    commerciale = (
        societes["categorie_juridique"].astype("string").str.startswith(PREFIXE_SOCIETE_COMMERCIALE)
    )
    active = societes["etat_administratif"] == "A"
    jamais_defaillante = ~societes["siren"].isin(sirens_defaillants)
    return societes.loc[commerciale.fillna(False) & active & jamais_defaillante]


def tirer_sains(
    candidats: pd.DataFrame, dates_reference: pd.Series, taille: int, graine: int = GRAINE
) -> pd.DataFrame:
    """Tire des sociétés saines et leur donne une date de référence tirée parmi les jugements.

    La colonne s'appelle date_jugement comme pour les défaillantes, pour réutiliser la même
    jointure ; seules les sociétés déjà créées à cette date sont gardées.
    """
    tirees = candidats.sample(n=min(taille, len(candidats)), random_state=graine)
    tirees = tirees.reset_index(drop=True)
    dates = dates_reference.sample(n=len(tirees), replace=True, random_state=graine)
    sains = pd.DataFrame({"siren": tirees["siren"], "date_jugement": dates.to_numpy()})
    sains["annee"] = sains["date_jugement"].dt.year
    deja_creee = tirees["date_creation"] < sains["date_jugement"]
    return sains.loc[deja_creee].reset_index(drop=True)


def assembler(defaillantes: pd.DataFrame, sains: pd.DataFrame) -> pd.DataFrame:
    """Réunit défaillantes (defaut = 1) et sociétés saines (defaut = 0) dans une seule table."""
    return pd.concat([defaillantes.assign(defaut=1), sains.assign(defaut=0)], ignore_index=True)


def garder_pour_scoring(echantillon: pd.DataFrame) -> pd.DataFrame:
    """Garde les lignes qui ont des comptes : le modèle a besoin des ratios de bilan."""
    return echantillon.loc[echantillon["a_des_comptes"]].reset_index(drop=True)


if __name__ == "__main__":
    defaillances = nettoyage_bodacc.nettoyer_bodacc(database.lire_table(NOM_TABLE_RAW))
    sirens_defaillants = set(defaillances["siren"])

    societes = nettoyage_sirene.nettoyer_sirene(
        nettoyage_sirene.lire_societes(sirene.chemin_fichier_sirene())
    )
    candidats = candidats_sains(societes, sirens_defaillants)
    sains = tirer_sains(
        candidats, defaillances["date_jugement"], NOMBRE_SAINS_PAR_DEFAILLANTE * len(defaillances)
    )
    sirens_utiles = sirens_defaillants | set(sains["siren"])
    societes_utiles = societes.loc[societes["siren"].isin(sirens_utiles)]
    print(f"Candidats sains : {len(candidats)} ; sains tirés : {len(sains)}")
    del societes, candidats
    gc.collect()

    bruts = nettoyage_comptes.lire_comptes(ratios.chemin_fichier_ratios())
    part_nulle = nettoyage_comptes.part_ca_nul_confidentiels(bruts)
    print(f"CA égal à 0 chez les confidentiels : {part_nulle:.1%}")
    comptes = nettoyage_comptes.nettoyer_comptes(bruts)
    comptes_utiles = comptes.loc[comptes["siren"].isin(sirens_utiles)]
    del bruts, comptes
    gc.collect()

    defaillantes_jointes = jointure.joindre_sources(defaillances, comptes_utiles, societes_utiles)
    sains_joints = jointure.joindre_sources(sains, comptes_utiles, societes_utiles)
    echantillon = assembler(defaillantes_jointes, sains_joints)
    print(echantillon.groupby("defaut")["a_des_comptes"].agg(["size", "mean"]).round(3).to_string())
    scoring = garder_pour_scoring(echantillon)
    print(
        f"Table de scoring : {len(scoring)} lignes, taux de défaut {scoring['defaut'].mean():.1%}"
    )
    colonnes = [
        "taux_d_endettement",
        "ratio_de_liquidite",
        "autonomie_financiere",
        "age_defaillance",
    ]
    print(scoring.groupby("defaut")[colonnes].median().round(1).to_string())

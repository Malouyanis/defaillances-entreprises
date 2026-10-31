"""Nettoyage des comptes annuels des sociétés (ratios financiers BCE/INPI).

Le résultat contient une ligne par société et par exercice comptable : la date de
clôture, les montants (chiffre d'affaires, résultat, EBE) et les principaux ratios.
"""

from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

from src.utils import ratios

TYPES_BILAN = ("C", "S")
MONTANTS = ("chiffre_d_affaires", "resultat_net", "ebe")
RATIOS = (
    "marge_ebe",
    "taux_d_endettement",
    "ratio_de_liquidite",
    "autonomie_financiere",
    "capacite_de_remboursement",
)
COLONNES_LUES = (
    "siren",
    "date_cloture_exercice",
    *MONTANTS,
    *RATIOS,
    "type_bilan",
    "confidentiality",
)
RATIOS_COMPTE_RESULTAT = ("marge_ebe", "capacite_de_remboursement")
COLONNES_NETTOYEES = (
    "siren",
    "date_cloture_exercice",
    *MONTANTS,
    *RATIOS,
    "type_bilan",
    "compte_resultat_publie",
)
QUANTILE_BAS = 0.01
QUANTILE_HAUT = 0.99


def lire_comptes(chemin: Path) -> pd.DataFrame:
    """Lit le Parquet des ratios en ne chargeant que les colonnes utiles et les bilans C/S.

    Le fichier complet compte 6,8 millions de lignes : pyarrow filtre pendant la lecture,
    ce qui évite de charger en mémoire les colonnes et les bilans inutiles.
    """
    table = pq.read_table(
        chemin,
        columns=list(COLONNES_LUES),
        filters=[("type_bilan", "in", list(TYPES_BILAN))],
    )
    return table.to_pandas()


def normaliser_siren(siren: pd.Series) -> pd.Series:
    """Renvoie le SIREN en texte de 9 chiffres (zéros de tête rétablis), sinon une case vide."""
    if pd.api.types.is_numeric_dtype(siren):
        siren = siren.astype("Int64")
    chiffres = siren.astype("string").str.replace(r"\D", "", regex=True).str.zfill(9)
    return chiffres.where(chiffres.str.len() == 9)


def est_confidentiel(comptes: pd.DataFrame) -> pd.Series:
    """Indique les dépôts « partiellement confidentiels » (compte de résultat non publié)."""
    confidentialite = comptes["confidentiality"].astype("string").str.lower()
    return confidentialite.str.contains("confidentiel", na=False)


def masquer_compte_resultat(comptes: pd.DataFrame) -> pd.DataFrame:
    """Garde les dépôts confidentiels, mais vide ce qui vient du compte de résultat caché.

    Leur bilan est public (endettement, liquidité, autonomie financière) ; leur chiffre
    d'affaires, leur résultat et leur EBE ne le sont pas et sont remplacés par une case vide.
    """
    confidentiel = est_confidentiel(comptes)
    masques = comptes.copy()
    for colonne in MONTANTS + RATIOS_COMPTE_RESULTAT:
        masques[colonne] = masques[colonne].mask(confidentiel)
    masques["compte_resultat_publie"] = ~confidentiel
    return masques


def part_ca_nul_confidentiels(comptes: pd.DataFrame) -> float:
    """Part des dépôts confidentiels dont le chiffre d'affaires est égal à 0 dans le fichier."""
    confidentiels = comptes.loc[est_confidentiel(comptes), "chiffre_d_affaires"]
    return float((confidentiels == 0).mean()) if len(confidentiels) else 0.0


def une_ligne_par_exercice(comptes: pd.DataFrame) -> pd.DataFrame:
    """Garde un seul bilan par société et date de clôture, le complet (C) avant le simplifié."""
    tries = comptes.sort_values(["siren", "date_cloture_exercice", "type_bilan"])
    uniques = tries.drop_duplicates(subset=["siren", "date_cloture_exercice"], keep="first")
    return uniques.reset_index(drop=True)


def plafonner_ratios(comptes: pd.DataFrame) -> pd.DataFrame:
    """Ramène chaque ratio entre ses percentiles 1 et 99 pour limiter les valeurs extrêmes.

    Un ratio explose quand son dénominateur est proche de zéro (fonds propres, CA) :
    ces valeurs écraseraient les moyennes et le modèle de scoring.
    """
    plafonnes = comptes.copy()
    for colonne in RATIOS:
        valeurs = pd.to_numeric(plafonnes[colonne], errors="coerce")
        bas, haut = valeurs.quantile([QUANTILE_BAS, QUANTILE_HAUT])
        plafonnes[colonne] = valeurs.clip(lower=bas, upper=haut)
    return plafonnes


def nettoyer_comptes(comptes: pd.DataFrame) -> pd.DataFrame:
    """Enchaîne les étapes de nettoyage et renvoie une ligne par société et par exercice."""
    masques = masquer_compte_resultat(comptes)
    prepares = masques.assign(
        siren=normaliser_siren(masques["siren"]),
        date_cloture_exercice=pd.to_datetime(masques["date_cloture_exercice"], errors="coerce"),
    ).dropna(subset=["siren", "date_cloture_exercice"])
    resultat = plafonner_ratios(une_ligne_par_exercice(prepares))
    return resultat.loc[:, list(COLONNES_NETTOYEES)]


def garder_ca_positif(comptes: pd.DataFrame) -> pd.DataFrame:
    """Garde les exercices avec un chiffre d'affaires strictement positif (histogramme du CA)."""
    return comptes.loc[comptes["chiffre_d_affaires"] > 0]


if __name__ == "__main__":
    comptes_bruts = lire_comptes(ratios.chemin_fichier_ratios())
    print(f"Bilans C et S lus : {len(comptes_bruts)}")
    print(comptes_bruts["type_bilan"].value_counts().to_string())
    print(comptes_bruts["confidentiality"].value_counts(dropna=False).to_string())
    print(f"CA égal à 0 chez les confidentiels : {part_ca_nul_confidentiels(comptes_bruts):.1%}")
    comptes_propres = nettoyer_comptes(comptes_bruts)
    print(f"Après nettoyage : {len(comptes_propres)} exercices")
    print(f"Sociétés distinctes : {comptes_propres['siren'].nunique()}")
    print(f"Exercices avec un CA > 0 : {len(garder_ca_positif(comptes_propres))}")
    print(comptes_propres[["chiffre_d_affaires", *RATIOS]].describe().round(2).to_string())

"""Application des filtres de la barre commune (période, procédure, région) aux données."""

import pandas as pd

DEPARTEMENTS_PAR_REGION = {
    "Auvergne-Rhône-Alpes": "01 03 07 15 26 38 42 43 63 69 73 74",
    "Bourgogne-Franche-Comté": "21 25 39 58 70 71 89 90",
    "Bretagne": "22 29 35 56",
    "Centre-Val de Loire": "18 28 36 37 41 45",
    "Corse": "2A 2B",
    "Grand Est": "08 10 51 52 54 55 57 67 68 88",
    "Hauts-de-France": "02 59 60 62 80",
    "Île-de-France": "75 77 78 91 92 93 94 95",
    "Normandie": "14 27 50 61 76",
    "Nouvelle-Aquitaine": "16 17 19 23 24 33 40 47 64 79 86 87",
    "Occitanie": "09 11 12 30 31 32 34 46 48 65 66 81 82",
    "Pays de la Loire": "44 49 53 72 85",
    "Provence-Alpes-Côte d'Azur": "04 05 06 13 83 84",
}
REGION_DU_DEPARTEMENT = {
    departement: region
    for region, departements in DEPARTEMENTS_PAR_REGION.items()
    for departement in departements.split()
}


def region_des_departements(departements: pd.Series) -> pd.Series:
    """Renvoie la région de chaque département (« 1 » et « 01 » sont reconnus)."""
    codes = departements.astype("string").str.strip().str.upper().str.zfill(2)
    return codes.map(REGION_DU_DEPARTEMENT)


def appliquer_filtres(
    donnees: pd.DataFrame,
    annees: list[int],
    procedures: list[str],
    regions: list[str],
) -> pd.DataFrame:
    """Garde les lignes dans la période, parmi les procédures et les régions choisies.

    Une liste de régions vide veut dire « toute la France métropolitaine ».
    """
    debut, fin = annees
    garde = donnees["annee"].between(debut, fin) & donnees["procedure"].isin(procedures)
    if regions:
        garde &= region_des_departements(donnees["departement"]).isin(regions)
    return donnees.loc[garde]

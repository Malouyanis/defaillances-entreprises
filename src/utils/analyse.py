"""Analyse des signaux financiers : qu'est-ce qui distingue une défaillante d'une saine ?

Tout part de la table scoring (défaillantes et sociétés saines avec comptes). Les tableaux
produits servent au Rapport d'analyse et au choix des variables du modèle de scoring.
"""

import pandas as pd

from src.utils import database, nettoyage_comptes
from src.utils.nettoyage_sirene import SECTIONS_NAF

NOM_TABLE_SCORING = "scoring"
VARIABLES_ANALYSE = (
    *nettoyage_comptes.MONTANTS,
    *nettoyage_comptes.RATIOS,
    "fonds_propres_negatifs",
    "age_defaillance",
)
QUARTILES = {0.25: "Q1", 0.5: "médiane", 0.75: "Q3"}
BORNES_AGE = (0, 3, 5, 10, 20, float("inf"))
TRANCHES_AGE = ("moins de 3 ans", "3 à 5 ans", "5 à 10 ans", "10 à 20 ans", "20 ans et plus")
MISE_EN_GARDE = (
    "Taux de défaut de l'échantillon (environ 45 % par construction) :"
    " il compare les groupes entre eux, ce n'est pas le vrai taux de défaut français."
)


def auc_univariee(valeurs: pd.Series, defaut: pd.Series) -> float:
    """Probabilité qu'une défaillante tirée au hasard ait une valeur plus élevée qu'une saine.

    Calcul par les rangs (statistique de Mann-Whitney) ; les égalités comptent pour moitié
    et les valeurs vides sont ignorées. 0,5 = aucun pouvoir discriminant.
    """
    paires = pd.DataFrame({"valeur": valeurs, "defaut": defaut}).dropna()
    nb_defauts = int(paires["defaut"].sum())
    nb_sains = len(paires) - nb_defauts
    if nb_defauts == 0 or nb_sains == 0:
        return float("nan")
    rangs = paires["valeur"].rank()
    somme_rangs_defauts = rangs[paires["defaut"] == 1].sum()
    u = somme_rangs_defauts - nb_defauts * (nb_defauts + 1) / 2
    return float(u / (nb_defauts * nb_sains))


def pouvoir_discriminant(scoring: pd.DataFrame) -> pd.DataFrame:
    """Classe les variables de la plus à la moins discriminante (AUC univariée)."""
    lignes = []
    for variable in VARIABLES_ANALYSE:
        auc = auc_univariee(scoring[variable], scoring["defaut"])
        lignes.append(
            {
                "variable": variable,
                "auc": round(auc, 3),
                "pouvoir": round(max(auc, 1 - auc), 3),
                "sens": "plus élevée chez les défaillantes" if auc > 0.5 else "plus basse",
                "part_renseignee": round(float(scoring[variable].notna().mean()), 3),
            }
        )
    tableau = pd.DataFrame(lignes).sort_values("pouvoir", ascending=False)
    return tableau.reset_index(drop=True)


def comparer_groupes(scoring: pd.DataFrame) -> pd.DataFrame:
    """Premier quartile, médiane et troisième quartile de chaque variable, par groupe."""
    colonnes: dict[str, pd.Series] = {}
    for defaut, groupe in ((0, "saines"), (1, "défaillantes")):
        variables = scoring.loc[scoring["defaut"] == defaut, list(VARIABLES_ANALYSE)]
        for quantile, nom in QUARTILES.items():
            colonnes[f"{groupe} {nom}"] = variables.quantile(quantile)
    return pd.DataFrame(colonnes).round(1)


def piege_endettement(scoring: pd.DataFrame) -> pd.DataFrame:
    """Médiane du taux d'endettement selon le signe des fonds propres et le groupe.

    Avec des capitaux propres négatifs, le ratio devient négatif : mélangé aux autres, il
    fait croire que les défaillantes sont moins endettées.
    """
    groupes = scoring.groupby(["fonds_propres_negatifs", "defaut"])["taux_d_endettement"]
    return pd.DataFrame(groupes.agg(effectif="size", mediane="median")).round(1)


def taux_par_groupe(scoring: pd.DataFrame, colonne: str) -> pd.DataFrame:
    """Effectif et taux de défaut de l'échantillon pour chaque valeur d'une colonne."""
    groupes = scoring.groupby(colonne, observed=True)["defaut"]
    tableau = pd.DataFrame(groupes.agg(effectif="size", taux_defaut="mean"))
    tableau["taux_defaut"] = tableau["taux_defaut"].round(3)
    return tableau.sort_values("taux_defaut", ascending=False)


def ajouter_libelles(scoring: pd.DataFrame) -> pd.DataFrame:
    """Ajoute le libellé du secteur et la tranche d'âge, plus lisibles dans les tableaux."""
    libelles = {lettre: libelle for lettre, _, _, libelle in SECTIONS_NAF}
    tranches = pd.cut(scoring["age_defaillance"], bins=BORNES_AGE, labels=TRANCHES_AGE, right=False)
    return scoring.assign(secteur=scoring["section_naf"].map(libelles), tranche_age=tranches)


if __name__ == "__main__":
    pd.set_option("display.width", 200)
    table = ajouter_libelles(database.lire_table(NOM_TABLE_SCORING))
    print(f"Table scoring : {len(table)} lignes, {int(table['defaut'].sum())} défaillantes")
    print("\n1) Pouvoir discriminant de chaque variable (AUC univariée)")
    print(pouvoir_discriminant(table).to_string(index=False))
    print("\n2) Quartiles par groupe")
    print(comparer_groupes(table).to_string())
    print("\n3) Le piège du taux d'endettement")
    print(piege_endettement(table).to_string())
    print(f"\n4) {MISE_EN_GARDE}")
    for colonne in ("secteur", "tranche_effectifs", "tranche_age"):
        print(f"\nPar {colonne} :")
        print(taux_par_groupe(table, colonne).head(10).to_string())

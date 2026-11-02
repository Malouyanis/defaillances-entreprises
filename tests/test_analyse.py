"""Tests de l'analyse des signaux financiers."""

import pandas as pd

from src.utils import analyse


def scoring_exemple() -> pd.DataFrame:
    """Six sociétés : les défaillantes ont moins d'autonomie financière que les saines."""
    lignes: dict[str, object] = {
        "defaut": [1, 1, 1, 0, 0, 0],
        "section_naf": ["F", "F", "I", "F", "G", "G"],
        "tranche_effectifs": ["1 à 2"] * 6,
        "age_defaillance": [2.0, 4.0, 6.0, 12.0, 25.0, None],
    }
    for variable in analyse.VARIABLES_ANALYSE:
        if variable not in lignes:
            lignes[variable] = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
    lignes["autonomie_financiere"] = [-10.0, 5.0, 8.0, 30.0, 40.0, None]
    lignes["fonds_propres_negatifs"] = [1.0, 0.0, 0.0, 0.0, 0.0, None]
    lignes["taux_d_endettement"] = [-50.0, 80.0, 60.0, 20.0, 10.0, None]
    return pd.DataFrame(lignes)


def test_auc_univariee() -> None:
    """Séparation parfaite = 0 ou 1 ; aucune séparation = 0,5 ; les vides sont ignorés."""
    defaut = pd.Series([1, 1, 0, 0])
    assert analyse.auc_univariee(pd.Series([3.0, 4.0, 1.0, 2.0]), defaut) == 1.0
    assert analyse.auc_univariee(pd.Series([1.0, 2.0, 3.0, 4.0]), defaut) == 0.0
    assert analyse.auc_univariee(pd.Series([1.0, 1.0, 1.0, 1.0]), defaut) == 0.5
    assert analyse.auc_univariee(pd.Series([3.0, None, 1.0, 2.0]), defaut) == 1.0


def test_pouvoir_discriminant() -> None:
    """L'autonomie financière, plus basse chez les défaillantes, sépare parfaitement."""
    tableau = analyse.pouvoir_discriminant(scoring_exemple())
    autonomie = tableau.set_index("variable").loc["autonomie_financiere"]
    assert autonomie["auc"] == 0.0
    assert autonomie["pouvoir"] == 1.0
    assert autonomie["sens"] == "plus basse"
    assert tableau["pouvoir"].is_monotonic_decreasing


def test_tableaux_par_groupe() -> None:
    """Quartiles par groupe, piège de l'endettement et taux de défaut par secteur."""
    table = analyse.ajouter_libelles(scoring_exemple())
    quartiles = analyse.comparer_groupes(table)
    assert quartiles.loc["autonomie_financiere", "défaillantes médiane"] == 5.0
    piege = analyse.piege_endettement(table)
    assert piege.loc[(1.0, 1), "mediane"] == -50.0
    par_secteur = analyse.taux_par_groupe(table, "secteur")
    assert par_secteur.loc["Construction", "taux_defaut"] == round(2 / 3, 3)
    assert table.loc[0, "tranche_age"] == "moins de 3 ans"

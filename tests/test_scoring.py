"""Tests du modèle de scoring."""

import numpy as np
import pandas as pd

from src.utils import scoring


def scoring_exemple(nombre: int = 400) -> pd.DataFrame:
    """Sociétés fictives : les défaillantes ont moins de liquidité et d'autonomie."""
    generateur = np.random.default_rng(0)
    defaut = np.tile([0, 1], nombre // 2)
    autonomie = generateur.normal(35, 15, nombre) - 25 * defaut
    resultat = generateur.normal(10_000, 20_000, nombre) - 15_000 * defaut
    table = pd.DataFrame(
        {
            "annee": np.repeat([2021, 2022, 2023, 2024], nombre // 4),
            "defaut": defaut,
            "section_naf": generateur.choice(["F", "G", "I"], nombre),
            "ratio_de_liquidite": generateur.normal(200, 50, nombre) - 80 * defaut,
            "autonomie_financiere": autonomie,
            "fonds_propres_negatifs": (autonomie < 0).astype(float),
            "taux_d_endettement": generateur.normal(30, 10, nombre) + 20 * defaut,
            "marge_ebe": generateur.normal(5, 5, nombre) - 4 * defaut,
            "resultat_net": resultat,
            "capacite_de_remboursement": generateur.normal(1, 1, nombre),
            "age_defaillance": generateur.uniform(1, 30, nombre),
        }
    )
    confidentiels = table.index % 5 == 0
    table.loc[confidentiels, ["marge_ebe", "resultat_net", "capacite_de_remboursement"]] = None
    return table


def test_ajouter_variables() -> None:
    """Endettement mis à 0 si fonds propres négatifs ; résultat négatif vide sans compte."""
    table = pd.DataFrame(
        {
            "fonds_propres_negatifs": [0.0, 1.0, 0.0],
            "taux_d_endettement": [40.0, -150.0, 10.0],
            "resultat_net": [-500.0, 2000.0, None],
        }
    )
    resultat = scoring.ajouter_variables(table)
    assert list(resultat["endettement_fonds_propres_positifs"]) == [40.0, 0.0, 10.0]
    assert resultat["resultat_negatif"].iloc[0] == 1.0
    assert resultat["resultat_negatif"].iloc[1] == 0.0
    assert pd.isna(resultat["resultat_negatif"].iloc[2])


def test_decouper_par_annee() -> None:
    """Jusqu'à 2023 pour apprendre, après pour tester, sans aucune ligne commune."""
    entrainement, test = scoring.decouper_par_annee(scoring_exemple())
    assert entrainement["annee"].max() == 2023
    assert test["annee"].min() == 2024
    assert len(entrainement) + len(test) == 400


def test_entrainement_et_evaluation() -> None:
    """Le modèle sépare bien les groupes fictifs et les coefficients ont le bon sens."""
    table = scoring.ajouter_variables(scoring_exemple())
    entrainement, test = scoring.decouper_par_annee(table)
    modele = scoring.entrainer(entrainement)
    assert scoring.auc(modele, test) > 0.85
    probabilites = scoring.probabilites_defaut(modele, test)
    assert probabilites.between(0, 1).all()
    coefs = scoring.coefficients(modele).set_index("variable")["coefficient"]
    assert coefs["ratio_de_liquidite"] < 0
    assert "missingindicator_marge_ebe" in coefs.index


def test_secteur_inconnu() -> None:
    """Un secteur absent de l'entraînement ne fait pas planter la notation."""
    table = scoring.ajouter_variables(scoring_exemple())
    modele = scoring.entrainer(table)
    nouvelle = table.head(1).assign(section_naf="Z")
    assert 0 <= scoring.probabilites_defaut(modele, nouvelle).iloc[0] <= 1

"""Tests de l'échantillon de sociétés saines."""

import pandas as pd

from src.utils import echantillon_sain


def societes_exemple() -> pd.DataFrame:
    """Quatre sociétés : une saine, une défaillante, une association et une société cessée."""
    return pd.DataFrame(
        {
            "siren": pd.Series(
                ["111111111", "222222222", "333333333", "444444444"], dtype="string"
            ),
            "date_creation": pd.to_datetime(
                ["2010-01-01", "2012-01-01", "2005-01-01", "2001-01-01"]
            ),
            "categorie_juridique": pd.Series(["5710", "5499", "9220", "5710"], dtype="string"),
            "etat_administratif": ["A", "A", "A", "C"],
        }
    )


def test_candidats_sains() -> None:
    """Seule la société commerciale active jamais défaillante est candidate."""
    candidats = echantillon_sain.candidats_sains(societes_exemple(), {"222222222"})
    assert list(candidats["siren"]) == ["111111111"]


def test_tirer_sains() -> None:
    """Chaque saine reçoit une date de référence ; une société créée après est écartée."""
    candidats = societes_exemple().assign(
        date_creation=pd.to_datetime(["2010-01-01", "2030-01-01", "2005-01-01", "2001-01-01"])
    )
    dates = pd.Series(pd.to_datetime(["2023-05-10"]))
    sains = echantillon_sain.tirer_sains(candidats, dates, taille=10)
    assert len(sains) == 3
    assert "222222222" not in set(sains["siren"])
    assert set(sains["annee"]) == {2023}


def test_assembler_et_garder_pour_scoring() -> None:
    """La cible vaut 1 pour les défaillantes, 0 pour les saines ; sans comptes, la ligne part."""
    defaillantes = pd.DataFrame({"siren": ["A", "B"], "a_des_comptes": [True, False]})
    sains = pd.DataFrame({"siren": ["C", "D"], "a_des_comptes": [True, True]})
    echantillon = echantillon_sain.assembler(defaillantes, sains)
    assert list(echantillon["defaut"]) == [1, 1, 0, 0]
    scoring = echantillon_sain.garder_pour_scoring(echantillon)
    assert list(scoring["siren"]) == ["A", "C", "D"]

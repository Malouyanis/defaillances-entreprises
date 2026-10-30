"""Tests de la jointure des trois sources."""

import pandas as pd

from src.utils import jointure, nettoyage_comptes


def defaillances_exemple() -> pd.DataFrame:
    """Trois défaillantes (SIREN en type « object », comme le vrai BODACC nettoyé)."""
    return pd.DataFrame(
        {
            "siren": pd.Series(["012345678", "523456789", "999999999"], dtype=object),
            "date_jugement": pd.to_datetime(["2024-03-15", "2024-06-01", "2024-06-01"]),
            "annee": [2024, 2024, 2024],
            "departement": ["75", "59", "13"],
            "procedure": ["Liquidation judiciaire"] * 3,
            "id_annonce": ["A1", "A2", "A3"],
        }
    )


def societes_exemple() -> pd.DataFrame:
    """Profils Sirene des deux premières défaillantes (la troisième n'est pas une société)."""
    return pd.DataFrame(
        {
            "siren": ["012345678", "523456789"],
            "date_creation": pd.to_datetime(["2014-03-15", "1001-01-01"]),
            "secteur": ["Construction", "Commerce"],
        }
    )


def comptes_exemple() -> pd.DataFrame:
    """Trois exercices (SIREN en type « string », comme les vrais comptes nettoyés)."""
    lignes = {
        "siren": ["012345678", "012345678", "523456789"],
        "date_cloture_exercice": pd.to_datetime(["2022-12-31", "2023-12-31", "2020-12-31"]),
        "chiffre_d_affaires": [300_000.0, 250_000.0, 80_000.0],
        "resultat_net": [5_000.0, -40_000.0, 1_000.0],
        "ebe": [10_000.0, -20_000.0, 2_000.0],
        "type_bilan": ["S", "S", "S"],
    }
    for colonne in nettoyage_comptes.RATIOS:
        lignes[colonne] = [1.0, 2.0, 3.0]
    comptes = pd.DataFrame(lignes)
    return comptes.assign(siren=comptes["siren"].astype("string"))


def test_calculer_age() -> None:
    """L'âge est en années ; une date de création impossible donne une case vide."""
    jugement = pd.to_datetime(pd.Series(["2024-03-15", "2024-03-15", "2024-03-15"]))
    creation = pd.to_datetime(pd.Series(["2014-03-15", "1001-01-01", "2028-01-01"]))
    age = jointure.calculer_age(jugement, creation)
    assert age.iloc[0] == 10.0
    assert age.iloc[1:].isna().all()


def test_joindre_sources() -> None:
    """Seules les sociétés restent ; on prend le dernier bilan clos avant le jugement."""
    resultat = jointure.joindre_sources(
        defaillances_exemple(), comptes_exemple(), societes_exemple()
    )
    assert list(resultat["siren"]) == ["012345678", "523456789"]
    assert resultat.loc[0, "chiffre_d_affaires"] == 250_000.0
    assert list(resultat["a_des_comptes"]) == [True, False]
    assert pd.isna(resultat.loc[1, "age_defaillance"])


def test_taux_renseignes() -> None:
    """La part de valeurs renseignées est calculée pour chaque niveau de confidentialité."""
    comptes = comptes_exemple().assign(
        confidentiality=["Public", "Partiellement confidentiel", "Partiellement confidentiel"],
        chiffre_d_affaires=[300_000.0, None, None],
    )
    taux = jointure.taux_renseignes(comptes)
    assert taux.loc["Public", "chiffre_d_affaires"] == 1.0
    assert taux.loc["Partiellement confidentiel", "chiffre_d_affaires"] == 0.0
    assert taux.loc["Partiellement confidentiel", "taux_d_endettement"] == 1.0

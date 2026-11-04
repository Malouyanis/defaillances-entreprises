"""Tests des calculs de la page Finances."""

import pandas as pd

from src.utils import finances


def table_exemple() -> pd.DataFrame:
    """Cinq sociétés : un CA nul (écarté), deux saines et deux défaillantes."""
    return pd.DataFrame(
        {
            "defaut": [0, 0, 1, 1, 1],
            "chiffre_d_affaires": [50_000.0, 2_000_000.0, 120_000.0, 130_000.0, 0.0],
        }
    )


def test_preparer_ca() -> None:
    """Les CA nuls sont écartés et chaque société reçoit son groupe."""
    donnees = finances.preparer_ca(table_exemple())
    assert len(donnees) == 4
    assert set(donnees["groupe"]) == {"Saines", "Défaillantes"}


def test_histogramme_ca() -> None:
    """Chaque société tombe dans une seule tranche ; les parts d'un groupe font 100 %."""
    histo = finances.histogramme_ca(table_exemple())
    assert len(histo) == len(finances.bornes_log()) - 1
    assert histo["Saines"].sum() == 2
    assert histo["Défaillantes"].sum() == 2
    assert histo["part_défaillantes"].sum() == 1.0
    tranche = histo.loc[(histo["debut"] <= 120_000) & (histo["fin"] > 130_000)]
    assert tranche["Défaillantes"].iloc[0] == 2


def test_statistiques_ca() -> None:
    """Médiane et effectif par groupe, en euros."""
    stats = finances.statistiques_ca(table_exemple())
    assert stats.loc["Défaillantes", "effectif"] == 2
    assert stats.loc["Défaillantes", "mediane"] == 125_000
    assert stats["q1"].lt(stats["q3"]).all()

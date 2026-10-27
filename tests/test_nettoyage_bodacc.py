"""Tests du nettoyage des jugements d'ouverture du BODACC."""

import pandas as pd

from src.utils import nettoyage_bodacc

LIQUIDATION = "Jugement d'ouverture de liquidation judiciaire"
REDRESSEMENT = "Jugement d'ouverture d'une procédure de redressement judiciaire"


def test_extraire_siren() -> None:
    """Le SIREN est le premier numéro du registre, sans espaces ; sinon None."""
    assert nettoyage_bodacc.extraire_siren("812 345 678, 812345678") == "812345678"
    assert nettoyage_bodacc.extraire_siren("523456789") == "523456789"
    assert nettoyage_bodacc.extraire_siren("12 345") is None
    assert nettoyage_bodacc.extraire_siren(None) is None


def test_categoriser_procedure() -> None:
    """Chaque nature de jugement tombe dans une des trois procédures."""
    categoriser = nettoyage_bodacc.categoriser_procedure
    assert categoriser(LIQUIDATION) == "Liquidation judiciaire"
    assert categoriser(REDRESSEMENT) == "Redressement judiciaire"
    assert categoriser("Jugement d'ouverture d'une procédure de sauvegarde accélérée") == (
        "Sauvegarde"
    )
    assert (
        categoriser("Jugement d'ouverture d'une procédure de traitement de sortie de crise")
        == "Redressement judiciaire"
    )
    assert categoriser("Autre jugement") is None


def test_corriger_date_jugement() -> None:
    """Une date absente, postérieure à la parution ou trop ancienne est remplacée."""
    jugement = pd.to_datetime(pd.Series(["2025-03-03", None, "5025-03-03", "2019-03-01"]))
    parution = pd.to_datetime(pd.Series(["2025-03-10"] * 4))
    resultat = nettoyage_bodacc.corriger_date_jugement(jugement, parution)
    attendu = pd.to_datetime(pd.Series(["2025-03-03", "2025-03-10", "2025-03-10", "2025-03-10"]))
    assert list(resultat) == list(attendu)


def test_nettoyer_bodacc() -> None:
    """Rectificatifs, outre-mer, hors période et doublons sont écartés ; une ligne par SIREN."""
    raw = pd.DataFrame(
        {
            "id": ["A1", "A2", "A3", "A4", "A5", "A6"],
            "dateparution": [
                "2025-03-10",
                "2025-03-20",
                "2025-03-12",
                "2025-04-02",
                "2025-03-11",
                "2019-01-05",
            ],
            "typeavis": ["annonce", "rectificatif", "annonce", "annonce", "annonce", "annonce"],
            "numerodepartement": ["59", "59", "974", "59", "2A", "75"],
            "registre": [
                "812 345 678, 812345678",
                "812 345 678",
                "434 567 890",
                "812 345 678",
                "523 456 789",
                "345 678 901",
            ],
            "jugement_nature": [REDRESSEMENT, REDRESSEMENT] + [LIQUIDATION] * 4,
            "jugement_date": [
                "2025-03-03",
                "2025-03-03",
                "2025-03-05",
                "2025-03-28",
                None,
                "2018-12-20",
            ],
        }
    )
    resultat = nettoyage_bodacc.nettoyer_bodacc(raw)
    assert list(resultat.columns) == list(nettoyage_bodacc.COLONNES_NETTOYEES)
    assert list(resultat["siren"]) == ["812345678", "523456789"]
    assert list(resultat["procedure"]) == ["Redressement judiciaire", "Liquidation judiciaire"]
    assert resultat.loc[1, "date_jugement"] == pd.Timestamp("2025-03-11")
    assert list(resultat["annee"]) == [2025, 2025]

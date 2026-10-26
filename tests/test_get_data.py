"""Tests de la construction de la table raw à partir des annonces du BODACC."""

import json

import pandas as pd

from src.utils import get_data


def jugement(nature: str, date: str = "2025-03-05") -> str:
    """Fabrique le texte JSON d'un jugement, comme dans le BODACC."""
    return json.dumps({"nature": nature, "date": date})


def test_extraire_jugement() -> None:
    """La nature et la date sont lues dans le JSON ; un champ vide donne None."""
    nature = "Jugement d'ouverture de liquidation judiciaire"
    assert get_data.extraire_jugement(jugement(nature)) == (nature, "2025-03-05")
    assert get_data.extraire_jugement(None) == (None, None)
    assert get_data.extraire_jugement("pas du json") == (None, None)
    assert get_data.extraire_jugement({"nature": nature}) == (nature, None)


def test_garder_jugements_ouverture() -> None:
    """Seuls les jugements d'ouverture sont gardés, avec les colonnes de la table raw."""
    annonces = pd.DataFrame(
        {
            "id": ["A1", "A2", "A3"],
            "dateparution": ["2025-03-10"] * 3,
            "typeavis": ["annonce"] * 3,
            "numerodepartement": ["59", "75", "13"],
            "registre": [["812 345 678", "812345678"], "523 456 789", "434 567 890"],
            "jugement": [
                jugement("Jugement d'ouverture de liquidation judiciaire"),
                jugement("Liste des créances nées après le jugement d'ouverture"),
                jugement("Jugement d'ouverture d'une procédure de redressement judiciaire"),
            ],
        }
    )
    resultat = get_data.garder_jugements_ouverture(annonces)
    assert list(resultat["id"]) == ["A1", "A3"]
    assert list(resultat.columns) == list(get_data.COLONNES_RAW)
    assert resultat.loc[0, "registre"] == "812 345 678, 812345678"

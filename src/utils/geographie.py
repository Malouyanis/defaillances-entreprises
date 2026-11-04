"""Contours et noms des départements, lus dans data/departements.geojson (Admin Express)."""

import json
from functools import cache as memoriser
from pathlib import Path

import config

NOM_FICHIER_GEOJSON = "departements.geojson"


def chemin_geojson() -> Path:
    """Chemin du fichier des contours des départements (à côté de la base, dans data)."""
    return Path(config.CHEMIN_BASE).parent / NOM_FICHIER_GEOJSON


@memoriser
def charger_geojson(chemin: Path) -> dict:
    """Lit une seule fois le fichier des contours des départements."""
    with open(chemin, encoding="utf-8") as fichier:
        return json.load(fichier)


def noms_departements(geojson: dict) -> dict[str, str]:
    """Correspondance code → nom de département (« 75 » → « Paris »)."""
    return {f["properties"]["code"]: f["properties"]["nom"] for f in geojson["features"]}

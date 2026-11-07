"""Contours et noms des départements, lus dans data/departements.geojson (Admin Express)."""

import json
from functools import cache as memoriser
from pathlib import Path

import config

NOM_FICHIER_GEOJSON = "departements.geojson"
DECIMALES = 3
POINTS_MINIMUM = 4


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


def arrondir_anneau(anneau: list, decimales: int = DECIMALES) -> list:
    """Arrondit les points d'un contour et retire ceux qui deviennent identiques au précédent.

    3 décimales de degré font environ 100 m : invisible à l'échelle d'un département.
    """
    points: list[list[float]] = []
    for longitude, latitude in anneau:
        point = [round(longitude, decimales), round(latitude, decimales)]
        if not points or point != points[-1]:
            points.append(point)
    return points


def alleger_geojson(geojson: dict, decimales: int = DECIMALES) -> dict:
    """Renvoie une copie plus légère des contours : mêmes départements, coordonnées arrondies.

    Un contour réduit à moins de 4 points (petite île) est retiré ; le contour extérieur de
    chaque département reste toujours assez grand pour être gardé.
    """
    departements = []
    for departement in geojson["features"]:
        geometrie = departement["geometry"]
        multiple = geometrie["type"] == "MultiPolygon"
        polygones = geometrie["coordinates"] if multiple else [geometrie["coordinates"]]
        alleges = []
        for polygone in polygones:
            anneaux = [arrondir_anneau(anneau, decimales) for anneau in polygone]
            anneaux = [anneau for anneau in anneaux if len(anneau) >= POINTS_MINIMUM]
            if anneaux:
                alleges.append(anneaux)
        coordonnees = alleges if multiple else alleges[0]
        departements.append(
            {
                "type": "Feature",
                "geometry": {"type": geometrie["type"], "coordinates": coordonnees},
                "properties": departement["properties"],
            }
        )
    return {"type": "FeatureCollection", "features": departements}


def main() -> None:
    """Allège data/departements.geojson une fois pour toutes et affiche les tailles."""
    chemin = chemin_geojson()
    avant = chemin.stat().st_size
    with open(chemin, encoding="utf-8") as fichier:
        geojson = json.load(fichier)
    with open(chemin, "w", encoding="utf-8") as fichier:
        json.dump(alleger_geojson(geojson), fichier, separators=(",", ":"))
    apres = chemin.stat().st_size
    print(f"{chemin.name} : {avant / 1000:.0f} Ko → {apres / 1000:.0f} Ko")


if __name__ == "__main__":
    main()

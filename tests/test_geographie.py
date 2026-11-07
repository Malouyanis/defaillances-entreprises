"""Tests des contours des départements et de leur allègement."""

from typing import Any

from src.utils import geographie

CARRE = [[2.12345, 45.0], [3.0, 45.0], [3.0, 46.0], [2.0, 46.0], [2.12345, 45.0]]
ILOT = [[8.00001, 42.0], [8.00002, 42.0], [8.00001, 42.00001], [8.00001, 42.0]]
GEOJSON: dict[str, Any] = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {"code": "75", "nom": "Paris"},
            "geometry": {"type": "Polygon", "coordinates": [CARRE]},
        },
        {
            "type": "Feature",
            "properties": {"code": "2A", "nom": "Corse-du-Sud"},
            "geometry": {"type": "MultiPolygon", "coordinates": [[CARRE], [ILOT]]},
        },
    ],
}


def test_arrondir_anneau() -> None:
    """Les coordonnées sont arrondies et un point devenu identique au précédent disparaît."""
    anneau = geographie.arrondir_anneau([[2.12345, 45.0], [2.12349, 45.0001], [3.0, 45.0]])
    assert anneau == [[2.123, 45.0], [3.0, 45.0]]


def test_alleger_geojson() -> None:
    """Mêmes départements et mêmes noms ; l'îlot réduit à moins de 4 points est retiré."""
    leger = geographie.alleger_geojson(GEOJSON)
    assert geographie.noms_departements(leger) == {"75": "Paris", "2A": "Corse-du-Sud"}
    paris, corse = leger["features"]
    assert paris["geometry"]["coordinates"][0][0] == [2.123, 45.0]
    assert len(corse["geometry"]["coordinates"]) == 1
    assert GEOJSON["features"][0]["geometry"]["coordinates"][0][0] == [2.12345, 45.0]

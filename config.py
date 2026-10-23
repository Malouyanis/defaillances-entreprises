"""Configuration du projet : chemins, sources de données et périmètre de l'étude."""

from pathlib import Path

RACINE = Path(__file__).resolve().parent
DOSSIER_DATA = RACINE / "data"
DOSSIER_RAW = DOSSIER_DATA / "raw"
CHEMIN_BASE = DOSSIER_DATA / "db.sqlite"

ANNEE_DEBUT = 2019
ANNEE_FIN = 2025
DEPARTEMENTS_OUTRE_MER = (
    "971", "972", "973", "974", "975", "976", "977", "978", "986", "987", "988",
)

TIMEOUT_HTTP = 300

BODACC_URL_EXPORT = (
    "https://bodacc-datadila.opendatasoft.com/api/explore/v2.1/catalog/"
    "datasets/annonces-commerciales/exports/json"
)
RATIOS_URL_EXPORT = (
    "https://data.economie.gouv.fr/api/explore/v2.1/catalog/"
    "datasets/ratios_inpi_bce/exports/parquet"
)
SIRENE_URL_STOCK_UNITE_LEGALE = (
    "https://www.data.gouv.fr/api/1/datasets/r/350182c9-148a-46e0-8389-76c2ec1374a3"
)
"""Nettoyage du répertoire Sirene : une ligne par société, avec son profil.

On garde les sociétés (pas les entrepreneurs individuels), leur date de création,
leur secteur d'activité (section NAF), leur taille et leur état (active ou cessée).
"""

from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from src.utils import sirene
from src.utils.nettoyage_comptes import normaliser_siren

CATEGORIE_ENTREPRENEUR_INDIVIDUEL = "1000"
SECTIONS_NAF = (
    ("A", 1, 3, "Agriculture"),
    ("B", 5, 9, "Industries extractives"),
    ("C", 10, 33, "Industrie manufacturière"),
    ("D", 35, 35, "Énergie"),
    ("E", 36, 39, "Eau et déchets"),
    ("F", 41, 43, "Construction"),
    ("G", 45, 47, "Commerce"),
    ("H", 49, 53, "Transports"),
    ("I", 55, 56, "Hébergement et restauration"),
    ("J", 58, 63, "Information et communication"),
    ("K", 64, 66, "Finance et assurance"),
    ("L", 68, 68, "Immobilier"),
    ("M", 69, 75, "Activités spécialisées et scientifiques"),
    ("N", 77, 82, "Services administratifs et de soutien"),
    ("O", 84, 84, "Administration publique"),
    ("P", 85, 85, "Enseignement"),
    ("Q", 86, 88, "Santé et action sociale"),
    ("R", 90, 93, "Arts et loisirs"),
    ("S", 94, 96, "Autres services"),
    ("T", 97, 98, "Ménages employeurs"),
    ("U", 99, 99, "Organismes extraterritoriaux"),
)
TRANCHES_EFFECTIFS = {
    "NN": "Non employeur",
    "00": "0 salarié",
    "01": "1 à 2",
    "02": "3 à 5",
    "03": "6 à 9",
    "11": "10 à 19",
    "12": "20 à 49",
    "21": "50 à 99",
    "22": "100 à 199",
    "31": "200 à 249",
    "32": "250 à 499",
    "41": "500 à 999",
    "42": "1 000 à 1 999",
    "51": "2 000 à 4 999",
    "52": "5 000 à 9 999",
    "53": "10 000 et plus",
}
COLONNES_NETTOYEES = (
    "siren",
    "date_creation",
    "categorie_juridique",
    "section_naf",
    "secteur",
    "tranche_effectifs",
    "categorie_entreprise",
    "etat_administratif",
)


def lire_societes(chemin: Path) -> pd.DataFrame:
    """Lit les colonnes utiles du stock Sirene en écartant dès la lecture les entrepreneurs
    individuels (catégorie juridique 1000), soit une grande partie des 30 millions de lignes.
    """
    type_categorie = pq.read_schema(chemin).field("categorieJuridiqueUniteLegale").type
    valeur_ei: str | int = CATEGORIE_ENTREPRENEUR_INDIVIDUEL
    if not pa.types.is_string(type_categorie) and not pa.types.is_large_string(type_categorie):
        valeur_ei = int(CATEGORIE_ENTREPRENEUR_INDIVIDUEL)
    table = pq.read_table(
        chemin,
        columns=list(sirene.COLONNES_SIRENE_UTILES),
        filters=[("categorieJuridiqueUniteLegale", "!=", valeur_ei)],
    )
    return table.to_pandas()


def section_naf(code_activite: object) -> str | None:
    """Renvoie la lettre de section NAF (A à U) à partir des deux premiers chiffres du code."""
    if not isinstance(code_activite, str) or not code_activite[:2].isdigit():
        return None
    division = int(code_activite[:2])
    for lettre, debut, fin, _ in SECTIONS_NAF:
        if debut <= division <= fin:
            return lettre
    return None


def nettoyer_sirene(societes: pd.DataFrame) -> pd.DataFrame:
    """Renomme, convertit et enrichit les colonnes Sirene ; une ligne par SIREN."""
    libelles_sections = {lettre: libelle for lettre, _, _, libelle in SECTIONS_NAF}
    categorie = societes["categorieJuridiqueUniteLegale"].astype("string").str.strip()
    resultat = pd.DataFrame(
        {
            "siren": normaliser_siren(societes["siren"]),
            "date_creation": pd.to_datetime(societes["dateCreationUniteLegale"], errors="coerce"),
            "categorie_juridique": categorie,
            "section_naf": societes["activitePrincipaleUniteLegale"].map(section_naf),
            "tranche_effectifs": societes["trancheEffectifsUniteLegale"]
            .astype("string")
            .str.zfill(2)
            .map(TRANCHES_EFFECTIFS),
            "categorie_entreprise": societes["categorieEntreprise"],
            "etat_administratif": societes["etatAdministratifUniteLegale"],
        }
    )
    resultat["secteur"] = resultat["section_naf"].map(libelles_sections)
    societes_seules = resultat.loc[categorie != CATEGORIE_ENTREPRENEUR_INDIVIDUEL]
    uniques = societes_seules.dropna(subset=["siren"]).drop_duplicates(subset="siren")
    return uniques.loc[:, list(COLONNES_NETTOYEES)].reset_index(drop=True)


if __name__ == "__main__":
    societes_brutes = lire_societes(sirene.chemin_fichier_sirene())
    print(f"Unités légales lues (hors entrepreneurs individuels) : {len(societes_brutes)}")
    societes_propres = nettoyer_sirene(societes_brutes)
    print(f"Sociétés après nettoyage : {len(societes_propres)}")
    print(societes_propres["etat_administratif"].value_counts(dropna=False).to_string())
    print(societes_propres["secteur"].value_counts(dropna=False).head(10).to_string())
    print(societes_propres["tranche_effectifs"].value_counts(dropna=False).head(8).to_string())
    print(societes_propres["categorie_entreprise"].value_counts(dropna=False).to_string())
    print(societes_propres["date_creation"].describe().to_string())

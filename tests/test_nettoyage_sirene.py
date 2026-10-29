"""Tests du nettoyage du répertoire Sirene."""

from pathlib import Path

import pandas as pd

from src.utils import nettoyage_sirene


def unites_exemple() -> pd.DataFrame:
    """Fabrique trois unités légales : une SAS, une SARL cessée et un entrepreneur individuel."""
    return pd.DataFrame(
        {
            "siren": ["012345678", "523456789", "434567890"],
            "dateCreationUniteLegale": ["2015-04-01", "2019-09-15", "2020-01-10"],
            "categorieJuridiqueUniteLegale": ["5710", "5499", "1000"],
            "activitePrincipaleUniteLegale": ["56.10A", "43.21A", "47.11B"],
            "trancheEffectifsUniteLegale": ["11", "NN", "00"],
            "categorieEntreprise": ["PME", None, "PME"],
            "etatAdministratifUniteLegale": ["A", "C", "A"],
        }
    )


def test_section_naf() -> None:
    """La section est trouvée à partir des deux premiers chiffres du code NAF."""
    assert nettoyage_sirene.section_naf("56.10A") == "I"
    assert nettoyage_sirene.section_naf("43.21A") == "F"
    assert nettoyage_sirene.section_naf("01.11Z") == "A"
    assert nettoyage_sirene.section_naf(None) is None
    assert nettoyage_sirene.section_naf("00.00Z") is None


def test_nettoyer_sirene() -> None:
    """Les entrepreneurs individuels sont écartés ; secteur et taille reçoivent un libellé."""
    resultat = nettoyage_sirene.nettoyer_sirene(unites_exemple())
    assert list(resultat.columns) == list(nettoyage_sirene.COLONNES_NETTOYEES)
    assert list(resultat["siren"]) == ["012345678", "523456789"]
    assert list(resultat["secteur"]) == ["Hébergement et restauration", "Construction"]
    assert list(resultat["tranche_effectifs"]) == ["10 à 19", "Non employeur"]
    assert resultat.loc[1, "date_creation"] == pd.Timestamp("2019-09-15")
    assert resultat.loc[1, "etat_administratif"] == "C"


def test_lire_societes(tmp_path: Path) -> None:
    """La lecture écarte les entrepreneurs individuels dès le fichier Parquet."""
    chemin = tmp_path / "sirene.parquet"
    unites_exemple().to_parquet(chemin)
    resultat = nettoyage_sirene.lire_societes(chemin)
    assert list(resultat["siren"]) == ["012345678", "523456789"]


def test_lire_societes_categorie_numerique(tmp_path: Path) -> None:
    """La lecture marche aussi quand la catégorie juridique est stockée comme un nombre."""
    chemin = tmp_path / "sirene.parquet"
    unites = unites_exemple().assign(categorieJuridiqueUniteLegale=[5710, 5499, 1000])
    unites.to_parquet(chemin)
    resultat = nettoyage_sirene.lire_societes(chemin)
    assert len(resultat) == 2
    assert list(nettoyage_sirene.nettoyer_sirene(resultat)["categorie_juridique"]) == [
        "5710",
        "5499",
    ]

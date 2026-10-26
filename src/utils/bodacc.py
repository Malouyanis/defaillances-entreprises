"""Téléchargement des annonces de procédures collectives publiées au BODACC."""

import json
import sys
from pathlib import Path

import requests

import config

COLONNES_BODACC = (
    "id",
    "dateparution",
    "typeavis",
    "familleavis",
    "numerodepartement",
    "departement_nom_officiel",
    "region_nom_officiel",
    "tribunal",
    "ville",
    "cp",
    "registre",
    "listepersonnes",
    "jugement",
)


def periode_mois(annee: int, mois: int) -> tuple[str, str]:
    """Renvoie le premier jour du mois (inclus) et le premier jour du mois suivant (exclu)."""
    debut = f"{annee}-{mois:02d}-01"
    fin = f"{annee + 1}-01-01" if mois == 12 else f"{annee}-{mois + 1:02d}-01"
    return debut, fin


def filtre_procedures_collectives(annee: int, mois: int) -> str:
    """Construit le filtre de l'API : procédures collectives publiées pendant le mois."""
    debut, fin = periode_mois(annee, mois)
    return (
        f'familleavis="collective" and dateparution>="{debut}" '
        f'and dateparution<"{fin}"'
    )


def chemin_fichier_mois(annee: int, mois: int) -> Path:
    """Chemin du fichier brut d'un mois dans data/raw/bodacc/."""
    return config.DOSSIER_RAW / "bodacc" / f"bodacc_{annee}-{mois:02d}.json"


def telecharger_mois(annee: int, mois: int, forcer: bool = False) -> Path:
    """Télécharge les annonces d'un mois et les enregistre telles quelles en JSON.

    Un mois déjà présent n'est pas retéléchargé, sauf si forcer=True. Le fichier est
    d'abord écrit sous un nom temporaire pour ne jamais laisser de fichier incomplet.
    """
    chemin = chemin_fichier_mois(annee, mois)
    if chemin.exists() and not forcer:
        return chemin
    chemin.parent.mkdir(parents=True, exist_ok=True)
    parametres = {
        "where": filtre_procedures_collectives(annee, mois),
        "select": ",".join(COLONNES_BODACC),
    }
    reponse = requests.get(
        config.BODACC_URL_EXPORT, params=parametres, timeout=config.TIMEOUT_HTTP
    )
    reponse.raise_for_status()
    chemin_temporaire = chemin.with_suffix(".tmp")
    chemin_temporaire.write_bytes(reponse.content)
    chemin_temporaire.replace(chemin)
    return chemin


def mois_de_la_periode(annee_debut: int, annee_fin: int) -> list[tuple[int, int]]:
    """Liste les couples (année, mois) de la période, bornes incluses."""
    return [(annee, mois) for annee in range(annee_debut, annee_fin + 1) for mois in range(1, 13)]


def telecharger_periode(
    annee_debut: int = config.ANNEE_DEBUT, annee_fin: int = config.ANNEE_FIN
) -> list[Path]:
    """Télécharge tous les mois de la période étudiée et renvoie les fichiers obtenus."""
    chemins = []
    for annee, mois in mois_de_la_periode(annee_debut, annee_fin):
        chemins.append(telecharger_mois(annee, mois))
        print(f"BODACC {annee}-{mois:02d} : OK")
    return chemins


def compter_annonces(chemin: Path) -> int:
    """Compte les annonces contenues dans un fichier brut."""
    return len(json.loads(chemin.read_text(encoding="utf-8")))


if __name__ == "__main__":
    if len(sys.argv) == 3:
        annee_test, mois_test = int(sys.argv[1]), int(sys.argv[2])
    else:
        annee_test, mois_test = 2025, 3
    fichier = telecharger_mois(annee_test, mois_test)
    print(f"{compter_annonces(fichier)} annonces enregistrées dans {fichier}")

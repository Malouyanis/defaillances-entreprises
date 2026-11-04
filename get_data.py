"""Téléchargement des données brutes : point d'entrée exigé par le projet.

Lance « python get_data.py » (ou « python get_data.py 2024 2025 » pour une période plus
courte). Le script télécharge le BODACC, les ratios financiers BCE/INPI et le stock Sirene
dans data/raw/, puis écrit la table raw dans data/db.sqlite. Il faut ensuite lancer
« python clean_data.py ». La base déjà construite est fournie dans le dépôt : ces deux
scripts ne servent qu'à tout reconstruire depuis les sources (environ 1,5 Go à télécharger).
"""

import sys

import config
from src.utils.get_data import recuperer_donnees

AVERTISSEMENT = (
    "Téléchargement des sources (environ 1,5 Go) : comptez plusieurs minutes. "
    "La base fournie dans le dépôt suffit pour lancer le dashboard (python main.py)."
)


def lire_periode(arguments: list[str]) -> tuple[int, int]:
    """Lit l'année de début et de fin passées en arguments ; sans arguments, toute la période."""
    if len(arguments) == 2:
        debut, fin = int(arguments[0]), int(arguments[1])
    else:
        debut, fin = config.ANNEE_DEBUT, config.ANNEE_FIN
    if not config.ANNEE_DEBUT <= debut <= fin <= config.ANNEE_FIN:
        raise ValueError(f"Période attendue entre {config.ANNEE_DEBUT} et {config.ANNEE_FIN}")
    return debut, fin


def main() -> None:
    """Télécharge les sources de la période choisie et écrit la table raw."""
    debut, fin = lire_periode(sys.argv[1:])
    print(AVERTISSEMENT)
    table = recuperer_donnees(debut, fin)
    print(f"Table raw : {len(table)} jugements d'ouverture ({debut}-{fin})")
    print("Étape suivante : python clean_data.py")


if __name__ == "__main__":
    main()

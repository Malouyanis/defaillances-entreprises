"""Notation : transformer les probabilités du modèle en notes de A (sûr) à E (risqué).

Le modèle apprend sur un échantillon où près d'une société sur deux fait défaut, alors que le
vrai taux annuel est bien plus bas. Ses probabilités classent bien les sociétés, mais elles sont
trop hautes : on les recale sur un taux de référence, puis on range les sociétés en cinq notes.
"""

import pandas as pd
from sklearn.pipeline import Pipeline

from src.utils import database, scoring

NOTES = ("A", "B", "C", "D", "E")
QUANTILES_SEUILS = (0.2, 0.4, 0.6, 0.8)
TAUX_DEFAUT_REFERENCE = 0.01
EXPLICATION_TAUX = (
    "Taux de référence de 1 % par an : hypothèse d'ordre de grandeur, à remplacer par un taux"
    " officiel si on en trouve un ; il change le niveau des probabilités, pas l'ordre des notes."
)


def recaler(
    probabilites: pd.Series, taux_echantillon: float, taux_reference: float = TAUX_DEFAUT_REFERENCE
) -> pd.Series:
    """Ramène des probabilités apprises sur l'échantillon au taux de défaut de référence.

    On multiplie la cote p / (1 - p) par le rapport des cotes des deux taux (correction
    d'échantillonnage) : l'ordre des sociétés ne change pas, seul le niveau baisse.
    """
    rapport = (taux_reference / (1 - taux_reference)) / (taux_echantillon / (1 - taux_echantillon))
    cote = probabilites / (1 - probabilites) * rapport
    return cote / (1 + cote)


def calculer_seuils(probabilites_entrainement: pd.Series) -> list[float]:
    """Seuils entre les notes : les quintiles des probabilités sur les années d'entraînement."""
    return [float(probabilites_entrainement.quantile(q)) for q in QUANTILES_SEUILS]


def attribuer_notes(probabilites: pd.Series, seuils: list[float]) -> pd.Series:
    """Range chaque société dans une note, de A (risque le plus faible) à E (le plus fort)."""
    bornes = [-float("inf"), *seuils, float("inf")]
    return pd.cut(probabilites, bins=bornes, labels=list(NOTES)).rename("note")


def grille_de_notation(
    notes: pd.Series, defaut: pd.Series, probabilites_recalees: pd.Series
) -> pd.DataFrame:
    """Tableau par note : effectif, part, taux de défaut observé et probabilité recalée moyenne."""
    table = pd.DataFrame({"note": notes, "defaut": defaut, "pd_recalee": probabilites_recalees})
    grille = table.groupby("note", observed=False).agg(
        effectif=("defaut", "size"),
        taux_defaut_observe=("defaut", "mean"),
        pd_recalee_moyenne=("pd_recalee", "mean"),
    )
    grille.insert(1, "part", grille["effectif"] / grille["effectif"].sum())
    return grille.round(4)


def est_croissante(grille: pd.DataFrame) -> bool:
    """Vrai si le taux de défaut observé augmente de note en note (de A à E)."""
    return bool(grille["taux_defaut_observe"].is_monotonic_increasing)


def noter_test(modele: Pipeline, entrainement: pd.DataFrame, test: pd.DataFrame) -> pd.DataFrame:
    """Calcule la grille de notation des années de test avec les seuils de l'entraînement."""
    probas_entrainement = scoring.probabilites_defaut(modele, entrainement)
    probas_test = scoring.probabilites_defaut(modele, test)
    seuils = calculer_seuils(probas_entrainement)
    notes = attribuer_notes(probas_test, seuils)
    recalees = recaler(probas_test, float(entrainement["defaut"].mean()))
    return grille_de_notation(notes, test["defaut"], recalees)


def main() -> None:
    """Point d'entrée quand le module est lancé seul : python -m src.utils.notation."""
    pd.set_option("display.width", 200)
    table = scoring.ajouter_variables(database.lire_table(scoring.NOM_TABLE_SCORING))
    entrainement, test = scoring.decouper_par_annee(table)
    modele = scoring.entrainer(entrainement)
    grille = noter_test(modele, entrainement, test)
    print("Grille de notation sur les années de test (2024-2025) :")
    print(grille.to_string())
    print(f"\nTaux de défaut croissant de A à E : {est_croissante(grille)}")
    print(EXPLICATION_TAUX)


if __name__ == "__main__":
    main()

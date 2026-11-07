"""Finances : distribution du chiffre d'affaires des sociétés saines et défaillantes.

Prépare les données de l'histogramme du chiffre d'affaires (la variable continue exigée pour
le tableau de bord). Le CA va de quelques milliers à plusieurs millions d'euros : on le compte
par tranches d'égale largeur sur une échelle logarithmique.
"""

import numpy as np
import pandas as pd

from src.utils import database

NOM_TABLE_SCORING = "scoring"
LOG_MIN = 3.0
LOG_MAX = 8.0
PAS_LOG = 0.25
LIBELLES_GROUPES = {0: "Saines", 1: "Défaillantes"}


def preparer_ca(table: pd.DataFrame) -> pd.DataFrame:
    """Garde les CA strictement positifs et ajoute le groupe (Saines ou Défaillantes)."""
    positifs = table.loc[table["chiffre_d_affaires"] > 0, ["defaut", "chiffre_d_affaires"]]
    return positifs.assign(groupe=positifs["defaut"].map(LIBELLES_GROUPES))


def bornes_log() -> np.ndarray:
    """Bornes des tranches, en euros : de 1 000 € à 100 M€, un pas de 0,25 en log10."""
    return 10 ** np.arange(LOG_MIN, LOG_MAX + PAS_LOG / 2, PAS_LOG)


def histogramme_ca(table: pd.DataFrame) -> pd.DataFrame:
    """Effectif et part de chaque groupe par tranche de CA (les CA hors bornes sont rabattus)."""
    donnees = preparer_ca(table)
    bornes = bornes_log()
    ca = donnees["chiffre_d_affaires"].clip(bornes[0], bornes[-1] * 0.999)
    tranches = pd.cut(ca, bins=list(bornes), right=False)
    comptes = donnees.groupby([tranches, donnees["groupe"]], observed=False).size()
    histo = comptes.unstack("groupe", fill_value=0).reset_index(drop=True)
    histo.insert(0, "debut", bornes[:-1])
    histo.insert(1, "fin", bornes[1:])
    for groupe in LIBELLES_GROUPES.values():
        if groupe in histo:
            histo[f"part_{groupe.lower()}"] = (histo[groupe] / histo[groupe].sum()).round(4)
    return histo


def statistiques_ca(table: pd.DataFrame) -> pd.DataFrame:
    """Effectif, quartiles et moyenne du CA par groupe, en euros arrondis."""
    donnees = preparer_ca(table)
    groupes = donnees.groupby("groupe")["chiffre_d_affaires"]
    stats = pd.DataFrame(
        groupes.agg(
            effectif="size",
            q1=lambda ca: ca.quantile(0.25),
            mediane="median",
            q3=lambda ca: ca.quantile(0.75),
            moyenne="mean",
        )
    )
    return stats.round(0)


def main() -> None:
    """Point d'entrée quand le module est lancé seul : python -m src.utils.finances."""
    pd.set_option("display.width", 200)
    scoring = database.lire_table(NOM_TABLE_SCORING)
    print("Chiffre d'affaires du dernier exercice (CA > 0), en euros :")
    print(statistiques_ca(scoring).to_string())
    histo = histogramme_ca(scoring)
    print(f"\nHistogramme : {len(histo)} tranches de 1 000 € à 100 M€ (échelle logarithmique)")
    print(histo.astype({"debut": int, "fin": int}).to_string(index=False))


if __name__ == "__main__":
    main()

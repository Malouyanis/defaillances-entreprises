"""Modèle de scoring : une régression logistique qui estime le risque de défaillance.

Le modèle apprend sur les années 2019 à 2023 et il est jugé sur 2024-2025, des années
qu'il n'a jamais vues : c'est la situation réelle d'une banque qui note des entreprises
avec un modèle construit sur le passé. Les effectifs et la catégorie d'entreprise sont
exclus : Sirene donne leur état actuel, mis à jour après la défaillance (fuite d'information).
"""

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.utils import database

NOM_TABLE_SCORING = "scoring"
ANNEE_FIN_ENTRAINEMENT = 2023
VARIABLES_NUMERIQUES = (
    "ratio_de_liquidite",
    "autonomie_financiere",
    "fonds_propres_negatifs",
    "endettement_fonds_propres_positifs",
    "marge_ebe",
    "resultat_negatif",
    "capacite_de_remboursement",
    "age_defaillance",
)
VARIABLES_CATEGORIELLES = ("section_naf",)
VARIABLES_MODELE = (*VARIABLES_NUMERIQUES, *VARIABLES_CATEGORIELLES)


def ajouter_variables(scoring: pd.DataFrame) -> pd.DataFrame:
    """Ajoute deux variables construites à partir des constats de l'analyse (J12).

    - endettement_fonds_propres_positifs : le taux d'endettement seulement quand les
      fonds propres sont positifs (0 sinon), pour déjouer le piège du ratio négatif ;
    - resultat_negatif : 1 si la société perd de l'argent, 0 sinon, vide sans compte de
      résultat (le montant en euros dépend trop de la taille de la société).
    """
    positifs = scoring["fonds_propres_negatifs"] == 0
    endettement = scoring["taux_d_endettement"].where(positifs, 0.0)
    resultat = scoring["resultat_net"]
    negatif = (resultat < 0).astype(float).where(resultat.notna())
    return scoring.assign(endettement_fonds_propres_positifs=endettement, resultat_negatif=negatif)


def decouper_par_annee(
    scoring: pd.DataFrame, annee_fin: int = ANNEE_FIN_ENTRAINEMENT
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Sépare les années d'entraînement (jusqu'à annee_fin) des années de test (après)."""
    entrainement = scoring["annee"] <= annee_fin
    return scoring.loc[entrainement], scoring.loc[~entrainement]


def construire_modele() -> Pipeline:
    """Assemble la préparation des variables et la régression logistique.

    Valeurs vides remplacées par la médiane, avec une colonne « était vide » (les comptes
    confidentiels n'ont pas de marge ni de résultat) ; variables ramenées à la même échelle ;
    secteur codé en colonnes 0/1.
    """
    numeriques = make_pipeline(
        SimpleImputer(strategy="median", add_indicator=True), StandardScaler()
    )
    categorielles = OneHotEncoder(handle_unknown="ignore")
    preparation = ColumnTransformer(
        [
            ("numeriques", numeriques, list(VARIABLES_NUMERIQUES)),
            ("categorielles", categorielles, list(VARIABLES_CATEGORIELLES)),
        ],
        verbose_feature_names_out=False,
    )
    return Pipeline(
        [("preparation", preparation), ("regression", LogisticRegression(max_iter=1000))]
    )


def entrainer(table: pd.DataFrame) -> Pipeline:
    """Entraîne le modèle sur une table qui contient les variables et la colonne defaut."""
    modele = construire_modele()
    modele.fit(table[list(VARIABLES_MODELE)], table["defaut"])
    return modele


def probabilites_defaut(modele: Pipeline, table: pd.DataFrame) -> pd.Series:
    """Probabilité de défaillance estimée par le modèle pour chaque société."""
    probabilites = modele.predict_proba(table[list(VARIABLES_MODELE)])[:, 1]
    return pd.Series(probabilites, index=table.index, name="probabilite_defaut")


def auc(modele: Pipeline, table: pd.DataFrame) -> float:
    """AUC du modèle : probabilité qu'une défaillante ait un score plus élevé qu'une saine."""
    return float(roc_auc_score(table["defaut"], probabilites_defaut(modele, table)))


def coefficients(modele: Pipeline) -> pd.DataFrame:
    """Coefficients de la régression, du plus influent au moins influent.

    Les variables sont à la même échelle : un coefficient positif augmente le risque,
    un coefficient négatif le diminue, et sa taille mesure la force de l'effet.
    """
    noms = modele.named_steps["preparation"].get_feature_names_out()
    valeurs = modele.named_steps["regression"].coef_[0]
    tableau = pd.DataFrame({"variable": noms, "coefficient": valeurs.round(3)})
    ordre = tableau["coefficient"].abs().sort_values(ascending=False).index
    return tableau.loc[ordre].reset_index(drop=True)


def main() -> None:
    """Point d'entrée quand le module est lancé seul : python -m src.utils.scoring."""
    scoring = ajouter_variables(database.lire_table(NOM_TABLE_SCORING))
    entrainement, test = decouper_par_annee(scoring)
    for nom, table in (("Entraînement (2019-2023)", entrainement), ("Test (2024-2025)", test)):
        print(f"{nom} : {len(table)} sociétés, {table['defaut'].mean():.1%} de défaillantes")
    modele = entrainer(entrainement)
    print(f"\nAUC entraînement : {auc(modele, entrainement):.3f}")
    print(f"AUC test         : {auc(modele, test):.3f}")
    print("(meilleure variable seule en J12 : AUC 0,719 pour le résultat net)")
    tableau = coefficients(modele)
    secteurs = tableau["variable"].str.startswith("section_naf_")
    print("\nCoefficients des variables financières (même échelle) :")
    print(tableau.loc[~secteurs].to_string(index=False))
    print("\nCoefficients des secteurs (positif = secteur plus risqué) :")
    print(tableau.loc[secteurs].to_string(index=False))


if __name__ == "__main__":
    main()

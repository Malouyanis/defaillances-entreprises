"""Tests de la notation A à E."""

import pandas as pd
import pytest

from src.utils import notation


def test_recaler_baisse_sans_changer_l_ordre() -> None:
    """Au taux de l'échantillon rien ne bouge ; à 1 % tout baisse, dans le même ordre."""
    probas = pd.Series([0.1, 0.5, 0.9])
    assert notation.recaler(probas, 0.45, 0.45).tolist() == pytest.approx([0.1, 0.5, 0.9])
    recalees = notation.recaler(probas, 0.5, 0.01)
    assert recalees.iloc[1] == pytest.approx(0.01)
    assert (recalees < probas).all()
    assert recalees.is_monotonic_increasing


def test_seuils_et_notes() -> None:
    """Les quintiles coupent en cinq notes égales, de A (faible risque) à E."""
    probas = pd.Series([i / 100 for i in range(1, 101)])
    seuils = notation.calculer_seuils(probas)
    assert len(seuils) == 4
    notes = notation.attribuer_notes(probas, seuils)
    assert notes.iloc[0] == "A"
    assert notes.iloc[-1] == "E"
    assert notes.value_counts().tolist() == [20] * 5


def test_grille_de_notation() -> None:
    """La grille compte les sociétés et le taux de défaut de chaque note."""
    notes = pd.Series(pd.Categorical(["A", "A", "C", "E", "E"], categories=list(notation.NOTES)))
    defaut = pd.Series([0, 0, 1, 1, 1])
    recalees = pd.Series([0.001, 0.002, 0.01, 0.05, 0.07])
    grille = notation.grille_de_notation(notes, defaut, recalees)
    assert grille.loc["A", "effectif"] == 2
    assert grille.loc["B", "effectif"] == 0
    assert grille.loc["E", "taux_defaut_observe"] == 1.0
    assert grille["part"].sum() == pytest.approx(1.0)
    assert notation.est_croissante(grille.dropna())

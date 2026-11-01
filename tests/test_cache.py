"""Tests du cache des tables et du bouton de mise à jour."""

from pathlib import Path

import pandas as pd

from src.components import mise_a_jour
from src.utils import cache, database


def test_cache_garde_la_table_jusqu_au_vidage(tmp_path: Path) -> None:
    """La table est lue une fois ; après vider_cache(), la nouvelle version est relue."""
    chemin = tmp_path / "essai.sqlite"
    database.ecrire_table(pd.DataFrame({"valeur": [1]}), "essai", chemin)
    cache.vider_cache()
    assert cache.charger_table("essai", chemin)["valeur"].tolist() == [1]
    database.ecrire_table(pd.DataFrame({"valeur": [2]}), "essai", chemin)
    assert cache.charger_table("essai", chemin)["valeur"].tolist() == [1]
    cache.vider_cache()
    assert cache.charger_table("essai", chemin)["valeur"].tolist() == [2]


def test_copie_protegee(tmp_path: Path) -> None:
    """Modifier la table reçue ne modifie pas la version gardée en mémoire."""
    chemin = tmp_path / "essai.sqlite"
    database.ecrire_table(pd.DataFrame({"valeur": [1]}), "essai", chemin)
    cache.vider_cache()
    table = cache.charger_table("essai", chemin)
    table.loc[0, "valeur"] = 99
    assert cache.charger_table("essai", chemin).loc[0, "valeur"] == 1


def test_bouton_vide_le_cache(tmp_path: Path) -> None:
    """Le clic sur le bouton vide le cache et renvoie un message de confirmation."""
    chemin = tmp_path / "essai.sqlite"
    database.ecrire_table(pd.DataFrame({"valeur": [1]}), "essai", chemin)
    cache.charger_table("essai", chemin)
    message = mise_a_jour.mettre_a_jour(1)
    assert cache.tables_en_cache() == 0
    assert message.startswith("Données rechargées")

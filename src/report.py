"""Génération du rapport de nettoyage NutriScope (TP 9)."""

from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import List, Dict
from src.models import Report
from src.config import KEY_NUTRIENTS
import pandas as pd

SOURCE = "Export Open Food Facts, périmètre France"
CREDIT = (
    "Données issues d'[Open Food Facts](https://world.openfoodfacts.org) "
    "(ODbL pour la base, CC-BY-SA pour les images)."
)
MACRO_COLUMNS = ["fat_100g", "carbohydrates_100g", "proteins_100g"]


@dataclass
class SousPartieMarkdown:
    titre: str
    texte: dict[str, str]

    def __str__(self) -> str:
        res = f"## {self.titre}"
        for nom, resultats in self.texte.items():
            res = res + f"\n ### {nom} \n {resultats}"
        return res

def _dict_to_string(dic: Dict[str, str]) -> str:
    res = ""
    for nom, element in dic.items():
        res = res + f" {nom} : {element}\n\n"
    return res

def _dict_to_tab_markdown(dic: Dict[str, str]) -> str:
    res = f"\n\n | {" | ".join([str(nom) for nom in dic.keys()])} |\n"
    res  = res + "|---" * len(dic) + "|\n"
    res = res + f"| {" | ".join([str(val) for val in dic.values()])} |\n"
    return res

def _anomalies(before: pd.DataFrame, after: pd.DataFrame) -> SousPartieMarkdown:
    before_values = _anomalies_list(before)
    after_values = _anomalies_list(after)
    return SousPartieMarkdown(
        "3. Anomalies métier",
        {
            "Avant nettoyage : ": before_values,
            "Après nettoyage : ": after_values
        }
    )


def _anomalies_list(df: pd.DataFrame) -> str:
    anomalies = {
        "Sucres > 100 g ": (df["sugars_100g"] > 100).sum(),
        "Matières grasses > 100 g ": (df["fat_100g"] > 100).sum(),
        "Sel > 100 g ": (df["salt_100g"] > 100).sum(),
        "Protéines > 100 g ": (df["proteins_100g"] > 100).sum(),
        "Énergie > 3 800 kJ ": (df["energy_100g"] > 3800).sum(),
        "Somme des macronutriments > 100 g ": (df[MACRO_COLUMNS].sum(axis=1) > 100).sum(),
        "Valeurs négatives ": _dict_to_tab_markdown((df[["energy_100g", *KEY_NUTRIENTS[1:]]] < 0).sum().to_dict()),
    }
    return _dict_to_string(anomalies)


def _volumetry(avant: pd.DataFrame, apres: pd.DataFrame) -> SousPartieMarkdown:
    return SousPartieMarkdown(
        "1. Volumétrie",
        {
            "Avant nettoyage : ": str(len(avant)),
            "Après nettoyage : ": str(len(apres))
        }
    )


def _rules(journal: List[Report]) -> SousPartieMarkdown:
    res = SousPartieMarkdown("2. Rapport de nettoyage", {})
    res.texte["Tableau des rapports : "] = (f"| Règle | Lignes avant | Lignes après | Lignes touchées | Détail |\n"
                                            f"|---|---|---|---|---|\n")
    for rapport in journal:
        res.texte["Tableau des rapports : "] = res.texte["Tableau des rapports : "] + rapport.to_tab_markdown() + "\n"
    return res


def _missing(avant: pd.DataFrame, apres: pd.DataFrame):
    return SousPartieMarkdown(
        "4. Manquants",
        {
            "Avant nettoyage : ": _dict_to_string(avant[KEY_NUTRIENTS].isna().sum()),
            "Après nettoyage : ": _dict_to_string(apres[KEY_NUTRIENTS].isna().sum())
        }
    )


def _product_by_food_group(apres: pd.DataFrame):
    res = _dict_to_string(apres.groupby("food_group")["food_group"].count())
    return SousPartieMarkdown(
        "5. Produits par rayon après nettoyage",
        {
            "Produits par rayon : ": res
        }
    )


def _columns(before, after):
    added = sorted(set(after.columns) - set(before.columns))
    removed = sorted(set(before.columns) - set(after.columns))
    return SousPartieMarkdown(
        " 6. Colonnes ajoutées et retirées",
        {
            "Colonnes ajoutées : ": ", ".join(f"`{col}`" for col in added),
            "Colonnes supprimées : ": ", ".join(f"`{col}`" for col in removed),
        }
    )


def generer_rapport(
        avant: pd.DataFrame, apres: pd.DataFrame, journal: list, chemin: Path
) -> None:
    """Écrit le rapport de nettoyage au format Markdown.

    Le contenu est déterministe : relancer la fonction sur les mêmes données
    produit le même fichier, à la date de génération près.

    Args:
        avant: données avant nettoyage.
        apres: données après nettoyage.
        journal: comptes rendus des règles appliquées, dans l'ordre. Chaque
            élément expose `name` (str), `rows_touched` (int) et
            `details` (dict sous-règle -> nombre de lignes).
        chemin: fichier de sortie, par exemple `docs/data/rapport_nettoyage.md`.
    """
    header = [
        "# Rapport de nettoyage NutriScope",
        "",
        f"- **Date** : {date.today().isoformat()}",
        f"- **Source** : {SOURCE}",
        f"- **Crédit** : {CREDIT}",
        "",
    ]
    sections = [
        _volumetry(avant, apres),
        _rules(journal),
        _anomalies(avant, apres),
        _missing(avant, apres),
        _product_by_food_group(apres),
        _columns(avant, apres),
    ]
    lines = header + [str(section) + "\n\n" for section in sections]
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text("\n".join(lines), encoding="utf-8")
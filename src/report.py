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
class MarkdownSubSection:
    title: str
    content: dict[str, str]

    def __str__(self) -> str:
        result = f"## {self.title}"
        for name, values in self.content.items():
            result = result + f"\n ### {name} \n {values}"
        return result


def _dict_to_string(data: Dict[str, str]) -> str:
    result = ""
    for name, item in data.items():
        result = result + f" {name} : {item}\n\n"
    return result


def _dict_to_markdown_table(data: Dict[str, str]) -> str:
    result = f"\n\n | {' | '.join([str(name) for name in data.keys()])} |\n"
    result = result + "|---" * len(data) + "|\n"
    result = result + f"| {' | '.join([str(value) for value in data.values()])} |\n"
    return result


def _anomalies(before: pd.DataFrame, after: pd.DataFrame) -> MarkdownSubSection:
    before_values = _anomalies_list(before)
    after_values = _anomalies_list(after)

    return MarkdownSubSection(
        "3. Anomalies métier",
        {
            "Avant nettoyage : ": before_values,
            "Après nettoyage : ": after_values,
        },
    )


def _anomalies_list(df: pd.DataFrame) -> str:
    anomalies = {
        "Sucres > 100 g ": (df["sugars_100g"] > 100).sum(),
        "Matières grasses > 100 g ": (df["fat_100g"] > 100).sum(),
        "Sel > 100 g ": (df["salt_100g"] > 100).sum(),
        "Protéines > 100 g ": (df["proteins_100g"] > 100).sum(),
        "Énergie > 3 800 kJ ": (df["energy_100g"] > 3800).sum(),
        "Somme des macronutriments > 100 g ": (
                df[MACRO_COLUMNS].sum(axis=1) > 100
        ).sum(),
        "Valeurs négatives ": _dict_to_markdown_table(
            (df[["energy_100g", *KEY_NUTRIENTS[1:]]] < 0)
            .sum()
            .to_dict()
        ),
    }

    return _dict_to_string(anomalies)


def _volumetry(before: pd.DataFrame, after: pd.DataFrame) -> MarkdownSubSection:
    return MarkdownSubSection(
        "1. Volumétrie",
        {
            "Avant nettoyage : ": str(len(before)),
            "Après nettoyage : ": str(len(after)),
        },
    )


def _rules(reports: List[Report]) -> MarkdownSubSection:
    result = MarkdownSubSection("2. Rapport de nettoyage", {})

    result.content["Tableau des rapports : "] = (
        "| Règle | Lignes avant | Lignes après | Lignes touchées | Détail |\n"
        "|---|---|---|---|---|\n"
    )

    for report in reports:
        result.content["Tableau des rapports : "] = (
                result.content["Tableau des rapports : "]
                + report.to_tab_markdown()
                + "\n"
        )

    return result


def _missing(before: pd.DataFrame, after: pd.DataFrame) -> MarkdownSubSection:
    return MarkdownSubSection(
        "4. Manquants",
        {
            "Avant nettoyage : ": _dict_to_string(
                before[KEY_NUTRIENTS].isna().sum()
            ),
            "Après nettoyage : ": _dict_to_string(
                after[KEY_NUTRIENTS].isna().sum()
            ),
        },
    )


def _products_by_food_group(after: pd.DataFrame) -> MarkdownSubSection:
    result = _dict_to_string(
        after.groupby("food_group")["food_group"].count()
    )

    return MarkdownSubSection(
        "5. Produits par rayon après nettoyage",
        {
            "Produits par rayon : ": result,
        },
    )


def _columns(before: pd.DataFrame, after: pd.DataFrame) -> MarkdownSubSection:
    added_columns = sorted(set(after.columns) - set(before.columns))
    removed_columns = sorted(set(before.columns) - set(after.columns))

    return MarkdownSubSection(
        "6. Colonnes ajoutées et retirées",
        {
            "Colonnes ajoutées : ": ", ".join(
                f"`{column}`" for column in added_columns
            ),
            "Colonnes supprimées : ": ", ".join(
                f"`{column}`" for column in removed_columns
            ),
        },
    )


def generate_report(
        before: pd.DataFrame,
        after: pd.DataFrame,
        reports: list,
        output_path: Path,
) -> None:
    """Écrit le rapport de nettoyage au format Markdown.

    Le contenu est déterministe : relancer la fonction sur les mêmes données
    produit le même fichier, à la date de génération près.

    Args:
        before: données avant nettoyage.
        after: données après nettoyage.
        reports: comptes rendus des règles appliquées, dans l'ordre. Chaque
            élément expose `name` (str), `rows_touched` (int) et
            `details` (dict sous-règle -> nombre de lignes).
        output_path: fichier de sortie, par exemple
            `docs/data/rapport_nettoyage.md`.
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
        _volumetry(before, after),
        _rules(reports),
        _anomalies(before, after),
        _missing(before, after),
        _products_by_food_group(after),
        _columns(before, after),
    ]

    lines = header + [str(section) + "\n\n" for section in sections]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")

"""Structures de données partagées : comptes rendus des règles et des étapes."""
from dataclasses import dataclass, field

import pandas as pd

@dataclass
class DataModel:
    """Ensemble des tables du modèle relationnel, sous forme de DataFrames.

    Attributes:
        products: table des produits.
        nutriments: nutriments principaux par produit.
        secondary_nutrients: référentiel des nutriments secondaires.
        products_secondary_nutrients: liaison produit -> nutriment secondaire.
        tag_fields: par champ de tags, le couple (référentiel, table de liaison).
    """
    products: pd.DataFrame
    nutriments: pd.DataFrame
    secondary_nutrients: pd.DataFrame
    products_secondary_nutrients: pd.DataFrame
    tag_fields: dict[str, tuple[pd.DataFrame, pd.DataFrame]]


@dataclass
class Report:
    """Compte rendu d'une règle de nettoyage.

    Attributes:
        rule: nom de la règle.
        lines_before: nombre de lignes avant la règle.
        lines_after: nombre de lignes après la règle.
        affected_lines: nombre de lignes modifiées ou supprimées.
        details: détail par sous-règle, nom -> nombre de lignes.
    """
    rule: str
    lines_before: int
    lines_after: int
    affected_lines: int
    details: dict[str, int] = field(default_factory=dict)

    def to_tab_markdown(self) -> str:
        """Renvoie le compte rendu en ligne de tableau Markdown (détails dans la dernière colonne)."""
        res = f"| {self.rule} | {self.lines_before} | {self.lines_after} | {self.affected_lines} |"
        for nom, detail in self.details.items() :
            res += f" {nom} : {detail} ;"
        res += "|"
        return res


@dataclass
class StepReport:
    """Compte rendu d'une étape du pipeline.

    Attributes:
        step: nom de l'étape.
        duration: durée en secondes.
        rows: nombre de lignes (produits) traitées ou écrites.
        files: fichiers produits par l'étape.
    """
    step: str
    duration: float
    rows: int
    files: list[str] = field(default_factory=list)
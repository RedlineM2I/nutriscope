from dataclasses import dataclass, field

import pandas as pd

@dataclass
class DataModel:
    products: pd.DataFrame
    nutriments: pd.DataFrame
    secondary_nutrients: pd.DataFrame
    products_secondary_nutrients: pd.DataFrame
    tag_fields: dict[str, tuple[pd.DataFrame, pd.DataFrame]]


@dataclass
class CompteRendu:
    regle: str
    lignes_avant: int
    lignes_apres: int
    lignes_touchees: int
    details: dict[str, int] = field(default_factory=dict)
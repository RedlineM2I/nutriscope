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
class Report:
    rule: str
    lines_before: int
    lines_after: int
    affected_lines: int
    details: dict[str, int] = field(default_factory=dict)
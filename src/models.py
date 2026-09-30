from dataclasses import dataclass

import pandas as pd

@dataclass
class DataModel:
    products: pd.DataFrame
    nutriments: pd.DataFrame
    secondary_nutrients: pd.DataFrame
    products_secondary_nutrients: pd.DataFrame
    tag_fields: dict[str, tuple[pd.DataFrame, pd.DataFrame]]
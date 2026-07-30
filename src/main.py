import pyarrow.parquet as pq
import pandas as pd
import numpy as np

PARQUET_FILE = '../data/food.parquet'


from tqdm import tqdm

import time
import numpy as np
import pyarrow.dataset as ds

def timer(function):
    def f():
        start = time.perf_counter()
        res = function()
        duration = time.perf_counter() - start
        print(f"Temps de traitement : {duration:.3f} secondes")
        return res

    return f


@timer
def main():

    dataset = ds.dataset("food.parquet", format="parquet")
    nb_rows = dataset.count_rows()

    scanner = dataset.scanner(
        columns=["product_name", "countries_tags", "nutriscore_score"],
        batch_size=200_000
    )

    total_france = 0
    nutriscore = 0

    with tqdm(total=nb_rows, desc="Recherche France", unit=" lignes", unit_scale=True) as progressbar:

        for batch in scanner.to_batches():
            df = batch.to_pandas()

            df_france = df[
                df["countries_tags"].apply(
                    lambda x: isinstance(x, np.ndarray) and np.any(x == "en:france")
                )
            ]

            total_france += len(df_france)
            nutriscore += len(df_france[df_france['nutriscore_score'].notna()])

             # Nombre de lignes effectivement traitées dans ce batch
            progressbar.update(batch.num_rows)

            # Information complémentaire dans la barre
            if total_france % 100 == 0:
                progressbar.set_postfix(trouves=int(total_france))

    print(f"Nombre total de produits contenant en:france : {total_france:_} dont {nutriscore:_} ont un nutriscore")


if __name__=="__main__":
    main()
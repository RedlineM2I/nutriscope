from tqdm import tqdm

import pyarrow.parquet as pq
import pandas as pd
import numpy as np
import polars as pl
import pyarrow.dataset as ds
import time
import duckdb

PARQUET_FILE = '../data/food.parquet'

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
    """Version déprécie étant donné que polars est plus bien plus performant pour ce genre de process"""

    dataset = ds.dataset("food_clean.parquet", format="parquet")
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



def keep_fr_or_default(val):
    if val is None:
        return None

    val = list(val)

    for lang in ("fr", "main", "en"):
        for item in val:
            if isinstance(item, dict) and item.get("lang") == lang:
                return item.get("text")

    return None



@timer
def main():
    table = pq.read_table("food_clean.parquet")
    df = table.slice(0, 1000).to_pandas()
    
    print(df)




@timer
def create_compact_parquet():
    lazy = (
        pl.scan_parquet("food.parquet")
        .with_columns(
            pl.col("countries_tags").cast(pl.List(pl.Utf8), strict=False)
        )
        .filter(
            pl.col("countries_tags").list.contains("en:france")
            # & pl.col("nutriscore_score").is_not_null()
        )
        .with_columns(
            pl.col("product_name")
            .map_elements(keep_fr_or_default, return_dtype=pl.Utf8)
            .alias("product_name")
        )
        .select([
            "product_name",
            "countries_tags",
            "nutriscore_score",
        ])
    )

    clean = lazy.collect(engine="streaming")
    clean.write_parquet("food_clean.parquet")


@timer
def main():
    resultat = duckdb.sql("""
        SELECT
            product_name,
            COUNT(*) AS nombre_produits
        FROM 'food_clean.parquet'
        GROUP BY product_name
        ORDER BY nombre_produits DESC LIMIT 1000 OFFSET 1
    """).df()

    print(resultat.head(1000))


def count_fr_rows():
    print(duckdb.sql("SELECT COUNT(*) from 'food_clean.parquet'").df())


def count_fr_rows_with_nutriscore():
    print(duckdb.sql("SELECT COUNT(*) from 'food_clean.parquet' WHERE nutriscore_score IS NOT NULL;").df())


def top_n_products(n: int = 10):
    resultat = duckdb.sql(f"""
        SELECT
            product_name,
            COUNT(*) AS nombre_produits
        FROM 'food_clean.parquet'
        GROUP BY product_name
        ORDER BY nombre_produits DESC LIMIT {n};
    """).df()

    print(resultat)


@timer
def main():
    print("Creation d'une version compacte du fichier parquet avec un premier nettoyage et filtrage de données")
    create_compact_parquet()

    print("Nombre d'entrées de produits disponible en france")
    count_fr_rows()

    print("Nombre d'entrées de produits disponible en france et disposant d'un nutriscore")
    count_fr_rows_with_nutriscore()

    print("Récupération du top 10 des produits les plus présents")
    top_n_products(10)



if __name__=="__main__":
    main()
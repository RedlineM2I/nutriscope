import pyarrow.parquet as pq
import pandas as pd
import numpy as np

PARQUET_FILE = '../data/food.parquet'


# https://static.openfoodfacts.org/data/data-fields.txt
# pq.set_option('display.max_columns', None)
# pd.set_option('display.max_columns', None)

def main():
    batch_dataframe = []

    parquet_file = pq.ParquetFile('../data/food.parquet')

    for i in parquet_file.iter_batches(batch_size=200):
        print("RecordBatch")
        print(i.to_pandas()['countries_tags'])
        # batch_dataframe.append()
        # print(i.to_pandas()['countries_tags'])
        # print(i.to_pandas()['states_tags'])
        
        # for c in i.to_pandas().columns:
        #     print(c)
        # print(table.column_names)
        break

def main():

    chunks = pd.read_json(r"C:\Users\Administrateur\Downloads\openfoodfacts-products.jsonl\openfoodfacts-products.jsonl", lines=True, chunksize=100_000, encoding="utf-8")
    # countries = next(chunks)['countries']


    # total = countries[countries=='France']
    # print(len(total))
    # for chunk in chunks:
    #     # traitement ici
    #     print(chunk['countries'].head())
    # break

    nb_products_fr = 0

    for chunk in chunks:
        nb_products_fr += len(chunk.countries[chunk.countries=='France'])
    
    print(nb_products_fr)
        


def nb_en_fr():

    cols = ["product_name", "countries_tags", "nutriscore_score"]

    pf = pq.ParquetFile(PARQUET_FILE)

    nb_products_fr = 0

    for i in range(pf.num_row_groups):
        table = pf.read_row_group(i, columns=cols)
        df = table.to_pandas()

        mask = df["countries_tags"].apply(
            lambda x: isinstance(x, (list, tuple, set, np.ndarray)) and "en:france" in x
        )
        df_france = df[mask]

        nb_products_fr += len(df_france)

        nb_vide += len(df_france[df_france['nutriscore_score'].notna()])
        
    print(nb_products_fr)
    print(nb_vide)
    print("total : 1247336")


# def main():

#     cols = ["product_name", "countries_tags", "nutriscore_score"]

#     pf = pq.ParquetFile(PARQUET_FILE)

#     nb_vide = 0

#     for i in range(pf.num_row_groups):
#         table = pf.read_row_group(i, columns=cols)
#         df = table.to_pandas()

#         nb_vide += len(df[df['nutriscore_score'].notna()])
        
#     print(nb_vide)
#     print("1381069")


if __name__=="__main__":
    main()
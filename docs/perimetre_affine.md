# Périmètre sélectionné parmi le fichier parquet

### Inventaires des colonnes utiles :

> Pour les colonnes STRUCT, il faut les déplier via `explode` ou en accédant aux champs internes

Pour filtrer : 
obsolete : indique si obsolete ; BOOLEAN
countries_tags : selection des pays (que en tags) ; VARCHAR[]

#### Général

code : code-bar ; VARCHAR
product_name ; STRUCT(lang VARCHAR, "text" VARCHAR)[]
quantity : quantité (à vérifier) ; VARCHAR
nutrition_data_per : valeurs nutritionnelles par portion ou 100g ; VARCHAR

#### Classification

brands_tags : marques ; VARCHAR[] ; 90541
categories_tags : cat des produits ; VARCHAR[] ; 38236
labels_tags ; VARCHAR[] ; 14002
origins_tags ; VARCHAR[] ; 9497

#### Ingrédients

ingredients_tags ; VARCHAR[]
additives_tags : additifs ; VARCHAR[]

nutriments ; STRUCT("name" VARCHAR, "value" FLOAT, "100g" FLOAT, serving FLOAT, unit VARCHAR, prepared_value FLOAT, prepared_100g FLOAT, prepared_serving FLOAT, prepared_unit VARCHAR)[]
nutriscore_grade ; VARCHAR
nutriscore_score ; INTEGER
nutrient_levels_tags ; VARCHAR[] : définitions de quantité de nutriments(en:fat-in-high-quantity)

nova_group : qualification nova, degré de transformation des aliments ; INTEGER

#### Qualité des données

completeness : entre 0 et 1, remplissage des données ; FLOAT

#### Environnement

environmental_score_grade ; VARCHAR
environmental_score_score ; INTEGER

#### Images

images ; STRUCT("key" VARCHAR, imgid INTEGER, rev INTEGER, sizes STRUCT("100" STRUCT(h INTEGER, w INTEGER), "200" STRUCT(h INTEGER, w INTEGER), "400" STRUCT(h INTEGER, w INTEGER), "full" STRUCT(h INTEGER, w INTEGER)), uploaded_t BIGINT, uploader VARCHAR)[]
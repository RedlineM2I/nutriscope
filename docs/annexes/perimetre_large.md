# Périmètre sélectionné parmi le fichier parquet

### Inventaires des colonnes utiles :

> Pour les colonnes STRUCT, il faut les déplier via `explode` ou en accédant aux champs internes

#### Général

code : code-bar ; VARCHAR
link : url ; VARCHAR
last_modified_t : date de la dernière mise a jour ; BIGINT
? last_updated_t : date de la dernière mise a jour ++ ; BIGINT
? rev : révision du produit ; INTEGER
obsolete : indique si obsolete (permet de trier) ; BOOLEAN
languages_tags : langues ; VARCHAR[]
product_name ; STRUCT(lang VARCHAR, "text" VARCHAR)[]
? generic_name ; STRUCT(lang VARCHAR, "text" VARCHAR)[]
quantity : quantité (à vérifier) ; VARCHAR
? product_quantity_unit : quantité (à vérifier) ; VARCHAR
? product_quantity : quantité (à vérifier) ; VARCHAR
serving_size : portion ; VARCHAR
? serving_quantity ; VARCHAR
nutrition_data_per : valeurs nutritionnelles par portion ou 100g ; VARCHAR

#### Classification

brands_tags : marques ; VARCHAR[]
categories_tags : cat des produits ; VARCHAR[]
labels_tags ; VARCHAR[]
origins_tags ; VARCHAR[]
? manufacturing_places_tags ; VARCHAR[]
countries_tags : selection des pays (que en tags) ; VARCHAR[]

#### Ingrédients

ingredients_tags ; VARCHAR[]
additives_tags : additifs ; VARCHAR[]

nutriments ; STRUCT("name" VARCHAR, "value" FLOAT, "100g" FLOAT, serving FLOAT, unit VARCHAR, prepared_value FLOAT, prepared_100g FLOAT, prepared_serving FLOAT, prepared_unit VARCHAR)[]
nutriscore_grade ; VARCHAR
nutriscore_score ; INTEGER
? nutrient_levels_tags ; VARCHAR[]

nova_group : qualification nova, degré de transformation des aliments ; INTEGER

#### Qualité des données

completeness : entre 0 et 1, remplissage des données ; FLOAT
? compared_to_category ; VARCHAR

#### Environnement

environmental_score_grade ; VARCHAR
environmental_score_data ; VARCHAR
environmental_score_score ; INTEGER
environmental_score_tags ; VARCHAR[]

#### Images

images ; STRUCT("key" VARCHAR, imgid INTEGER, rev INTEGER, sizes STRUCT("100" STRUCT(h INTEGER, w INTEGER), "200" STRUCT(h INTEGER, w INTEGER), "400" STRUCT(h INTEGER, w INTEGER), "full" STRUCT(h INTEGER, w INTEGER)), uploaded_t BIGINT, uploader VARCHAR)[]
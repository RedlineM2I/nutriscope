# Récupération des données

## Choix du format d'export des données

Sur le site (https://world.openfoodfacts.org/data), plusieurs types de données sont fournies :
- JSONL
- Parquet
- CSV

Nous avons choisi d'utiliser le fichier **Parquet** car :
- il utilise le format en colonne, ce qui permet une selection précise lors de l'import 
et donc un gain de temps et de ressources important
- Pandas le lit nativement et efficacement
- Typages intégrés
- Beaucoup plus compact qu'un csv pour le même nombre de données

Ce fichier fait **7.5 GO** de mémoire

> Date de l'export : 29/07/26

Pour télécharger le jeu de données (fichier parquet):
````bash
python ../src/data/fetch_data.py
````

## Questions :

#### Combien de produits vendus en France ?

#### Quelle part a un nutri-score renseigné ?

Il y a 1 381 069 produits qui ont un nutri-score

#### le taux de manquants sur les nutriments clés ( energy_100g , sugars_100g , salt_100g ) ? 



### Colonnes :

'additives_n',
 'additives_tags',
 'allergens_tags',
 'brands_tags',
 *'brands'*,
 *'categories'*,
 'categories_tags',
 'categories_properties',
 'checkers_tags',
 'ciqual_food_name_tags',
 'cities_tags',
 'code',
 'compared_to_category',
 'complete',
 'completeness',
 'correctors_tags',
 *'countries_tags'*,
 'created_t',
 'creator',
 'data_quality_errors_tags',
 'data_quality_info_tags',
 'data_quality_warnings_tags',
 'data_sources_tags',
 'environmental_score_data',
 'environmental_score_grade',
 'environmental_score_score',
 'environmental_score_tags',
 'editors',
 'emb_codes_tags',
 'emb_codes',
 'entry_dates_tags',
 'food_groups_tags',
 'generic_name',
 'images',
 'informers_tags',
 'ingredients_analysis_tags',
 'ingredients_from_palm_oil_n',
 'ingredients_n',
 'ingredients_original_tags',
 'ingredients_percent_analysis',
 'ingredients_tags',
 'ingredients_text',
 'ingredients_with_specified_percent_n',
 'ingredients_with_unspecified_percent_n',
 'ingredients_without_ciqual_codes_n',
 'ingredients_without_ciqual_codes',
 'ingredients',
 'known_ingredients_n',
 'labels_tags',
 'labels',
 'lang',
 'languages_tags',
 'last_edit_dates_tags',
 'last_editor',
 'last_image_t',
 'last_modified_by',
 'last_modified_t',
 'last_updated_t',
 'link',
 'main_countries_tags',
 'manufacturing_places_tags',
 'manufacturing_places',
 'max_imgid',
 'minerals_tags',
 'misc_tags',
 'new_additives_n',
 'no_nutrition_data',
 'nova_group',
 'nova_groups_tags',
 'nova_groups',
 'nucleotides_tags',
 'nutrient_levels_tags',
 'nutriments',
 'nutriscore_grade',
 *'nutriscore_score'*,
 'nutrition_data_per',
 'obsolete',
 'origins_tags',
 'origins',
 'owner_fields',
 'owner',
 'packagings_complete',
 'packaging_recycling_tags',
 'packaging_shapes_tags',
 'packaging_tags',
 'packaging_text',
 'packaging',
 'packagings',
 'photographers',
 'popularity_key',
 'popularity_tags',
 *'product_name'*,
 'product_quantity_unit',
 'product_quantity',
 'purchase_places_tags',
 'quantity',
 'rev',
 'scans_n',
 'serving_quantity',
 'serving_size',
 'states_tags',
 'stores_tags',
 'stores',
 'traces_tags',
 'unique_scans_n',
 'unknown_ingredients_n',
 'unknown_nutrients_tags',
 'vitamins_tags',
 'with_non_nutritive_sweeteners',
 'with_sweeteners',
 'schema_version'
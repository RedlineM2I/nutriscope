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

#### Caractéristiques :

- Dimensions : (4636471, 111)
- Types : bool(1), float32(1), float64(25), int32(1), object(56), str(27)
- Utilisation mémoire : 21.8+ GB de ram
- Taux de remplissage par colonne : 75.72 %

## Questions :

#### Combien de produits vendus en France ?

Il y a 1 254 128 produits vendus en France

#### Quelle part a un nutri-score renseigné ?

Il y a 466 032 produits vendus en France avec un nutri-score. Ceux qui ne sont pas éligibles ne sont pas inclus.

### Les dix marques les plus présentes ?

Elles sont : Carrefour, U, Auchan, Leader Price, Casino, Cora, Le Gaulois, Picard, Monoprix et Nestlé

#### le taux de manquants sur les nutriments clés ( energy_100g , sugars_100g , salt_100g ) ? 

Taux de manquants :
- Sucre : 29.1 %
- Sel : 33.5 %
- Énergie : 28.5 %

### Qu'est-ce qui vous semble le plus « sale » dans ces données ?

Les dictionnaires stockés dans les colonnes sont plutôt difficiles à gérer, et on n'est jamais sûr de trouver la donnée qu'on cherche. Il y a beaucoup de données vides. Les intitulés des colonnes sont aussi très peu explicites et diffèrent entre les différents jeux de données. Beaucoup de données sont aussi dupliquées (pas de clés étrangères, catégories sous forme de texte, etc.).

### Colonnes :

```
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
```

### TP-9

Dans ce tp on a fait le choix de ne pas recontroler le ratio 4/4/9 pour les kcal inférieures à 1 kcal/100g

### TP-13

Pipeline bout-en-bout, jalon J3 (tag `v0.3`). Documentation : [docs/data/pipeline.md](data/pipeline.md).

**Choix**

- Orchestration par la CLI existante (`python -m src.pipeline --all` et une option par étape), sans Makefile ni orchestrateur : le flux complet prend environ 5 minutes sur une machine. Les noms d'étapes restent ceux du projet, en anglais (`download`, `clean`, `load_database`, `extract_parquet`, `build_dataset`).
- Toutes les sorties sont datées (AAAAMMJJ). Une étape lit la sortie du jour de l'étape précédente, sinon la plus récente, sinon elle échoue en disant quelle étape lancer.
- Le brut France est figé dans `data/raw/` avec un manifeste (SHA-256 de la source et du brut). Le parquet de 8 Go n'est retéléchargé que s'il manque ou avec `--force`. `NUTRISCOPE_SOURCE` permet de partir d'un échantillon.
- Idempotence : tri par code et écriture sur un seul thread pour le brut, le Parquet partitionné et l'export. Deux passages donnent les mêmes octets (vérifié par SHA-256, aussi sur le jeu complet).
- Le dossier partitionné reçoit un `_SUCCESS` écrit en dernier ; `build_dataset` ignore un dossier sans marqueur.
- Split train/test : stratifié sur `nutriscore_grade`, 20 % de test, graine 42. Fait en SQL (classement par `md5(code || '42')` dans chaque grade) plutôt qu'avec numpy : plus court, et l'affectation d'un produit ne dépend que de son code. L'export refuse de s'écraser sans `--force`.
- `load_database` et `extract_parquet` vérifient qu'ils ont autant de produits que le nettoyé (548 913 sur le jeu complet).
- Journal des durées : `data/logs/pipeline.jsonl`, une ligne par étape, échecs compris.
- `requirements.txt` réencodé en UTF-8 (il était en UTF-16) et réduit au pipeline ; les notebooks ont `requirements-notebooks.txt`.

**Corrections en passant**

- Tests du nettoyage cassés depuis le TP 12 (colonne passée deux fois à `make_product`) ; quatre attentes réalignées sur le code.
- `limit_nutriments` ne traitait plus les énergies négatives depuis le TP 12 : kcal et kJ négatives repassent à NA.
- Import de `date` manquant dans `export_features.py`.
- Les ✔ / ✘ faisaient planter l'affichage sur une console Windows en cp1252 (trouvé au test sur clone neuf) : la sortie est forcée en UTF-8.

**Test machine vierge**

- Clone neuf, venv neuf, `pip install -r requirements.txt`, `.env` rempli, `NUTRISCOPE_SOURCE` vers un échantillon de 20 000 produits : 86 tests verts, les cinq étapes passent en 4,4 s.
- Reste à faire : l'échange avec une autre équipe et ses retours écrits.

**Dette**

- `docs/data/rapport_nettoyage.md` est versionné mais réécrit par chaque `clean` : un `git status` le montre modifié après une exécution.
- `data/exports/schema.json` n'est pas daté : un export d'un autre jour réécrit le schéma du précédent.
- `docs/data/architecture.md` cite encore d'anciens chemins (`data/food_france.parquet`, `data/parquet/produits`).

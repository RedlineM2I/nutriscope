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


### TP-14

Prédiction du Nutri-Score (a → e) : notebook `notebooks/ml_nutriscore.ipynb`, jeu `nutriscope_ml_sample.parquet` (24 076 produits en train, 5 965 en test, colonne `split` figée).

**Synthèse**

Forêt aléatoire avec `class_weight="balanced"` : F1 macro de 0,860 ± 0,006 en validation croisée et de 0,863 sur le test, contre 0,685 pour la meilleure baseline (arbre de profondeur 8). L'écart entre validation croisée et test (0,003) confirme que le protocole tient.

**Choix**

- Métrique principale : F1 macro. La baseline majoritaire a une accuracy 3,2 fois plus élevée que son F1 macro (0,286 contre 0,089) : sur des classes déséquilibrées, l'accuracy récompense le modèle qui répond toujours la classe majoritaire.
- Toute la préparation est dans un seul `Pipeline` : imputation par la médiane avec indicateur de manquant, features dérivées (ratios graisses saturées/lipides et sucres/glucides, écart d'énergie 4/4/9) par `FunctionTransformer`, standardisation, one-hot avec `min_frequency=80`. Cela donne 66 colonnes. Un test vérifie que le préparateur n'a pas vu le test.
- Validation croisée à 5 plis stratifiés, `random_state=42`, plis créés une seule fois et identiques pour tous les modèles.
- Logistique multinomiale 0,767, forêt 0,858 : la forêt capte les interactions entre nutriments, ce que ne fait pas la logistique, linéaire.
- Déséquilibre modéré (2,65 fois plus de « e » que de « b »). `class_weight="balanced"` ne change pas le F1 global (+0,002, sous l'écart-type), mais fait passer le rappel de « b » de 0,68 à 0,74. Je n'ai pas testé SMOTE : c'est plus complexe et ça risque de créer une fuite, pour un déséquilibre modéré.

**Fuite**

- `nutriscore_score` ajouté volontairement : le F1 passe à 0,986, et cette seule colonne pèse 0,671 en importance par permutation, contre 0,022 pour la suivante. La lettre est un découpage de ce score, et une fiche sans grade n'a pas de score non plus.
- Correction : une liste `FORBIDDEN` (`nutriscore_score`, `code`, `product_name`, `brands`, `split`) est vérifiée par un `assert` dès la définition des features.
- Contrôle négatif avec `completeness` : F1 inchangé (0,859) et importance de 0,001. Le détecteur ne crie pas au loup.
- Importances du modèle honnête : sel, graisses saturées et sucres en tête, ce qui correspond aux composantes défavorables du barème. Lipides totaux, glucides totaux et rayons sont des proxies, pas des fuites. Fibres et fruits-légumes pèsent peu, car environ 45 % des valeurs manquent.

**Erreurs analysées**

- 722 erreurs sur le test, dont 90 % à une lettre près.
- Trois cas de natures différentes : boudin blanc noté « a » avec 10,9 g de graisses saturées (fiche fausse), vodka (hors périmètre du Nutri-Score), jus carotte-mangue rangé dans « Fruits » alors que les boissons ont une grille plus sévère (règle absente des features).

**Pour le TP 15**

- Ajouter une feature « est une boisson » et exclure le rayon alcool.
- Ajouter au nettoyage une règle de cohérence entre le grade déclaré et les nutriments.
- Mesurer le gradient boosting avec la même préparation, les mêmes plis et les mêmes métriques.

### TP-15

Méthodes d'ensemble : notebook `notebooks/methodes_ensemble.ipynb`, même jeu et même
`split` que le TP 14. Livrables : `docs/decisions/ADR-001-modele-nutriscore.md`,
`docs/ml/limites_nutriscore.md`.

**Synthèse**

LightGBM avec ses réglages par défaut est retenu : F1 macro de 0,888 ± 0,007 en validation
croisée et de 0,886 sur le test, contre 0,858 pour la forêt du TP 14. Les trois boosters
(HistGB, XGBoost, LightGBM) sont indiscernables en F1 ; LightGBM est choisi sur la latence
(7,6 ms par produit), la taille (1,74 Mo) et le temps de réentraînement (0,7 s).

**Choix**

- Logistique et forêt réentraînées dans le nouveau notebook : 0,767 et 0,858, identiques au
  TP 14. La préparation n'a pas bougé.
- Cible encodée en entiers (`LabelEncoder`, a=0 … e=4) pour tous les modèles : XGBoost
  l'exige, et l'ordre des grades sert à mesurer la gravité des erreurs.
- Boosting contre forêt : +0,03, soit 4 à 5 écarts-types. Le gain est réel.
- Réglage Optuna de LightGBM seul (30 essais, 3 plis, MedianPruner) : 10,9 min réelles
  contre 5 estimées, car l'estimation ignorait l'effet de `num_leaves` sur la taille des
  arbres. Gain de +0,007, sous le seuil de 2 écarts-types (0,020), pour un modèle 16 fois
  plus gros. On garde les réglages par défaut.
- Test regardé une seule fois, pour les 6 modèles : écarts CV/test ≤ 0,005.
- La latence unitaire (6 à 11 ms) est dominée par la préparation. Elle ne départage pas
  les boosters.

**Erreurs analysées**

- 574 erreurs sur 5 965, dont 89 % à une lettre près et 11 produits à 3 lettres ou plus.
- Classe la plus difficile : B (rappel 0,77), qui part autant vers A que vers C. Elle est
  rare, au milieu de l'échelle et couvre une bande étroite du score (1 à 2).
- Pire rayon : alcools (accuracy 0,70 sur 10 produits), hors périmètre du Nutri-Score.
- Sur 5 produits hésitants entre B et C : 1 limite du modèle (œufs de cailles, score 2),
  1 règle métier absente (yaourt à boire noté avec la grille boissons), 3 fiches fausses
  ou douteuses (bière, avoine préparée, pastilles).
- Le rayon ne suffit pas à repérer les boissons : le yaourt à boire est rangé dans les
  produits laitiers.

**Pour le TP 16**

- Appliquer les 3 règles d'abstention de la note de limites (alcools, boissons,
  probabilité maximale sous 0,5) avant de prédire les produits sans grade.
- Le seuil de 0,5 est une proposition, à calibrer.
- Une feature « boisson / solide » reste la piste principale d'amélioration. Elle
  déclencherait une révision de l'ADR.


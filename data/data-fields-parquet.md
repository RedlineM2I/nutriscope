# Data fields — export Parquet Open Food Facts (NutriScope)

Ce document met en correspondance les colonnes du fichier **Parquet** (`food.parquet`,
téléchargé depuis Hugging Face / static.openfoodfacts.org) avec les champs décrits dans
l'ancien **`data-fields.txt`** (export CSV historique fourni).

**Méthode :** rapprochement par nom, sémantique et documentation officielle Open Food Facts
(wiki, GitHub `openfoodfacts-server`, doc API). Les astérisques Markdown autour de certains
noms de colonnes dans votre liste (`*brands*`, `*categories*`, `*countries_tags*`,
`*nutriscore_score*`, `*product_name*`) sont de la mise en forme et n'ont pas été prises en
compte dans les noms de colonnes.

**Légende de la colonne "Correspondance" :**
- un nom de champ = correspondance directe (même donnée, éventuellement renommée) ;
- `Champ inconnu` = pas d'équivalent dans le `data-fields.txt` fourni (champ nouveau,
  apparu avec le schéma Parquet / MongoDB de Product Opener) — une courte note explique
  ce que contient probablement le champ, quand c'est établi de façon fiable ;
- `≈` = lien conceptuel avec un ancien champ, mais structure ou granularité différente
  (donc traité comme *inconnu* au sens strict demandé).

---

## A. Identification générale, dates, contributeurs, quantités

| Colonne (Parquet) | Correspondance (data-fields.txt) | Remarque |
|---|---|---|
| `code` | `code` | Code-barres du produit. |
| `link` | `url` | URL de la fiche produit. |
| `creator` | `creator` | Contributeur ayant créé la fiche. |
| `created_t` | `created_t` | Date de création (timestamp UNIX). |
| `last_modified_t` | `last_modified_t` | Date de dernière modification de la fiche. |
| `last_updated_t` | Champ inconnu | Distinct de `last_modified_t` ; inclut probablement les mises à jour de données dérivées (popularité, scans) et pas seulement l'édition de la fiche. |
| `last_modified_by` | Champ inconnu | Identifiant du dernier contributeur ayant modifié la fiche. |
| `last_editor` | Champ inconnu | Probable doublon/synonyme de `last_modified_by`. |
| `rev` | Champ inconnu | Numéro de révision de la fiche produit. |
| `obsolete` | Champ inconnu | Indique si le produit est marqué comme retiré/obsolète. |
| `lang` | Champ inconnu | Langue principale déclarée de la fiche. |
| `languages_tags` | Champ inconnu | Liste des langues détectées sur la fiche. |
| `product_name` | `product_name` | Nom du produit. |
| `generic_name` | `generic_name` | Nom générique. |
| `quantity` | `quantity` | Quantité et unité en texte libre. |
| `product_quantity` | Champ inconnu | ≈ valeur numérique extraite de `quantity`. |
| `product_quantity_unit` | Champ inconnu | ≈ unité extraite de `quantity`. |
| `serving_size` | `serving_size` | Taille d'une portion (texte). |
| `serving_quantity` | Champ inconnu | ≈ valeur numérique extraite de `serving_size`. |
| `nutrition_data_per` | Champ inconnu | Indique si les valeurs nutritionnelles sont exprimées "pour 100 g" ou "par portion". |
| `owner` | Champ inconnu | Compte "propriétaire" de la fiche (producteurs en marque propre). |
| `owner_fields` | Champ inconnu | Champs renseignés directement par le propriétaire (producteur). |
| `schema_version` | Champ inconnu | Version du schéma de l'export Parquet. |

## B. Tags & classification (marques, catégories, origines, emballage, lieux de vente…)

| Colonne (Parquet) | Correspondance (data-fields.txt) | Remarque |
|---|---|---|
| `brands` | `brands` | |
| `brands_tags` | `brands_tags` | |
| `categories` | `categories` | |
| `categories_tags` | `categories_tags` | |
| `categories_properties` | Champ inconnu | Propriétés enrichies rattachées aux catégories (ex. codes CIQUAL). |
| `labels` | `labels` | |
| `labels_tags` | `labels_tags` | |
| `origins` | `origins` | |
| `origins_tags` | `origins_tags` | |
| `manufacturing_places` | `manufacturing_places` | |
| `manufacturing_places_tags` | `manufacturing_places_tags` | |
| `emb_codes` | `emb_codes` | |
| `emb_codes_tags` | `emb_codes_tags` | |
| `cities_tags` | `cities_tags` | |
| `purchase_places_tags` | `purchase_places` | Ancien champ en texte libre, sans variante `_tags`. |
| `stores` | `stores` | |
| `stores_tags` | Champ inconnu | ≈ `stores`, pas de variante `_tags` dans l'ancien fichier. |
| `countries_tags` | `countries_tags` | |
| `main_countries_tags` | Champ inconnu | ≈ `countries_tags` mais restreint au(x) pays principal/principaux de commercialisation. |
| `packaging` | `packaging` | Texte libre (forme, matière). |
| `packaging_text` | `packaging` | Version texte brut/normalisée, probablement dupliquée avec `packaging` dans ce schéma. |
| `packaging_tags` | `packaging_tags` | |
| `packagings` | Champ inconnu | Structure détaillée par élément d'emballage (matière, forme, poids, recyclabilité) utilisée pour l'Eco-score. |
| `packagings_complete` | Champ inconnu | Indique si la description détaillée de l'emballage est complète. |
| `packaging_shapes_tags` | Champ inconnu | Formes d'emballage normalisées (extrait de `packagings`). |
| `packaging_recycling_tags` | Champ inconnu | Consignes/tags de recyclage (extrait de `packagings`). |
| `food_groups_tags` | Champ inconnu | Groupes alimentaires (classification NOVA/PNNS), absents de l'ancien fichier. |
| `states_tags` | Champ inconnu | État d'avancement de la fiche (photos manquantes, ingrédients à compléter, etc.). |
| `misc_tags` | Champ inconnu | Tags divers (ex. présence de photo, produit complet…). |

## C. Ingrédients, additifs, allergènes, composition

| Colonne (Parquet) | Correspondance (data-fields.txt) | Remarque |
|---|---|---|
| `ingredients_text` | `ingredients_text` | Texte brut de la liste d'ingrédients. |
| `ingredients` | Champ inconnu | ≈ `ingredients_text` mais structuré (liste imbriquée avec sous-ingrédients, %, id). |
| `ingredients_tags` | Champ inconnu | Liste normalisée des ingrédients (tags), absente de l'ancien fichier. |
| `ingredients_original_tags` | Champ inconnu | Version non re-catégorisée des tags d'ingrédients. |
| `ingredients_n` | Champ inconnu | Nombre total d'ingrédients détectés. |
| `known_ingredients_n` | Champ inconnu | Nombre d'ingrédients reconnus/taxonomisés. |
| `unknown_ingredients_n` | Champ inconnu | Nombre d'ingrédients non reconnus. |
| `ingredients_with_specified_percent_n` | Champ inconnu | Ingrédients dont le % est indiqué. |
| `ingredients_with_unspecified_percent_n` | Champ inconnu | Ingrédients sans % indiqué. |
| `ingredients_percent_analysis` | Champ inconnu | Résultat de l'analyse d'estimation des %. |
| `ingredients_without_ciqual_codes` | Champ inconnu | Ingrédients sans code CIQUAL associé. |
| `ingredients_without_ciqual_codes_n` | Champ inconnu | Nombre correspondant. |
| `ciqual_food_name_tags` | Champ inconnu | Libellés CIQUAL associés aux ingrédients. |
| `ingredients_analysis_tags` | Champ inconnu | Résultat d'analyse (végan, végétarien, huile de palme…) ; recoupe partiellement `ingredients_from_palm_oil_tags` / `ingredients_that_may_be_from_palm_oil_tags` de l'ancien fichier, sans leur être identique. |
| `ingredients_from_palm_oil_n` | `ingredients_from_palm_oil_n` | |
| `traces_tags` | `traces_tags` | |
| `allergens_tags` | Champ inconnu | Absent du `data-fields.txt` fourni. |
| `additives_n` | `additives_n` | |
| `new_additives_n` | Champ inconnu | ≈ recalcul/variante de `additives_n` selon une taxonomie plus récente. |
| `additives_tags` | `additives_tags` | |
| `nucleotides_tags` | Champ inconnu | L'ancien fichier ne connaît que la valeur mesurée `nucleotides_100g` (nutriment), pas une liste de tags d'ingrédients. |
| `vitamins_tags` | Champ inconnu | L'ancien fichier détaille chaque vitamine en champ `_100g` séparé, pas de liste de tags. |
| `minerals_tags` | Champ inconnu | Idem, minéraux détaillés individuellement (`calcium_100g`, `iron_100g`…) dans l'ancien fichier. |
| `unknown_nutrients_tags` | Champ inconnu | Nutriments non reconnus. |
| `with_sweeteners` | Champ inconnu | Présence d'édulcorants. |
| `with_non_nutritive_sweeteners` | Champ inconnu | Présence d'édulcorants non nutritifs. |
| `no_nutrition_data` | `no_nutriments` | Renommé. |

## D. Nutrition (valeurs et scores)

| Colonne (Parquet) | Correspondance (data-fields.txt) | Remarque |
|---|---|---|
| `nutriments` | bloc `*_100g` / `*_serving` | Structure imbriquée regroupant l'ensemble des nutriments (equivalent de toute la section "nutrition facts" de l'ancien fichier : `energy_100g`, `proteins_100g`, `sugars_100g`, `sodium_100g`, etc., pour 100 g et par portion). |
| `nutriscore_grade` | `nutrition_grade_fr` | Renommé (Nutri-Score, note A à E). |
| `nutriscore_score` | `nutrition-score-fr_100g` | Renommé (score numérique). |
| `nutrient_levels_tags` | Champ inconnu | Niveaux qualitatifs (faible/modéré/élevé) par nutriment, absent de l'ancien fichier. |

## E. Qualité des données, complétude, historique de contribution

*(section quasi entièrement nouvelle par rapport au CSV historique, qui ne suit pas la qualité/complétude des fiches)*

| Colonne (Parquet) | Correspondance (data-fields.txt) | Remarque |
|---|---|---|
| `complete` | Champ inconnu | Indicateur booléen : fiche jugée complète ou non. |
| `completeness` | Champ inconnu | Score de complétude (0 à 1,1) basé sur photo, nom, quantité, emballage, marque, catégorie, origine, code emballage, ingrédients, nutriments, etc. |
| `compared_to_category` | Champ inconnu | Catégorie de référence utilisée pour comparer les valeurs nutritionnelles du produit. |
| `data_quality_errors_tags` | Champ inconnu | Erreurs de qualité détectées automatiquement. |
| `data_quality_warnings_tags` | Champ inconnu | Avertissements de qualité. |
| `data_quality_info_tags` | Champ inconnu | Informations de qualité (non bloquantes). |
| `data_sources_tags` | Champ inconnu | Origine(s) de la donnée (import producteur, app mobile, etc.). |
| `checkers_tags` | Champ inconnu | Contributeurs ayant vérifié la fiche. |
| `correctors_tags` | Champ inconnu | Contributeurs ayant corrigé la fiche. |
| `informers_tags` | Champ inconnu | Contributeurs ayant complété des informations. |
| `editors` | Champ inconnu | Liste de tous les contributeurs ayant édité la fiche (l'ancien fichier n'a que `creator`, le tout premier). |
| `photographers` | Champ inconnu | Contributeurs ayant ajouté des photos. |
| `entry_dates_tags` | Champ inconnu | ≈ `created_t`, sous forme de tags (année, mois, jour). |
| `last_edit_dates_tags` | Champ inconnu | ≈ `last_modified_t`, sous forme de tags. |

## F. Environnement (Eco-score / Green-Score)

*(entièrement absent de l'ancien fichier, qui ne comportait que `carbon-footprint_100g` dans la section nutrition — une notion différente et bien plus ancienne)*

| Colonne (Parquet) | Correspondance (data-fields.txt) | Remarque |
|---|---|---|
| `environmental_score_data` | Champ inconnu | Détail du calcul de l'Eco-score/Green-Score (agriculture, transport, emballage…). |
| `environmental_score_grade` | Champ inconnu | Note Eco-score (A à E). |
| `environmental_score_score` | Champ inconnu | Score numérique Eco-score. |
| `environmental_score_tags` | Champ inconnu | Tags liés à l'Eco-score. |

## G. Images

| Colonne (Parquet) | Correspondance (data-fields.txt) | Remarque |
|---|---|---|
| `images` | `image_url`, `image_small_url` | Structure enrichie et imbriquée (par type — front/ingredients/nutrition/packaging — et par langue, avec identifiant `imgid`), là où l'ancien fichier ne fournissait que l'URL de l'image principale et sa miniature. |
| `last_image_t` | Champ inconnu | Date d'ajout de la dernière image. |
| `max_imgid` | Champ inconnu | Identifiant de la dernière image uploadée. |

## H. Popularité / usage

*(absent du CSV historique)*

| Colonne (Parquet) | Correspondance (data-fields.txt) | Remarque |
|---|---|---|
| `scans_n` | Champ inconnu | Nombre de scans du produit (app mobile). |
| `unique_scans_n` | Champ inconnu | Nombre de scans par utilisateurs uniques. |
| `popularity_key` | Champ inconnu | Clé utilisée pour classer la popularité. |
| `popularity_tags` | Champ inconnu | Tags de popularité (par pays/mois). |

## I. Classification NOVA (transformation des aliments)

*(absent du CSV historique)*

| Colonne (Parquet) | Correspondance (data-fields.txt) | Remarque |
|---|---|---|
| `nova_group` | Champ inconnu | Groupe NOVA (1 à 4, degré de transformation). |
| `nova_groups` | Champ inconnu | Détail/texte du groupe NOVA. |
| `nova_groups_tags` | Champ inconnu | Tags associés au groupe NOVA. |

---

## Synthèse

- **Colonnes avec correspondance directe dans `data-fields.txt`** : ~37 sur 111 (identification, marques/catégories/labels/origines, ingrédients texte, additifs de base, packaging simple, Nutri-Score, images en partie).
- **Colonnes sans équivalent (`Champ inconnu`)** : le reste, correspond principalement à quatre familles de nouveautés apparues avec le passage au format Parquet / à l'API interne de Product Opener :
  1. **Qualité et complétude des fiches** (`completeness`, `data_quality_*`, rôles de contributeurs) ;
  2. **Environnement / Eco-score** (`environmental_score_*`) ;
  3. **Structuration fine des ingrédients et de l'emballage** (`ingredients` imbriqué, `packagings`, analyses dérivées) ;
  4. **Usage / popularité et NOVA** (`scans_n`, `popularity_*`, `nova_*`).

Pour le chantier NutriScope, ce sont précisément ces champs "nouveaux" (Nutri-Score, NOVA, Eco-score, `completeness`, `images`, `ingredients_analysis_tags`) qui seront les plus utiles pour le score de qualité nutritionnelle et les recommandations d'alternatives — à documenter précisément avant l'étape de nettoyage/fiabilisation de la base.

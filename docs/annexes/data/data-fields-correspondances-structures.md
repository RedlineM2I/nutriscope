# Data fields — CSV historique → Parquet, avec structures imbriquées

Objectif : à partir de n'importe quel champ de `data-fields.txt`, retrouver **la colonne
Parquet correspondante ET la manière d'accéder à la valeur**, y compris quand cette colonne
Parquet est un tableau (`LIST`) ou une structure (`STRUCT`/`MAP`) plutôt qu'une valeur simple.

⚠️ **Important sur la fiabilité de ce document** : je n'ai pas d'accès réseau pour ouvrir
votre `food.parquet` et lancer `DESCRIBE SELECT * FROM 'food.parquet'`. Les chemins d'accès
indiqués ci-dessous sont reconstruits à partir de la documentation publique Open Food
Facts (structure du JSON produit exposé par l'API, wiki DuckDB, dataset Hugging Face
`openfoodfacts/product-database`), qui reflète en général fidèlement le contenu du
Parquet. **Avant intégration dans le pipeline NutriScope, faites tourner la commande
ci-dessous pour confirmer les types réels** :

```sql
-- DuckDB : liste des colonnes et de leur type exact
DESCRIBE SELECT * FROM 'food.parquet';

-- Pour une colonne imbriquée en particulier
SELECT typeof(nutriments), typeof(images), typeof(packagings)
FROM 'food.parquet' LIMIT 1;
```

---

## Règle générale de typage

| Type de champ CSV | Type Parquet | Conséquence pratique |
|---|---|---|
| Champ simple (texte, nombre, date) : `code`, `product_name`, `created_t`… | Scalaire (`VARCHAR`, `BIGINT`, `DOUBLE`…) | Correspondance directe, aucune transformation nécessaire. |
| Champ `*_tags` (liste de tags séparés par virgule en CSV) | `LIST(VARCHAR)` (tableau) | Il n'y a plus de virgules à parser : on utilise `list_contains(col, 'valeur')`, `UNNEST(col)`, ou `array_contains` selon l'outil (DuckDB / pandas / polars). |
| Champs regroupés par thème (tous les `*_100g`/`*_serving`, tous les champs image, tous les composants d'emballage…) | `MAP` / `STRUCT` / `LIST(STRUCT)` | Il faut accéder à une **clé** ou **exploser** (`UNNEST`) la structure pour retrouver l'équivalent d'une colonne CSV. Détail en section F. |

---

## A. Informations générales

| Champ CSV | Type CSV | Colonne Parquet | Type Parquet | Accès |
|---|---|---|---|---|
| `code` | texte | `code` | VARCHAR | direct |
| `url` | texte | `link` | VARCHAR | direct |
| `creator` | texte | `creator` | VARCHAR | direct |
| `created_t` | timestamp UNIX | `created_t` | BIGINT | direct |
| `created_datetime` | ISO8601 | Champ inconnu | — | à recalculer depuis `created_t` (`to_timestamp(created_t)` en DuckDB). |
| `last_modified_t` | timestamp UNIX | `last_modified_t` | BIGINT | direct |
| `last_modified_datetime` | ISO8601 | Champ inconnu | — | à recalculer depuis `last_modified_t`. |
| `product_name` | texte | `product_name` | VARCHAR | direct |
| `generic_name` | texte | `generic_name` | VARCHAR | direct |
| `quantity` | texte | `quantity` | VARCHAR | direct |

## B. Tags & classification

*(rappel : toute colonne `*_tags` ci-dessous est un `LIST(VARCHAR)`, pas une chaîne à
découper par virgule)*

| Champ CSV | Colonne Parquet | Accès |
|---|---|---|
| `packaging` | `packaging`, `packaging_text` | direct (texte, dupliqué entre les deux colonnes) |
| `packaging_tags` | `packaging_tags` | `UNNEST(packaging_tags)` / `list_contains(...)` |
| `brands` | `brands` | direct |
| `brands_tags` | `brands_tags` | liste |
| `categories` | `categories` | direct |
| `categories_tags` | `categories_tags` | liste |
| `categories_fr` | Champ inconnu | à reconstruire : `list_filter(categories_tags, x -> x LIKE 'fr:%')` |
| `origins` | `origins` | direct |
| `origins_tags` | `origins_tags` | liste |
| `manufacturing_places` | `manufacturing_places` | direct |
| `manufacturing_places_tags` | `manufacturing_places_tags` | liste |
| `labels` | `labels` | direct |
| `labels_tags` | `labels_tags` | liste |
| `labels_fr` | Champ inconnu | reconstruire depuis `labels_tags` filtré `fr:` |
| `emb_codes` | `emb_codes` | direct |
| `emb_codes_tags` | `emb_codes_tags` | liste |
| `first_packaging_code_geo` | Champ inconnu | absent du schéma fourni |
| `cities` | Champ inconnu | seule `cities_tags` (liste) existe |
| `cities_tags` | `cities_tags` | liste |
| `purchase_places` | `purchase_places_tags` | liste (pas de version texte libre) |
| `stores` | `stores` | direct |
| `countries` | Champ inconnu | seule `countries_tags` (liste) existe |
| `countries_tags` | `countries_tags` | liste |
| `countries_fr` | Champ inconnu | reconstruire depuis `countries_tags` filtré `fr:` |

## C. Ingrédients

| Champ CSV | Colonne Parquet | Type Parquet | Accès |
|---|---|---|---|
| `ingredients_text` | `ingredients_text` | VARCHAR | direct |
| `traces` | Champ inconnu | — | seule `traces_tags` (liste) existe |
| `traces_tags` | `traces_tags` | LIST(VARCHAR) | liste |

## D. Données diverses

| Champ CSV | Colonne Parquet | Type Parquet | Accès |
|---|---|---|---|
| `serving_size` | `serving_size` | VARCHAR | direct |
| `no_nutriments` | `no_nutrition_data` | BOOLEAN | direct (renommé) |
| `additives_n` | `additives_n` | BIGINT | direct |
| `additives` | Champ inconnu | — | seule `additives_tags` (liste) existe |
| `additives_tags` | `additives_tags` | LIST(VARCHAR) | liste |
| `ingredients_from_palm_oil_n` | `ingredients_from_palm_oil_n` | BIGINT | direct |
| `ingredients_from_palm_oil` | Champ inconnu | — | probablement absorbé dans `ingredients_analysis_tags` (liste, ex. `en:palm-oil`) |
| `ingredients_from_palm_oil_tags` | Champ inconnu | — | idem |
| `ingredients_that_may_be_from_palm_oil_*` (3 champs) | Champ inconnu | — | absents ; à défaut, chercher `en:may-contain-palm-oil` dans `ingredients_analysis_tags` |
| `nutrition_grade_fr` | `nutriscore_grade` | VARCHAR | direct (renommé) |
| `main_category` | Champ inconnu | — | reconstruire : dernier élément de `categories_tags`, ou premier selon convention retenue |
| `main_category_fr` | Champ inconnu | — | idem, filtré `fr:` |
| `image_url` | `images` | STRUCT/MAP | **imbriqué**, voir section F.2 |
| `image_small_url` | `images` | STRUCT/MAP | **imbriqué**, voir section F.2 |

## E. Valeurs nutritionnelles (`*_100g` / `*_serving`)

Les ~92 champs de cette section (`energy_100g`, `proteins_100g`, `sugars_100g`,
`saturated-fat_100g`, `sodium_100g`, toutes les vitamines et minéraux, etc.) sont
**tous regroupés dans la colonne imbriquée `nutriments`**, à l'exception de :

| Champ CSV | Colonne Parquet | Remarque |
|---|---|---|
| `carbon-footprint_100g` | Champ inconnu | pas d'équivalent direct (voir `environmental_score_data`) |
| `nutrition-score-fr_100g` | `nutriscore_score` | sorti de `nutriments`, colonne indépendante |
| `nutrition-score-uk_100g` | Champ inconnu | absent du schéma fourni |

Pour tous les autres → **`nutriments`**, détail d'accès en section F.1.

---

## F. Zoom sur les colonnes structurées (STRUCT / LIST / MAP)

### F.1 `nutriments`

Dans le JSON produit d'Open Food Facts (dont dérive le Parquet), `nutriments` est une
structure à clés dynamiques (`MAP` en DuckDB), avec **une clé par nutriment et par
variante** : `<nom>_100g`, `<nom>_serving`, `<nom>_unit`, `<nom>_value`. Le nom du
nutriment est identique à celui du CSV (avant `_100g`), par exemple `sugars`,
`saturated-fat`, `vitamin-c`, `nutrition-score-fr`.

```sql
-- DuckDB : retrouver l'équivalent de sugars_100g et sodium_100g du CSV
SELECT
    code,
    nutriments['sugars_100g']       AS sugars_100g,
    nutriments['saturated-fat_100g'] AS saturated_fat_100g,
    nutriments['sodium_100g']        AS sodium_100g
FROM 'food.parquet';

-- Toutes les clés présentes pour un produit donné
SELECT UNNEST(map_keys(nutriments)) AS cle FROM 'food.parquet' WHERE code = '...';
```

```python
# pandas / polars (après lecture du parquet)
df["nutriments"].apply(lambda d: d.get("sugars_100g") if d else None)
```

### F.2 `images`

Structure à deux niveaux :
- des **images brutes** uploadées, indexées par un numéro (`"1"`, `"2"`, …) avec
  `sizes`, `uploaded_t`, `uploader` ;
- des **images sélectionnées** par type et langue : `front_<lang>`, `ingredients_<lang>`,
  `nutrition_<lang>`, `packaging_<lang>` (ex. `front_fr`), contenant `imgid` et un objet
  `sizes` (résolutions disponibles : `100`, `200`, `400`, `full`).

Il n'y a pas d'URL toute faite comme dans le CSV : `image_url`/`image_small_url`
se **reconstruisent** à partir du code-barres et de l'`imgid`, selon le schéma d'URL
standard des images OFF (dossier dérivé du code-barres + `imgid` + taille).

```sql
-- Exemple d'exploration de la structure (à adapter une fois le vrai schéma confirmé)
SELECT code, images['front_fr'] FROM 'food.parquet' WHERE code = '...';
```

### F.3 `packagings`

`LIST(STRUCT)` : un élément par composant d'emballage (utilisé pour l'Eco-score), avec
typiquement les clés `number_of_units`, `shape`, `material`, `recycling`,
`quantity_per_unit`, `weight_measured`. Pas d'équivalent CSV — c'est une donnée plus fine
que l'ancien champ texte `packaging`.

```sql
SELECT code, UNNEST(packagings) FROM 'food.parquet' WHERE code = '...';
```

### F.4 `categories_properties`

`MAP`/`STRUCT` de propriétés rattachées aux catégories du produit (ex. codes CIQUAL,
propriétés nutritionnelles par défaut de la catégorie). Pas d'équivalent CSV.

### F.5 `environmental_score_data`

`STRUCT` imbriqué contenant le détail du calcul de l'Eco-score/Green-Score (agriculture,
transport, emballage, ajustements). Les colonnes `environmental_score_grade` et
`environmental_score_score` en sont des extraits déjà "aplatis". Pas d'équivalent CSV.

### F.6 `ingredients`

`LIST(STRUCT)` : un élément par ingrédient (et sous-ingrédient imbriqué), avec des clés
telles que `id`, `text`, `percent_estimate`, `vegan`, `vegetarian`. Plus riche que le texte
brut `ingredients_text`, sans équivalent CSV direct.

---

## Synthèse pratique

Pour retrouver **n'importe quel champ** de `data-fields.txt` dans le Parquet :

1. Chercher le nom (ou son renommage : `url`→`link`, `nutrition_grade_fr`→`nutriscore_grade`,
   `no_nutriments`→`no_nutrition_data`, `nutrition-score-fr_100g`→`nutriscore_score`).
2. Si c'est un champ `*_100g`/`*_serving` → chercher la clé correspondante dans `nutriments`.
3. Si c'est un champ `*_tags` → même nom en Parquet, mais type `LIST` (plus de parsing par
   virgule).
4. Si c'est `image_url`/`image_small_url` → reconstruire depuis `images`.
5. Sinon → très probablement absent (`Champ inconnu`), souvent parce que c'est une variante
   par langue (`_fr`) ou parce que la donnée a été jugée redondante lors de la conversion
   CSV/JSONL → Parquet (le README du dataset Hugging Face confirme que « les colonnes
   dupliquées ou utilisées pour le debug interne » ont été filtrées).

**Recommandation avant la phase de fiabilisation :** faire tourner un `DESCRIBE` complet
sur votre `food.parquet` et comparer sa sortie à ce document pour corriger les points
marqués comme reconstruits par déduction (notamment la structure exacte d'`images` et de
`packagings`).

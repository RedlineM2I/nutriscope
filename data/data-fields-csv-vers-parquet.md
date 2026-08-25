# Data fields — CSV historique → export Parquet Open Food Facts (NutriScope)

Même mapping que le document précédent, mais avec **`data-fields.txt` (CSV) comme référence
en première colonne**, et sa correspondance vers le schéma **Parquet** (`food.parquet`)
en seconde colonne.

**Légende :**
- un nom de champ = correspondance directe (même donnée, éventuellement renommée) ;
- `Champ inconnu` = pas d'équivalent parmi les 111 colonnes Parquet que vous avez fournies
  (champ absent, fusionné dans un autre champ, ou remplacé par une structure différente) ;
- pour les champs de nutrition (`*_100g`), voir la règle générale en section E.

---

## A. Informations générales

| Colonne (data-fields.txt) | Correspondance (Parquet) | Remarque |
|---|---|---|
| `code` | `code` | |
| `url` | `link` | |
| `creator` | `creator` | |
| `created_t` | `created_t` | |
| `created_datetime` | Champ inconnu | Pas de variante ISO 8601 dédiée dans la liste Parquet fournie ; seule la version timestamp `created_t` existe. |
| `last_modified_t` | `last_modified_t` | |
| `last_modified_datetime` | Champ inconnu | Idem `created_datetime` : pas de variante `_datetime` dans la liste fournie. |
| `product_name` | `product_name` | |
| `generic_name` | `generic_name` | |
| `quantity` | `quantity` | |

## B. Tags

| Colonne (data-fields.txt) | Correspondance (Parquet) | Remarque |
|---|---|---|
| `packaging` | `packaging`, `packaging_text` | Le nouveau schéma semble dupliquer ce texte libre entre deux champs. |
| `packaging_tags` | `packaging_tags` | |
| `brands` | `brands` | |
| `brands_tags` | `brands_tags` | |
| `categories` | `categories` | |
| `categories_tags` | `categories_tags` | |
| `categories_fr` | Champ inconnu | Pas de variante par langue dédiée dans la liste fournie ; à reconstruire en filtrant `categories_tags`/`categories` sur le préfixe `fr:`. |
| `origins` | `origins` | |
| `origins_tags` | `origins_tags` | |
| `manufacturing_places` | `manufacturing_places` | |
| `manufacturing_places_tags` | `manufacturing_places_tags` | |
| `labels` | `labels` | |
| `labels_tags` | `labels_tags` | |
| `labels_fr` | Champ inconnu | Idem `categories_fr`. |
| `emb_codes` | `emb_codes` | |
| `emb_codes_tags` | `emb_codes_tags` | |
| `first_packaging_code_geo` | Champ inconnu | Absent de la liste des 111 colonnes fournie. |
| `cities` | Champ inconnu | Seule `cities_tags` figure dans la nouvelle liste, pas de version texte libre. |
| `cities_tags` | `cities_tags` | |
| `purchase_places` | `purchase_places_tags` | Le CSV a un champ texte libre, le Parquet ne fournit que la version taguée. |
| `stores` | `stores` | |
| `countries` | Champ inconnu | Seule `countries_tags` figure dans la nouvelle liste, pas de version texte libre. |
| `countries_tags` | `countries_tags` | |
| `countries_fr` | Champ inconnu | Idem `categories_fr`. |

## C. Ingrédients

| Colonne (data-fields.txt) | Correspondance (Parquet) | Remarque |
|---|---|---|
| `ingredients_text` | `ingredients_text` | |
| `traces` | Champ inconnu | Seule `traces_tags` figure dans la nouvelle liste, pas de champ texte libre. |
| `traces_tags` | `traces_tags` | |

## D. Données diverses

| Colonne (data-fields.txt) | Correspondance (Parquet) | Remarque |
|---|---|---|
| `serving_size` | `serving_size` | |
| `no_nutriments` | `no_nutrition_data` | Renommé. |
| `additives_n` | `additives_n` | |
| `additives` | Champ inconnu | Seule `additives_tags` figure dans la nouvelle liste. |
| `additives_tags` | `additives_tags` | |
| `ingredients_from_palm_oil_n` | `ingredients_from_palm_oil_n` | |
| `ingredients_from_palm_oil` | Champ inconnu | Pas de champ texte libre équivalent ; probablement absorbé dans `ingredients_analysis_tags`. |
| `ingredients_from_palm_oil_tags` | Champ inconnu | Non présent tel quel ; probablement absorbé dans `ingredients_analysis_tags`. |
| `ingredients_that_may_be_from_palm_oil_n` | Champ inconnu | Absent de la liste fournie. |
| `ingredients_that_may_be_from_palm_oil` | Champ inconnu | Absent de la liste fournie. |
| `ingredients_that_may_be_from_palm_oil_tags` | Champ inconnu | Absent de la liste fournie ; probablement absorbé dans `ingredients_analysis_tags`. |
| `nutrition_grade_fr` | `nutriscore_grade` | Renommé. |
| `main_category` | Champ inconnu | Absent de la liste fournie ; se déduit en général du premier élément de `categories_tags`. |
| `main_category_fr` | Champ inconnu | Idem. |
| `image_url` | `images` | L'URL simple devient une clé dans la structure imbriquée `images` (variante "front"). |
| `image_small_url` | `images` | Idem, variante miniature dans la même structure imbriquée. |

## E. Valeurs nutritionnelles (`*_100g`)

**Règle générale :** dans le Parquet, l'ensemble de ces valeurs (mesure pour 100 g **et**
pour la portion) est regroupé dans un **unique champ imbriqué `nutriments`**, avec une clé
portant le même nom que dans le CSV (ex. `sugars_100g`, `sugars_serving`). Il n'existe donc
pas de colonne « top-level » dédiée par nutriment dans le Parquet — sauf les deux
exceptions listées en bas de section.

### Énergie, protéines, glucides
`energy_100g`, `energy-kj_100g`, `energy-kcal_100g`, `proteins_100g`, `casein_100g`,
`serum-proteins_100g`, `nucleotides_100g`, `carbohydrates_100g`, `sugars_100g`,
`sucrose_100g`, `glucose_100g`, `fructose_100g`, `lactose_100g`, `maltose_100g`,
`maltodextrins_100g`, `starch_100g`, `polyols_100g`
→ **`nutriments`** (clé de même nom)

### Lipides et acides gras
`fat_100g`, `saturated-fat_100g`, `butyric-acid_100g`, `caproic-acid_100g`,
`caprylic-acid_100g`, `capric-acid_100g`, `lauric-acid_100g`, `myristic-acid_100g`,
`palmitic-acid_100g`, `stearic-acid_100g`, `arachidic-acid_100g`, `behenic-acid_100g`,
`lignoceric-acid_100g`, `cerotic-acid_100g`, `montanic-acid_100g`, `melissic-acid_100g`,
`monounsaturated-fat_100g`, `polyunsaturated-fat_100g`, `omega-3-fat_100g`,
`alpha-linolenic-acid_100g`, `eicosapentaenoic-acid_100g`, `docosahexaenoic-acid_100g`,
`omega-6-fat_100g`, `linoleic-acid_100g`, `arachidonic-acid_100g`,
`gamma-linolenic-acid_100g`, `dihomo-gamma-linolenic-acid_100g`, `omega-9-fat_100g`,
`oleic-acid_100g`, `elaidic-acid_100g`, `gondoic-acid_100g`, `mead-acid_100g`,
`erucic-acid_100g`, `nervonic-acid_100g`, `trans-fat_100g`, `cholesterol_100g`
→ **`nutriments`** (clé de même nom)

### Fibres, sel, alcool
`fiber_100g`, `sodium_100g`, `alcohol_100g`
→ **`nutriments`** (clé de même nom)

### Vitamines
`vitamin-a_100g`, `vitamin-d_100g`, `vitamin-e_100g`, `vitamin-k_100g`, `vitamin-c_100g`,
`vitamin-b1_100g`, `vitamin-b2_100g`, `vitamin-pp_100g`, `vitamin-b6_100g`,
`vitamin-b9_100g`, `vitamin-b12_100g`, `biotin_100g`, `pantothenic-acid_100g`
→ **`nutriments`** (clé de même nom) — *à ne pas confondre avec `vitamins_tags` côté Parquet,
qui est une liste de tags distincte, sans les valeurs mesurées.*

### Minéraux
`silica_100g`, `bicarbonate_100g`, `potassium_100g`, `chloride_100g`, `calcium_100g`,
`phosphorus_100g`, `iron_100g`, `magnesium_100g`, `zinc_100g`, `copper_100g`,
`manganese_100g`, `fluoride_100g`, `selenium_100g`, `chromium_100g`, `molybdenum_100g`,
`iodine_100g`
→ **`nutriments`** (clé de même nom) — *idem, à ne pas confondre avec `minerals_tags`.*

### Autres
`caffeine_100g`, `taurine_100g`, `ph_100g`, `fruits-vegetables-nuts_100g`
→ **`nutriments`** (clé de même nom)

### Exceptions (hors champ `nutriments`)

| Colonne (data-fields.txt) | Correspondance (Parquet) | Remarque |
|---|---|---|
| `carbon-footprint_100g` | Champ inconnu | Pas d'équivalent direct ; le sujet environnemental est désormais couvert par `environmental_score_data` / `environmental_score_score` / `environmental_score_grade`, mais ce ne sont pas la même métrique. |
| `nutrition-score-fr_100g` | `nutriscore_score` | Renommé, sorti du champ `nutriments` en colonne indépendante. |
| `nutrition-score-uk_100g` | Champ inconnu | Le score UK FSA n'apparaît pas dans la liste des 111 colonnes Parquet fournie. |

---

## Synthèse

- Sur les **~10 champs "généraux"**, 8 ont un équivalent direct.
- Sur les **~24 champs de "tags"**, une quinzaine ont un équivalent direct ; les variantes
  par langue (`_fr`) et les versions texte libre sans `_tags` (`cities`, `countries`,
  `traces`) n'ont pas d'équivalent dans la liste Parquet fournie.
- Sur les **~16 champs "divers"**, la moitié a un équivalent direct ; le triplet
  `ingredients_that_may_be_from_palm_oil*` n'a pas d'équivalent identifié — il est
  probablement fusionné dans `ingredients_analysis_tags` côté Parquet, mais ce n'est
  pas garanti sans vérifier le contenu réel du champ.
- Sur les **~92 champs de nutrition (`*_100g`)**, la quasi-totalité se retrouve dans
  l'unique champ imbriqué `nutriments` ; seuls le Nutri-Score FR (renommé) et deux champs
  (empreinte carbone, score UK) sortent de cette règle et n'ont pas d'équivalent garanti
  dans le Parquet.

Point de vigilance pour la fiabilisation de la base NutriScope : comme `nutriments` est un
champ imbriqué (struct/map), il faudra un `UNNEST` (DuckDB) ou un `explode`/accès par clé
(pandas/polars) pour retrouver l'équivalent "une colonne = un nutriment" du CSV historique.

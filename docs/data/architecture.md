# Architecture des données — NutriScope

> Mis à jour : TP 13 · Branche `feat/tp13`
> Données : © Open Food Facts contributors — licence ODbL (base), CC-BY-SA (images). Toute donnée produite à partir de ces sources est repartagée dans les mêmes conditions.

Légende d'avancement : ✅ en place dans le code · ⏳ prévu, pas encore implémenté.

---

## En 30 secondes

| Question | Réponse |
|---|---|
| **Où l'API lit-elle un produit ?** | Dans la **base relationnelle** (PostgreSQL), table `products`, par sa clé primaire `id` ou son code-barres `code` (unique). Jamais dans les Parquet. |
| **Où l'entraînement ML lit-il ses features ?** | Dans un **export figé** daté (⏳ `--build_datasets`). Jamais dans la base, jamais dans le Parquet nettoyé. |
| **Le principe** | La base sert l'**application** (accès par clé, une fiche à la fois). Les Parquet servent l'**analyse et le ML** (balayages de colonnes sur tout le catalogue). |

---

## 1. Les magasins de données

| Magasin | Contenu | Producteur | Format | Emplacement | Dans Git ? | État |
|---|---|---|---|---|---|---|
| **Brut** | Export complet Open Food Facts (Hugging Face), jamais modifié ; vérifié par SHA-256 au téléchargement | `src/fetch_data.py` (`--download`) | Parquet | `data/food.parquet` | ❌ Non | ✅ |
| **Périmètre France** | Brut restreint aux produits vendus en France (`en:france`) et aux colonnes utiles (`COLUMNS` dans `src/config.py`) | `get_products_from` dans `src/db_parquet/products.py` (`--download`, 2ᵉ moitié) | Parquet | `data/food_france.parquet` | ❌ Non | ✅ |
| **Nettoyé** | Une ligne par produit du périmètre, nutriments aplatis en colonnes `*_100g`, règles de nettoyage appliquées (voir ci-dessous) | `src/cleaning.py`, orchestré par `clean` dans `src/pipeline.py` (`--clean`) | Parquet | `data/parquet/food_clean.parquet` | ❌ Non | ✅ |
| **Base relationnelle** | Tables `products`, `categories`, `brands`, `labels`, `origins`, `ingredients`, `additives`, leurs tables de liaison `products_*`, plus `nutritional_values`, `secondary_nutrients`, `products_secondary_nutrients`, `foodgroups`, `images` ; contraintes et clés | `src/flat_to_relational.py` (découpage) puis `load_database` dans `src/pipeline.py` (`--load_database`), schéma dans `src/db_psql/create_tables.sql` | PostgreSQL | Serveur local | ❌ Non — le DDL et le code de chargement le sont | ✅ partiel (voir note) |
| **Rapport de nettoyage** | Avant / après de chaque règle | `src/report.py` | Markdown | `docs/data/rapport_nettoyage.md` | ✅ Oui | ✅ |
| **Export des tables** | Un Parquet ZSTD par table PostgreSQL | `export_to_parquet` dans `src/pipeline.py` (non branchée sur la CLI) | Parquet | `data/export/<table>.parquet` | ❌ Non | ✅ fonction écrite, pas appelée |
| **Parquet analytique** | Le nettoyé partitionné par groupe alimentaire | `--extract_parquet` | Parquet partitionné Hive | `data/parquet/produits/food_group=<slug>/…` (`PARQUET_CLEAN_BY_FOOD_GROUP`) | ❌ Non | ⏳ |
| **Exports ML** | Features + cible (Nutri-Score), figés à une date | `--build_datasets` | Parquet + `schema.json` | `data/exports/features_nutriscore_<AAAAMMJJ>.parquet` | ❌ Non — `schema.json` ✅ oui | ⏳ |

> **Note sur le chargement.** `load_database` alimente aujourd'hui `products`, `nutritional_values`, `secondary_nutrients` et `products_secondary_nutrients` (`src/db_parquet/nutriments.py`) et, pour chaque `Tag` (`category`, `origin`, `label`, `additive`, `brand`, `ingredient`), la table du tag et sa table de liaison `products_<tags>`. Les tables `foodgroups` et `images` sont créées par le DDL mais pas encore remplies ; `products.main_category` et `products.foodgroup_id` non plus (colonnes commentées dans `RelationalReader.get_products`).
Ce qui est **toujours** dans Git : le code qui produit chaque magasin, le DDL, les schémas, les rapports (`docs/data/*.md`).

### Règles de nettoyage (`CLEANING_RULES`, dans cet ordre)

1. `set_column_types` — types des colonnes
2. `normalize_texts` — textes et tags normalisés
3. `deduplicate_codes` — un seul produit par `code`
4. `normalize_units` — unités (avant les bornes : un sel dérivé du sodium peut ensuite être borné)
5. `limit_nutriments` — bornes de plausibilité
6. `fix_energy` — recalcul de l'énergie (4 / 4 / 9), après les bornes pour s'appuyer sur des macronutriments plausibles
7. `handle_empty_categories` — catégories vides
8. `missing_values_strategy` — valeurs manquantes (voir `docs/data/strategie_manquants.md`)

### Schéma relationnel (`src/db_psql/create_tables.sql`)

| Table | Rôle | Clé |
|---|---|---|
| `products` | Un produit par code-barres : `code`, `product_name`, `main_category` → `categories`, `foodgroup_id` → `foodgroups`, `nutrition_data_per`, `nutriscore_grade`, `nutriscore_score`, `nova_group` (1-4), `completeness`, `environmental_score_grade`, `environmental_score_score`, `last_modified_t` | `id` (SERIAL), `code` UNIQUE |
| `categories`, `foodgroups`, `brands`, `labels`, `origins`, `ingredients`, `additives` | Référentiels `(id, name)` | `id`, `name` UNIQUE |
| `products_categories`, `products_brands`, `products_labels`, `products_origins`, `products_ingredients`, `products_additives` | Liaisons plusieurs-à-plusieurs `(product_id, <tag>_id)` | clé composite |
| `nutritional_values` | Nutriments principaux d'un produit : `energy_kcal_100g`, `fat_100g`, `saturated_fat_100g`, `carbohydrates_100g`, `sugars_100g`, `fiber_100g`, `proteins_100g`, `salt_100g`, `sodium_100g`, `fruits_nuts_100g`, `fruits_legumes_100g` | `product_id` (FK) |
| `secondary_nutrients` + `products_secondary_nutrients` | Nutriments secondaires : référentiel `(id, name, unit)` et valeur `value_100g` par produit | clé composite `(product_id, nutrient_id)` |
| `images` | Plusieurs photos par produit : `url`, `type`, `language` | `id` (SERIAL) |

`create_tables.sql` commence par des `DROP TABLE … CASCADE` : lancer `--load_database` **réinitialise** la base avant de la recharger.

---

## 2. Qui lit quoi

| Consommateur | Ce qu'il lit | Pourquoi | Ce qu'il ne lit **pas** |
|---|---|---|---|
| **API** (FastAPI) ⏳ | Base relationnelle : `products` par `code`, jointures marques / catégories / nutriments | Accès par clé, une fiche à la fois, index de la clé primaire ; données cohérentes avec les contraintes | Les Parquet (pas faits pour lire une ligne), les exports (figés, donc périmés pour l'appli) |
| **Moteur de substitution** ⏳ | Base relationnelle pour le produit demandé et ses candidats de la même catégorie | Appelé par l'API, mêmes besoins qu'elle | Les Parquet en production |
| **Notebooks d'EDA** (`notebooks/`) | `data/parquet/food_clean.parquet` via DuckDB | Agrégats et distributions sur tout le catalogue : DuckDB ne lit que les colonnes utiles | La base (balayages lents, charge inutile), le brut (non nettoyé) |
| **Entraînement ML** ⏳ | Export figé `features_nutriscore_<date>.parquet` | Reproductibilité : même fichier, mêmes résultats d'une exécution à l'autre | Le Parquet nettoyé (reconstruit à chaque `--clean`, donc il bouge), la base |
| **Contrôles qualité** | `src/db_psql/requetes_controle.sql` sur la base ; `rapport_nettoyage.md` pour le nettoyage | Vérifier que ce qu'on sert correspond au nettoyé | Le brut (les contrôles portent sur ce qu'on sert, pas sur ce qu'on reçoit) |

---

## 3. Cinq règles

1. **Une seule source de vérité.** Tout descend du **nettoyé** produit par `src/cleaning.py`. La base est chargée depuis `food_clean.parquet`, par script ; on ne corrige jamais une donnée à la main en base. Une valeur aberrante retourne dans `cleaning.py` sous forme de règle, pas dans un `WHERE` ailleurs.
2. **Les données restent hors Git.** `data/` est dans le `.gitignore` (brut, nettoyé, exports). On versionne les scripts qui les produisent, le DDL, les schémas et les rapports. Un clone neuf + le README doivent suffire pour tout régénérer.
3. **Chaque étape se relance seule.** `--download`, `--clean` et `--load_database` lisent et écrivent des fichiers ou la base ; `--all` les enchaîne dans cet ordre. Le nettoyé est réécrit à chaque `--clean` (jetable, il se refait). Seules `flatten_to_relational` et `load_database` partagent une connexion DuckDB (tables temporaires en mémoire) et doivent tourner dans le même processus : c'est le rôle de `step_load_database`.
4. **Un téléchargement n'est jamais corrompu.** Le fichier est écrit dans `food.parquet.part`, son SHA-256 est comparé à celui publié par Hugging Face, puis il est renommé en `food.parquet` (renommage atomique). Et ⏳ **un export ML n'est jamais réécrit** : `features_nutriscore_<AAAAMMJJ>.parquet` sera daté, décrit par son `schema.json` (commit Git, SHA-256, filtres), et une nouvelle version = une nouvelle date.
5. **Chargement rapide et sûr de la base.** Les tables de liaison sont vidées de leurs PK/FK avant le chargement (`drop_constraints`), alimentées par `COPY` (`psql_insert_copy`), puis les contraintes sont rétablies (`restore_constraints`) : pas d'index à maintenir ni de FK à vérifier pendant l'insertion, mais les contraintes sont bien présentes à la fin.

> ⏳ **Partitionnement du Parquet analytique : par groupe alimentaire, et seulement par groupe alimentaire.** Le groupe alimentaire (`food_groups_tags`) est le filtre présent dans presque toutes les requêtes prévues : EDA, export, substitution « dans le même groupe ». Partitionner dessus permet à DuckDB d'ignorer les dossiers inutiles (élagage de partitions) tout en gardant des fichiers de taille raisonnable. Une seconde clé (marque, code-barres) produirait des milliers de minuscules fichiers dont les métadonnées coûteraient plus cher à lire que les données. Les autres filtres (grade, nutriments) restent efficaces grâce aux statistiques min/max des groupes de lignes Parquet.

---

## 4. Le flux

```
 Open Food Facts (food.parquet, Hugging Face, ODbL)
        │  src/fetch_data.py  — téléchargement + vérification SHA-256
        ▼
 data/food.parquet                              [brut, jamais modifié]
        │  get_products_from  — filtre France + colonnes utiles
        ▼
 data/food_france.parquet
        │  src/db_parquet/products.py (extract_products) → src/cleaning.py
        │  8 règles, rapport dans docs/data/rapport_nettoyage.md
        ▼
 data/parquet/food_clean.parquet             [SOURCE DE VÉRITÉ]
        │
        ├──────────────────────────────┐
        │ src/flat_to_relational.py    │ ⏳ --extract_parquet
        │ (tables temporaires DuckDB)  ▼
        │ src/pipeline.py              data/parquet/produits/food_group=*/
        │ (load_database, COPY)               │
        ▼                                     ├──► notebooks EDA (DuckDB)
 PostgreSQL                                   │
 (products, categories, brands,               │ ⏳ --build_datasets
  labels, origins, ingredients,               ▼
  additives, tables products_*)        data/exports/features_nutriscore_<date>.parquet
        │                                     + schema.json (SHA-256, commit)
        │                                     │
        │ export_to_parquet                   ▼
        ▼                              entraînement ML ⏳
 data/export/<table>.parquet                  │
                                              ▼ modèle sérialisé
        ▼                                     ▼
   API FastAPI ⏳  ◄──────────────────────────┘
   (fiche, score, substituts)
```

Sens de lecture : les flèches vont toujours vers le bas. Aucun consommateur n'écrit dans un magasin situé au-dessus de lui.

**Lancer la pipeline :** `python -m src.pipeline --all` (ou `--download`, `--clean`, `--load_database` séparément). La connexion PostgreSQL est lue dans le `.env` (`POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`). Un dossier `airflow/` est prévu pour orchestrer les mêmes étapes.

---

## 5. Ce qui change en phases suivantes

| Aujourd'hui (local) | Phase cloud | Ce qui ne change pas |
|---|---|---|
| `data/` sur le disque de l'équipe | **Stockage objet** (bucket S3 ou compatible) ; DuckDB lit directement via l'extension `httpfs` | Les chemins logiques, le partitionnement, les règles de reproductibilité |
| PostgreSQL local | **Base managée** : sauvegardes planifiées, accès réseau restreint à l'API | L'API reste le seul client applicatif ; le script de chargement reste la seule façon d'y écrire |
| Pipeline lancée à la main | Pipeline lancée par Airflow ou la CI, secrets en variables d'environnement | Chaque étape reste relançable seule et reproductible |
| Modèle chargé depuis le disque | Modèle et export de référence publiés avec leur empreinte | Le modèle cite l'export sur lequel il a été entraîné |

---

_Documents liés : `docs/data/rapport_nettoyage.md` · `docs/data/strategie_manquants.md` · `src/db_psql/create_tables.sql` · `docs/annexes/MCD-NutriScope.svg`._

# Pipeline NutriScope : du parquet brut aux données ML

> TP 13 · jalon J3 · tag `v0.3`
> Données : © Open Food Facts contributors, licence ODbL. Chaque fichier produit le rappelle
> (manifeste, schémas, rapport de nettoyage).

Une commande, depuis la racine du dépôt :

```bash
python -m src.pipeline --all
```

Installation et configuration : voir le [README](../../README.md).

---

## 1. Schéma du flux

```
 Open Food Facts (Hugging Face, 8 Go)          NUTRISCOPE_SOURCE (échantillon, extrait)
            │ téléchargé si absent                        │
            ▼                                             │
     data/food.parquet ───────────────┬───────────────────┘
                                      │
 ┌─ download ─────────────────────────▼───────────────────────────────────────────────┐
 │ filtre France + colonnes utiles, code en texte, tri par code                       │
 │ → data/raw/food_france_<date>.parquet                                              │
 │ → data/raw/manifest_<date>.json   (SHA-256 source et brut, lignes, filtre, ODbL)   │
 └────────────────────────────────────┬───────────────────────────────────────────────┘
                                      │ lu par : clean
 ┌─ clean ────────────────────────────▼───────────────────────────────────────────────┐
 │ 8 règles du TP 9, dans l'ordre (types, textes, doublons, unités, bornes,           │
 │ énergie, catégories, manquants)                                                    │
 │ → data/parquet/food_clean_<date>.parquet   ← SOURCE DE VÉRITÉ UNIQUE               │
 │ → docs/data/rapport_nettoyage.md           (compte rendu règle par règle)          │
 └──────────────┬─────────────────────────────────────────────────┬───────────────────┘
                │ lu par : load_database                          │ lu par : extract_parquet
 ┌─ load_database ▼───────────────────────┐   ┌─ extract_parquet ──▼────────────────────────┐
 │ tables recréées, COPY, contraintes     │   │ types compacts, ZSTD, tri par code          │
 │ → PostgreSQL (products, tags,          │   │ → data/parquet/products_<date>/             │
 │   nutriments, liaisons)                │   │     food_group=<rayon>/… + _SUCCESS         │
 │ contrôle : nb produits = nettoyé       │   │ → schema_products_<date>.json               │
 └──────────────┬─────────────────────────┘   │ contrôle : nb produits = nettoyé            │
                │                             └──────────────┬──────────────────────────────┘
                ▼                                            │ lu par : build_dataset
      APPLICATION (API)                     ┌─ build_dataset ─▼─────────────────────────────┐
      accès par clé, une fiche              │ filtres ML, ratios, split stratifié (graine 42)│
      à la fois                             │ → data/exports/features_<date>.parquet  FIGÉ  │
                                            │ → data/exports/schema.json                     │
                                            └──────────────┬────────────────────────────────┘
                                                           ▼
                                             ANALYSE ET ML (phase 4, TP 14-16)

 Chaque étape ajoute une ligne à data/logs/pipeline.jsonl (horodatage, étape, durée, statut, lignes).
```

Ce qu'il faut retenir (reprise de [architecture.md](architecture.md)) :

- **La base sert l'application**, le **Parquet sert l'analyse et le ML**. L'entraînement ne lit
  jamais la base, ni le nettoyé : il lit l'export figé.
- `load_database` et `extract_parquet` partent **du même nettoyé**. Chacune vérifie qu'elle a écrit
  autant de produits que lui, et échoue sinon.
- **Tout est daté** (`<date>` = AAAAMMJJ). Chaque étape lit la sortie du jour de l'étape précédente,
  sinon la plus récente ; si elle n'en trouve aucune, elle dit quelle étape lancer avant.
- Un dossier partitionné n'est lu que s'il contient `_SUCCESS`, écrit en dernier.
- Tout `data/` est hors Git ; la commande, la graine et les règles sont dans le dépôt.

## 2. Commandes

| Besoin | Commande |
| --- | --- |
| Tout, du brut aux exports | `python -m src.pipeline --all` |
| Une étape seule | `python -m src.pipeline --download` (ou `--clean`, `--load_database`, `--extract_parquet`, `--build_dataset`) |
| Échantillon au lieu du jeu complet | `NUTRISCOPE_SOURCE=<chemin du parquet>` dans `.env` (ou dans l'environnement), puis la même commande |
| Jeu complet (extrait France) | laisser `NUTRISCOPE_SOURCE` vide : le parquet Open Food Facts est téléchargé une fois dans `data/food.parquet` |
| Retélécharger la source | `python -m src.pipeline --download --force` |
| Réécrire l'export ML du jour | `python -m src.pipeline --build_dataset --force` (même graine : même fichier, même SHA-256) |
| Rejouer une date | les sorties d'une date restent en place : une étape relancée seule reprend la plus récente. Pour produire un nouvel export sans écraser l'ancien, le lancer un autre jour ; l'ancien `features_<date>.parquet` reste intact |
| Tests | `python -m pytest -q` |
| Tout est cassé | `rm -rf data/raw data/parquet data/exports data/logs` puis `python -m src.pipeline --all` (garder `data/food.parquet` évite 8 Go de téléchargement) |

Si l'entrée d'une étape manque, le message dit quoi faire et le code de sortie vaut 1 :

```
✘ Aucune sortie 'food_clean_*.parquet' complète dans …/data/parquet : lancer d'abord `python -m src.pipeline --clean`.
```

## 3. Durées mesurées

Durées relevées dans `data/logs/pipeline.jsonl`, exécution `--all` du 12/11/2026.

**Machine** : Intel Core i7-11700 (8 cœurs, 2,5 GHz), 32 Go de RAM, Windows 11 Entreprise ·
Python 3.12.10 · DuckDB 1.5.5 · pandas 3.0.5 · pyarrow 25.0.1 · PostgreSQL 18.6 en local.

| Étape | Échantillon : durée | Échantillon : lignes | Extrait France : durée | Extrait France : lignes |
| --- | ---: | ---: | ---: | ---: |
| `download` | 0,2 s | 5 273 | 72,0 s | 1 294 426 |
| `clean` | 0,6 s | 2 208 | 148,3 s | 548 913 |
| `load_database` | 3,3 s | 2 208 | 86,6 s | 548 913 |
| `extract_parquet` | 0,2 s | 2 208 | 2,1 s | 548 913 |
| `build_dataset` | 0,1 s | 1 858 | 1,7 s | 464 175 |
| **Total** | **4,4 s** | | **≈ 5 min 10 s** | |

- **Échantillon** : 20 000 produits tirés du parquet Open Food Facts
  (`USING SAMPLE reservoir(20000 ROWS) REPEATABLE (42)`), dont 5 273 vendus en France.
  Exécuté dans un clone neuf, avec un venv neuf, en suivant le README.
- **Extrait France** : le parquet complet (8 Go) déjà présent, donc **sans le téléchargement**
  (non mesuré : il dépend du réseau). `download` se décompose en 64 s de filtre et de tri, puis environ
  8 s pour les empreintes SHA-256 du manifeste.
- Une relance de `load_database` seule a pris 66,3 s.

**Lecture.** `clean` domine (près de la moitié du total) : les règles du TP 9 tournent en pandas,
ligne par ligne pour certaines (textes, marques, tags), sur 1,3 million de produits. Viennent ensuite
`load_database`, limité par l'écriture dans PostgreSQL et la recréation des contraintes, puis `download`,
qui relit les 8 Go de la source et trie sur un seul thread pour écrire des octets identiques
à chaque exécution. Les deux étapes DuckDB sur Parquet (`extract_parquet`, `build_dataset`) prennent
quelques secondes. Avec cinq minutes de bout en bout, une chaîne linéaire et une seule machine,
**un orchestrateur (Airflow, Prefect) n'est pas justifié** : la CLI suffit. S'il faut gagner du temps,
le levier est le nettoyage (vectoriser les règles ou les passer en DuckDB), pas l'orchestration.

## 4. Ce que la phase 4 lira

**Le fichier** : `data/exports/features_<date>.parquet`, décrit par `data/exports/schema.json`.
Export du 12/11/2026 : 464 175 produits, SHA-256
`c3d8555768d7442af3b6714d406d58efc9924bd51d002deb5f271ccf7f3c0f77`.

**Le split** : colonne `split` (`train` / `test`), stratifiée sur `nutriscore_grade`.
Dans chaque grade, les produits sont classés par `md5(code || '42')` et les 20 % premiers vont en test.
L'affectation d'un produit ne dépend que de son code, de son grade et de la graine : elle est la même
à chaque exécution. 20 % laisse assez de produits a et b dans le test, et 80 % pour l'entraînement
et la validation croisée.

| Grade | Train | Test | Part de test |
| --- | ---: | ---: | ---: |
| a | 49 058 | 12 265 | 0,20 |
| b | 37 807 | 9 452 | 0,20 |
| c | 77 824 | 19 456 | 0,20 |
| d | 99 566 | 24 892 | 0,20 |
| e | 107 084 | 26 771 | 0,20 |

**Le schéma** :

| Colonne | Type | Unité | Rôle | Manquants (%) |
| --- | --- | --- | --- | ---: |
| `code` | VARCHAR | - | identifiant | 0 |
| `food_group` | VARCHAR | - | feature | 0 |
| `energy-kcal_100g` | FLOAT | kcal/100g | feature | 0 |
| `fat_100g` | FLOAT | g/100g | feature | 0 |
| `saturated-fat_100g` | FLOAT | g/100g | feature | 0 |
| `carbohydrates_100g` | FLOAT | g/100g | feature | 0 |
| `sugars_100g` | FLOAT | g/100g | feature | 0 |
| `proteins_100g` | FLOAT | g/100g | feature | 0 |
| `salt_100g` | FLOAT | g/100g | feature | 0 |
| `additives_n` | SMALLINT | nombre | feature | 0 |
| `nova_group` | TINYINT | 1-4 | feature | 0 |
| `sugars_to_carbs_ratio` | FLOAT | ratio | feature | 6,4 |
| `sat_fat_to_fat_ratio` | FLOAT | ratio | feature | 7,3 |
| `fat_energy_share` | FLOAT | ratio | feature | 0 |
| `nutriscore_score` | SMALLINT | points | **fuite, interdit** | 0 |
| `nutriscore_grade` | VARCHAR | a-e | **cible** | 0 |
| `split` | VARCHAR | - | split | 0 |

`schema.json` donne aussi, par colonne, la politique d'imputation prévue, plus les filtres appliqués,
le commit Git, la graine et les effectifs par grade.

**Les règles d'usage** :

- `fit` sur le train seulement. Le test n'est regardé qu'une fois, à la fin. La validation croisée
  se fait à l'intérieur du train.
- **Ne pas recalculer le split** : utiliser la colonne `split` telle quelle.
- **Ne pas utiliser `nutriscore_score`** pour prédire le grade : le grade en est déduit directement.
- **Ne pas utiliser `code`, `product_name` ou `brands` comme features** (identifiants, pas des propriétés
  nutritionnelles ; `product_name` et `brands` ne sont d'ailleurs pas dans l'export).
- Quand une règle de nettoyage change, régénérer tout avec une nouvelle date, sans écraser
  l'export précédent, et noter dans le suivi des modèles sur quel `features_<date>.parquet`
  (et quel `sha256`) chacun a été entraîné.

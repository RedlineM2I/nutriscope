# Nutriscope

Projet fil rouge de la formation dev IA : un pipeline qui va du parquet brut Open Food Facts
aux données prêtes pour le machine learning (prédiction du Nutri-Score).

Une commande enchaîne cinq étapes :

| Étape             | Lit                                   | Écrit                                                              |
| ----------------- | ------------------------------------- | ------------------------------------------------------------------ |
| `download`        | parquet Open Food Facts (ou `NUTRISCOPE_SOURCE`) | `data/raw/food_france_<date>.parquet` + `manifest_<date>.json`     |
| `clean`           | brut France le plus récent            | `data/parquet/food_clean_<date>.parquet` + `docs/data/rapport_nettoyage.md` |
| `load_database`   | nettoyé le plus récent                | base PostgreSQL (tables recréées à chaque fois)                    |
| `extract_parquet` | nettoyé le plus récent                | `data/parquet/products_<date>/` partitionné par rayon + `_SUCCESS` |
| `build_dataset`   | Parquet partitionné le plus récent    | `data/exports/features_<date>.parquet` (colonne `split`) + `schema.json` |

Le détail du flux, des commandes et des durées mesurées est dans [docs/data/pipeline.md](docs/data/pipeline.md).

Données : © Open Food Facts contributors, licence ODbL. Le dépôt contient le code qui produit
les données, jamais les données : tout `data/` est ignoré par Git.

## 1. Prérequis

- **Python 3.12** (testé avec 3.12.10). Vérifier : `python --version`
- **Git**
- **PostgreSQL** (testé avec la version 18), avec une base et un utilisateur qui en est
  propriétaire : le pipeline supprime et recrée les tables lui-même.
  La création pas à pas est décrite dans [docs/annexes/creation_base.md](docs/annexes/creation_base.md).
- **Espace disque** : environ 10 Go pour le jeu complet (le parquet Open Food Facts fait 8 Go),
  quelques Mo avec un échantillon.

## 2. Installation

Toutes les commandes se lancent **depuis la racine du dépôt** (le dossier qui contient ce README).

```bash
git clone https://github.com/RedlineM2I/nutriscope.git
cd nutriscope

python -m venv .venv
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
# Windows (Git Bash)
source .venv/Scripts/activate
# Linux / macOS
source .venv/bin/activate

python -m pip install -r requirements.txt
```

Pour les notebooks d'exploration seulement : `python -m pip install -r requirements-notebooks.txt`.

## 3. Configuration

Copier le modèle de configuration puis le remplir :

```bash
cp .env.example .env
```

| Variable            | Exemple      | Rôle                                                     |
| ------------------- | ------------ | -------------------------------------------------------- |
| `POSTGRES_HOST`     | `localhost`  | serveur PostgreSQL                                       |
| `POSTGRES_PORT`     | `5432`       | port                                                     |
| `POSTGRES_DB`       | `nutriscope` | base (doit exister)                                      |
| `POSTGRES_USER`     | `nutriscope_app` | utilisateur propriétaire de la base                  |
| `POSTGRES_PASSWORD` | `...`        | mot de passe                                             |
| `NUTRISCOPE_SOURCE` | *(vide)*     | optionnel : parquet source à utiliser au lieu du téléchargement |

## 4. Les données source

Deux possibilités :

- **Jeu complet** : laisser `NUTRISCOPE_SOURCE` vide. L'étape `download` télécharge le parquet
  Open Food Facts depuis Hugging Face (8 Go) dans `data/food.parquet`, en vérifie l'empreinte
  SHA-256, puis ne le retélécharge plus tant qu'il est présent.
- **Échantillon** : définir `NUTRISCOPE_SOURCE` avec le chemin d'un parquet **au même format
  qu'Open Food Facts** (celui de Hugging Face), par exemple l'échantillon du jeu partagé.
  Un chemin relatif est pris depuis la racine du dépôt. Rien n'est téléchargé.

```bash
# dans .env
NUTRISCOPE_SOURCE=C:/chemin/vers/echantillon.parquet
```

## 5. Lancer le pipeline

```bash
python -m src.pipeline --all
```

Chaque étape peut aussi se lancer seule, elle retrouve sa propre entrée :

```bash
python -m src.pipeline --download
python -m src.pipeline --clean
python -m src.pipeline --load_database
python -m src.pipeline --extract_parquet
python -m src.pipeline --build_dataset
```

L'export ML est **figé** : relancer `--build_dataset` le même jour est refusé.
Pour le réécrire en l'assumant : `python -m src.pipeline --build_dataset --force`
(avec la même graine, il redonne exactement le même fichier).

> **Windows** : si l'affichage plante sur `UnicodeEncodeError` (console en cp1252),
> lancer d'abord `set PYTHONIOENCODING=utf-8` (cmd), `$env:PYTHONIOENCODING="utf-8"` (PowerShell)
> ou `export PYTHONIOENCODING=utf-8` (Git Bash).

## 6. Sortie attendue

En fin d'exécution, un récapitulatif affiche une ligne par étape (durée, lignes, fichiers) :

```
 >> RÉCAPITULATIF
✔ download            …  s    <n_france> lignes  …
✔ clean               …  s    <n_clean>  lignes  …
✔ load_database       …  s    <n_clean>  lignes
✔ extract_parquet     …  s    <n_clean>  lignes  …
✔ build_dataset       …  s    <n_export> lignes  …
Journal des durées : …/data/logs/pipeline.jsonl
```

`load_database` et `extract_parquet` affichent **le même nombre de produits** que le nettoyé :
les deux étapes le vérifient et échouent sinon.

Si une étape n'a pas son entrée, elle s'arrête avec un message qui dit quoi lancer avant, par exemple :

```
✘ Aucune sortie 'food_clean_*.parquet' complète dans …/data/parquet : lancer d'abord `python -m src.pipeline --clean`.
```

## 7. Vérifier que ça a marché

1. Les tests passent : `python -m pytest -q`
2. Les fichiers du jour existent :
   - `data/raw/food_france_<date>.parquet` et `data/raw/manifest_<date>.json`
   - `data/parquet/food_clean_<date>.parquet`
   - `data/parquet/products_<date>/_SUCCESS`
   - `data/exports/features_<date>.parquet` et `data/exports/schema.json`
3. Dans `data/exports/schema.json`, `split.seed` vaut `42` et `split.counts_by_grade`
   donne une part de test (`test_share`) proche de 0,20 pour chacun des grades a à e.
4. `data/logs/pipeline.jsonl` contient une ligne `"status": "ok"` par étape lancée.

## 8. Quand tout est cassé

Supprimer les sorties puis tout relancer (le parquet téléchargé `data/food.parquet` peut être gardé) :

```bash
rm -rf data/raw data/parquet data/exports data/logs
python -m src.pipeline --all
```

## Structure du dépôt

```
src/            code du pipeline (pipeline.py = point d'entrée)
  cleaning.py   règles de nettoyage (TP 9)
  db_psql/      schéma et chargement PostgreSQL (TP 4)
  storage/      conversion Parquet et export ML (TP 12, 13)
tests/          tests pytest, sur données synthétiques en dossiers temporaires
docs/           cadrage, documentation data, journal d'équipe
notebooks/      exploration (TP 1, 2, 10)
data/           sorties du pipeline, hors Git
```

# Benchmark honnête

## Ce que « honnête » veut dire

Un benchmark est honnête quand chacun peut le rejouer et que ses limites sont écrites. Voici comment il a été mené.

**Méthode**
- **Un sous-processus neuf par mesure** : aucun cache Python, DuckDB ou pandas n'est partagé d'une mesure à l'autre.
- **Trois répétitions** : on retient la **médiane** des temps (résistante aux pics ponctuels) et le **maximum** des pics mémoire (RSS).
- **Temps = lecture + requête** : charger les données fait partie du coût, pour pandas comme pour les autres.
- **Mesure de référence « imports seulement »** (`baseline`) : elle donne le poids de l'interpréteur et des bibliothèques, à soustraire mentalement des pics mémoire.
- **Résultats vérifiés avant chronométrage** : les trois moteurs renvoient le même nombre de lignes, et des tris avec départage (`ORDER BY …, code`) évitent que les ex æquo changent l'ordre.
- **Aucun avantage donné à un moteur** : PostgreSQL est mesuré **sans index ajouté** pour l'occasion, et pandas ne lit que les colonnes utiles (`columns=`).

**Limites connues**
- **Pandas lit le Parquet complet, pas un CSV** (le sujet prévoyait un CSV, mais notre jeu nettoyé est en Parquet). L'écart pandas / DuckDB mesure donc le **moteur**, et non le format : le coût de lecture d'un CSV n'est pas mesuré.
- **PostgreSQL et le Parquet ne répondent pas exactement à la même question pour les marques** : la base garde toutes les marques d'un produit, le Parquet seulement la première (`brands_tags[1]`). Les 20 marques du top peuvent différer.
- **Cache du système d'exploitation** : un fichier déjà lu est plus rapide à relire. Les sous-processus neufs ne l'effacent pas, donc les mesures reflètent un disque « chaud ».
- **Une seule machine, un seul jeu de données** : les ordres de grandeur sont fiables, pas les valeurs exactes.
- **Pic mémoire par processus** : pour PostgreSQL, il mesure le **client** Python, pas la mémoire du serveur de base de données.
- **Le coût de construction** de chaque support (Parquet complet, Parquet partitionné, base chargée) est indiqué à part et n'est pas inclus dans les temps de requête.

## Machines utilisées

| Nom         | Composant                                     |
|-------------|-----------------------------------------------|
| Processeur  | 11th Gen Intel(R) Core(TM) i7-11700 @ 2.50GHz |
| Mémoire RAM | 32,0 Go 3200 MT/s                             |
| Disque      | NVMe Samsung 1024GB                           |
| OS          | Windows 11                                    |

## Versions

| Dépendance | Version |
|------------|---------|
| Python     | 3.12.10 |
| duckdb     | 1.5.5   |
| pandas     | 3.0.5   |
| PostgreSQL | 17.11   |

## Coûts de constructions

| Méthode             | Temps  |
|---------------------|--------|
| Parquet complet     | s      |
| Base PostgreSQL     | s      |
| Parquet partitionné | 1.308s |

## Tableau comparatif

Données : © Open Food Facts contributors, ODbL

| Moteur / requête                  | Temps médian (s) | Pic mémoire (Mo) | Lignes |
|-----------------------------------|------------------|------------------|--------|
| pandas_parquet/aggregate          | 0.09             | 248              | 12     |
| duckdb_parquet/aggregate          | 0.03             | 167              | 12     |
| postgres/aggregate                | 0.25             | 160              | 0      |
| pandas_parquet/filter             | 0.17             | 288              | 20     |
| duckdb_parquet/filter             | 0.04             | 161              | 20     |
| postgres/filter                   | 0.24             | 161              | 0      |
| pandas_parquet/brand_completeness | 0.52             | 301              | 20     |
| duckdb_parquet/brand_completeness | 0.06             | 187              | 20     |
| postgres/brand_completeness       | 0.83             | 160              | 20     |
| -/baseline                        | 0.04             | 158              | 0      |

## Interprétation

- Pour une fonction d'agrégation classique (moyenne des sucres et du sel par rayon), DuckDB et Pandas n'ont pas beaucoup
  d'écart, sauf pour le pic mémoire ou DuckDB est beaucoup plus efficace.
- Pour les fonctions de filtre (les produits les plus sucrés par rayon) DuckDB est beaucoup plus rapide et efficace que
  les deux autres méthodes.
- Lorsqu'on veut récupérer la complétude du Nutri-Score par marques, DuckDB est de loin le plus efficace sur les
  fichiers parquets séparés. Par contre, il a un pic de mémoire plus élevé que la BDD Postgresql

En conclusion, on peut dire que l'utilisation de DuckDB sur des fichiers parquets séparés rend les requêtes entre 3x et
10x plus efficace en therme de temps d'exécution les 3 types de requêtes testées.
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


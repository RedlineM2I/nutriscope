# ADR-001 — Modèle de prédiction du Nutri-Score

Date : 2026-11-24 · Statut : acceptée · Source des chiffres : `notebooks/methodes_ensemble.ipynb`

## Contexte

NutriScope doit prédire le grade Nutri-Score (a à e) des produits qui n'en ont pas, pour
alimenter le moteur de substitution (TP 16) puis l'API (phase 6). L'API charge le pipeline
persisté et répond produit par produit : la taille du fichier et la latence d'une prédiction
sont des contraintes, en plus de la performance.

Protocole commun à toutes les options : même préparation (`prep_pipeline`), mêmes 5 plis
(`StratifiedKFold`, graine 42), mêmes métriques, colonne `split` du TP 13. Le test
(5 965 produits) n'a été évalué qu'une fois, après toutes les décisions.

## Options considérées

| Modèle | F1 macro CV | F1 test | Latence (1 produit) | Taille | Réentraînement |
|---|---|---|---|---|---|
| Régression logistique | 0,767 ± 0,008 | 0,772 | 5,8 ms | 0,01 Mo | 1,0 s |
| Forêt aléatoire (TP 14) | 0,858 ± 0,007 | 0,857 | 9,9 ms | 81,5 Mo | 2,4 s |
| HistGradientBoosting | 0,892 ± 0,006 | 0,891 | 11,1 ms | 1,84 Mo | 2,0 s |
| XGBoost | 0,894 ± 0,005 | 0,892 | 11,4 ms | 1,78 Mo | 1,1 s |
| **LightGBM (défaut)** | **0,888 ± 0,007** | **0,886** | **7,6 ms** | **1,74 Mo** | **0,7 s** |
| LightGBM réglé (Optuna) | 0,895 ± 0,010 | 0,893 | 8,0 ms | 27,7 Mo | 7,5 s |

- Les trois boosters sont **indiscernables** en performance (écarts ≤ un écart-type).
  Ils battent la forêt d'environ 0,03, soit 4 à 5 écarts-types.
- Le réglage Optuna (30 essais, 10,9 min) apporte +0,007, sous le seuil de 2 écarts-types
  (0,020), pour un fichier 16 fois plus gros et un réentraînement 11 fois plus long.
- Explicabilité : équivalente pour les boosters (ensembles d'arbres, importances et SHAP
  possibles). La logistique est plus lisible, mais perd 0,12 de F1 macro.

## Décision

NutriScope utilise **LightGBM** avec ses réglages par défaut, dans le pipeline de préparation commun.

## Conséquences

- LightGBM devient une dépendance de l'API (phase 6), en plus de scikit-learn.
- Le pipeline persisté pèse 1,74 Mo et répond en 7,6 ms par produit.
- On renonce à +0,006 de F1 (XGBoost) et à +0,007 (réglage) : gains non démontrés.
- Les limites documentées dans `docs/ml/limites_nutriscore.md` s'appliquent : rappel de
  « b » à 0,77, boissons notées sans leur grille spéciale, alcools hors périmètre.

## Ce qui déclencherait une révision

- Sur un nouvel export, le F1 macro du modèle descend sous 0,86 (niveau de la forêt).
- Le passage au jeu complet (`nutriscope_ml_full`) change le classement des boosters
  de plus d'un écart-type.
- L'ajout d'une feature « boisson » : il faudra remesurer toutes les options.
- La latence mesurée dans l'API dépasse le budget fixé en phase 6.

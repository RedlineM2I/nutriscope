# Jeux de données prêts pour le machine learning : phase 4

- `nutriscope_ml_full.parquet` : 422 470 produits (13.8 Mo), colonne `split` train / test 80-20 stratifiée sur le grade, graine 42.
- `nutriscope_ml_sample.parquet` : 30 041 produits (1.3 Mo), stratifiés grade × rayon, même colonne `split`

## Colonnes

| Colonne                                                                                                                 | Rôle                                                                                                                          |
| ----------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `code`, `product_name`, `brands`                                                                                        | identification, analyse d'erreurs (jamais des features)                                                                       |
| `pnns_groups_1`, `pnns_groups_2`                                                                                        | rayon et sous-rayon PNNS (catégorielles)                                                                                      |
| `nova_group`, `additives_n`                                                                                             | transformation et additifs (entiers nullables)                                                                                |
| `energy-kcal_100g`, `fat_100g`, `saturated-fat_100g`, `carbohydrates_100g`, `sugars_100g`, `proteins_100g`, `salt_100g` | les sept nutriments obligatoires (sans manquant)                                                                              |
| `fiber_100g`, `fruits-vegetables-legumes_100g`                                                                          | nutriments optionnels (manquants fréquents : à imputer ou à signaler)                                                         |
| `nutriscore_score`                                                                                                      | **cible de régression** (entier, −15 à 40) — dérivé des nutriments : **interdit comme feature** pour prédire le grade (fuite) |
| `nutriscore_grade`                                                                                                      | **cible de classification** (a-e)                                                                                             |
| `completeness`, `last_modified`                                                                                         | métadonnées                                                                                                                   |
| `split`                                                                                                                 | `train` ou `test` : ne jamais réajuster le découpage, ne jamais regarder le test avant la fin                                 |

### Grades — jeu complet

| Valeur | Produits |
| ------ | -------- |
| a      | 56 752   |
| b      | 45 365   |
| c      | 87 437   |
| d      | 111 838  |
| e      | 121 078  |

### Rayons — jeu complet

| Valeur                  | Produits |
| ----------------------- | -------- |
| Sugary snacks           | 91 348   |
| Fish Meat Eggs          | 77 367   |
| Milk and dairy products | 53 050   |
| Cereals and potatoes    | 45 966   |
| Composite foods         | 36 267   |
| Beverages               | 31 449   |
| Fat and sauces          | 30 856   |
| Fruits and vegetables   | 29 063   |
| Salty snacks            | 27 058   |
| Alcoholic beverages     | 46       |

### Grades — échantillon

| Valeur | Produits |
| ------ | -------- |
| a      | 4 030    |
| b      | 3 230    |
| c      | 6 235    |
| d      | 7 942    |
| e      | 8 604    |

### Split — échantillon

| Valeur | Produits |
| ------ | -------- |
| train  | 24 076   |
| test   | 5 965    |

### Manquants dans l'échantillon (%)

| Colonne                          | Manquants |
| -------------------------------- | --------- |
| `product_name`                   | 1.3 %     |
| `brands`                         | 20.9 %    |
| `nova_group`                     | 43.6 %    |
| `additives_n`                    | 41.2 %    |
| `fiber_100g`                     | 46.8 %    |
| `fruits-vegetables-legumes_100g` | 41.7 %    |

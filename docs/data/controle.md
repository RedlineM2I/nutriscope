# Contrôles de qualité (DuckDB sur Parquet)

Données : © Open Food Facts contributors, ODbL

## comptage_par_rayon

| rayon | produits | part_pct |
|---|---|---|
| sugary-snacks | 104966 | 19.2 |
| fish-meat-eggs | 84228 | 15.4 |
| milk-and-dairy-products | 57679 | 10.55 |
| unknown | 54873 | 10.04 |
| cereals-and-potatoes | 53914 | 9.86 |
| beverages | 43977 | 8.04 |
| composite-foods | 37358 | 6.83 |
| fats-and-sauces | 35976 | 6.58 |
| fruits-and-vegetables | 34335 | 6.28 |
| salty-snacks | 28660 | 5.24 |
| alcoholic-beverages | 8347 | 1.53 |
| baby-foods-and-milks | 2446 | 0.45 |

## completude

| rayon | produits | nutriscore_pct | nutriments_cles_pct | categorie_pct |
|---|---|---|---|---|
| sugary-snacks | 104966 | 89.76 | 91.96 | 100.0 |
| fish-meat-eggs | 84228 | 94.3 | 94.65 | 100.0 |
| milk-and-dairy-products | 57679 | 94.38 | 94.95 | 100.0 |
| unknown | 54873 | 66.18 | 85.54 | 100.0 |
| cereals-and-potatoes | 53914 | 89.58 | 93.05 | 100.0 |
| beverages | 43977 | 73.93 | 84.42 | 100.0 |
| composite-foods | 37358 | 94.85 | 96.56 | 100.0 |
| fats-and-sauces | 35976 | 87.23 | 93.22 | 100.0 |
| fruits-and-vegetables | 34335 | 86.67 | 88.32 | 100.0 |
| salty-snacks | 28660 | 94.79 | 95.31 | 100.0 |
| alcoholic-beverages | 8347 | 0.69 | 23.51 | 100.0 |
| baby-foods-and-milks | 2446 | 0.0 | 91.29 | 100.0 |

## doublons_codes

| groupes_en_double | lignes_en_trop |
|---|---|
| 0 | 0 |

## doublons_nom_marque

| product_name | brand | n |
|---|---|---|
| Comté | unknown | 402 |
| Huile d'olive | unknown | 270 |
| Huile d'olive vierge extra | unknown | 244 |
| Filet de poulet | la-nouvelle-agriculture | 239 |
| Pain complet | unknown | 221 |
| Saucisson sec | unknown | 184 |
| Filet de poulet | le-gaulois | 180 |
| Abricot sec | unknown | 177 |
| Miel | unknown | 168 |
| Emmental | unknown | 165 |
| Filet de poulet | unknown | 152 |
| Amandes décortiquées | unknown | 146 |
| Filets de poulet | la-nouvelle-agriculture | 141 |
| Saumon fumé | unknown | 140 |
| Filets de poulet rôti | le-gaulois | 138 |
| Jambon à l'ancienne | unknown | 136 |
| Chipolatas | unknown | 135 |
| Mayonnaise | unknown | 123 |
| Terrine de campagne | unknown | 120 |
| Pain au chocolat | unknown | 117 |

## bornes_et_coherences

| nutriments_hors_0_100 | energie_hors_0_900 | sucres_sup_glucides | satures_sup_lipides | energie_nulle_avec_macros | sel_incoherent |
|---|---|---|---|---|---|
| 0 | 7 | 269 | 309 | 678 | 0 |

## distribution_nutriscore

| grade | produits | part_pct | score_moyen |
|---|---|---|---|
| a | 63444 | 11.6 | -2.94 |
| b | 49430 | 9.04 | 0.59 |
| c | 97618 | 17.85 | 5.62 |
| d | 124465 | 22.76 | 14.08 |
| e | 134048 | 24.52 | 23.26 |
| not-applicable | 27039 | 4.95 | None |
| null | 50715 | 9.28 | None |

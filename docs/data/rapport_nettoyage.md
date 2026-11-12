# Rapport de nettoyage NutriScope

- **Date** : 2026-11-12
- **Source** : Export Open Food Facts, périmètre France
- **Crédit** : Données issues d'[Open Food Facts](https://world.openfoodfacts.org) (ODbL pour la base, CC-BY-SA pour les images).

## 1. Volumétrie
 ### Avant nettoyage :  
 1294426
 ### Après nettoyage :  
 548913


## 2. Rapport de nettoyage
 ### Tableau des rapports :  
 | Règle | Lignes avant | Lignes après | Lignes touchées | Détail |
|---|---|---|---|---|
| typer_colonnes | 1294426 | 1294426 | 0 ||
| normalize_texts | 1294426 | 1294426 | 1267475 | noms_vides : 1 ; noms_majuscules : 15859 ; nutriscore_grade_unknown : 746922 ; environmental_score_grade_unknown : 796080 ; categories_tags_normalises : 685612 ; origins_tags_normalises : 402510 ; labels_tags_normalises : 702848 ; additives_tags_normalises : 370143 ; brands_tags_normalises : 728555 ; ingredients_tags_normalises : 370603 ; food_groups_tags_normalises : 1264149 ; marques_fusionnees : 90636 ;|
| Dédupliquer les codes | 1294426 | 1294398 | 28 | sans_code : 0 ; doublons_supprimes : 28 ;|
| normalize_units | 1294398 | 1294398 | 128128 | kcal_derivees : 364 ; kcal_recalculees : 114995 ; sel_derive : 1 ; sodium_derive : 0 ; sodium_recalcule : 13463 ;|
| limit_nutriments | 1294398 | 1294398 | 3125 | energy-kcal_100g_negatifs : 8 ; energy-kcal_100g_au_dessus : 0 ; sugars_100g_negatifs : 0 ; sugars_100g_au_dessus : 45 ; carbohydrates_100g_negatifs : 0 ; carbohydrates_100g_au_dessus : 85 ; fat_100g_negatifs : 1 ; fat_100g_au_dessus : 45 ; saturated-fat_100g_negatifs : 1 ; saturated-fat_100g_au_dessus : 15 ; salt_100g_negatifs : 0 ; salt_100g_au_dessus : 55 ; proteins_100g_negatifs : 1 ; proteins_100g_au_dessus : 35 ; fiber_100g_negatifs : 19 ; fiber_100g_au_dessus : 21 ; sodium_100g_negatifs : 0 ; sodium_100g_au_dessus : 55 ; fruits-vegetables-legumes_100g_negatifs : 51 ; fruits-vegetables-legumes_100g_au_dessus : 2173 ; energy_100g_negatifs : 8 ; energy_100g_au_dessus : 0 ; sucres : 436 ; satures : 243 ;|
| fix_energy | 1294398 | 1294398 | 5637 | nulles_recalculees : 389 ; nulles_invalidees_macros_aberrants : 0 ; >900_recalculees : 143 ; >900_invalidees : 73 ; incoherentes_recalculees : 5032 ;|
| traiter_categories_vides | 1294398 | 639478 | 730189 | categorie_vide : 654920 ; food_group_derive_de_vide : 730189 ; food_group_unknown_total : 730189 ; inclassables_supprimes : 654920 ;|
| strategie_manquants | 639478 | 548913 | 624437 | quantity → drop_column : 1 ; brands_tags → constant : 162102 ; labels_tags → constant : 292559 ; origins_tags → constant : 558076 ; ingredients_tags → constant : 312768 ; additives_tags → constant : 471228 ; energy-kcal_100g → flag : 111414 ; fat_100g → flag : 114987 ; saturated-fat_100g → flag : 117354 ; carbohydrates_100g → flag : 115139 ; sugars_100g → flag : 116553 ; fiber_100g → flag : 357951 ; proteins_100g → flag : 114438 ; salt_100g → flag : 130493 ; sodium_100g → flag : 130493 ; nova_group → mode : 318187 ; dropped_columns : ['quantity'] ; rows_dropped_no_nutrient : 90565 ;|



## 3. Anomalies métier
 ### Avant nettoyage :  
  Sucres > 100 g  : 45

 Matières grasses > 100 g  : 45

 Sel > 100 g  : 55

 Protéines > 100 g  : 35

 Énergie > 3 800 kJ  : 113

 Somme des macronutriments > 100 g  : 2738

 Valeurs négatives  : 

 | energy_100g | sugars_100g | carbohydrates_100g | fat_100g | saturated-fat_100g | salt_100g | proteins_100g | fiber_100g | sodium_100g | fruits-vegetables-legumes_100g |
|---|---|---|---|---|---|---|---|---|---|
| 8 | 0 | 0 | 1 | 1 | 0 | 1 | 19 | 0 | 51 |



 ### Après nettoyage :  
  Sucres > 100 g  : 0

 Matières grasses > 100 g  : 0

 Sel > 100 g  : 0

 Protéines > 100 g  : 0

 Énergie > 3 800 kJ  : 0

 Somme des macronutriments > 100 g  : 1275

 Valeurs négatives  : 

 | energy_100g | sugars_100g | carbohydrates_100g | fat_100g | saturated-fat_100g | salt_100g | proteins_100g | fiber_100g | sodium_100g | fruits-vegetables-legumes_100g |
|---|---|---|---|---|---|---|---|---|---|
| 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |





## 4. Manquants
 ### Avant nettoyage :  
  energy-kcal_100g : 379793

 sugars_100g : 387206

 carbohydrates_100g : 386546

 fat_100g : 386778

 saturated-fat_100g : 388388

 salt_100g : 444280

 proteins_100g : 385122

 fiber_100g : 897022

 sodium_100g : 444279

 fruits-vegetables-legumes_100g : 935997


 ### Après nettoyage :  
  energy-kcal_100g : 20849

 sugars_100g : 25988

 carbohydrates_100g : 24574

 fat_100g : 24422

 saturated-fat_100g : 26789

 salt_100g : 39928

 proteins_100g : 23873

 fiber_100g : 267386

 sodium_100g : 39928

 fruits-vegetables-legumes_100g : 232345




## 5. Produits par rayon après nettoyage
 ### Produits par rayon :  
  alcoholic-beverages : 8362

 baby-foods-and-milks : 2451

 beverages : 44288

 cereals-and-potatoes : 54291

 composite-foods : 37435

 fats-and-sauces : 36136

 fish-meat-eggs : 84335

 fruits-and-vegetables : 34419

 milk-and-dairy-products : 57899

 salty-snacks : 28742

 sugary-snacks : 105501

 unknown : 55054




## 6. Colonnes ajoutées et retirées
 ### Colonnes ajoutées :  
 `carbohydrates_100g_manquant`, `category_empty`, `energy-kcal_100g_manquant`, `fat_100g_manquant`, `fiber_100g_manquant`, `food_group`, `main_category`, `proteins_100g_manquant`, `salt_100g_manquant`, `saturated-fat_100g_manquant`, `sodium_100g_manquant`, `sugars_100g_manquant`
 ### Colonnes supprimées :  
 `quantity`


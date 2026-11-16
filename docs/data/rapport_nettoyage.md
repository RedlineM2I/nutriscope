# Rapport de nettoyage NutriScope

- **Date** : 2026-11-16
- **Source** : Export Open Food Facts, périmètre France
- **Crédit** : Données issues d'[Open Food Facts](https://world.openfoodfacts.org) (ODbL pour la base, CC-BY-SA pour les images).

## 1. Volumétrie
 ### Avant nettoyage :  
 1297912
 ### Après nettoyage :  
 549727


## 2. Rapport de nettoyage
 ### Tableau des rapports :  
 | Règle | Lignes avant | Lignes après | Lignes touchées | Détail |
|---|---|---|---|---|
| typer_colonnes | 1297912 | 1297912 | 0 ||
| normalize_texts | 1297912 | 1297912 | 1271126 | noms_vides : 1 ; noms_majuscules : 15842 ; nutriscore_grade_unknown : 750054 ; environmental_score_grade_unknown : 799115 ; categories_tags_normalises : 686514 ; origins_tags_normalises : 403238 ; labels_tags_normalises : 707449 ; additives_tags_normalises : 370729 ; brands_tags_normalises : 729551 ; ingredients_tags_normalises : 371190 ; food_groups_tags_normalises : 1267801 ; marques_fusionnees : 91232 ;|
| Dédupliquer les codes | 1297912 | 1297884 | 28 | sans_code : 0 ; doublons_supprimes : 28 ;|
| normalize_units | 1297884 | 1297884 | 128435 | kcal_derivees : 359 ; kcal_recalculees : 115116 ; sel_derive : 1 ; sodium_derive : 0 ; sodium_recalcule : 13659 ;|
| limit_nutriments | 1297884 | 1297884 | 3623 | energy-kcal_100g_negatifs : 8 ; energy-kcal_100g_au_dessus : 0 ; sugars_100g_negatifs : 0 ; sugars_100g_au_dessus : 46 ; carbohydrates_100g_negatifs : 0 ; carbohydrates_100g_au_dessus : 89 ; fat_100g_negatifs : 1 ; fat_100g_au_dessus : 43 ; saturated-fat_100g_negatifs : 1 ; saturated-fat_100g_au_dessus : 12 ; salt_100g_negatifs : 0 ; salt_100g_au_dessus : 49 ; proteins_100g_negatifs : 1 ; proteins_100g_au_dessus : 34 ; fiber_100g_negatifs : 20 ; fiber_100g_au_dessus : 21 ; sodium_100g_negatifs : 0 ; sodium_100g_au_dessus : 49 ; fruits-vegetables-legumes_100g_negatifs : 47 ; fruits-vegetables-legumes_100g_au_dessus : 2685 ; energy_100g_negatifs : 8 ; energy_100g_au_dessus : 0 ; sucres : 441 ; satures : 242 ;|
| fix_energy | 1297884 | 1297884 | 5646 | nulles_recalculees : 392 ; nulles_invalidees_macros_aberrants : 0 ; >900_recalculees : 138 ; >900_invalidees : 75 ; incoherentes_recalculees : 5041 ;|
| traiter_categories_vides | 1297884 | 640400 | 732824 | categorie_vide : 657484 ; food_group_derive_de_vide : 732824 ; food_group_unknown_total : 732824 ; inclassables_supprimes : 657484 ;|
| strategie_manquants | 640400 | 549727 | 625292 | quantity → drop_column : 1 ; brands_tags → constant : 162274 ; labels_tags → constant : 291637 ; origins_tags → constant : 558892 ; ingredients_tags → constant : 313092 ; additives_tags → constant : 471860 ; energy-kcal_100g → flag : 111520 ; fat_100g → flag : 115076 ; saturated-fat_100g → flag : 117383 ; carbohydrates_100g → flag : 115250 ; sugars_100g → flag : 116646 ; fiber_100g → flag : 357702 ; proteins_100g → flag : 114533 ; salt_100g → flag : 130650 ; sodium_100g → flag : 130650 ; nova_group → mode : 318297 ; dropped_columns : ['quantity'] ; rows_dropped_no_nutrient : 90673 ;|



## 3. Anomalies métier
 ### Avant nettoyage :  
  Sucres > 100 g  : 46

 Matières grasses > 100 g  : 43

 Sel > 100 g  : 49

 Protéines > 100 g  : 34

 Énergie > 3 800 kJ  : 108

 Somme des macronutriments > 100 g  : 2745

 Valeurs négatives  : 

 | energy_100g | sugars_100g | carbohydrates_100g | fat_100g | saturated-fat_100g | salt_100g | proteins_100g | fiber_100g | sodium_100g | fruits-vegetables-legumes_100g |
|---|---|---|---|---|---|---|---|---|---|
| 8 | 0 | 0 | 1 | 1 | 0 | 1 | 20 | 0 | 47 |



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
  energy-kcal_100g : 380456

 sugars_100g : 387856

 carbohydrates_100g : 387214

 fat_100g : 387431

 saturated-fat_100g : 388991

 salt_100g : 445295

 proteins_100g : 385776

 fiber_100g : 898332

 sodium_100g : 445294

 fruits-vegetables-legumes_100g : 938876


 ### Après nettoyage :  
  energy-kcal_100g : 20847

 sugars_100g : 25973

 carbohydrates_100g : 24577

 fat_100g : 24403

 saturated-fat_100g : 26710

 salt_100g : 39977

 proteins_100g : 23860

 fiber_100g : 267029

 sodium_100g : 39977

 fruits-vegetables-legumes_100g : 233020




## 5. Produits par rayon après nettoyage
 ### Produits par rayon :  
  alcoholic-beverages : 8366

 baby-foods-and-milks : 2455

 beverages : 44424

 cereals-and-potatoes : 54145

 composite-foods : 37123

 fats-and-sauces : 36144

 fish-meat-eggs : 84402

 fruits-and-vegetables : 35614

 milk-and-dairy-products : 57994

 salty-snacks : 28186

 sugary-snacks : 105741

 unknown : 55133




## 6. Colonnes ajoutées et retirées
 ### Colonnes ajoutées :  
 `carbohydrates_100g_empty`, `category_empty`, `energy-kcal_100g_empty`, `fat_100g_empty`, `fiber_100g_empty`, `food_group`, `main_category`, `proteins_100g_empty`, `salt_100g_empty`, `saturated-fat_100g_empty`, `sodium_100g_empty`, `sugars_100g_empty`
 ### Colonnes supprimées :  
 `quantity`


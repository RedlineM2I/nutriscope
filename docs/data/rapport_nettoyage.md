# Rapport de nettoyage NutriScope

- **Date** : 2026-11-12
- **Source** : Export Open Food Facts, périmètre France
- **Crédit** : Données issues d'[Open Food Facts](https://world.openfoodfacts.org) (ODbL pour la base, CC-BY-SA pour les images).

## 1. Volumétrie
 ### Avant nettoyage :  
 1296604
 ### Après nettoyage :  
 549484


## 2. Rapport de nettoyage
 ### Tableau des rapports :  
 | Règle | Lignes avant | Lignes après | Lignes touchées | Détail |
|---|---|---|---|---|
| typer_colonnes | 1296604 | 1296604 | 0 ||
| normalize_texts | 1296604 | 1296604 | 1269751 | noms_vides : 1 ; noms_majuscules : 15852 ; nutriscore_grade_unknown : 748916 ; environmental_score_grade_unknown : 797941 ; categories_tags_normalises : 686250 ; origins_tags_normalises : 403054 ; labels_tags_normalises : 705802 ; additives_tags_normalises : 370512 ; brands_tags_normalises : 729241 ; ingredients_tags_normalises : 370973 ; food_groups_tags_normalises : 1266426 ; marques_fusionnees : 91119 ;|
| Dédupliquer les codes | 1296604 | 1296576 | 28 | sans_code : 0 ; doublons_supprimes : 28 ;|
| normalize_units | 1296576 | 1296576 | 128248 | kcal_derivees : 358 ; kcal_recalculees : 115016 ; sel_derive : 1 ; sodium_derive : 0 ; sodium_recalcule : 13567 ;|
| limit_nutriments | 1296576 | 1296576 | 3612 | energy-kcal_100g_negatifs : 8 ; energy-kcal_100g_au_dessus : 0 ; sugars_100g_negatifs : 0 ; sugars_100g_au_dessus : 45 ; carbohydrates_100g_negatifs : 0 ; carbohydrates_100g_au_dessus : 89 ; fat_100g_negatifs : 1 ; fat_100g_au_dessus : 43 ; saturated-fat_100g_negatifs : 1 ; saturated-fat_100g_au_dessus : 12 ; salt_100g_negatifs : 0 ; salt_100g_au_dessus : 49 ; proteins_100g_negatifs : 1 ; proteins_100g_au_dessus : 34 ; fiber_100g_negatifs : 20 ; fiber_100g_au_dessus : 21 ; sodium_100g_negatifs : 0 ; sodium_100g_au_dessus : 49 ; fruits-vegetables-legumes_100g_negatifs : 47 ; fruits-vegetables-legumes_100g_au_dessus : 2672 ; energy_100g_negatifs : 8 ; energy_100g_au_dessus : 0 ; sucres : 443 ; satures : 242 ;|
| fix_energy | 1296576 | 1296576 | 5642 | nulles_recalculees : 391 ; nulles_invalidees_macros_aberrants : 0 ; >900_recalculees : 137 ; >900_invalidees : 74 ; incoherentes_recalculees : 5040 ;|
| traiter_categories_vides | 1296576 | 640131 | 731790 | categorie_vide : 656445 ; food_group_derive_de_vide : 731790 ; food_group_unknown_total : 731790 ; inclassables_supprimes : 656445 ;|
| strategie_manquants | 640131 | 549484 | 625048 | quantity → drop_column : 1 ; brands_tags → constant : 162240 ; labels_tags → constant : 292078 ; origins_tags → constant : 558672 ; ingredients_tags → constant : 313031 ; additives_tags → constant : 471690 ; energy-kcal_100g → flag : 111480 ; fat_100g → flag : 115037 ; saturated-fat_100g → flag : 117350 ; carbohydrates_100g → flag : 115212 ; sugars_100g → flag : 116609 ; fiber_100g → flag : 357676 ; proteins_100g → flag : 114495 ; salt_100g → flag : 130609 ; sodium_100g → flag : 130609 ; nova_group → mode : 318280 ; dropped_columns : ['quantity'] ; rows_dropped_no_nutrient : 90647 ;|



## 3. Anomalies métier
 ### Avant nettoyage :  
  Sucres > 100 g  : 45

 Matières grasses > 100 g  : 43

 Sel > 100 g  : 49

 Protéines > 100 g  : 34

 Énergie > 3 800 kJ  : 107

 Somme des macronutriments > 100 g  : 2739

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
  energy-kcal_100g : 380194

 sugars_100g : 387597

 carbohydrates_100g : 386957

 fat_100g : 387174

 saturated-fat_100g : 388731

 salt_100g : 444922

 proteins_100g : 385520

 fiber_100g : 897699

 sodium_100g : 444921

 fruits-vegetables-legumes_100g : 937765


 ### Après nettoyage :  
  energy-kcal_100g : 20833

 sugars_100g : 25962

 carbohydrates_100g : 24565

 fat_100g : 24390

 saturated-fat_100g : 26703

 salt_100g : 39962

 proteins_100g : 23848

 fiber_100g : 267029

 sodium_100g : 39962

 fruits-vegetables-legumes_100g : 232979




## 5. Produits par rayon après nettoyage
 ### Produits par rayon :  
  alcoholic-beverages : 8357

 baby-foods-and-milks : 2451

 beverages : 44357

 cereals-and-potatoes : 54106

 composite-foods : 37119

 fats-and-sauces : 36134

 fish-meat-eggs : 84393

 fruits-and-vegetables : 35582

 milk-and-dairy-products : 57971

 salty-snacks : 28188

 sugary-snacks : 105689

 unknown : 55137




## 6. Colonnes ajoutées et retirées
 ### Colonnes ajoutées :  
 `carbohydrates_100g_manquant`, `category_empty`, `energy-kcal_100g_manquant`, `fat_100g_manquant`, `fiber_100g_manquant`, `food_group`, `main_category`, `proteins_100g_manquant`, `salt_100g_manquant`, `saturated-fat_100g_manquant`, `sodium_100g_manquant`, `sugars_100g_manquant`
 ### Colonnes supprimées :  
 `quantity`


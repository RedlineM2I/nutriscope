# Rapport de nettoyage NutriScope

- **Date** : 2026-10-28
- **Source** : Export Open Food Facts, périmètre France
- **Crédit** : Données issues d'[Open Food Facts](https://world.openfoodfacts.org) (ODbL pour la base, CC-BY-SA pour les images).

## 1. Volumétrie
 ### Avant nettoyage :  
 1290451
 ### Après nettoyage :  
 546759


## 2. Rapport de nettoyage
 ### Tableau des rapports :  
 | Règle | Lignes avant | Lignes après | Lignes touchées | Détail |
|---|---|---|---|---|
| typer_colonnes | 1290451 | 1290451 | 0 ||
| normalize_texts | 1290451 | 1290451 | 1263468 | noms_vides : 1 ; noms_majuscules : 15833 ; nutriscore_grade_unknown : 744954 ; environmental_score_grade_unknown : 793711 ; categories_tags_normalises : 683320 ; origins_tags_normalises : 400888 ; labels_tags_normalises : 700640 ; additives_tags_normalises : 368325 ; brands_tags_normalises : 726335 ; ingredients_tags_normalises : 368785 ; food_groups_tags_normalises : 1260142 ; marques_fusionnees : 90484 ;|
| Dédupliquer les codes | 1290451 | 1290423 | 28 | sans_code : 0 ; doublons_supprimes : 28 ;|
| normalize_units | 1290423 | 1290423 | 127467 | kcal_derivees : 363 ; kcal_recalculees : 114681 ; sel_derive : 1 ; sodium_derive : 0 ; sodium_recalcule : 13090 ;|
| limit_nutriments | 1290423 | 1290423 | 3064 | sugars_100g_negatifs : 0 ; sugars_100g_au_dessus : 46 ; carbohydrates_100g_negatifs : 0 ; carbohydrates_100g_au_dessus : 85 ; fat_100g_negatifs : 1 ; fat_100g_au_dessus : 45 ; saturated-fat_100g_negatifs : 1 ; saturated-fat_100g_au_dessus : 16 ; salt_100g_negatifs : 0 ; salt_100g_au_dessus : 53 ; proteins_100g_negatifs : 1 ; proteins_100g_au_dessus : 35 ; fiber_100g_negatifs : 19 ; fiber_100g_au_dessus : 21 ; sodium_100g_negatifs : 0 ; sodium_100g_au_dessus : 53 ; fruits-vegetables-legumes_100g_negatifs : 53 ; fruits-vegetables-legumes_100g_au_dessus : 2128 ; sucres : 432 ; satures : 240 ;|
| fix_energy | 1290423 | 1290423 | 5609 | nulles_recalculees : 379 ; nulles_invalidees_macros_aberrants : 0 ; >900_recalculees : 144 ; >900_invalidees : 72 ; incoherentes_recalculees : 5014 ;|
| traiter_categories_vides | 1290423 | 637206 | 728286 | categorie_vide : 653217 ; food_group_derive_de_vide : 728286 ; food_group_unknown_total : 728286 ; inclassables_supprimes : 653217 ;|
| strategie_manquants | 637206 | 546759 | 622296 | quantity → drop_column : 1 ; brands_tags → constant : 161865 ; labels_tags → constant : 291770 ; origins_tags → constant : 556234 ; ingredients_tags → constant : 312257 ; additives_tags → constant : 469957 ; energy-kcal_100g → flag : 111260 ; fat_100g → flag : 114819 ; saturated-fat_100g → flag : 117156 ; carbohydrates_100g → flag : 114969 ; sugars_100g → flag : 116371 ; fiber_100g → flag : 357385 ; proteins_100g → flag : 114270 ; salt_100g → flag : 130263 ; sodium_100g → flag : 130263 ; nova_group → mode : 317560 ; dropped_columns : ['quantity'] ; rows_dropped_no_nutrient : 90447 ;|



## 3. Anomalies métier
 ### Avant nettoyage :  
  Sucres > 100 g  : 46

 Matières grasses > 100 g  : 45

 Sel > 100 g  : 53

 Protéines > 100 g  : 35

 Énergie > 3 800 kJ  : 113

 Somme des macronutriments > 100 g  : 2724

 Valeurs négatives  : 

 | energy_100g | sugars_100g | carbohydrates_100g | fat_100g | saturated-fat_100g | salt_100g | proteins_100g | fiber_100g | sodium_100g | fruits-vegetables-legumes_100g |
|---|---|---|---|---|---|---|---|---|---|
| 8 | 0 | 0 | 1 | 1 | 0 | 1 | 19 | 0 | 53 |



 ### Après nettoyage :  
  Sucres > 100 g  : 0

 Matières grasses > 100 g  : 0

 Sel > 100 g  : 0

 Protéines > 100 g  : 0

 Énergie > 3 800 kJ  : 0

 Somme des macronutriments > 100 g  : 1269

 Valeurs négatives  : 

 | energy_100g | sugars_100g | carbohydrates_100g | fat_100g | saturated-fat_100g | salt_100g | proteins_100g | fiber_100g | sodium_100g | fruits-vegetables-legumes_100g |
|---|---|---|---|---|---|---|---|---|---|
| 7 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |





## 4. Manquants
 ### Avant nettoyage :  
  energy_100g : 387031

 sugars_100g : 386554

 carbohydrates_100g : 385903

 fat_100g : 386139

 saturated-fat_100g : 387724

 salt_100g : 443388

 proteins_100g : 384494

 fiber_100g : 895443

 sodium_100g : 443387

 fruits-vegetables-legumes_100g : 933825


 ### Après nettoyage :  
  energy_100g : 20813

 sugars_100g : 25924

 carbohydrates_100g : 24522

 fat_100g : 24372

 saturated-fat_100g : 26709

 salt_100g : 39816

 proteins_100g : 23823

 fiber_100g : 266938

 sodium_100g : 39816

 fruits-vegetables-legumes_100g : 231887




## 5. Produits par rayon après nettoyage
 ### Produits par rayon :  
  alcoholic-beverages : 8347

 baby-foods-and-milks : 2446

 beverages : 43977

 cereals-and-potatoes : 53914

 composite-foods : 37358

 fats-and-sauces : 35976

 fish-meat-eggs : 84228

 fruits-and-vegetables : 34335

 milk-and-dairy-products : 57679

 salty-snacks : 28660

 sugary-snacks : 104966

 unknown : 54873




## 6. Colonnes ajoutées et retirées
 ### Colonnes ajoutées :  
 `carbohydrates_100g_manquant`, `category_empty`, `energy-kcal_100g_manquant`, `fat_100g_manquant`, `fiber_100g_manquant`, `food_group`, `main_category`, `proteins_100g_manquant`, `salt_100g_manquant`, `saturated-fat_100g_manquant`, `sodium_100g_manquant`, `sugars_100g_manquant`
 ### Colonnes supprimées :  
 `quantity`


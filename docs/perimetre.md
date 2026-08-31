# Périmètre NutriScope

> Livrable du TP 2 (25/08). Les chiffres viennent de `notebooks/tp2-profiling.ipynb`.
> Export Open Food Facts du 29/07/2026.

## 1. D'où on part

L'export mondial contient 4 636 471 produits et 111 colonnes. C'est trop pour nos machines.

On a fait deux coupes :

1. **On ne garde que la France** (`countries_tags` contient `en:france`) → 1 257 105 produits.
2. **On ne garde que 19 colonnes sur 111**.

Le fichier passe de 7,3 Go à 275 Mo. C'est ce qui rend le projet faisable.

## 2. Les colonnes qu'on garde

Les colonnes `STRUCT` ne se lisent pas directement. Il faut aller chercher les champs à
l'intérieur (voir la vue `products` dans le notebook).

### Général

| Colonne | Type | À quoi ça sert |
|---|---|---|
| `code` | VARCHAR | code-barres, c'est la clé du produit |
| `product_name` | STRUCT(lang, text)[] | le nom, en plusieurs langues. On prend le français, sinon l'anglais |
| `quantity` | VARCHAR | la quantité du paquet |
| `nutrition_data_per` | VARCHAR | dit si les valeurs sont pour 100 g ou pour une portion |

### Classification

| Colonne | Type | À quoi ça sert |
|---|---|---|
| `brands_tags` | VARCHAR[] | les marques |
| `categories_tags` | VARCHAR[] | les catégories, c'est ce qui définit les rayons |
| `labels_tags` | VARCHAR[] | bio, sans gluten, etc. |
| `origins_tags` | VARCHAR[] | provenance |

### Ingrédients

| Colonne | Type | À quoi ça sert |
|---|---|---|
| `ingredients_tags` | VARCHAR[] | la liste des ingrédients |
| `additives_tags` | VARCHAR[] | les additifs |

### Nutrition

| Colonne | Type | À quoi ça sert |
|---|---|---|
| `nutriments` | STRUCT(...)[] | toutes les valeurs nutritionnelles. On en sort énergie, sucres, sel, matières grasses, protéines |
| `nutriscore_grade` | VARCHAR | la note A à E |
| `nutriscore_score` | INTEGER | le score chiffré |
| `nutrient_levels_tags` | VARCHAR[] | « trop gras », « trop salé »… pour l'affichage |
| `nova_group` | INTEGER | niveau de transformation du produit |

### Qualité et environnement

| Colonne | Type | À quoi ça sert |
|---|---|---|
| `completeness` | FLOAT | à quel point la fiche est remplie (entre 0 et 1) |
| `environmental_score_grade` | VARCHAR | note environnementale |
| `environmental_score_score` | INTEGER | score environnemental |

### Images

| Colonne | Type | À quoi ça sert |
|---|---|---|
| `images` | STRUCT(...)[] | les photos du produit, pour l'appli et pour le TP 17 |

## 3. Les colonnes qu'on écarte

On enlève 92 colonnes. Elles se rangent en quatre groupes.

**Les infos sur les contributeurs** : `creator`, `editors`, `photographers`, `correctors_tags`,
`informers_tags`, `last_modified_by`. Ce sont des pseudonymes de personnes. On n'en a pas besoin,
et les garder nous obligerait à les gérer dans le registre RGPD.

**Les doublons** : `brands` et `brands_tags` disent la même chose, pareil pour `categories`,
`labels`, `origins`. On garde toujours la version `_tags` : elle est normalisée et plus propre.
Les versions en texte libre sont sales.

**Ce qui est calculé à partir du Nutri-Score** : `compared_to_category`, `nutriscore_data`.
Si on s'en sert pour prédire le Nutri-Score au TP 14, le modèle va tricher. On garde quand même
`nutrient_levels_tags` mais seulement pour l'affichage, jamais comme donnée d'entrée du modèle.

**Ce qui ne sert pas à NutriScope** : `packagings`, `emb_codes`, `stores_tags`,
`purchase_places_tags`, `cities_tags`, `traces_tags`, `minerals_tags`, `vitamins_tags`.
L'emballage et la distribution n'ont rien à voir avec la qualité nutritionnelle. On pourra les
rajouter plus tard si besoin, ça ne change pas l'architecture.

## 4. Les rayons choisis

On a listé les 20 catégories les plus présentes dans les données, puis on en a gardé 7.

On a utilisé trois critères :

1. **Les plus représentées.** Un rayon avec peu de produits ne permet pas de proposer
   d'alternative intéressante.
2. **Les plus globales.** Quand une catégorie et sa sous-catégorie sont toutes les deux dans la
   liste, on prend la catégorie large.
3. **Bien distinctes les unes des autres.** Un dessert et une viande n'ont rien à voir, c'est ce
   qu'on veut. Si deux rayons se recouvrent, on n'en garde qu'un.

| Rayon | Tag | Produits |
|---|---|---|
| Snacks | `en:snacks` | 109 304 |
| Boissons | `en:beverages` | 71 259 |
| Viandes | `en:meats` | 63 842 |
| Fruits et légumes | `en:fruits-and-vegetables-based-foods` | 51 649 |
| Desserts | `en:desserts` | 39 089 |
| Fromages | `en:cheeses` | 33 924 |
| Poissons | `en:fishes` | 17 861 |

Six de ces rayons viennent du top 20. On a ajouté les poissons, plus petits, parce que ça
correspond à un vrai rayon de magasin et que ça complète les viandes.

### Les catégories du top 20 qu'on n'a pas prises

| Écartée | Produits | Pourquoi |
|---|---|---|
| `en:plant-based-foods-and-beverages` | 192 272 | trop large, ça mélange des aliments et des boissons |
| `en:plant-based-foods` | 166 862 | trop large, et ça recouvre déjà nos fruits et légumes |
| `en:sweet-snacks` | 91 745 | c'est une sous-catégorie de `en:snacks`, qu'on a déjà pris |
| `en:meats-and-their-products` | 83 912 | ça recouvre `en:meats`, qu'on a déjà pris |
| `en:dairies` | 60 169 | ça recouvre `en:cheeses`, qu'on a déjà pris |
| `en:fermented-foods`, `en:fermented-milk-products` | 49 056 / 47 562 | ce sont des sous-ensembles des produits laitiers |
| `en:biscuits-and-cakes`, `en:prepared-meats`, `en:spreads`, `en:condiments` | 38 000 à 43 000 | trop précises par rapport aux rayons qu'on a déjà |
| `en:cereals-and-potatoes`, `en:meals`, `en:breakfasts` | 33 000 à 51 000 | bons candidats, mais 7 rayons c'est déjà assez pour commencer |

> ⚠️ **À calculer** : le nombre de produits qui restent une fois tous les filtres appliqués.
> Les 7 rayons se recoupent quand même un peu (un produit peut être dans plusieurs catégories),
> donc on ne peut pas juste additionner la colonne du tableau.

## 5. Les critères pour garder un produit

Un produit entre dans le catalogue s'il remplit tout ça :

| Critère | Pourquoi |
|---|---|
| Il est dans au moins un des 7 rayons | sinon on ne peut pas lui proposer un produit comparable |
| Il a un nom | l'utilisateur doit reconnaître le produit à l'écran |
| Il a au moins une image | pour la fiche produit et pour le TP 17 |
| Il a énergie, sucres, sel, matières grasses et protéines pour 100 g | ce sont les données dont le modèle a besoin |
| `completeness >= 0.5` | pour éliminer les fiches presque vides |

On ne demande **pas** que le Nutri-Score soit renseigné. Les produits qui n'en ont pas sont
justement ceux qu'on veut prédire au TP 14.

## 6. Ce qu'on écarte aussi

| Écarté | Pourquoi |
|---|---|
| Les produits hors France | décision prise au TP 1, on lance sur le marché français |
| Les produits sans catégorie | ils représentent 50,5 % du catalogue France, mais sans catégorie on ne peut pas faire de substitution |

## 7. Ce qu'on a trouvé de sale

### Les marques ne sont pas normalisées

Il y a 90 819 marques différentes, mais le vrai chiffre est plus bas. `xx:carrefour` (11 070) et
`xx:Carrefour` (4 188) sont comptés comme deux marques différentes. Pareil pour `xx:u` / `xx:U`
et `xx:leclerc` / `xx:e-leclerc`.

Donc un `GROUP BY` sur la marque donne un résultat faux.
→ À faire : tout mettre en minuscules, enlever le préfixe `xx:`, et regrouper les alias.

### On ne sait pas à quoi correspondent les valeurs nutritionnelles

`nutrition_data_per` est vide pour 72,1 % des produits. Et parmi eux, **826 832 ont quand même des
valeurs nutritionnelles**. On ne sait donc pas si le chiffre est pour 100 g ou pour une portion.

C'est le problème le plus embêtant du jeu de données. Une valeur de sucre fausse mais visible se
repère facilement. Une valeur juste mais exprimée dans la mauvaise unité, non.

En plus, 4 812 produits sont explicitement « par portion » : on ne peut pas les comparer aux autres
sans les convertir d'abord.

### Il y a des valeurs impossibles

Sur 100 g de produit, on ne peut pas avoir plus de 100 g d'un ingrédient. Pourtant :

| Problème | Nombre de produits |
|---|---|
| Sucres > 100 g | 49 |
| Matières grasses > 100 g | 44 |
| Sel > 100 g | 55 |
| Protéines > 100 g | 34 |
| Valeurs négatives | 9 |
| Énergie > 3 800 kJ | 121 |

Ça reste peu par rapport à 1,2 million de produits. Mais il y a aussi des erreurs moins visibles :
4 029 produits dont la somme des macronutriments dépasse 100 g.

→ À faire : borner les valeurs entre 0 et 100, vérifier la cohérence, et noter quelque part les
lignes qu'on jette (jamais les supprimer en silence).

### Le reste va bien

27 doublons de codes-barres sur 1 257 105 produits, soit 0,002 %. La clé est propre.

## 8. Le Nutri-Score est moins présent qu'il n'y paraît

C'est le piège qu'on a failli manquer. `nutriscore_grade` est rempli à 98 %, mais avec des valeurs
qui ne servent à rien :

| Valeur | Produits | Part |
|---|---|---|
| `unknown` | 724 267 | 57,6 % |
| e | 133 097 | 10,6 % |
| d | 123 443 | 9,8 % |
| c | 97 192 | 7,7 % |
| a | 63 414 | 5,0 % |
| b | 49 615 | 3,9 % |
| `not-applicable` | 41 306 | 3,3 % |
| NULL | 24 771 | 2,0 % |

Le Nutri-Score utilisable (A à E) ne concerne donc que **37,1 %** des produits, pas 98 %.

Les nutriments manquent aussi souvent : 28,7 % pour l'énergie, 29,3 % pour les sucres, 33,7 % pour
le sel.

## 9. Les limites de notre choix

On sait que notre périmètre n'est pas parfait. Les points qu'une autre équipe peut nous reprocher :

- **`en:snacks` reste large.** Il regroupe le sucré et le salé. Il faudra sûrement le découper en
  sous-catégories pour que la substitution ait du sens.
- **On n'a pas regardé la qualité rayon par rayon.** On a choisi sur le volume et sur la
  distinction entre rayons, mais on n'a pas vérifié si le Nutri-Score était bien rempli dans
  chacun.
- **Les rayons peuvent quand même se recouper.** Un même produit peut être dans plusieurs de nos
  7 catégories. Il faudra décider à quel rayon on le rattache.
- **On n'a pas encore le volume final** du catalogue une fois tous les filtres appliqués.
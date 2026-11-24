# Limites du modèle Nutri-Score

Modèle : LightGBM (réglages par défaut), notebook `notebooks/methodes_ensemble.ipynb`.
Évalué une seule fois sur le jeu de test (5 965 produits, colonne `split` figée).

## 1. Ce que le modèle sait faire

Résultats globaux :
- F1 macro : 0.886
- accuracy_test : 0.904 

Erreurs : 574 sur 5965
- À 1 cran : 508 (89%)
- À 2 crans : 55 (10%)
- À 3 crans ou + : 11 (2%)

Les produits sont classés correctement 9 fois sur 10. La plupart des erreurs concernent un écart d'une lettre.


## 2. Les classes difficiles

Classe la moins bien reconnue : B, avec 0.77 de rappel

Elle part vers A et C de manière équivalente (0.11)

Il s'agit de la classe la plus rare du set de données : le modèle en a vu le moins d'exemple, ce qui peut expliquer cette erreur. B est aussi au milieu de l'échelle contrairement à A et E. De plus, B concerne une bande étroite du score, augmentant le risque d'erreur si un écart se produit.

Le risque pour l'utilisateur est qu'il voit un produit surnoté (A au lieu de B) et donc l'afficher meilleur qu'il ne l'est réellement.

## 3. Les rayons non couverts ou mal couverts

| | Nb produits | Précision |
|-|-|-|
|Alcoholic beverages	|10	|0.700|
|Fruits and vegetables	|403	|0.829|
|Cereals and potatoes	|603	|0.839|
|Beverages	|471	|0.858|
|Composite foods	|494	|0.877|

5 produits diagnostiqués :
- **18 oeufs de caille** : C au lieu de B, pourtant avec un score officiel de 2 sur une fiche crédible. Le modèle hésite à 50/50 : limite du modèle.
- **Yaourt à boire** : C au lieu de D, a un score de 8 et apparait donc ne C dans la grille des aliments, mais en D dans la grille des boissons. C'est une règl emétier absente, aucune feature ne dit "boisson"
- **Königs Pilsener** : C pour C, certes, mais c'et une bière et le nutriscore ne s'applique pas aux boissons alcoolisées. Le grade ne devrait pas exister : donnée fausse
- **Easy Oats Original** : C au lieu de B, le kcal / 100g est errroné (92 au lieu des env. 370 habituels), ce qui peut correspondre au produit préparé. Donnée fausse.
- **Pastillas balsamicas menta** : C au lieu de B, 95g de glucides et 0g de sucres, 10g de fruits et légumes. Les données ne corrollent pas avec le type de produit : donnée fausse.

## 4. Quand ne pas faire confiance au modèle

*Une liste de situations où l'application doit s'abstenir. Chaque ligne = une condition vérifiable + la raison.* ⏳

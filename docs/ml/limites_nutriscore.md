# Limites du modèle Nutri-Score

Modèle : LightGBM (réglages par défaut), notebook `notebooks/methodes_ensemble.ipynb`.
Évalué une seule fois sur le jeu de test (5 965 produits, colonne `split` figée).

## 1. Ce que le modèle sait faire

Résultats globaux :
- F1 macro (test) : 0.886
- Accuracy (test) : 0.904 

Erreurs : 574 sur 5965
- À 1 cran : 508 (89%)
- À 2 crans : 55 (10%)
- À 3 crans ou + : 11 (2%)

Les produits sont classés correctement 9 fois sur 10. La plupart des erreurs concernent un écart d'une lettre.


## 2. Les classes difficiles

Classe la moins bien reconnue : B, avec 0.77 de rappel

Elle part vers A et C de manière équivalente (11% vers A et 11% vers C)

Il s'agit de la classe la plus rare du set de données : le modèle en a vu le moins d'exemples ce qui peut expliquer cette erreur. B est aussi au milieu de l'échelle contrairement à A et E. De plus, B concerne une bande étroite du score, augmentant le risque d'erreur si un écart se produit.

Le risque pour l'utilisateur est qu'il voit un produit surnoté (A au lieu de B) et donc l'afficher meilleur qu'il ne l'est réellement.

## 3. Les rayons non couverts ou mal couverts

| | Nb produits | Accuracy |
|-|-|-|
|Alcoholic beverages	|10	|0.700|
|Fruits and vegetables	|403	|0.829|
|Cereals and potatoes	|603	|0.839|
|Beverages	|471	|0.858|
|Composite foods	|494	|0.877|

5 produits diagnostiqués :
- **18 oeufs de caille** `(3460200508992)` : C au lieu de B, pourtant avec un score officiel de 2 sur une fiche crédible. Le modèle hésite à 50/50 : limite du modèle.
- **Yaourt à boire** `(3701002404519)` : C au lieu de D, a un score de 8 et apparait donc en C dans la grille des aliments, mais en D dans la grille des boissons. C'est une règle métier absente, aucune feature ne dit "boisson"
- **Königs Pilsener** `(4100770059874)` : C pour C, certes, mais c'est une bière et le nutriscore ne s'applique pas aux boissons alcoolisées. Le grade ne devrait pas exister : donnée fausse probable
- **Easy Oats Original** `(5054268892285)` : C au lieu de B, le kcal / 100g est étrange (92 au lieu des env. 370 habituels), ce qui peut correspondre au produit préparé. Donnée fausse.
- **Pastillas balsamicas menta** `(8470003501576)` : C au lieu de B, 95g de glucides et 0g de sucres, 10g de fruits et légumes. Les données ne correspondent pas avec le type de produit : donnée fausse.

Pour rappel : Alcoholic beverages est hors-périmètre (en plus de n'avoir que 10 produits), et Beverages fait appel à une grille spécifique

## 4. Quand ne pas faire confiance au modèle

- **Ne pas afficher de lettre** si `pnns_groups_1` vaut *Alcoholic beverages*, car le Nutri-Score ne s'applique pas aux boissons alcoolisées : toute lettre affichée serait fausse par principe. Constat : accuracy de 0.70 sur ce rayon (10 produits au test) ; la Königs Pilsener porte un grade C qui ne devrait pas exister.
- **Afficher un avertissement sur la lettre** si `pnns_groups_1` vaut Beverages, car l'association ne s'effectue pas sur la même grille et peut différer de la réalité. Constat : accuracy de 0.858 sur 471 boissons au test.
Note : cette règle ne couvre pas les boissons rangées dans d'autres rayons (Yaourt à boire, rayon Milk and dairy products, noté D avec la grille boissons alors que le modèle prédit C). Il faudrait une information "boisson / solide" que les données ne portent pas actuellement.
- **Ne pas afficher de lettre** si la probabilité la plus haute renvoyée par `predict_proba` est inférieure à 0.5, car il s'agit d'une hésitation du modèle sur le grade. Constat : 18 oeufs de caille ont un score appartenant à la lettre B mais sont tout de même classé en C (probabilié maximale de 0.47).
Note : le seuil de 0.5 est une proposition et non une mesure, il sera à calibrer en phase 7.
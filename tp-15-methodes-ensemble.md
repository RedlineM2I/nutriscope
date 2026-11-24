# TP 15 — Méthodes d'ensemble

> Projet fil rouge **NutriScope** · jeudi 22/10, avec **Christophe Ringot**
> Après le module 4.4 « Méthodes d'ensemble »
> En équipe de 2-3, dans le dépôt Git de l'équipe
> Données : `data-nutriscope/ml/nutriscope_ml_sample.parquet` — Open Food Facts, © Open Food Facts contributors — ODbL

## Le sujet, tel qu'il figure au Cahier de TP

**Objectif : pousser la performance proprement et savoir dire ce que le modèle rate.**

1. Gradient boosting sur le même problème ; recherche d'hyperparamètres raisonnée (pas de grid search aveugle de trois heures).
2. Comparaison à conditions égales avec les modèles du TP 14 : mêmes plis, mêmes métriques, tableau unique.
3. Analyse des confusions restantes : où le modèle hésite-t-il (B/C ? D/E ?) et pourquoi — retour aux données.
4. Choix du modèle retenu pour l'application, avec ses critères (performance, latence, simplicité de maintenance) tracés dans une ADR (`docs/decisions/`).
5. Rédiger la note honnête « ce que le modèle rate » : limites, biais possibles par rayon, cas où ne pas lui faire confiance.

**À committer** : notebook comparatif + ADR + `docs/ml/limites_nutriscore.md`.

## Mise en situation

Vous avez livré au TP 14 un modèle à 0,859 de F1 macro et un tableau comparatif. La
direction de NutriScope — c'est-à-dire vos formateurs — a lu le tableau et posé deux
questions auxquelles vous n'avez pas encore de réponse écrite.

La première : « peut-on faire mieux ? » Vous savez maintenant que oui, et de combien.
La seconde, plus embarrassante : « sur quoi ce modèle se trompe-t-il, et qu'est-ce qu'on
risque quand il se trompe ? » C'est cette seconde question qui fait la différence entre
un prototype de démonstration et une brique qu'on met en production.

Ce TP produit les deux réponses. La première est une affaire de mesure ; la seconde est
une affaire d'honnêteté, et elle compte autant dans la note.

Un avertissement à lire avant de commencer : **la moitié des points de la grille ne
porte pas sur la performance du modèle**. Une équipe qui livre un modèle à 0,905 sans
ADR ni note de limites sera moins bien notée qu'une équipe à 0,895 qui documente
correctement.

## Prérequis

- **TP 14** : votre `ml_nutriscore.ipynb`, votre `classification_lib.py`, votre tableau
  comparatif. Vous en reprenez la préparation et les plis
- **TP 13** : la colonne `split` figée. Vous ne la recalculez pas
- **Module 4.4**
- L'environnement : xgboost 3.4, lightgbm 4.7, catboost 1.2, optuna 5, shap 0.52

## Étapes, avec leurs points de contrôle

### Étape 1 — Remettre le décor en place (20 min)

Avant d'ajouter quoi que ce soit, **réentraînez les modèles du TP 14** dans ce notebook :
la régression logistique multinomiale et la forêt aléatoire.

Ne recopiez pas les chiffres de la semaine dernière. Réentraînez-les avec la préparation
et les plis que vous allez utiliser aujourd'hui.

> **Point de contrôle 1.** Vos deux modèles du TP 14 retrouvent-ils, à quelques
> millièmes près, les chiffres de votre tableau du TP 14 ? Si l'écart dépasse 0,01,
> quelque chose a changé dans votre préparation : trouvez quoi **avant** de continuer.
> Un tableau comparatif construit sur une préparation qui a bougé ne vaut rien.

### Étape 2 — Le boosting (45 min) — point 1 du sujet

Entraînez au moins trois implémentations de gradient boosting parmi
`HistGradientBoostingClassifier`, XGBoost, LightGBM et CatBoost.

Réglez ensuite **une seule** d'entre elles, avec un budget que vous annoncez dans le
notebook avant de lancer : 30 essais Optuna avec pruning, ou une grille de 12
combinaisons maximum. Notez le temps réel.

> **Point de contrôle 2.** Votre notebook contient-il, écrit **avant** la cellule
> d'optimisation, une phrase du type « budget : 30 essais, 3 plis, MedianPruner,
> environ N minutes attendues » ? C'est ce que « raisonné » veut dire. Une recherche
> dont on découvre le coût après coup n'est pas raisonnée.

> **Point de contrôle 3.** Le gain de votre réglage dépasse-t-il deux fois l'écart-type
> des plis ? Si non — et ce sera probablement le cas — vous devez l'écrire. C'est un
> résultat, pas un échec.

### Étape 3 — Le tableau unique (30 min) — point 2 du sujet

Un seul tableau, avec au minimum : la logistique, la forêt, vos trois boosters, votre
modèle réglé. Pour chaque ligne : F1 macro CV, écart-type, F1 macro test, accuracy test,
temps d'ajustement, temps de prédiction.

Les quatre conditions de l'égalité, à vérifier une par une :

| Condition        | Comment la vérifier                                         |
| ---------------- | ----------------------------------------------------------- |
| même préparation | un seul objet `preparation()`, appelé partout               |
| mêmes plis       | un seul `StratifiedKFold(5, shuffle=True, random_state=42)` |
| mêmes métriques  | un seul dictionnaire de scoring                             |
| même `split`     | la colonne du TP 13, jamais recalculée                      |

> **Point de contrôle 4.** L'écart entre validation croisée et test dépasse-t-il 0,02
> pour l'un de vos modèles ? Si oui, vous avez probablement regardé le test plus d'une
> fois. Relisez l'ordre de vos cellules.

### Étape 4 — Les confusions restantes (40 min) — point 3 du sujet

Sur le test, avec votre meilleur modèle :

- la matrice de confusion 5 × 5 **normalisée par ligne** ;
- les cinq couples (réel, prédit) les plus fréquents parmi les erreurs ;
- la **gravité** des erreurs : combien à un cran d'écart, combien à deux, combien à
  trois ou plus ;
- la performance **par rayon** (`pnns_groups_1`), triée du pire au meilleur.

Puis le retour aux données, qui est le cœur du point 3 : sortez **cinq produits réels**
sur lesquels le modèle hésite entre deux classes voisines (b/c ou d/e), avec leur nom,
leur code-barres, leurs nutriments et leur score officiel. Regardez-les un par un.

> **Point de contrôle 5.** Pour chacun de vos cinq produits, avez-vous tranché entre
> trois diagnostics : **donnée fausse** (la fiche Open Food Facts est erronée),
> **règle métier absente** (le barème applique une grille spéciale que vos features ne
> portent pas), ou **limite du modèle** (le produit est réellement à la frontière) ?
> C'est cette classification qui vaut les points, pas la liste.

Le module 4.4 vous a montré les valeurs SHAP : s'en servir ici pour expliquer une
hésitation est un vrai plus, et prépare la phase 6.

### Étape 5 — L'ADR (30 min) — point 4 du sujet

Un fichier `docs/decisions/ADR-001-modele-nutriscore.md`, une page, cinq sections :
contexte, options considérées (au moins trois, avec leurs chiffres), décision,
conséquences, ce qui déclencherait une révision.

Les six critères vus au module : performance, latence, taille, explicabilité,
maintenance, coût de réentraînement. **Mesurez** la latence et la taille, ne les estimez
pas : `joblib.dump` puis `Path.stat().st_size` pour la taille, le temps de prédiction
divisé par le nombre de produits pour la latence.

> **Point de contrôle 6.** Votre section « Décision » tient-elle en une phrase, au
> présent, sans conditionnel ? « Nous retiendrons probablement LightGBM si les
> performances se confirment » n'est pas une décision, c'est une intention.

> **Point de contrôle 7.** Votre ADR cite-t-elle au moins un chiffre qui **n'est pas**
> le F1 macro ? Si le F1 macro était le seul critère, l'ADR n'aurait pas lieu d'être.

### Étape 6 — La note de limites (25 min) — point 5 du sujet

`docs/ml/limites_nutriscore.md`, quatre rubriques :

1. **Ce que le modèle sait faire** : le chiffre global, mais aussi la part d'erreurs à un
   cran près — c'est ce qui compte pour l'utilisateur ;
2. **Les classes difficiles** : laquelle, avec quel rappel, et vers quoi elle part ;
3. **Les rayons non couverts** : lesquels, avec leur effectif, et pourquoi ;
4. **Quand ne pas faire confiance au modèle** : la liste des situations où l'application
   devrait s'abstenir plutôt que d'annoncer une lettre.

> **Point de contrôle 8.** La rubrique 4 est-elle rédigée de façon **actionnable** ?
> « le modèle a des limites sur certains produits » ne l'est pas. « ne pas afficher de
> prédiction pour les produits du rayon _Alcoholic beverages_ : le barème y applique une
> grille fondée sur le degré d'alcool, absent de nos features » l'est.

## Conseils

- **Commencez par l'étape 1**, même si elle paraît une perte de temps. Une équipe sur
  trois découvre à l'étape 3 que sa préparation a bougé, et doit tout refaire.
- **Ne réglez qu'un seul modèle.** Régler les quatre consomme la séance entière et ne rapporte rien
- **Écrivez la note de limites en même temps que vous mesurez**, pas à la fin. Chaque
  chiffre que vous produisez à l'étape 4 y a sa place ; les rassembler après coup prend
  deux fois plus de temps.
- **Le test se regarde une fois.** Structurez votre notebook pour que la première
  occurrence de `X_test` arrive après toutes vos décisions.
- **CatBoost** : `allow_writing_files=False` et un `train_dir` temporaire, sinon un
  dossier `catboost_info/` se retrouvera dans votre commit.

## Dépannage

**« LightGBM refuse mes noms de colonnes »**
Il n'accepte ni crochets, ni tirets, ni espaces. Les colonnes issues du one-hot en
contiennent. Ajoutez une étape de nettoyage des noms en fin de préparation — la même
pour tous les modèles, pour que les conditions restent égales.

**« CatBoost me renvoie des prédictions de forme (n, 1) et mes métriques sont bizarres »**
C'est un piège connu de l'API CatBoost en multiclasse. NumPy diffuse silencieusement et
vos scores deviennent faux **sans qu'aucune erreur ne s'affiche**. Enveloppez le modèle
pour aplatir : `np.asarray(pred).ravel().astype(int)`.

**« Mon Optuna tourne depuis vingt minutes »**
Vous n'avez pas annoncé de budget, ou vous l'avez fixé trop large. Interrompez, passez à
3 plis pendant la recherche et 5 pour la mesure finale, réduisez `n_estimators` à 1200 au
maximum. Une recherche qui dépasse le quart d'heure sur ce jeu est mal paramétrée.

**« Mon boosting fait moins bien que la forêt du TP 14 »**
Vérifiez trois choses : que votre cible est bien codée en entiers 0-4 et non en lettres,
que `nutriscore_score` n'est pas dans vos features, et que vous comparez bien deux
chiffres issus des mêmes plis. Un boosting sous 0,88 sur ce jeu signale une erreur de
protocole, pas un mauvais réglage.

**« L'écart entre ma validation croisée et mon test est de 0,05 »**
Vous avez regardé le test plus d'une fois, ou vous avez ajusté quelque chose dessus.
Reprenez l'ordre de vos cellules : toute décision prise après avoir vu un chiffre de
test invalide ce chiffre.

## Grille d'évaluation sur 20

| Critère                            | Points | Ce qui est attendu                                                                             |
| ---------------------------------- | ------ | ---------------------------------------------------------------------------------------------- |
| **Boosting entraîné** (point 1)    | 3      | au moins trois implémentations, mêmes conditions, chiffres réels                               |
| **Réglage raisonné** (point 1)     | 3      | budget annoncé avant, espace justifié, temps mesuré, gain confronté à l'écart-type             |
| **Tableau unique** (point 2)       | 4      | modèles du TP 14 réentraînés, quatre conditions d'égalité vérifiables dans le code, CV et test |
| **Confusions analysées** (point 3) | 4      | matrice normalisée, gravité, par rayon, et **cinq produits réels diagnostiqués**               |
| **ADR** (point 4)                  | 3      | cinq sections, trois options chiffrées, décision au présent, critères mesurés                  |
| **Note de limites** (point 5)      | 3      | quatre rubriques, rubrique 4 actionnable                                                       |

**Bonus (jusqu'à +2, sans dépasser 20)** : explication SHAP d'une confusion · comparaison
honnête d'un ensemble (vote ou stacking) avec son verdict de significativité · journal
Optuna versionné · tests pytest sur la bibliothèque du notebook.

**Malus** : un chiffre cité sans être produit par le code du notebook (−2) · le test
manifestement regardé plusieurs fois (−3) · `catboost_info/` ou un modèle de plus de
50 Mo commité (−1) · une conclusion « A est meilleur que B » sur un écart inférieur à un
écart-type (−1).

## Ce que le TP suivant reprendra

Le **TP 16** du 28/10 avec Benjamin Quinet utilisera votre modèle retenu pour prédire le
grade des produits qui n'en ont pas, et alimenter le moteur de substitution. La phase 6
chargera le pipeline persisté dans l'API : sa taille et sa latence, que vous mesurez
aujourd'hui, seront les contraintes à tenir. La phase 7 partira de votre note de limites
pour définir ce qu'il faudra surveiller en production.

Autrement dit : les trois livrables d'aujourd'hui sont lus jusqu'en mars. Écrivez-les
pour quelqu'un qui n'était pas dans la salle.

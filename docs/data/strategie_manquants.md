# Stratégie de valeurs manquantes — NutriScope

> Documente, colonne par colonne, la décision appliquée par `strategie_manquants(df, strategie)`
> (`src/cleaning.py`), en cohérence avec `DEFAULT_STRATEGY` (`strategie.py`).
> Source des taux de manquants : `docs/perimetre.md` §8 et le profiling du TP 2
> (`notebooks/tp2-profiling.ipynb`), sur l'extrait France complet.
> Aucune imputation statistique (médiane, KNN) n'est appliquée ici : cette étape
> prépare le catalogue pour l'usage applicatif (affichage, substitution), pas pour
> l'entraînement ML. L'imputation du pipeline ML se fait après le split train/test
> (TP 14), indépendamment de ce document.
>
> Vocabulaire des décisions en anglais (choix d'équipe assumé), cohérent avec le
> code source déjà en anglais — voir `ValueError` levée par `strategie_manquants`
> sur toute décision hors de cette liste.

## Vocabulaire fermé

| Décision | Effet |
|---|---|
| `keep` | Aucune modification. Le manquant reste tel quel. |
| `flag` | Ajoute `<colonne>_manquant` (booléen). La colonne d'origine n'est pas touchée. |
| `constant:<v>` | Remplace les manquants par la valeur fixe `<v>`. |
| `foodgroup_median` | Remplace par la médiane du rayon du produit (`groupby("rayon")`). |
| `mode` | Remplace par la valeur la plus fréquente de la colonne. |
| `drop_column` | Retire la colonne du DataFrame. |

## Décisions par colonne

### Identité / général

| Colonne | % manquant | Décision | Pourquoi |
|---|---|---|---|
| `code` | ~0 % | `keep` | Clé du produit, normalement toujours renseignée ; un manquant resterait visible tel quel plutôt que masqué, et serait de toute façon écarté par `dedupliquer_codes` en amont dans le pipeline. |
| `product_name` | faible | `keep` | Texte libre : aucune valeur de substitution n'aurait de sens pour l'affichage d'une fiche produit. Un nom manquant doit rester visible comme tel. |
| `quantity` | **~65 %** | `drop_column` | Texte libre non structuré (« 500g », « 1L », formats hétérogènes), et aux deux tiers vide. Ni une constante ni un mode n'apporteraient d'information fiable ; la colonne n'est pas utilisée ailleurs dans le pipeline (score, substitution, affichage de la fiche ne la requièrent pas directement). |
| `nutrition_data_per` | 72,1 % | `keep` | Déjà traitée en amont comme une incertitude structurelle (booléen nullable via `typer_colonnes` : `TRUE` = pour 100 g, `FALSE` = à la portion, `NULL` = inconnu, cf. `schema_nutriscope_optimise.sql`). Remplacer ce `NULL` masquerait justement l'ambiguïté qu'on a choisi de préserver plutôt que de deviner. |

### Classification

| Colonne | % manquant | Décision | Pourquoi |
|---|---|---|---|
| `brands_tags` | faible à modéré | `constant:unknown` | Une marque manquante n'empêche pas d'afficher ou de substituer un produit. `"unknown"` est un libellé d'affichage sûr, cohérent avec le traitement déjà appliqué à `food_group`/`rayon` dans `traiter_categories_vides`. |
| `categories_tags` | — | `keep` | Déjà traitée en amont par `traiter_categories_vides` (dérivation de `main_category`, drapeau `category_empty`, suppression des produits inclassables). Revenir dessus ici dupliquerait une décision déjà prise et documentée ailleurs. |
| `labels_tags` | élevé | `constant:none` | L'absence de label listé est interprétée comme « aucun label déclaré », pas comme une vraie donnée manquante — hypothèse à vérifier mais raisonnable pour un champ qui liste des mentions volontaires (bio, sans gluten...). Documentée ici explicitement, comme demandé en cas d'ambiguïté. |
| `origins_tags` | élevé | `constant:unknown` | Contrairement aux labels, l'absence de provenance n'est pas « pas de provenance » — c'est une vraie inconnue. D'où un libellé différent (`unknown` plutôt que `none`) pour ne pas laisser croire à une absence de provenance réelle. |
| `food_groups_tags` | — | `keep` | Déjà traitée par `traiter_categories_vides` (dérivation de `food_group`, valeur `unknown` pour les rayons vides). Même logique que `categories_tags`. |

### Ingrédients

| Colonne | % manquant | Décision | Pourquoi |
|---|---|---|---|
| `ingredients_tags` | élevé | `constant:unknown` | Une liste d'ingrédients manquante est une vraie absence d'information (contrairement aux labels), pas une absence de valeur par défaut — d'où `unknown` et non `none`. |
| `additives_tags` | élevé | `constant:none` | Hypothèse retenue : l'absence de tag signifie « aucun additif déclaré ». **Point de vigilance documenté** : un produit peut avoir des additifs non déclarés par la marque, ce qui diffère de « zéro additif » — hypothèse à confirmer lors de l'EDA (TP 10) si des écarts apparaissent par rayon. |

### Nutrition — nutriments clés

| Colonne | % manquant (perimetre.md §8) | Décision | Pourquoi |
|---|---|---|---|
| `energy-kcal_100g` | 28,7 % | `flag` | MNAR (Missing Not At Random) probable : l'absence n'est pas aléatoire, elle corrèle avec le type de produit (marques moins transparentes, produits bruts non transformés). Remplacer par une valeur masquerait ce signal, utile pour l'EDA (TP 10) et pour comprendre les biais du futur modèle (TP 14). |
| `sugars_100g` | 29,3 % | `flag` | Même raisonnement. C'est aussi une variable à forte valeur explicative pour le Nutri-Score : imputer statistiquement ici biaiserait toute analyse descriptive faite avant le split ML. |
| `salt_100g` | 33,7 % | `flag` | Idem — un des taux de manquants les plus élevés parmi les nutriments clés. |
| `fat_100g` | à mesurer | `flag` | Même traitement que les autres nutriments clés, par cohérence de la stratégie plutôt que colonne par colonne — l'absence d'un nutriment informe potentiellement sur la catégorie de produit. |
| `saturated-fat_100g` | à mesurer | `flag` | Idem. |
| `carbohydrates_100g` | à mesurer | `flag` | Idem. |
| `fiber_100g` | > 10 %, souvent le plus élevé | `flag` | Cas MNAR le plus classique du jeu de données : les fibres sont rarement déclarées par les marques, indépendamment de la qualité réelle du produit. C'est la colonne nommément citée dans le point de contrôle du TP (`fiber_100g_manquant`) : le drapeau est impératif ici, pas seulement recommandé. |
| `proteins_100g` | à mesurer | `flag` | Idem aux autres nutriments clés. |
| `sodium_100g` | à mesurer | `flag` | Idem. Noter que `sodium_100g` peut déjà avoir été partiellement complété par `normalize_units` (dérivation depuis le sel) avant d'arriver à cette étape — le drapeau ici capture donc le manquant résiduel après cette dérivation, pas le manquant brut d'origine. |

> ⚠️ **À compléter** : les taux de manquants marqués « à mesurer » doivent être repris depuis le profiling du TP 2 avant la clôture du TP 9 — `perimetre.md` ne donne les chiffres exacts que pour l'énergie, les sucres et le sel. Le point de contrôle 3 exige une ligne par colonne à plus de 10 % de manquants.

### Scores

| Colonne | % manquant (perimetre.md §8) | Décision | Pourquoi |
|---|---|---|---|
| `nutriscore_grade` | 62,9 % de valeurs non exploitables (`unknown`/`not-applicable`/NULL) | `keep` | C'est la cible potentielle de la classification du TP 14. Toute imputation ici (même un drapeau à vocation purement descriptive) risquerait d'introduire une confusion entre nettoyage général et préparation spécifique au modèle — l'imputation de cette colonne, si nécessaire, se décide après le split, dans le pipeline ML, jamais ici. |
| `nutriscore_score` | proche de `nutriscore_grade` | `keep` | Même raisonnement : variable numérique liée à la cible, à ne pas toucher avant le split pour éviter toute fuite de données. |
| `nova_group` | modéré | `mode` | Variable ordinale à faible cardinalité (1 à 4) : le mode est une approximation défendable pour un usage d'affichage (contrairement aux nutriments continus, où le mode n'aurait pas de sens). **Point à trancher en équipe** : une absence de classification NOVA peut elle-même être informative (produit non classifié = souvent peu transformé ou fiche incomplète) ; un `flag` serait une alternative tout aussi légitime — `mode` a été retenu ici pour simplifier l'affichage produit, à documenter comme choix assumé plutôt qu'évident. |
| `environmental_score_grade` | élevé, score récent chez Open Food Facts | `keep` | Score encore peu répandu au moment de l'export ; imputer donnerait une fausse impression de couverture. Un manquant visible est plus honnête qu'une valeur par défaut. |
| `environmental_score_score` | élevé | `keep` | Même raisonnement que son pendant catégoriel. |

### Qualité

| Colonne | % manquant | Décision | Pourquoi |
|---|---|---|---|
| `completeness` | ~0 % | `keep` | Sert justement à mesurer la qualité de la fiche produit ; la fausser par une imputation serait contradictoire avec son rôle. |
| `last_modified_t` | ~0 % | `keep` | Horodatage technique sans signification à imputer — un manquant signale une anomalie à investiguer, pas une valeur à deviner. |

### Images

| Colonne | % manquant | Décision | Pourquoi |
|---|---|---|---|
| `images` | — | `keep` | Déjà couverte par le critère de périmètre « au moins une image » (`perimetre.md` §5) : un produit sans image est déjà écarté du catalogue en amont, donc aucune action nécessaire ici. |

## Choix non retenus et pourquoi

- **`foodgroup_median` n'est utilisée pour aucune colonne dans cette version.** Les nutriments clés, qui auraient été les candidats naturels, sont volontairement traités en `flag` plutôt qu'imputés : le point de contrôle du TP est explicite — *« aucune imputation statistique (médiane, KNN) n'est appliquée ici »*. `foodgroup_median` reste disponible dans le vocabulaire pour un usage futur (par exemple si une fiche produit doit afficher une valeur même approximative plutôt qu'un manquant visible), mais ce choix n'a pas été fait à ce stade.
- **Suppression des lignes sans aucun nutriment clé** : appliquée en complément du dictionnaire, après le traitement colonne par colonne. Un produit sans une seule valeur nutritionnelle n'a pas sa place dans un catalogue dont la promesse est justement d'informer sur la qualité nutritionnelle.

## Lien avec le reste du pipeline

- Les drapeaux posés ici (`energy-kcal_100g_manquant`, `fiber_100g_manquant`, etc.) sont repris tels quels par l'EDA du TP 10 pour distinguer un manquant structurel d'une vraie valeur à zéro.
- Les colonnes `keep`-ées sur les scores (`nutriscore_grade`, `nutriscore_score`) sont les seules intentionnellement intouchées avant le split du TP 13 — le `ColumnTransformer` du TP 14 est le bon endroit pour toute imputation statistique les concernant.
# Synthese EDA - NutriScope (TP10)

## Contexte
- Source: echantillon France Open Food Facts (`docs/annexes/data/echantillon_france.csv`)
- Credit: © Open Food Facts contributors - ODbL
- Nettoyage applique (cas degrade TP10):
  - dedoublonnage sur `code` (premiere occurrence)
  - suppression des lignes avec nutriments hors bornes [0, 100] g/100 g
  - suppression des lignes avec energie hors bornes [0, 900] kcal/100 g
  - exclusion du rayon `unknown` pour les comparaisons par rayon

## Messages cles (avec chiffres)
1. Le nettoyage minimal reduit modereement le volume, mais le perimetre reste exploitable.
   - 8 689 lignes brutes -> 8 408 lignes nettoyees -> 6 682 lignes comparees par rayon.

2. Le rayon `unknown` reste non-negligeable et biaise les comparaisons segmentaires s'il est conserve.
   - Part `unknown` apres nettoyage: 20.5%.

3. Les distributions nutrimentaires sont fortement asymetriques.
   - Mediane sucres: 3.2 g/100 g.
   - Mediane sel: 0.5 g/100 g.
   - Mediane energie: 253 kcal/100 g.

4. Le profil Nutri-Score depend du rayon.
   - V de Cramer rayon x grade: 0.34 (signal de liaison modere).

5. Les correlations avec le score Nutri-Score confirment des signaux robustes.
   - Plus fortes correlations Spearman: graisses saturees (0.54), energie (0.53), lipides (0.47), sucres (0.39), sel (0.39).

6. Des redondances fortes existent dans les variables nutriments.
   - `salt_100g` vs `sodium_100g`: rho = 0.99.
   - `fat_100g` vs `saturated-fat_100g`: rho = 0.89.

7. La completude est tres heterogene selon les rayons.
   - `Composite foods`: 89.9% de fiches completes.
   - `Alcoholic beverages`: 14.6% de fiches completes.

8. Les controles metier restent necessaires avant modelisation.
   - Principaux drapeaux: `satures_sup_lipides` (1.57%), `sucres_sup_glucides` (1.49%), `sel_diff_sodium` (1.25%).

## Registre d'hypotheses (extrait)
La logique de test est adaptative: Welch quand les deux groupes ont des distributions assez proches et des variances comparables, Mann-Whitney sinon.
| Hypothese | Methode | Decision |
|---|---|---|
| H1 sucres(DE) > sucres(AB) | Welch ou Mann-Whitney selon la forme des groupes | Voir `docs/data/registre_hypotheses.csv` |
| H2 boissons plus energetiques que cereales | Welch ou Mann-Whitney selon la forme des groupes | Voir `docs/data/registre_hypotheses.csv` |
| H3 sel(DE) > sel(AB) | Welch ou Mann-Whitney selon la forme des groupes | Voir `docs/data/registre_hypotheses.csv` |
| H4 energie boissons > cereales | Welch ou Mann-Whitney selon la forme des groupes | Voir `docs/data/registre_hypotheses.csv` |

## Decisions par TP
- TP9 (nettoyage):
  - Ajouter/maintenir des drapeaux qualite: `energie_nulle_avec_macros`, `sucres_sup_glucides`, `satures_sup_lipides`, `sel_diff_sodium`.
  - Ajouter un drapeau metier pour sel tres eleve (ex: > 15 g/100 g hors condiments).

- TP11 (storytelling marche):
  - Axe narratif principal: contraste inter-rayons sur sucres/sel + heterogeneite de qualite des fiches.

- TP12 (perimetre):
  - Decider explicitement du traitement du rayon `unknown` (hors comparaison vs reintegration controlee).

- TP14 (modelisation):
  - Conserver `pnns_groups_1` dans les features.
  - Retirer une variable par paire redondante (par exemple retirer `sodium_100g`).
  - Privilegier Spearman pour l'exploration initiale et controler les effets par rayon.

## Limites
- Resultats fondes sur un echantillon (pas l'integralite France).
- Tests statistiques utilises ici a visee exploratoire; l'inference stricte sera traitee au module 3.4.
- Certains extremes peuvent etre plausibles metierement (condiments, huiles, sirops) et ne doivent pas etre auto-supprimes sans regle de contexte.

# Conventions d'équipes pour l'utilisation de GIT

## Règles de protection

- `main` : version stable et protégée
- `dev` : branche d'intégration protégée
- `feat/...` : nouvelles fonctionnalités
- `fix/...` : corrections
- `refactor/...` : refactoring
- `test/...` : tests


## Pull-Requests

- Une PR doit être relue par au moins une personne.
- Une PR doit rester courte et concerner un seul sujet.
- Les tests doivent passer avant la fusion.
- Aucun push direct sur `main`.
- Les conflits doivent être résolus par l'auteur de la PR.

## Format des messages de commit

type: description courte

Exemples :
- `feat: ajoute le calcul du score`
- `fix: corrige la gestion des valeurs nulles`
- `docs: complète le guide de contribution`

Les messages de commit sont écrits en français
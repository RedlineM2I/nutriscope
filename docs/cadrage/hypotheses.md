# TP 7 — Hypothèses de coûts et de revenus (NutriScope)

## 1. Idée générale

On chiffre ce que coûterait NutriScope **s'il tournait vraiment en production pendant un an**.
- Hypothèse des coûts sur 12 mois
- Hypothèse des revenus / économies selon le modèle choisi (au TP 6)
- Calcul de ROI sur trois scénarios : pessimiste, central et optimiste

## 2. Hypothèses de coûts sur 12 mois

### 2.1 Hébergement (API + base + front)

Pensée générale : hébergement simple type VPS/PaaS (Scalingo, Railway, OVH, Fly.io) plutôt qu'une grosse infra cloud (en estimant un faible trafic sur la v1).

| Poste | Hypothèse | Coût mensuel | Coût annuel |
|---|---|---|---|
| API + front (conteneurs Docker) | 1 petit VPS ou PaaS (2 vCPU, 4 Go RAM) | ~25 € | ~300 € |
| Base de données | PostgreSQL managé, petit tier | ~20 € | ~240 € |
| Base vectorielle (RAG) | Qdrant/Chroma en instance légère, colocalisée | inclus ou ~10 € | ~0-120 € |
| **Total hébergement** | | **~45-55 €** | **~540-660 €** |

Au volume visé (quelques centaines à quelques milliers d'utilisateurs), un VPS suffit. Le coût n'explose seulement que si le trafic est massif.

### 2.2 Tokens LLM (assistant conversationnel)

Le coût dépend de trois choses : le nombre de conversations par jour, la taille moyenne d'une conversation (tokens en entrée = question + contexte RAG, tokens en sortie = réponse), et le prix du modèle choisi.

Hypothèses : un modèle économique type GPT-4o-mini ou Mistral Small (~0,15 €/million de tokens en entrée, ~0,6 €/million en sortie), une conversation moyenne de 1 500 tokens en entrée (question + extraits RAG cités) et 500 tokens en sortie.

| Scénario | Conversations/jour | Conversations/an | Coût LLM/an |
|---|---|---|---|
| Pessimiste | 50 | ~18 250 | ~10 € |
| Central | 200 | ~73 000 | ~40 € |
| Optimiste | 800 | ~292 000 | ~155 € |

Un modèle "mini" coûte très peu par conversation. Le vrai risque n'est pas le prix unitaire mais un usage massif ou un modèle mal choisi (un modèle "grand" 20 à 50 fois plus cher changerait complètement le calcul). C'est pour ça que l'objectif Q7 de la note de cadrage impose de suivre le coût par conversation en continu et pas seulement de l'estimer une fois.

### 2.3 Stockage images

Les photos produits viennent d'Open Food Facts (déjà hébergées par eux), mais on suppose un cache local ou des miniatures générées pour l'appli.

| Scénario | Volume stocké | Coût/Go/mois | Coût annuel |
|---|---|---|---|
| Pessimiste | 20 Go | 0,02 € | ~5 € |
| Central | 50 Go | 0,02 € | ~12 € |
| Optimiste | 150 Go | 0,02 € | ~36 € |

Le stockage brut est le point le moins cher de tous. Le vrai coût caché serait la bande passante si l'appli sert elle-même des millions d'images, mais en s'appuyant sur les URLs Open Food Facts en v1, ce risque est évité.

### 2.4 Temps homme

C'est le point qui domine tout le reste, de très loin. Une fois le produit déployé (après le TP, en exploitation réelle), il faut du temps pour la maintenance, le support, et les évolutions.

Une hypothèse simple : 3 heures/semaine sur ~44 semaines actives (hors pauses), à un taux chargé de 45 €/heure (ordre de grandeur alternant/junior avec charges) :

- 132 heures/an × 45 €/heure = **~5 940 €/an**

Si on passe à un vrai temps plein pour la maintenance (par exemple en phase de croissance), ce chiffre peut être multiplié par 10 ou plus. C'est le paramètre le plus fragile car il dépend entièrement du niveau d'ambition retenu après la certification.

### 2.5 Total récapitulatif (coûts/an)

| Poste | Pessimiste | Central | Optimiste |
|---|---|---|---|
| Hébergement | 540 € | 600 € | 660 € |
| Tokens LLM | 10 € | 40 € | 155 € |
| Stockage images | 5 € | 12 € | 36 € |
| Temps homme | 5 940 € | 5 940 € | 5 940 € |
| **Total** | **~6 500 €** | **~6 590 €** | **~6 790 €** |

Constat pédagogique clé : sur ces trois scénarios, **le temps homme représente 85 à 90 % du coût total**, pas la technique. C'est cohérent avec l'objectif Q7 de la note de cadrage ("coût par conversation maîtrisé") : le vrai enjeu financier d'un projet comme celui-ci n'est pas l'infrastructure, c'est l'humain qui la fait vivre.

## 3. Hypothèses de revenus ou d'économies selon le modèle du TP 6

Le benchmark TP 6 documente trois familles de modèles observés chez les concurrents. On applique chacun à NutriScope, sur le scénario central (8 000 utilisateurs actifs en fin d'année).

### 3.1 Freemium (comme Yuka)

Gratuit avec un abonnement payant qui débloque des fonctions avancées (recherche sans scan, alertes personnalisées, historique).

- Hypothèse de conversion : 5 % des utilisateurs actifs passent à l'abonnement (taux réaliste pour une v1 sans notoriété, contre les ~part payante de Yuka qui a 10 ans de marché).
- Prix : 3 €/mois (positionnement moins cher que Yuka à 10 €/an... ici plutôt ~36 €/an, à ajuster selon le choix d'équipe).
- Calcul : 8 000 × 5 % × 3 €/mois × 12 mois = **~14 400 €/an**.

C'est le modèle le plus proche de ce que fait le leader du marché, mais il suppose déjà une base d'utilisateurs significative — difficile à atteindre en v1 sans budget d'acquisition, ce que le SWOT du benchmark souligne explicitement.

### 3.2 B2B (comme myLabel ou ScanUp)

L'application reste gratuite pour le grand public ; le revenu vient de la vente de données anonymisées ou d'études aux marques, distributeurs, ou acteurs de la santé (mutuelles, assureurs).

- Hypothèse : 2 clients B2B (par exemple une enseigne de distribution et une mutuelle santé) à 6 000 €/an chacun pour un accès à des tableaux de bord agrégés par rayon.
- Calcul : 2 × 6 000 € = **~12 000 €/an**.

Ce modèle valorise la donnée déjà nettoyée par le pipeline, qui est en réalité l'actif le plus solide du projet. Le risque : il faut des volumes et une réputation de neutralité pour convaincre des clients B2B, ce que ScanUp a par exemple perdu en abandonnant Open Food Facts pour des données "propres" mais fermées.

### 3.3 Marque blanche

On licencie la technologie (score, moteur de substitution, assistant) à un tiers (distributeur, application santé) qui l'intègre sous sa propre marque.

- Hypothèse : 1 licence à 15 000 €/an avec un distributeur régional ou une chaîne de magasins bio, incluant maintenance et évolutions mineures.
- Calcul : **~15 000 €/an**.

C'est le modèle qui rapporte le plus par client mais qui dépend d'un seul contrat — le risque de concentration est élevé (perte du client = perte de tout le revenu), contrairement au freemium qui répartit le risque sur beaucoup de petits utilisateurs.

### 3.4 Synthèse comparative

| Modèle | Revenu estimé/an (scénario central) | Dépendance principale | Risque principal |
|---|---|---|---|
| Freemium | ~14 400 € | Volume d'utilisateurs et notoriété | Taux de conversion faible sans budget marketing |
| B2B | ~12 000 € | Qualité et volume de données | Besoin de crédibilité/neutralité auprès des marques |
| Marque blanche | ~15 000 € | Un ou deux gros contrats | Concentration du risque sur peu de clients |

Avec un coût total d'exploitation autour de 6 500-6 800 €/an (section 2.5), les trois modèles seraient en théorie rentables sur le scénario central — mais c'est un chiffrage pédagogique volontairement optimiste sur l'acquisition de clients/utilisateurs, qui doit être présenté comme tel à l'oral, avec les hypothèses les plus fragiles clairement identifiées (taux de conversion freemium, capacité à signer 2 clients B2B ou 1 client marque blanche en 12 mois).

## 4. Les trois hypothèses les plus fragiles (à assumer à l'oral)

1. **Le taux de conversion freemium à 5 %** : sans budget d'acquisition ni notoriété face à Yuka (88 % de part d'usage), ce chiffre pourrait être surestimé d'un facteur 2 à 5.
2. **Le temps homme à 3h/semaine** : sous-estimé si l'assistant RAG génère du support utilisateur (questions mal répondues, garde-fous à ajuster) ou si l'infrastructure a des incidents, comme le vit Open Food Facts lui-même avec son serveur à 3x sa capacité.
3. **La capacité à signer des contrats B2B/marque blanche en 12 mois** : ce sont des cycles de vente longs (plusieurs mois de négociation), incompatibles avec le calendrier pédagogique du fil rouge ; ce sont des hypothèses de moyen terme, pas de l'année 1.

## Bonus : coûts de conception

Nous ne prenons pas en compte les coups de conception dans le calcul sur un an, mais si l'on doit estimer ces derniers en tenant compte de la taille de notre équipe et en prenant notre TP fil rouge comme référentiel (216 h), on aurait alors :

216 (heures) x 3 (personnes) x 45 (taux horaire chargé) = **29 160 €** de coûts de conception.

Cependant, il s'agit d'une hypothèse volontairement simple, car en réalité nous ne sommes pas mobilisés nécessairement à 100% sur chaque TP. Ce chiffre représente donc un plafond raisonnable et non une mesure fine.
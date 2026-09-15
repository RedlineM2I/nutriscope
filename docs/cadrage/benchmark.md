# Benchmark — TP 6

## 1. Les quatre acteurs

**Yuka** — l'application que tout le monde connaît. 22 millions d'utilisateurs en France, 6 millions de produits, alimentaire + cosmétiques. Elle donne une note unique sur 100, calculée à 60 % sur la nutrition, 30 % sur les additifs, 10 % sur le bio. Si un additif est jugé à risque, la note est plafonnée à 49. Modèle freemium : gratuit avec un abonnement à 10 €/an qui débloque la recherche sans scan, le mode hors ligne et les alertes personnalisées. Aucune publicité, base de données propriétaire, pas d'API.

**myLabel** — l'approche inverse : pas de note unique, mais 21 critères que l'utilisateur choisit lui-même, répartis en santé / planète / société. Deux personnes obtiennent donc deux résultats différents sur le même produit. Elle ajoute un score nutritionnel ajusté à l'âge, au sexe et à la portion réellement mangée. Gratuite, financée en vendant des études aux marques. 800 000 produits, très peu d'utilisateurs.

**Open Food Facts** — ce n'est pas vraiment un concurrent, c'est notre fournisseur de données. Association à but non lucratif, base collaborative sous licence ouverte, 4,5 millions de produits, API publique gratuite. L'application affiche les scores officiels (Nutri-Score, NOVA, score environnemental) mais ne calcule aucune note maison et ne tranche pas à la place de l'utilisateur. Ce sont eux qui ont les meilleurs filtres allergènes et régimes du panel.

**ScanUp** — l'application grand public n'est plus maintenue depuis fin 2023. Le vrai métier de la société est la vente d'études aux industriels. Données fournies directement par les fabricants, donc plus propres, mais catalogue le plus petit du panel et pas d'API.

## 2. Matrice comparative

✅ présent · 🔒 payant · ➖ absent

| | Yuka | myLabel | Open Food Facts | ScanUp | NutriScope |
|---|---|---|---|---|---|
| Note de synthèse unique | ✅ | ➖ | ➖ | ➖ | ✅ |
| Note quand le Nutri-Score est absent | ➖ | ➖ | ➖ | ➖ | ✅ |
| Explication du calcul de la note | ➖ | ➖ | ➖ | ➖ | ✅ |
| Alternatives plus saines | ✅ | ✅ | ✅ | ✅ | ✅ |
| Reconnaissance du produit par photo | ➖ | ➖ | ➖ | ➖ | ✅ |
| Assistant conversationnel | ➖ | ➖ | ➖ | ➖ | ✅ |
| Additifs | ✅ | ✅ | ✅ | ✅ | ➖ |
| Filtres allergènes / régimes | 🔒 | ➖ | ✅ | ➖ | ➖ |
| Personnalisation au profil | ➖ | ✅ | ➖ | ➖ | ➖ |
| Mode hors ligne | 🔒 | ➖ | ➖ | ➖ | ➖ |
| API publique | ➖ | ➖ | ✅ | ➖ | ✅ |
| Gratuit intégralement | ➖ | ✅ | ✅ | ✅ | ✅ |
| Comparaison en temps réel (scan d'affilé) | ➖ | ➖ | ➖ | ➖ | ✅ |

## 3. Points faibles de chacun

**Yuka** : la pondération 60/30/10 n'a aucune justification scientifique publiée, et le concepteur du Nutri-Score la juge arbitraire. Conséquence concrète : la pénalité additifs écrase le signal nutritionnel, si bien que des fruits secs et des biscuits salés peuvent finir avec la même note. Le score est donné sans explication. Les fonctions les plus utiles en magasin (hors ligne, recherche) sont payantes. Écosystème fermé : ni API, ni licence de données.

**myLabel** : très peu d'utilisateurs, catalogue étroit, aucune formule publiée (on ne sait donc pas ce que le score calcule vraiment), et l'application ne fonctionne pas quand le réseau passe mal en magasin — c'est-à-dire au moment exact où on en a besoin. Le modèle économique repose sur les données d'usage revendues aux marques.

**Open Food Facts** : c'est le point à retenir pour nous. Environ un tiers des fiches françaises sont incomplètes ou incohérentes. Nos propres mesures du TP 2 le confirment : le Nutri-Score n'est exploitable que sur 37 % des produits, l'unité des valeurs nutritionnelles est inconnue sur 72 % des fiches, et les marques ne sont pas normalisées. Autre risque : l'association ne finance que 30 % de son infrastructure et son serveur principal tourne à trois fois sa capacité. On dépend d'un service fragile.

**ScanUp** : produit abandonné côté grand public, plus petit catalogue, et un problème de fond — les données viennent des industriels qui sont aussi les clients payants de la société.

## 4. Ce que personne ne fait

C'est là qu'on se place.

1. **Personne n'explique la note.** Yuka donne un chiffre, myLabel des smileys, Open Food Facts des lettres brutes. Aucun ne dit pourquoi.
2. **Personne ne note les produits sans Nutri-Score officiel.** Or c'est 63 % du catalogue. Les quatre applications sont muettes sur ces produits, ou affichent « inconnu ».
3. **Personne ne dit quand la donnée n'est pas fiable.** Un tiers des fiches sont mauvaises et aucune application ne l'indique à l'utilisateur.
4. **Personne ne croise un filtre personnel avec les alternatives proposées** (par exemple : je veux du bio, donc propose-moi un substitut bio).

Le reste (hors ligne gratuit, portion réelle, liste de courses) est aussi mal couvert, mais hors de notre périmètre v1 : ça part au backlog.

## 5. SWOT

| | Favorable | Défavorable |
|---|---|---|
| **Interne** | On note les produits que les autres ignorent. On explique la note et on cite nos sources. API ouverte et données sous licence libre. Périmètre resserré à 7 rayons : on va au fond plutôt que large. | Équipe de 2-3 personnes et 216 heures face à une entreprise de 20 salariés. Catalogue limité à 7 rayons et à la France. Aucune notoriété. Pas de cosmétiques, pas de hors ligne, pas de filtres allergènes en v1. On dépend entièrement d'Open Food Facts. |
| **Externe** | Marché qui double en cinq ans. Le Nutri-Score est connu de 93 % des Français mais cité spontanément par seulement 18 % : il y a tout à expliquer. Son algorithme a changé en 2025 et 30 à 40 % des produits changent de lettre — personne ne l'explique. Les critiques sur l'opacité des notes sont publiques et documentées. | Yuka écrase le marché : 88 % des utilisateurs français. Les industriels attaquent en justice ce genre d'application. Open Food Facts est financièrement fragile. La donnée d'entrée est sale. Le Nutri-Score lui-même est contesté et certains industriels s'en retirent. Sur ce marché, les gens désinstallent vite. |

## 6. Proposition de valeur

En une phrase :

> **NutriScope note tous les produits, y compris les deux tiers qui n'affichent aucun Nutri-Score, et vous montre d'où vient la note. Il propose une expérience de comparaison poussée**

En un paragraphe :

Aujourd'hui, une application de scan vous donne une lettre ou un chiffre, sans dire comment il a été obtenu, et n'a rien à répondre quand le produit n'a pas de Nutri-Score — c'est le cas d'environ deux produits sur trois. NutriScope calcule le score manquant à partir de la composition du produit, explique en clair ce qui le tire vers le bas, indique quand la fiche est trop incomplète pour être sûre, et propose un produit comparable mieux noté dans le même rayon. Nous ne demandons pas de faire confiance à une note : nous montrons sur quoi elle repose.
De plus, nous proposons une option de "multi-scan" pour permettre de comparer de façon plus intuitive et rapide les différents produits. Le temps gagné en magasin permettrait de pouvoir comparer beaucoup plus de produits, et donc améliorer l'expérience utilisateur.

Ce qu'on ne fait pas, et qu'on assume : ni cosmétiques, ni conseil médical, ni suivi de régime personnalisé.

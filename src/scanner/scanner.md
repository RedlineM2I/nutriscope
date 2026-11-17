# **Atelier — Le scanner d'étiquettes (jeudi 12/11, journée)**

En magasin, l'utilisateur de NutriScope ne tape pas le nom d'un produit. Il le **photographie**. Votre assistant doit alors reconnaître le produit et lire ses valeurs nutritionnelles sur l'étiquette. Puis il répond à la question de l'utilisateur. Il ne doit jamais inventer un chiffre.

Aujourd'hui, vous construisez ce scanner sous la forme d'un workflow.

- Un **workflow** est une suite d'étapes. C'est **votre code** qui enchaîne ces étapes et qui choisit le chemin.
- Un **modèle de vision** est un modèle de langage qui accepte aussi des images. Il sert à lire la photo. Il ne décide pas de la suite.

Aucun code n'est fourni pour le scanner. Vous organisez votre code comme vous voulez. Une seule chose est imposée : la forme du résultat. Elle est imposée parce que le scanner servira tel quel à l'assistant gelé au jalon J5, puis à l'application de démonstration.

Toute la journée, vous mesurez. Le lot contient 22 photos réelles. Pour chacune, on connaît les vraies valeurs : c'est la **vérité terrain**. Un script fourni compare votre scanner à cette vérité terrain. Il vous dit si une nouvelle version lit mieux que la précédente, et ce que ce progrès coûte.

## **Ce que vous faites aujourd'hui, en bref**

Vous écrivez une fonction Python, `scanner_etiquette(image)` :

- **elle reçoit** la photo d'un emballage, par exemple `data/photos/10_3608580065340_etiquette.jpg` ;
- **elle rend** un dictionnaire de forme imposée : les valeurs lues sur l'étiquette (`{"kcal": 551, "sucres": 51, …}`), un statut et des alertes (voir « Le seul contrat imposé » plus bas).

Vous l'améliorez palier par palier :

| Palier | Ce que vous ajoutez |
|---|---|
| 0 | Envoyer une photo au modèle de vision et lire sa réponse |
| 1 | En faire `scanner_etiquette` : lire, extraire le JSON, rendre le dictionnaire |
| 2 | Vérifier la lecture (valeurs plausibles, aucun 0 inventé), relancer le modèle si elle est fausse |
| 3 | Retrouver le produit dans le catalogue avec `chercher_produit` (TP 18) et comparer |
| 4 | Lire plusieurs fois, garder la valeur majoritaire, et voir si le gain vaut le coût |
| 5 | Répondre à une question (« C'est sucré ? ») sans aucun chiffre inventé |
| 6 | Brancher le scanner sur votre assistant |

À la fin de chaque palier, vous lancez `python outils/mesurer_scanner.py --version <nom>`. Le script passe votre fonction sur les 22 photos et la compare aux vraies valeurs, par exemple : « 94 % juste, 0 valeur inventée, 10 s par photo ». Le fil de la journée : **améliorer, mesurer, comparer**.

**Cours à mobiliser** (rien n'y est refait ici) :

- `courses/llm/001_llm_fondamentaux.ipynb` : le client unique pour le local et l'API, les clés, le coût d'un appel.
- `courses/llm/002_llm_echelle_embeddings_outils.ipynb`, section 3 : l'appel d'outils et sa boucle.
- `courses/llm/003_prompt_engineering.ipynb` : le prompt structuré (section 1, dont 1.3 « Mesurer une extraction »), les gabarits (section 5), le vote de plusieurs réponses (exercice 3).
- `courses/llm/004_hallucinations_garde_fous_outils.ipynb` : le schéma Pydantic et la règle « aucun nombre qui ne vienne des faits » (section 3) ; la boucle d'outils sécurisée et l'injection par un résultat d'outil (section 4).
- TP 18 (`fil_rouge/tp18_architecture_assistant/README.md`) : votre outil `chercher_produit` et votre architecture.

## **Ce qui est nouveau aujourd'hui**

### Les quatre schémas de workflow

Rappel de vocabulaire. Dans un **workflow**, le chemin est écrit dans votre code. Dans un **agent** (cours 6.4), le modèle choisit lui-même ses étapes. Aujourd'hui, on reste dans le workflow : chaque étape et chaque branchement se lisent dans votre code.

| Schéma | Principe | Le piège |
|---|---|---|
| **Enchaînement** | La sortie d'une étape devient l'entrée de la suivante. Entre les deux, un **contrôle** bloque une sortie invalide. | Enchaîner sans contrôler. L'erreur de la première étape arrive alors jusqu'à la réponse. |
| **Aiguillage** | On classe l'entrée. Puis on l'envoie vers le bon traitement. Une règle écrite en code vaut mieux qu'un modèle quand elle suffit. | Oublier une branche. Que fait-on quand aucun cas ne s'applique ? |
| **Parallélisation et vote** | On fait la **même** tâche plusieurs fois (ou avec plusieurs modèles). Puis on combine les réponses. | Payer trois fois plus sans avoir mesuré le gain de fiabilité. |
| **Rédacteur et relecteur** | Un premier appel produit une réponse. Un second appel (ou du code) la vérifie avec des **critères écrits**. Si elle échoue, on recommence. | Une boucle sans fin. Limitez le nombre de tours et prévoyez une réponse de repli. |

Source : Anthropic, *Building effective agents* (lien en bas de page). L'article nomme ces schémas *prompt chaining*, *routing*, *parallelization* et *evaluator-optimizer*.

### Les points difficiles, expliqués

Chaque encadré dit **pourquoi** le point compte et **ce qu'on attend**. Le comment vous appartient.

#### 1. Envoyer une image à un modèle de vision

**Pourquoi.** Le modèle ne peut pas ouvrir un fichier de votre disque. Ollama ne va pas non plus chercher une image sur Internet. Il faut donc mettre l'image **dans le message**, sous forme de texte.

**Comment, en quatre étapes.** Cette partie est de la plomberie : elle vous est donnée en entier.

1. **Lire les octets du fichier** : `Path("data/photos/….jpg").read_bytes()`.
2. **Les encoder en base64.** Le base64 transforme des octets en texte (lettres, chiffres, `+`, `/`). `base64.b64encode(octets)` rend des octets ; `.decode("ascii")` en fait une chaîne.
3. **Construire une adresse `data:`.** Elle a la forme `data:<type>;base64,<le texte base64>`. Le type est `image/jpeg` pour un `.jpg`, `image/png` pour un `.png`. Cette adresse contient l'image entière : rien n'est téléchargé.
4. **Faire du contenu du message une liste de morceaux**, au lieu d'une chaîne : un morceau `"text"` (la consigne) et un morceau `"image_url"` (l'adresse `data:`). Le reste de l'appel ne change pas : même client `OpenAI` qu'au cours 001, même `chat.completions.create`.

**Exemple complet**, à lancer tel quel depuis la racine de votre dépôt (Ollama démarré, modèle installé) :

```python
import base64
import time
from pathlib import Path

from openai import OpenAI

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

# 1 et 2 : le fichier devient du texte base64
photo = Path("data/photos/10_3608580065340_etiquette.jpg")
image_b64 = base64.b64encode(photo.read_bytes()).decode("ascii")

# 3 : l'adresse data: (le type doit correspondre au format du fichier)
url_image = f"data:image/jpeg;base64,{image_b64}"

# 4 : un message en deux morceaux, texte puis image
messages = [{"role": "user", "content": [
    {"type": "text", "text": "Recopie le tableau nutritionnel de cette photo."},
    {"type": "image_url", "image_url": {"url": url_image}},
]}]

debut = time.perf_counter()
reponse = client.chat.completions.create(
    model="qwen3-vl:8b-instruct", messages=messages, temperature=0
)
print(reponse.choices[0].message.content)
print(f"{time.perf_counter() - debut:.1f} s,",
      reponse.usage.prompt_tokens, "tokens en entrée,",
      reponse.usage.completion_tokens, "en sortie")
```

- **Par API** (secours OpenRouter) : seule la création du client change, avec `base_url="https://openrouter.ai/api/v1"`, la clé lue dans une variable d'environnement, et le nom du modèle (`qwen/qwen3-vl-8b-instruct`). Le message est identique.
- **Plusieurs images** (la face avant et l'étiquette) : ajoutez un second morceau `"image_url"` dans la même liste.
- **Réduire l'image** avant de l'envoyer : ouvrez-la avec Pillow (`Image.open`), réduisez-la avec `img.thumbnail((800, 800))`, enregistrez-la en JPEG dans un `io.BytesIO()`, puis encodez `buffer.getvalue()` en base64 comme à l'étape 2.

**À retenir.**

- Une image coûte des **tokens** d'entrée, souvent plus que tout le texte du prompt. Le dernier `print` de l'exemple les affiche : notez-les.
- Plus l'image a de pixels, plus elle coûte de tokens et plus la **latence** (le temps d'attente de la réponse) augmente. Mais les chiffres sont plus lisibles. Mesurez ce réglage, ne le devinez pas.
- Ce que le modèle écrit en lisant l'image est une **donnée non fiable**. Validez-la, comme les arguments d'un appel d'outil.

#### 2. Les valeurs pour 100 ml

**Pourquoi.** Les boissons donnent leurs valeurs pour 100 ml, pas pour 100 g. Pour passer de l'un à l'autre, il faudrait connaître la densité du liquide. L'étiquette ne la donne pas.

**Quoi.**

- Recopiez les valeurs telles qu'elles sont imprimées. Ne les convertissez pas.
- Indiquez la base dans `"base"` : `"100 ml"` ou `"100 g"`.
- Attention à la colonne voisine. Beaucoup d'étiquettes ont aussi une colonne « par portion » (une canette, un verre). Ce n'est pas celle du contrat.

**Exemple** (canette de soda) :

| Étiquette | Pour 100 ml | Par canette (330 ml) |
|---|---|---|
| Sucres | 10,6 g | 35 g |

Résultat attendu : `"base": "100 ml"` et `"sucres": 10.6`.

#### 3. La mention « < 0,5 g »

**Pourquoi.** L'étiquette ne donne pas la valeur exacte. Elle dit seulement « moins de 0,5 g ». Écrire `0` affirmerait quelque chose que l'étiquette ne dit pas. Écrire `null` perdrait une information que l'étiquette donne.

**Quoi.**

- Mettez le seuil comme valeur : `0.5`.
- Ajoutez la clé du nutriment dans la liste `"inferieur_a"`.
- Au moment de comparer avec le catalogue : une fiche qui indique 0 ou 0,3 g ne contredit pas « < 0,5 g ».

**Exemple** : l'étiquette indique « Sucres < 0,5 g ». Résultat attendu : `"sucres": 0.5` et `"inferieur_a": ["sucres"]`.

#### 4. Aucun chiffre inventé

**Pourquoi.** Une valeur inventée est une valeur présente dans le résultat alors que l'étiquette n'en donne pas. C'est l'erreur la plus grave du scanner. L'utilisateur la croira, car elle a l'air d'avoir été lue. Les modèles en produisent souvent : quand une ligne manque, ils la remplissent par 0, ou par une valeur « typique ».

**Quoi.**

- À la lecture : une valeur absente ou illisible vaut `null`, jamais 0.
- Dans la réponse à l'utilisateur (palier 5) : chaque chiffre cité doit se retrouver dans le résultat du scanner.
- Montrez **comment** vous le garantissez. Un contrôle écrit en code se démontre mieux qu'une phrase dans le prompt.

**Exemple** : l'étiquette du Nutella n'a pas de ligne « fibres ». Le modèle rend `"fibres": 0`. C'est une valeur inventée : il fallait `"fibres": null`. De même, la réponse « Il contient 2 g de fibres » cite un chiffre inventé.

#### 5. L'aiguillage par code-barres

**Pourquoi.** Le code-barres identifie un produit de façon unique. Un nom, lui, peut correspondre à plusieurs fiches (« Prince » ou « Prince goût chocolat au blé complet » ?). Retrouver la fiche du catalogue permet de **recouper** la lecture : comparer l'étiquette à une seconde source.

**Quoi.**

- Si un code-barres est lu, cherchez d'abord avec lui. Sinon, cherchez avec le nom.
- Un code-barres EAN-13 a 13 chiffres. Le dernier est une **clé de contrôle** : il se calcule à partir des 12 autres. Si le modèle lit mal un chiffre, la clé ne correspond presque jamais. Vérifiez donc la clé avant de chercher (voir la page EAN-13 dans les ressources).
- Produit trouvé sans ambiguïté : statut `verifie`. Listez alors les écarts entre l'étiquette et la fiche.
- Produit absent ou ambigu : statut `non_verifie`. Mieux vaut un vrai « non vérifié » qu'un faux « vérifié » rattaché à la mauvaise fiche.

**Exemple** : le modèle lit `3154230810131`. La clé est juste : on cherche, et on trouve la fiche Herta. Il lit `3154230810137` : la clé est fausse, donc ce code est mal lu. On ne cherche pas avec lui, et on le signale dans `alertes`.

#### 6. Le consensus champ par champ (vote)

**Pourquoi.** Une lecture peut se tromper sur un chiffre. Plusieurs lectures se trompent rarement toutes de la même façon. On combine donc plusieurs lectures. On décide **champ par champ**, pas pour la lecture entière : une lecture peut avoir le bon sel et le mauvais sucre.

**Quoi.**

- Pour chaque champ, retenez la valeur donnée par la majorité des lectures.
- Sans majorité, ne choisissez pas au hasard : mettez `null` et une alerte.
- Fixez votre règle d'égalité : `1.1` et `1.10` sont la même valeur.
- Mesurez ce que le vote rapporte (justesse) et ce qu'il coûte (tokens, latence). À température 0, un même modèle rend souvent trois fois la même lecture : vous payez trois fois pour rien.

**Exemple** : trois lectures d'une même photo.

| Champ | Lecture 1 | Lecture 2 | Lecture 3 | Consensus |
|---|---|---|---|---|
| sel | 1.1 | 1.1 | 11 | 1.1 |
| fibres | 3.8 | null | 3.0 | null + alerte « désaccord sur fibres » |

## **Ce que le scanner doit faire**

1. **Lire.** Le modèle de vision lit l'image et rend un JSON : nom, marque, code-barres s'il est visible, ingrédients s'ils sont lisibles, valeurs nutritionnelles pour 100 g ou 100 ml.
2. **Valider.** Votre code vérifie cette lecture avant d'aller plus loin : schéma Pydantic, unités, valeurs plausibles, cohérence de l'étiquette. Aucune valeur inventée (encadré 4).
3. **Aiguiller.** Un code-barres lu ou un nom lisible part vers votre outil `chercher_produit` (TP 18). Si le produit est trouvé, comparez la lecture à sa fiche. Sinon, rendez la lecture avec le statut `non_verifie` (encadré 5).
4. **Voter.** Faites plusieurs lectures (ou utilisez deux modèles). Combinez-les champ par champ (encadré 6). Mesurez le gain et le coût.
5. **Répondre.** Un rédacteur répond à la question de l'utilisateur. Un relecteur vérifie la réponse : aucun chiffre qui ne vienne de l'étiquette ou du catalogue, et une lecture non vérifiée est signalée. La boucle de relecture a un nombre de tours limité.

Enfin, **branchez le scanner sur votre assistant** : une photo devient une entrée comme une autre.

## **Le seul contrat imposé : le résultat du scanner**

Écrivez une fonction `scanner_etiquette(image)`. Elle reçoit le chemin d'un fichier image, ou les octets de l'image. Elle rend ce dictionnaire :

```
{
  "statut": "verifie" | "non_verifie" | "illisible",
  "produit": {"nom": <texte> | null, "marque": <texte> | null, "code_barres": <texte> | null},
  "base": "100 g" | "100 ml" | null,
  "nutriments": {"kj", "kcal", "lipides", "satures", "glucides", "sucres", "fibres", "proteines", "sel"} : nombre ou null,
  "inferieur_a": [<clés de nutriments lues avec « < »>],
  "ingredients": [<texte>, ...] | null,
  "fiche_catalogue": <fiche renvoyée par chercher_produit> | null,
  "ecarts": [{"champ": <clé>, "etiquette": nombre | null, "catalogue": nombre | null}, ...],
  "alertes": [<texte>, ...],
  "mesures": {"appels_modele": <entier>, "latence_s": <nombre>, "tokens_entree": <entier>, "tokens_sortie": <entier>}
}
```

Les règles du contrat :

- `nutriments` contient **ce que dit l'étiquette**, et rien d'autre. Valeurs pour 100 g (ou 100 ml), en grammes. L'énergie en kJ et en kcal. Un point décimal, pas une virgule.
- Une valeur absente ou illisible vaut `null`, **jamais 0**.
- « < 0,5 g » s'écrit `0.5`, et la clé du nutriment va dans `inferieur_a` (encadré 3).
- `verifie` : `chercher_produit` a retrouvé le produit sans ambiguïté. `fiche_catalogue` contient sa fiche. `ecarts` liste les nutriments où l'étiquette et la fiche ne concordent pas.
- `non_verifie` : rien n'a été recoupé. `fiche_catalogue` vaut `null` et `ecarts` est vide.
- `illisible` : aucun produit identifié et aucune valeur lue.
- `alertes` dit en clair ce qui a posé problème : contrôle échoué, désaccord entre lectures, valeur écartée, produit ambigu…
- Le scanner ne lève jamais d'exception. Image illisible, JSON mal formé, modèle injoignable : il rend quand même un résultat conforme, avec ses alertes.
- Vous pouvez ajouter d'autres clés.

## **Tester votre scanner : deux outils fournis**

Le dossier `outils/` contient deux outils prêts à l'emploi. Ils appellent seulement votre fonction `scanner_etiquette`. Ils ne contiennent aucune partie du scanner. Ne les modifiez pas : vos chiffres doivent rester comparables d'une version à l'autre, et d'une équipe à l'autre.

**Installation.** Copiez `outils/` et `data/` à la racine de votre dépôt. Lancez les commandes depuis cette racine. Par défaut, les outils cherchent la fonction `scanner_etiquette` dans `src/scanner.py`.

**Les deux commandes :**

```
pytest outils                                        # 1. le résultat a-t-il la bonne forme ?
python outils/mesurer_scanner.py --version palier1   # 2. le scanner lit-il juste ? (sur les 22 photos)
```

Votre fonction est dans un autre fichier ? Ajoutez la même option aux deux commandes : `--scanner src/mon_fichier.py:scanner_etiquette`.

**1. Les tests du contrat** (`pytest outils`). Ils vérifient la **forme** du résultat, pas la justesse de la lecture : statut permis, 9 nutriments, des nombres ou `null`, `null` quand une valeur manque sur l'étiquette, pas d'exception sur une fausse image, etc. Ils scannent 5 photos et une fausse image.
- Quand : dès que `scanner_etiquette` existe, puis avant chaque commit.
- Un test qui échoue dit quelle règle du contrat n'est pas respectée.

**2. Le script de mesure** (`python outils/mesurer_scanner.py --version <nom>`). Il passe votre scanner sur les 22 photos et compare chaque valeur à la vérité terrain. Chaque valeur tombe dans une case :
- **juste** : la bonne valeur (aux arrondis près), ou `null` quand l'étiquette n'en donne pas ;
- **fausse** : une valeur, mais pas la bonne ;
- **inventée** : une valeur alors que l'étiquette n'en donne pas ;
- **manquée** : `null` alors que l'étiquette donne une valeur.

Il affiche un tableau par photo, un tableau par champ, puis le total : justesse, valeurs inventées, statuts, latence, tokens. Il écrit le détail dans `resultats/<version>.csv` et ajoute une ligne à `resultats/historique.csv`.
- Quand : à la fin de chaque palier, avec un nouveau nom de version (`palier1`, `validation`, `vote3`…). La première version mesurée (`palier1`) est votre **référence** : le tableau de l'historique montre l'écart de chaque version avec elle.
- Pour chronométrer avant de lancer tout le lot : `--ids 02 10 21` (trois photos seulement). Comparez ensuite des versions passées sur les mêmes photos.
- Par API : ajoutez `--prix-entree 0.25 --prix-sortie 0.75` (dollars par million de tokens) pour obtenir le coût par photo.
- Pour revoir le tableau des versions sans relancer : `python outils/mesurer_scanner.py --historique`.

## **Les données**

Tout est dans `data/`, déjà téléchargé (environ 5 Mo). Rien ne dépend du réseau de la salle.

| Fichier | Contenu |
|---|---|
| `photos/NN_<code>_etiquette.jpg` | 22 photos du tableau nutritionnel, prises par les contributeurs d'Open Food Facts (1 200 px au plus) |
| `photos/NN_<code>_face.jpg` | la face avant des mêmes 22 produits |
| `verite_terrain.csv` | les valeurs **relevées à la main sur chaque photo** : nom, marque, base, les 9 nutriments (case vide = absent de l'étiquette), `inferieur_a`, ce qui rend la photo difficile, les écarts connus avec la fiche Open Food Facts |
| `catalogue_off_lot.csv` | les fiches Open Food Facts de ces 22 produits, extraites le 11/11/2026. Ajoutez-les à votre catalogue s'ils n'y sont pas, pour tester l'aiguillage |
| `sources_photos.csv` | l'origine de chaque photo : adresse, contributeur, date, licence |

Le lot n'est pas propre, et c'est voulu. Vous y trouverez :

- des tableaux en plusieurs langues, ou coupés en deux ;
- des valeurs écrites dans une phrase, sans tableau ;
- des photos minuscules ;
- des boissons pour 100 ml ;
- une photo de brique entière, où le tableau est tout petit ;
- une « photo du tableau » qui ne montre aucun tableau ;
- des produits dont la recette a changé depuis la fiche du catalogue.

La vérité terrain sert **à mesurer**, jamais à aider le modèle. Ne la mettez pas dans un prompt. N'utilisez aucun produit du lot comme exemple dans le prompt (*few-shot*, c'est-à-dire des exemples de questions et de réponses donnés au modèle) : prenez une photo à vous.

## **Les modèles (installation avant 9 h, ou dès l'arrivée)**

**En local, avec Ollama 0.12.7 ou plus récent.** Vérifiez avec `ollama --version` : les modèles Qwen3-VL ne tournent pas sur une version plus ancienne.

```
ollama pull qwen3-vl:8b-instruct      # 6,2 Go : le modèle de référence de la journée
ollama pull qwen3-vl:4b-instruct      # 3,3 Go : pour un poste à 8 Go de mémoire ou sans carte graphique
ollama pull qwen2.5vl:7b              # 6,0 Go (ou qwen2.5vl:3b, 3,2 Go) : un second modèle, pour le vote entre modèles
pip install openai pydantic pillow pytest
```

- Écrivez bien `-instruct`. Sans ce suffixe, `qwen3-vl:8b` est la variante qui **réfléchit** longtemps avant de répondre (même piège que `qwen3:4b` au cours 002).
- Premier essai, sans code : `ollama run qwen3-vl:4b-instruct "Recopie le tableau nutritionnel : ./data/photos/10_3608580065340_etiquette.jpg"`.
- Sur un portable sans carte graphique, une lecture peut prendre une minute environ. **Chronométrez une lecture avant de lancer le lot entier.** Travaillez sur quelques photos tant que votre workflow change.

**Secours par API, si les postes ne suffisent pas.** Utilisez OpenRouter, avec le même client et le même format de message. Adresse : `base_url="https://openrouter.ai/api/v1"`. La clé est lue dans une variable d'environnement, comme au cours 001.

- `qwen/qwen3-vl-8b-instruct` : le même modèle qu'en local, servi en ligne. Prix : 0,25 $ par million de tokens en entrée, 0,75 $ en sortie (relevé le 11/11/2026).
- Second modèle pour le vote : `mistralai/mistral-small-3.2-24b-instruct` (0,10 $ / 0,30 $) ou `google/gemini-2.5-flash-lite` (0,10 $ / 0,40 $).

Comptez vos tokens : vous saurez exactement ce que coûte un passage sur le lot.

## **Les paliers**

Les horaires sont des **repères**, pas un barème. Une équipe qui a fini un palier passe au suivant. Une équipe en retard livre un palier qui marche, plutôt que trois à moitié faits.

Chaque palier se termine par **une mesure** (`python outils/mesurer_scanner.py --version <nom>`) et **un commit**.

### Palier 0 — Premier contact (8 h 30 – 9 h 15)

**Objectif :** lire une photo avec un modèle de vision, sans encore écrire de workflow.

**À faire :**
- Installez un modèle (ou configurez le secours par API).
- Lisez une photo « à la main », avec `ollama run` ou un premier appel en Python.
- Notez la latence et les tokens de cette lecture.
- Copiez `outils/` et `data/` à la racine de votre dépôt.

**C'est réussi si :** vous avez une lecture réelle d'une photo, avec sa latence et ses tokens notés.

### Palier 1 — Lire (9 h 15 – 10 h 45)

**Objectif :** une première version de `scanner_etiquette`, mesurée sur tout le lot.

**À faire :**
- Écrivez `scanner_etiquette(image)` : un appel au modèle, un JSON extrait, un résultat au format du contrat.
- Lancez `pytest outils` jusqu'à ce que la forme soit bonne.
- Lancez `python outils/mesurer_scanner.py --version palier1`.

**C'est réussi si :** les tests du contrat passent, et vous connaissez vos premiers chiffres : justesse par champ, valeurs inventées, valeurs manquées, latence, tokens. Cette mesure est **votre référence**.

### Palier 2 — Enchaîner et valider (11 h 00 – 12 h 30)

**Objectif :** ne laisser passer que des lectures valides.

**À faire :**
- Validez la lecture avec un schéma Pydantic.
- Ajoutez des contrôles : unités, valeurs plausibles, cohérence interne de l'étiquette, valeurs inventées (encadré 4).
- Quand une lecture est invalide, relancez le modèle. Limitez le nombre de relances.
- Mesurez la nouvelle version.

**C'est réussi si :** vous savez dire combien d'erreurs vos contrôles attrapent, et combien de bonnes lectures ils rejettent à tort.

### Palier 3 — Aiguiller (13 h 30 – 14 h 30)

**Objectif :** recouper la lecture avec le catalogue quand le produit est identifié.

**À faire :**
- Code-barres lu, sinon nom lu : appelez `chercher_produit` (encadré 5).
- Donnez le bon statut : `verifie`, `non_verifie` ou `illisible`.
- Listez les écarts entre l'étiquette et la fiche.
- Regardez de près deux cas du lot : les produits dont la recette a changé, et la photo sans tableau.

**C'est réussi si :** un produit retrouvé est `verifie` avec ses écarts, un produit absent ou ambigu reste `non_verifie`, et aucune étiquette n'est rattachée à la mauvaise fiche.

### Palier 4 — Paralléliser et voter (14 h 30 – 15 h 45)

**Objectif :** savoir si plusieurs lectures valent leur prix.

**À faire :**
- Faites plusieurs lectures de la même photo, ou utilisez deux modèles.
- Combinez-les champ par champ (encadré 6). Signalez les désaccords.
- Mesurez trois versions : une lecture, trois lectures, deux modèles.

**C'est réussi si :** vous avez un tableau qui met côte à côte, pour ces trois versions, la justesse, les valeurs inventées, la latence et le coût.

### Palier 5 — Rédacteur et relecteur (16 h 00 – 17 h 00)

**Objectif :** répondre à une question sur la photo sans inventer de chiffre.

**À faire :**
- Écrivez un rédacteur qui répond à une question (« C'est sucré ? », « Combien de sel pour 100 g ? »).
- Écrivez un relecteur. Il vérifie que chaque chiffre de la réponse se trouve dans le résultat du scanner, et qu'une lecture non vérifiée est signalée.
- Limitez le nombre de tours. Prévoyez une réponse de repli.

**C'est réussi si :** chaque chiffre de la réponse se retrouve dans le résultat du scanner, et la boucle s'arrête toujours.

### Palier 6 — Brancher (17 h 00 – 17 h 20)

**Objectif :** une photo devient une entrée de votre assistant.

**À faire :**
- Branchez le scanner sur l'assistant : comme un outil, ou comme une étape avant la boucle. Choisissez et justifiez.
- Exécutez la démonstration sur trois photos : une vérifiée, une non vérifiée, la photo sans tableau.

**C'est réussi si :** la démonstration tourne sur un vrai modèle de vision et sa sortie est committée.

### Tour de table (17 h 20 – 17 h 30)

Chaque équipe montre son historique de mesures et dit quelle version elle garde.

Pauses vers 10 h 45 et 15 h 45, déjeuner vers 12 h 30.

**Bonus, pour les équipes rapides** (dans l'ordre de votre choix). Pour chacun, mesurez l'effet.

- Envoyer la face avant **et** l'étiquette : une lecture avec deux images, ou deux lectures ? (`--photo face` passe la face avant au script de mesure.)
- Préparer l'image avant l'envoi (recadrage, taille, contraste).
- Imposer la sortie structurée côté fournisseur (`response_format`, quand il l'accepte), au lieu de demander le JSON dans le prompt.
- Comparer un relecteur LLM (le juge du cours 004, section 3.5) à votre relecteur en code : qu'attrape l'un que l'autre rate ?
- Tirer les allergènes de la liste d'ingrédients, avec la même exigence : rien d'inventé.
- Calculer le coût et la durée de 1 000 scans par jour, en local et par API.
- Ajouter vos propres photos de produits au lot, avec leur vérité terrain relevée par vous.

## **À committer**

| Fichier | Contenu |
|---|---|
| `src/…` (organisation libre) | le scanner, ses contrôles, l'aiguillage, le vote, le rédacteur et le relecteur, avec les tests que vous jugez utiles |
| `outils/` et `data/` | copiés tels quels, sans modification |
| `resultats/historique.csv` et `resultats/<version>.csv` | les sorties du script de mesure, une par version |
| `docs/mesures_scanner.md` | le tableau des versions (repris de l'historique), avec le coût par photo ; puis trois lignes : la version retenue, et pourquoi |
| `notebooks/atelier_scanner_demo.ipynb` (ou un script et sa sortie) | la démonstration **exécutée** : nom du modèle, les trois photos, le résultat du scanner, la question, la réponse |
| `docs/architecture.md` | votre schéma du TP 18, avec le scanner à sa place |
| `docs/journal.md` | trois lignes : fait, problème, suite |

## **Critères de réussite**

1. **Le contrat tient sur les 22 photos.** Un résultat conforme pour chacune, aucune exception, y compris pour la photo sans tableau. Le script de mesure l'affiche (« exceptions 0, hors contrat 0 »).
2. **Aucune valeur inventée** sur le lot, ou chacune attrapée par une alerte. Vous savez les compter et les montrer.
3. **Un progrès mesuré.** Au moins deux versions passées sur le lot entier avec le script de mesure. Un choix argumenté entre fiabilité, coût et latence. Aucun seuil de justesse n'est imposé : il dépend du modèle et du poste. On attend que vous connaissiez **vos** chiffres.
4. **Un aiguillage juste.** Un produit retrouvé est `verifie`, avec ses écarts. Un produit absent ou ambigu reste `non_verifie`. Aucune étiquette n'est rattachée à la mauvaise fiche.
5. **Une réponse fidèle.** Chaque chiffre vient de l'étiquette ou du catalogue. La lecture non vérifiée est annoncée. La relecture a un nombre de tours limité.
6. **Le scanner branché** sur votre assistant, avec une démonstration exécutée sur un vrai modèle de vision.

## **Les règles**

- La clé d'API vient d'une variable d'environnement (fichier `.env` ignoré par Git). Jamais dans le code, jamais dans le dépôt.
- Démonstration et mesures se font sur un vrai modèle. Un faux client dans vos tests unitaires est bienvenu, s'il est nommé comme tel. Un résultat simulé présenté comme réel ne compte pas.
- Tout ce que renvoie le modèle est une donnée non fiable. Analysez et validez le JSON. N'utilisez jamais `eval`.
- Le texte d'une image est une entrée comme une autre. Une étiquette qui contiendrait des instructions ne doit rien déclencher (cours 004, section 4.5).
- Hors sujet aujourd'hui : le RAG et les embeddings (cours 6.3) ; LangChain, LlamaIndex ou CrewAI ; un agent qui choisit lui-même ses étapes (cours 6.4). L'enchaînement est écrit dans votre code.
- Créditez Open Food Facts dans vos livrables. La base est sous licence ODbL, les photos sous licence **CC-BY-SA 3.0** ; leurs auteurs sont dans `data/sources_photos.csv`. Une photo du lot réutilisée dans l'application de démonstration garde son crédit.

## **Ressources**

- Anthropic, *Building effective agents* (les schémas de workflow) : <https://www.anthropic.com/engineering/building-effective-agents>
- Ollama, modèles de vision : <https://docs.ollama.com/capabilities/vision>
- Ollama, compatibilité avec le client OpenAI (images, `response_format`) : <https://docs.ollama.com/api/openai-compatibility>
- OpenRouter, envoyer une image : <https://openrouter.ai/docs/features/multimodal/images>
- OpenAI, images et vision (même format côté client) : <https://platform.openai.com/docs/guides/images-vision>
- Pydantic, validateurs : <https://docs.pydantic.dev/latest/concepts/validators/>
- Le code-barres EAN-13 et sa clé de contrôle : <https://fr.wikipedia.org/wiki/EAN_13>
- API et conditions d'utilisation d'Open Food Facts : <https://openfoodfacts.github.io/openfoodfacts-server/api/>, <https://world.openfoodfacts.org/terms-of-use>

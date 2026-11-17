"""Tests du contrat de scanner_etiquette (README, « Le seul contrat imposé »).

Ces tests vérifient la **forme** du résultat, pas la qualité de la lecture : celle-ci se
mesure avec ``outils/mesurer_scanner.py``. Ils appellent seulement ``scanner_etiquette`` :
l'organisation de votre code vous appartient.

Photos utilisées (5 lectures par le modèle, plus une fausse image) :

- 02 Prince : un tableau ordinaire, envoyé une fois en chemin, une fois en octets ;
- 01 Nutella : pas de ligne « fibres » sur l'étiquette ;
- 03 Skyr : des valeurs « < 0,5 g » ;
- 08 Alpro : une boisson, valeurs pour 100 ml ;
- 21 Madeleines : la « photo du tableau » ne montre aucun tableau.
"""

from __future__ import annotations

import pytest

from atelier_commun import REGLES, charger_verite, photo, regle_dictionnaire

PRODUITS = {v["id"]: v for v in charger_verite()}
PHOTOS = ("02", "01", "03", "08", "21")


def resultat_de(scanner_une_fois, cle: str) -> dict:
    """``cle`` = numéro de photo (envoyée en chemin), ``02-octets`` ou ``fausse-image``."""
    if cle == "fausse-image":
        image = b"ceci n'est pas une image"
    elif cle.endswith("-octets"):
        image = photo(PRODUITS[cle.split("-")[0]]).read_bytes()
    else:
        image = str(photo(PRODUITS[cle]))
    r = scanner_une_fois(cle, image)
    probleme = regle_dictionnaire(r)
    if probleme:
        pytest.fail("résultat incomplet : " + " ; ".join(probleme), pytrace=False)
    return r


IMAGES = (*PHOTOS, "02-octets", "fausse-image")


@pytest.mark.parametrize("image", IMAGES)
def test_rend_un_dictionnaire_complet_sans_exception(scanner_une_fois, image):
    resultat_de(scanner_une_fois, image)


@pytest.mark.parametrize("regle", REGLES)
@pytest.mark.parametrize("image", IMAGES)
def test_regle_du_contrat(scanner_une_fois, image, regle):
    r = resultat_de(scanner_une_fois, image)
    problemes = REGLES[regle](r)
    assert not problemes, " ; ".join(problemes)


def test_fausse_image_rend_illisible_avec_une_alerte(scanner_une_fois):
    r = resultat_de(scanner_une_fois, "fausse-image")
    assert r["statut"] == "illisible", f"statut = {r['statut']!r} pour une image qui n'en est pas une"
    assert all(v is None for v in r["nutriments"].values()), "aucune valeur ne peut être lue sur une fausse image"
    assert r["alertes"], "le résultat doit dire en clair ce qui a cloché (alertes vide)"


def test_absent_vaut_null_jamais_zero_nutella_fibres(scanner_une_fois):
    r = resultat_de(scanner_une_fois, "01")
    assert r["nutriments"]["fibres"] is None, (
        f"fibres = {r['nutriments']['fibres']!r} : l'étiquette du Nutella n'a pas de ligne fibres, il faut null")


def test_photo_sans_tableau_aucune_valeur_madeleines(scanner_une_fois):
    r = resultat_de(scanner_une_fois, "21")
    lues = {k: v for k, v in r["nutriments"].items() if v is not None}
    assert not lues, f"la photo 21 ne montre aucun tableau, mais le scanner rend : {lues}"


def test_chemin_et_octets_donnent_la_meme_forme(scanner_une_fois):
    chemin, octets = resultat_de(scanner_une_fois, "02"), resultat_de(scanner_une_fois, "02-octets")
    assert set(octets) >= set(chemin) - {"mesures"}, "les octets de l'image doivent donner un résultat aussi complet"
    assert octets["statut"] != "illisible" or chemin["statut"] == "illisible", (
        "la photo 02 est lue depuis son chemin mais pas depuis ses octets")

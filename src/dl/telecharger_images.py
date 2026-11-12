"""Télécharge les photos du TP 17 depuis le bucket public Open Food Facts.

    python telecharger_images.py --liste
    python telecharger_images.py --rayons sodas yaourts biscuits cereales pizzas chocolats

Écrit data/images/<rayon>/<code>.jpg (version 400 px). Relancer le script ne retélécharge
que ce qui manque. Photos : CC BY-SA, contributeurs Open Food Facts.
"""
import argparse
import csv
import http.client
import sys
import time
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ICI = Path(__file__).resolve().parent
BUCKET = "https://openfoodfacts-images.s3.eu-west-3.amazonaws.com/"
ESSAIS = 5


def telecharger(ligne, dest):
    chemin = dest / ligne["rayon"] / f"{ligne['code']}.jpg"
    if chemin.exists():
        return "déjà là"
    for essai in range(ESSAIS):
        try:
            with urllib.request.urlopen(BUCKET + ligne["cle_s3"], timeout=60) as reponse:
                contenu = reponse.read()
            break
        except (OSError, http.client.HTTPException):
            time.sleep(2**essai)
    else:
        return "échec"
    temporaire = chemin.with_suffix(".tmp")
    temporaire.write_bytes(contenu)
    temporaire.replace(chemin)
    return "téléchargée"


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--rayons", nargs="+", help="5 à 8 rayons de votre périmètre")
    parser.add_argument("--liste", action="store_true", help="affiche les rayons disponibles")
    parser.add_argument("--dest", type=Path, default=Path("data") / "images")
    parser.add_argument("--manifest", type=Path, default=ICI / "manifest_bucket.csv")
    parser.add_argument("--fils", type=int, default=8, help="téléchargements simultanés")
    args = parser.parse_args()

    with args.manifest.open(encoding="utf-8", newline="") as fichier:
        lignes = list(csv.DictReader(fichier))
    disponibles = Counter(ligne["rayon"] for ligne in lignes)

    if args.liste or not args.rayons:
        for rayon, effectif in sorted(disponibles.items()):
            print(f"{rayon:15s} {effectif}")
        return
    inconnus = set(args.rayons) - set(disponibles)
    if inconnus:
        sys.exit(f"Rayons inconnus : {sorted(inconnus)}. Voir --liste.")

    choisies = [ligne for ligne in lignes if ligne["rayon"] in args.rayons]
    for rayon in args.rayons:
        (args.dest / rayon).mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(args.fils) as pool:
        bilan = Counter(pool.map(lambda ligne: telecharger(ligne, args.dest), choisies))
    print(dict(bilan))
    if bilan["échec"]:
        print("Des photos ont échoué : relancez la même commande.")


if __name__ == "__main__":
    main()

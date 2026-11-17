"""Mesure de votre scanner sur le lot de 22 photos.

Le script appelle votre fonction ``scanner_etiquette(image)`` sur chaque photo d'étiquette,
puis compare son résultat à ``data/verite_terrain.csv``. Il ne contient aucune partie du scanner.

Lancement, depuis la racine de votre dépôt (``outils/`` et ``data/`` côte à côte) :

    python outils/mesurer_scanner.py --version palier1
    python outils/mesurer_scanner.py --version palier1 --ids 02 10 21      # 3 photos seulement
    python outils/mesurer_scanner.py --version vote3 --scanner src/workflow.py:scanner_etiquette
    python outils/mesurer_scanner.py --historique                          # revoir le tableau des versions

Pour chaque photo et chaque nutriment, la valeur rendue tombe dans une case :

- juste    : la bonne valeur (aux arrondis près), ou null quand l'étiquette n'en donne pas ;
- fausse   : une valeur, mais pas la bonne ;
- inventee : une valeur alors que l'étiquette n'en donne pas (le cas le plus grave) ;
- manquee  : null alors que l'étiquette donne une valeur ;
- sans_resultat : le scanner a levé une exception ou n'a pas rendu de dictionnaire.

Sorties, dans ``resultats/`` :

- ``<version>.csv`` : une ligne par photo, avec le détail des erreurs ;
- ``historique.csv`` : une ligne par passage ; la première version est votre référence.
"""

from __future__ import annotations

import argparse
import csv
import statistics
import sys
import time
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any

from atelier_commun import (NUTRIMENTS, SCANNER_PAR_DEFAUT, STATUTS, ScannerIntrouvable, charger_scanner, charger_verite,
                    est_nombre, photo, problemes_contrat)

CASES = ("juste", "fausse", "inventee", "manquee")


# --- Comparaison d'un résultat avec la vérité terrain ---

def meme_valeur(lu: float, vrai: float) -> bool:
    """Tolérance d'arrondi : 0,49 et 0,5 diffèrent, 467 et 467,0 non."""
    return abs(lu - vrai) <= 0.011 + 0.005 * abs(vrai)


def case(lu: Any, vrai: float | None) -> str:
    if vrai is None:
        return "juste" if lu is None else "inventee"
    if lu is None:
        return "manquee"
    return "juste" if est_nombre(lu) and meme_valeur(float(lu), vrai) else "fausse"


def mots(texte: str) -> set[str]:
    sans_accents = unicodedata.normalize("NFKD", texte.lower()).encode("ascii", "ignore").decode()
    return set("".join(c if c.isalnum() else " " for c in sans_accents).split())


def nom_juste(lu: Any, attendu: str) -> bool:
    """Juste si tous les mots de l'un se retrouvent dans l'autre (casse et accents ignorés)."""
    if not isinstance(lu, str) or not lu.strip():
        return False
    a, b = mots(lu), mots(attendu)
    return bool(a) and (a <= b or b <= a)


def comparer(resultat: Any, produit: dict[str, Any], latence: float, erreur: str | None) -> dict[str, Any]:
    ligne: dict[str, Any] = {"id": produit["id"], "produit": produit["nom"]}
    if not erreur and not isinstance(resultat, dict):
        erreur = f"le scanner a rendu {type(resultat).__name__}, pas un dictionnaire"
    r = resultat if isinstance(resultat, dict) else {}
    nutriments = r.get("nutriments") if isinstance(r.get("nutriments"), dict) else {}
    ligne["statut"] = "EXCEPTION" if erreur else str(r.get("statut"))
    details = []
    for k in NUTRIMENTS:
        lu, vrai = nutriments.get(k), produit["nutriments"][k]
        ligne[k] = "sans_resultat" if erreur else case(lu, vrai)   # aucune case « juste » sans résultat
        if ligne[k] != "juste":
            details.append(f"{k}: lu {lu if lu is not None else 'null'} / attendu {vrai if vrai is not None else 'null'}")
    for c in CASES:
        ligne[c] = sum(ligne[k] == c for k in NUTRIMENTS)
    p = r.get("produit") if isinstance(r.get("produit"), dict) else {}
    ligne["nom_juste"] = nom_juste(p.get("nom"), produit["nom"])
    ligne["base_juste"] = r.get("base") == produit["base"]
    lu_inf = set(r.get("inferieur_a") or []) if isinstance(r.get("inferieur_a"), list) else set()
    ligne["inferieur_a_juste"] = lu_inf == set(produit["inferieur_a"])
    mesures = r.get("mesures") if isinstance(r.get("mesures"), dict) else {}
    ligne["latence_s"] = round(latence, 2)
    for k in ("appels_modele", "tokens_entree", "tokens_sortie"):
        ligne[k] = mesures.get(k) if est_nombre(mesures.get(k)) else None
    ligne["alertes"] = len(r.get("alertes") or []) if isinstance(r.get("alertes"), list) else 0
    contrat = [] if erreur else problemes_contrat(resultat)
    ligne["hors_contrat"] = " | ".join(contrat)
    ligne["erreurs"] = erreur or " ; ".join(details)
    return ligne


# --- Affichage ---

def tableau(entetes: list[str], lignes: list[list[Any]]) -> str:
    textes = [[str(c) for c in l] for l in [entetes, *lignes]]
    largeurs = [max(len(l[i]) for l in textes) for i in range(len(entetes))]

    def rangee(l: list[str]) -> str:
        return "  ".join(c.ljust(w) for c, w in zip(l, largeurs)).rstrip()

    return "\n".join([rangee(textes[0]), "  ".join("-" * w for w in largeurs), *map(rangee, textes[1:])])


def pct(n: int, total: int) -> str:
    return f"{100 * n / total:.0f} %" if total else "-"


def moyenne(valeurs: list[Any]) -> float | None:
    v = [x for x in valeurs if x is not None]
    return statistics.mean(v) if v else None


def afficher(lignes: list[dict[str, Any]], resume: dict[str, Any]) -> None:
    print("\nPar photo")
    print(tableau(["id", "produit", "statut", "justes/9", "inventées", "manquées", "fausses", "latence s", "alertes"],
                  [[l["id"], l["produit"][:30], l["statut"], l["juste"], l["inventee"], l["manquee"], l["fausse"],
                    f"{l['latence_s']:.1f}", l["alertes"]] for l in lignes]))
    n = len(lignes)
    print("\nPar champ")
    rangs = [[k, sum(l[k] == "juste" for l in lignes), sum(l[k] == "fausse" for l in lignes),
              sum(l[k] == "inventee" for l in lignes), sum(l[k] == "manquee" for l in lignes),
              pct(sum(l[k] == "juste" for l in lignes), n)] for k in NUTRIMENTS]
    rangs += [[champ, sum(l[cle] for l in lignes), n - sum(l[cle] for l in lignes), "", "", pct(sum(l[cle] for l in lignes), n)]
              for champ, cle in (("nom", "nom_juste"), ("base", "base_juste"), ("inferieur_a", "inferieur_a_juste"))]
    print(tableau(["champ", "justes", "fausses", "inventées", "manquées", "justesse"], rangs))
    print(f"\nGlobal ({n} photos, {n * len(NUTRIMENTS)} valeurs de nutriments)")
    print(f"  justesse des nutriments : {resume['justesse']}")
    print(f"  valeurs inventées : {resume['inventees']}   manquées : {resume['manquees']}   fausses : {resume['fausses']}")
    print(f"  statuts : " + "   ".join(f"{s} {resume[s]}" for s in STATUTS)
          + f"   exceptions {resume['exceptions']}   hors contrat {resume['hors_contrat']}")
    print(f"  latence : moyenne {resume['latence_moy_s']} s, max {resume['latence_max_s']} s")
    print(f"  par photo : {resume['appels_par_photo']} appel(s) au modèle, {resume['tokens_entree_par_photo']} tokens "
          f"en entrée, {resume['tokens_sortie_par_photo']} en sortie, coût {resume['cout_par_photo_usd']} $")
    for l in lignes:
        if l["statut"] == "EXCEPTION":
            print(f"  ✗ photo {l['id']} : exception — {l['erreurs']}")
        elif l["hors_contrat"]:
            print(f"  ✗ photo {l['id']} hors contrat : {l['hors_contrat']}")


def afficher_historique(chemin: Path) -> None:
    if not chemin.exists():
        print(f"Pas encore d'historique ({chemin}).")
        return
    with open(chemin, encoding="utf-8") as f:
        versions = list(csv.DictReader(f))
    if not versions:
        return
    ref = versions[0]
    rangs = []
    for v in versions:
        ecart = float(v["justesse"].rstrip(" %")) - float(ref["justesse"].rstrip(" %"))
        texte_ecart = f"{ecart:+.0f} pts" if v["ids"] == ref["ids"] else "autres photos"
        rangs.append([v["version"], v["photos"], v["justesse"], texte_ecart, v["inventees"],
                      v["manquees"], v["exceptions"], v["latence_moy_s"], v["tokens_entree_par_photo"],
                      v["cout_par_photo_usd"]])
    print(f"\nHistorique des versions (référence : {ref['version']})")
    print(tableau(["version", "photos", "justesse", "écart / réf.", "inventées", "manquées", "exceptions",
                   "latence s", "tokens entrée", "coût $"], rangs))
    print("Comparez seulement des versions passées sur les mêmes photos.")


# --- Programme ---

def resumer(lignes: list[dict[str, Any]], prix_entree: float, prix_sortie: float, version: str,
            ids: list[str] | None) -> dict[str, Any]:
    total = len(lignes) * len(NUTRIMENTS)
    te, ts = moyenne([l["tokens_entree"] for l in lignes]), moyenne([l["tokens_sortie"] for l in lignes])
    cout = (te or 0) * prix_entree / 1e6 + (ts or 0) * prix_sortie / 1e6
    appels = moyenne([l["appels_modele"] for l in lignes])
    return {
        "version": version, "date": datetime.now().strftime("%Y-%m-%d %H:%M"), "photos": len(lignes),
        "ids": " ".join(ids) if ids else "tout",
        "justesse": pct(sum(l["juste"] for l in lignes), total),
        "inventees": sum(l["inventee"] for l in lignes), "manquees": sum(l["manquee"] for l in lignes),
        "fausses": sum(l["fausse"] for l in lignes),
        "noms_justes": sum(l["nom_juste"] for l in lignes), "bases_justes": sum(l["base_juste"] for l in lignes),
        "exceptions": sum(l["statut"] == "EXCEPTION" for l in lignes),
        "hors_contrat": sum(bool(l["hors_contrat"]) for l in lignes),
        **{s: sum(l["statut"] == s for l in lignes) for s in STATUTS},
        "latence_moy_s": round(statistics.mean(l["latence_s"] for l in lignes), 2),
        "latence_max_s": round(max(l["latence_s"] for l in lignes), 2),
        "appels_par_photo": "?" if appels is None else round(appels, 1),
        "tokens_entree_par_photo": "?" if te is None else round(te),
        "tokens_sortie_par_photo": "?" if ts is None else round(ts),
        "cout_par_photo_usd": round(cout, 5),
    }


def ecrire(chemin: Path, lignes: list[dict[str, Any]], ajouter: bool = False) -> None:
    chemin.parent.mkdir(parents=True, exist_ok=True)
    nouveau = not chemin.exists() or not ajouter
    with open(chemin, "a" if ajouter else "w", newline="", encoding="utf-8") as f:
        ecrivain = csv.DictWriter(f, fieldnames=list(lignes[0]))
        if nouveau:
            ecrivain.writeheader()
        ecrivain.writerows(lignes)


def main(argv: list[str] | None = None) -> int:
    # Console Windows en cp1252 (sortie redirigée) : un caractère comme ✗ ne doit pas faire planter.
    for flux in (sys.stdout, sys.stderr):
        if hasattr(flux, "reconfigure"):
            flux.reconfigure(errors="replace")
    p = argparse.ArgumentParser(description="Mesure de scanner_etiquette sur le lot de 22 photos.")
    p.add_argument("--version", help="nom de la version mesurée (palier1, validation, vote3…)")
    p.add_argument("--scanner", default=SCANNER_PAR_DEFAUT,
                   help=f"où est votre fonction : fichier.py:nom_fonction (défaut : {SCANNER_PAR_DEFAUT})")
    p.add_argument("--ids", nargs="+", help="numéros des photos à passer (ex. 02 10 21) ; défaut : les 22")
    p.add_argument("--photo", choices=("etiquette", "face"), default="etiquette", help="photo envoyée (défaut : etiquette)")
    p.add_argument("--prix-entree", type=float, default=0.0, help="$ par million de tokens en entrée (0 en local)")
    p.add_argument("--prix-sortie", type=float, default=0.0, help="$ par million de tokens en sortie (0 en local)")
    p.add_argument("--resultats", default="resultats", help="dossier des sorties (défaut : resultats/)")
    p.add_argument("--historique", action="store_true", help="afficher seulement le tableau des versions")
    a = p.parse_args(argv)
    dossier = Path(a.resultats)
    if a.historique:
        afficher_historique(dossier / "historique.csv")
        return 0
    if not a.version:
        p.error("donnez un nom à la version mesurée : --version palier1")

    try:
        scanner_etiquette = charger_scanner(a.scanner)
    except ScannerIntrouvable as e:
        print(f"✗ Scanner introuvable : {e}", file=sys.stderr)
        return 2

    produits = charger_verite()
    if a.ids:
        inconnus = set(a.ids) - {v["id"] for v in produits}
        if inconnus:
            p.error(f"photos inconnues : {' '.join(sorted(inconnus))} (numéros de 01 à 22)")
        produits = [v for v in produits if v["id"] in a.ids]

    lignes = []
    for v in produits:
        print(f"photo {v['id']} ({v['nom'][:40]})…", end=" ", flush=True)
        debut, erreur, resultat = time.perf_counter(), None, None
        try:
            resultat = scanner_etiquette(str(photo(v, a.photo)))
        except Exception as e:  # le contrat l'interdit : on le compte, on continue
            erreur = f"{type(e).__name__}: {e}"
        latence = time.perf_counter() - debut
        lignes.append(comparer(resultat, v, latence, erreur))
        print(f"{lignes[-1]['statut']}, {lignes[-1]['juste']}/9 justes, {latence:.1f} s")

    resume = resumer(lignes, a.prix_entree, a.prix_sortie, a.version, a.ids)
    afficher(lignes, resume)
    nom_fichier = "".join(c if c.isalnum() or c in "-_" else "_" for c in a.version)
    ecrire(dossier / f"{nom_fichier}.csv", lignes)
    ecrire(dossier / "historique.csv", [resume], ajouter=True)
    afficher_historique(dossier / "historique.csv")
    print(f"\nDétail par photo : {dossier / (nom_fichier + '.csv')}")
    return 1 if resume["exceptions"] or resume["hors_contrat"] else 0


if __name__ == "__main__":
    sys.exit(main())

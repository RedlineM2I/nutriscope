"""Outils de test de l'atelier « scanner d'étiquettes » : ce que partagent la mesure et les tests.

Ce fichier ne contient aucune partie du scanner. Il sait seulement :

- retrouver votre fonction ``scanner_etiquette`` (option ``--scanner``) ;
- lire la vérité terrain du lot (``data/verite_terrain.csv``) ;
- vérifier la forme du résultat (le contrat du README).

Vous n'avez pas à le modifier.
"""

from __future__ import annotations

import csv
import importlib
import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Any, Callable

# Où chercher la fonction si on ne précise rien : src/scanner.py, fonction scanner_etiquette.
SCANNER_PAR_DEFAUT = "src/scanner/scanner.py:scan_label"

# Dossier data/ placé à côté du dossier outils/.
DATA = Path(__file__).resolve().parent.parent / "data"

NUTRIMENTS = ("kj", "kcal", "lipides", "satures", "glucides", "sucres", "fibres", "proteines", "sel")
STATUTS = ("verifie", "non_verifie", "illisible")
BASES = ("100 g", "100 ml", None)
MESURES = ("appels_modele", "latence_s", "tokens_entree", "tokens_sortie")


class ScannerIntrouvable(Exception):
    """La fonction indiquée par --scanner n'a pas pu être chargée."""


def charger_scanner(indication: str = SCANNER_PAR_DEFAUT) -> Callable[[Any], dict[str, Any]]:
    """Charge ``fichier.py:fonction`` (ou ``paquet.module:fonction``), depuis le dossier courant."""
    if ":" not in indication:
        raise ScannerIntrouvable(f"« {indication} » : écrivez fichier.py:nom_fonction, par exemple {SCANNER_PAR_DEFAUT}")
    chemin, nom_fonction = indication.rsplit(":", 1)
    fichier = Path(chemin if chemin.endswith(".py") else chemin.replace(".", "/") + ".py")
    fichier = (Path.cwd() / fichier).resolve() if not fichier.is_absolute() else fichier
    # Le dossier courant (import « from src.x import … ») et le dossier du fichier
    # (import d'un module voisin, « from controles import … ») sont tous deux cherchés.
    if not fichier.is_file():
        raise ScannerIntrouvable(
            f"fichier introuvable : {chemin} (cherché depuis {Path.cwd()}).\n"
            f"Lancez la commande depuis la racine de votre dépôt, ou indiquez où est votre fonction :\n"
            f"  --scanner chemin/vers/fichier.py:scanner_etiquette")
    for dossier in (fichier.parent, Path.cwd()):
        if str(dossier) not in sys.path:
            sys.path.insert(0, str(dossier))
    try:
        relatif = fichier.relative_to(Path.cwd().resolve()).with_suffix("")
    except ValueError:
        relatif = None
    try:
        if relatif is not None and all(p.isidentifier() for p in relatif.parts):
            # Import par nom de module : les imports relatifs (« from .controles import … ») marchent.
            mod = importlib.import_module(".".join(relatif.parts))
        else:
            spec = importlib.util.spec_from_file_location(fichier.stem, fichier)
            mod = importlib.util.module_from_spec(spec)
            sys.modules[fichier.stem] = mod
            spec.loader.exec_module(mod)
    except Exception as e:
        raise ScannerIntrouvable(f"{chemin} existe, mais son import échoue : {type(e).__name__}: {e}") from None
    fonction = getattr(mod, nom_fonction, None)
    if not callable(fonction):
        raise ScannerIntrouvable(f"{chemin} ne définit pas de fonction {nom_fonction}(image)")
    return fonction


def charger_verite(chemin: Path = DATA / "verite_terrain.csv") -> list[dict[str, Any]]:
    """Les 22 produits du lot. Une case vide = valeur absente de l'étiquette (None)."""
    with open(chemin, encoding="utf-8") as f:
        lignes = list(csv.DictReader(f))
    for ligne in lignes:
        ligne["nutriments"] = {k: float(ligne[k]) if ligne[k] else None for k in NUTRIMENTS}
        ligne["inferieur_a"] = [k for k in ligne["inferieur_a"].split(";") if k]
        ligne["base"] = ligne["base"] or None
    return lignes


def photo(produit: dict[str, Any], face: str = "etiquette") -> Path:
    return DATA / "photos" / f"{produit['id']}_{produit['code']}_{face}.jpg"


def est_nombre(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


# --- Le contrat, règle par règle. Chaque règle rend la liste de ses problèmes (vide si tout va bien). ---

def _cles(r: dict, cles: tuple) -> list[str]:
    manquantes = [k for k in cles if k not in r]
    return [f"clé manquante : {k}" for k in manquantes]


def regle_dictionnaire(r: Any) -> list[str]:
    if not isinstance(r, dict):
        return [f"le scanner doit rendre un dictionnaire, il a rendu : {type(r).__name__}"]
    return _cles(r, ("statut", "produit", "base", "nutriments", "inferieur_a", "ingredients",
                     "fiche_catalogue", "ecarts", "alertes", "mesures"))


def regle_statut(r: dict) -> list[str]:
    if r.get("statut") not in STATUTS:
        return [f"statut = {r.get('statut')!r} ; valeurs permises : {', '.join(STATUTS)}"]
    return []


def regle_produit(r: dict) -> list[str]:
    p = r.get("produit")
    if not isinstance(p, dict):
        return ["produit doit être un dictionnaire {nom, marque, code_barres}"]
    pb = _cles(p, ("nom", "marque", "code_barres"))
    pb += [f"produit.{k} doit être un texte ou null, pas {type(p[k]).__name__}"
           for k in ("nom", "marque", "code_barres") if k in p and p[k] is not None and not isinstance(p[k], str)]
    return pb


def regle_base(r: dict) -> list[str]:
    if r.get("base") not in BASES:
        return [f"base = {r.get('base')!r} ; valeurs permises : \"100 g\", \"100 ml\" ou null"]
    return []


def regle_nutriments(r: dict) -> list[str]:
    n = r.get("nutriments")
    if not isinstance(n, dict):
        return ["nutriments doit être un dictionnaire"]
    pb = [f"nutriment manquant : {k}" for k in NUTRIMENTS if k not in n]
    pb += [f"nutriment en trop : {k} (les 9 clés du contrat, pas d'autres)" for k in n if k not in NUTRIMENTS]
    for k, v in n.items():
        if v is not None and not est_nombre(v):
            pb.append(f"nutriments.{k} = {v!r} : un nombre (point décimal) ou null, pas un texte")
        elif v is not None and v < 0:
            pb.append(f"nutriments.{k} = {v} : une valeur négative est impossible")
    return pb


def regle_inferieur_a(r: dict) -> list[str]:
    ia, n = r.get("inferieur_a"), r.get("nutriments") or {}
    if not isinstance(ia, list):
        return ["inferieur_a doit être une liste (vide s'il n'y a aucun « < »)"]
    return [f"inferieur_a contient {k!r} : il faut une clé de nutriment dont la valeur n'est pas null"
            for k in ia if k not in NUTRIMENTS or n.get(k) is None]


def regle_ingredients(r: dict) -> list[str]:
    ing = r.get("ingredients")
    if ing is None or (isinstance(ing, list) and all(isinstance(i, str) for i in ing)):
        return []
    return ["ingredients doit être une liste de textes, ou null"]


def regle_statut_fiche(r: dict) -> list[str]:
    statut, fiche, ecarts = r.get("statut"), r.get("fiche_catalogue"), r.get("ecarts")
    pb = []
    if statut == "verifie" and fiche is None:
        pb.append("statut verifie mais fiche_catalogue est null")
    if statut != "verifie" and fiche is not None:
        pb.append(f"statut {statut} mais fiche_catalogue est remplie : seul « verifie » a une fiche")
    if statut != "verifie" and ecarts:
        pb.append(f"statut {statut} mais ecarts n'est pas vide : sans fiche, pas d'écart")
    return pb


def regle_illisible(r: dict) -> list[str]:
    if r.get("statut") != "illisible":
        return []
    pb = []
    if any(v is not None for v in (r.get("nutriments") or {}).values()):
        pb.append("statut illisible mais des nutriments sont lus : ce serait non_verifie")
    if any(v is not None for v in (r.get("produit") or {}).values()):
        pb.append("statut illisible mais le produit est identifié : ce serait non_verifie")
    return pb


def regle_ecarts(r: dict) -> list[str]:
    ecarts = r.get("ecarts")
    if not isinstance(ecarts, list):
        return ["ecarts doit être une liste"]
    pb = []
    for e in ecarts:
        if not isinstance(e, dict) or set(e) < {"champ", "etiquette", "catalogue"}:
            pb.append(f"écart mal formé : {e!r} (attendu : champ, etiquette, catalogue)")
        elif e["champ"] not in NUTRIMENTS:
            pb.append(f"écart sur {e['champ']!r} : ce n'est pas une clé de nutriment")
        elif any(e[c] is not None and not est_nombre(e[c]) for c in ("etiquette", "catalogue")):
            pb.append(f"écart sur {e['champ']} : etiquette et catalogue sont des nombres ou null")
    return pb


def regle_alertes(r: dict) -> list[str]:
    a = r.get("alertes")
    if isinstance(a, list) and all(isinstance(x, str) for x in a):
        return []
    return ["alertes doit être une liste de textes"]


def regle_mesures(r: dict) -> list[str]:
    m = r.get("mesures")
    if not isinstance(m, dict):
        return ["mesures doit être un dictionnaire"]
    pb = _cles(m, MESURES)
    pb += [f"mesures.{k} = {m[k]!r} : un nombre" for k in MESURES if k in m and not est_nombre(m[k])]
    return pb


def regle_json(r: dict) -> list[str]:
    try:
        json.dumps(r)
    except (TypeError, ValueError) as e:
        return [f"le résultat ne passe pas en JSON (il doit pouvoir partir tel quel vers l'API) : {e}"]
    return []


REGLES = {
    "statut": regle_statut, "produit": regle_produit, "base": regle_base, "nutriments": regle_nutriments,
    "inferieur_a": regle_inferieur_a, "ingredients": regle_ingredients, "statut_et_fiche": regle_statut_fiche,
    "illisible": regle_illisible, "ecarts": regle_ecarts, "alertes": regle_alertes, "mesures": regle_mesures,
    "json": regle_json,
}


def problemes_contrat(r: Any) -> list[str]:
    """Tous les écarts au contrat d'un résultat (liste vide = conforme)."""
    pb = regle_dictionnaire(r)
    if not isinstance(r, dict):
        return pb
    for regle in REGLES.values():
        try:
            pb += regle(r)
        except Exception as e:  # résultat trop abîmé pour cette règle
            pb.append(f"{regle.__name__} : {type(e).__name__}: {e}")
    return pb

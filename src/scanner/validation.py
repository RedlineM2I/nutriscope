"""Module de validation des données extraites par le scanner.

Contient les schémas Pydantic (Étape A), les contrôles de cohérence
nutritionnelle (Étape B) et la détection des valeurs inventées (Étape C).
"""

from typing import Any, Literal
from pydantic import BaseModel, Field, field_validator, ValidationError

NUTRIENT_KEYS: tuple[str, ...] = (
    "kj", "kcal", "lipides", "satures", "glucides", "sucres",
    "fibres", "proteines", "sel",
)
VALID_BASES: tuple[str, ...] = ("100 g", "100 ml")


# ============================================================================
# Étape A : Schémas Pydantic
# ============================================================================

class ProductSchema(BaseModel):
    """Informations d'identification du produit."""
    nom: str | None = None
    marque: str | None = None
    code_barres: str | None = None

    @field_validator("nom", "marque", "code_barres", mode="before")
    @classmethod
    def clean_text(cls, value: Any) -> str | None:
        """Nettoie le texte ou renvoie None si vide ou non textuel."""
        if isinstance(value, str) and value.strip():
            return value.strip()
        return None


class NutrientsSchema(BaseModel):
    """Valeurs nutritionnelles pour 100 g ou 100 ml."""
    kj: float | None = Field(default=None, ge=0.0)
    kcal: float | None = Field(default=None, ge=0.0, le=900.0)
    lipides: float | None = Field(default=None, ge=0.0, le=100.0)
    satures: float | None = Field(default=None, ge=0.0, le=100.0)
    glucides: float | None = Field(default=None, ge=0.0, le=100.0)
    sucres: float | None = Field(default=None, ge=0.0, le=100.0)
    fibres: float | None = Field(default=None, ge=0.0, le=100.0)
    proteines: float | None = Field(default=None, ge=0.0, le=100.0)
    sel: float | None = Field(default=None, ge=0.0, le=100.0)

    @field_validator("*", mode="before")
    @classmethod
    def reject_booleans_and_coerce(cls, value: Any) -> Any:
        """Empêche la conversion implicite de booléens en nombres."""
        if isinstance(value, bool):
            raise ValueError("Un booléen n'est pas un nombre nutritionnel valide")
        return value


class LabelExtractionSchema(BaseModel):
    """Schéma global de l'extraction brute issue du modèle."""
    produit: ProductSchema = Field(default_factory=ProductSchema)
    base: Literal["100 g", "100 ml"] | None = None
    nutriments: NutrientsSchema = Field(default_factory=NutrientsSchema)
    inferieur_a: list[str] = Field(default_factory=list)
    ingredients: list[str] | None = None


def validate_with_pydantic(raw_data: Any) -> tuple[dict[str, Any], list[str]]:
    """Valide les données brutes avec Pydantic sans jamais lever d'exception.

    Returns:
        tuple[dict, list[str]]: Le dictionnaire nettoyé conforme et les alertes.
    """
    alerts: list[str] = []

    if not isinstance(raw_data, dict):
        alerts.append("Réponse du modèle sans JSON exploitable")
        return {
            "produit": {"nom": None, "marque": None, "code_barres": None},
            "base": None,
            "nutriments": {k: None for k in NUTRIENT_KEYS},
            "inferieur_a": [],
            "ingredients": None,
        }, alerts

    # 1. Validation du produit
    product_dict = {
        "nom": raw_data.get("nom"),
        "marque": raw_data.get("marque"),
        "code_barres": raw_data.get("code_barres"),
    }
    try:
        product_obj = ProductSchema.model_validate(product_dict)
        cleaned_product = product_obj.model_dump()
        for k in ("nom", "marque", "code_barres"):
            raw_val = product_dict[k]
            if raw_val is not None and cleaned_product[k] is None:
                alerts.append(f"Valeur invalide pour {k}, ignorée")
    except ValidationError as err:
        cleaned_product = {"nom": None, "marque": None, "code_barres": None}
        alerts.append(f"Erreur validation produit : {err}")

    # 2. Validation de la base
    raw_base = raw_data.get("base")
    if raw_base in VALID_BASES:
        cleaned_base = raw_base
    elif raw_base is not None:
        cleaned_base = None
        alerts.append(f"Base inconnue : {raw_base!r}, ignorée")
    else:
        cleaned_base = None

    # 3. Validation des nutriments (champ par champ pour isoler les erreurs)
    raw_nutrients = raw_data.get("nutriments")
    cleaned_nutrients: dict[str, float | None] = {k: None for k in NUTRIENT_KEYS}

    if isinstance(raw_nutrients, dict):
        for key in NUTRIENT_KEYS:
            if key in raw_nutrients:
                val = raw_nutrients[key]
                if val is None:
                    continue
                try:
                    # Valide la valeur individuellement via NutrientsSchema
                    single_val = NutrientsSchema.model_validate({key: val})
                    cleaned_nutrients[key] = getattr(single_val, key)
                except ValidationError:
                    alerts.append(f"{key} invalide ou hors limites ({val!r}), écarté")
    elif raw_nutrients is not None:
        alerts.append("Bloc nutriments mal formé, ignoré")

    # 4. Validation inferieur_a
    raw_lt = raw_data.get("inferieur_a")
    cleaned_lt: list[str] = []
    if isinstance(raw_lt, list):
        for item in raw_lt:
            if isinstance(item, str) and item in NUTRIENT_KEYS and cleaned_nutrients.get(item) is not None:
                cleaned_lt.append(item)
            elif item not in NUTRIENT_KEYS:
                alerts.append(f"Clé inconnue dans inferieur_a : {item!r}")

    # 5. Ingrédients
    raw_ing = raw_data.get("ingredients")
    cleaned_ing: list[str] | None = None
    if isinstance(raw_ing, list):
        cleaned_list = [
            t.strip() for t in raw_ing if isinstance(t, str) and t.strip()
        ]
        cleaned_ing = cleaned_list or None

    cleaned_data = {
        "produit": cleaned_product,
        "base": cleaned_base,
        "nutriments": cleaned_nutrients,
        "inferieur_a": cleaned_lt,
        "ingredients": cleaned_ing,
    }

    return cleaned_data, alerts


# ============================================================================
# Étape B : Contrôles de cohérence nutritionnelle
# ============================================================================

def check_nutritional_coherence(
    nutriments: dict[str, float | None],
    base: str | None = None,
) -> list[str]:
    """Vérifie la cohérence physique et biologique des valeurs nutritionnelles.

    Args:
        nutriments: Dictionnaire des 9 nutriments nettoyés.
        base: Base déclarée ("100 g" ou "100 ml").

    Returns:
        list[str]: Alertes décrivant les incohérences constatées.
    """
    alerts: list[str] = []

    # 1. Sous-totaux : saturés <= lipides
    lipides = nutriments.get("lipides")
    satures = nutriments.get("satures")
    if lipides is not None and satures is not None:
        if satures > lipides + 0.05:
            alerts.append(
                f"Incohérence sous-total : acides gras saturés ({satures} g) "
                f"supérieurs aux lipides totaux ({lipides} g)"
            )

    # 2. Sous-totaux : sucres <= glucides
    glucides = nutriments.get("glucides")
    sucres = nutriments.get("sucres")
    if glucides is not None and sucres is not None:
        if sucres > glucides + 0.05:
            alerts.append(
                f"Incohérence sous-total : sucres ({sucres} g) "
                f"supérieurs aux glucides totaux ({glucides} g)"
            )

    # 3. Somme des macronutriments (lipides + glucides + protéines + fibres + sel)
    # Tolérance de 5 % (105 g) pour compenser les arrondis et l'humidité
    macro_keys = ("lipides", "glucides", "proteines", "fibres", "sel")
    present_macros = [nutriments[k] for k in macro_keys if nutriments.get(k) is not None]
    if present_macros:
        somme_macros = sum(present_macros)
        if somme_macros > 105.0:
            alerts.append(
                f"Incohérence masse : somme des nutriments ({somme_macros:.1f} g) "
                f"supérieure à 100 g (+ marge d'arrondi)"
            )

    # 4. Cohérence énergétique : 1 kcal ≈ 4.184 kJ
    # Ratio acceptable entre 3.7 et 4.6 compte tenu des facteurs de conversion et arrondis
    kj = nutriments.get("kj")
    kcal = nutriments.get("kcal")
    if kj is not None and kcal is not None and kcal > 0:
        ratio = kj / kcal
        if not (3.7 <= ratio <= 4.6):
            alerts.append(
                f"Incohérence énergétique : ratio kJ/kcal ({ratio:.2f}) "
                f"hors des normes réglementaires [3.7, 4.6]"
            )

    return alerts


# ============================================================================
# Étape C : Détection des valeurs inventées
# ============================================================================

def check_invented_values(
    nutriments: dict[str, float | None],
    inferieur_a: list[str],
) -> list[str]:
    """Détecte les potentielles valeurs inventées par le modèle (ex: faux 0).

    Args:
        nutriments: Dictionnaire des nutriments.
        inferieur_a: Liste des nutriments précédés d'un symbole '<'.

    Returns:
        list[str]: Alertes signalant les anomalies de valeurs inventées.
    """
    alerts: list[str] = []

    # 1. Règle 'inferieur_a' : si < 0.5 g, la valeur doit être le seuil (0.5), jamais 0.0
    for key in inferieur_a:
        val = nutriments.get(key)
        if val == 0.0:
            alerts.append(
                f"Valeur potentiellement inventée ou mal reportée : {key} est dans "
                f"'inferieur_a' mais vaut 0.0 au lieu du seuil positif"
            )

    # 2. Fibres à 0.0 : les fibres ne font pas partie des 7 mentions obligatoires en Europe.
    # Les modèles ont tendance à halluciner 'fibres: 0' quand elles sont omises de l'étiquette.
    fibres = nutriments.get("fibres")
    if fibres == 0.0:
        alerts.append(
            "Suspicion de valeur inventée : fibres vaut 0.0 (souvent omis sur l'emballage)"
        )

    return alerts

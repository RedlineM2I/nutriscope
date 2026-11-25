from typing import Literal, TypedDict

import duckdb
from langchain_core.tools import tool

from src.config import PARQUET_CLEAN_DATASET

# ── Constantes ───────────────────────────────────────────────

NUTRI_COLS = {  # noms bruts, sans guillemets SQL
    "kcal": "energy-kcal_100g",
    "lipides": "fat_100g",
    "satures": "saturated-fat_100g",
    "sucres": "sugars_100g",
    "sel": "salt_100g",
    "fibres": "fiber_100g",
    "proteines": "proteins_100g",
}

# ── Types communs ────────────────────────────────────────────

Status = Literal["ok", "introuvable", "ambiguous"]


class ProductResult(TypedDict):
    """Fiche produit renvoyée par ``find_product``."""

    code: str
    name: str
    nutriscore: str | None
    nutrients: dict[str, float | None]
    incomplete_data: bool


class SubstituteResult(TypedDict):
    """Un produit alternatif proposé par ``substitute``."""

    code: str
    product_name: str
    nutriscore_grade: str
    nutritional_distance: float


class SourceReference(TypedDict):
    """Une source citée dans une réponse."""

    title: str
    origin: str
    license: str


class SourceResult(TypedDict):
    """Réponse du RAG avec ses sources."""

    answer: str
    sources: list[SourceReference]


# ── Enveloppes de retour ─────────────────────────────────────


class FindProductResponse(TypedDict):
    """Enveloppe de retour de ``find_product``."""

    status: Status
    total: int
    results: list[ProductResult]


class SubstituteResponse(TypedDict):
    """Enveloppe de retour de ``substitute``."""

    status: Status
    total: int
    results: list[SubstituteResult]


class AnswerSourceResponse(TypedDict):
    """Enveloppe de retour de ``answer_source``."""

    status: Status
    total: int
    results: list[SourceResult]


# ── Fonctions internes ───────────────────────────────────────


def _build_filter(nom: str | None, code: str | None) -> str:
    if code:
        return f"code LIKE '{code}'"
    return f"strip_accents(product_name) ILIKE '%' || strip_accents('{nom}') || '%'"


# ── Outils LangChain ────────────────────────────────────────


@tool(parse_docstring=True)
def find_product(
    name: str | None = None,
    code: str | None = None,
    limit: int = 3,
) -> FindProductResponse:
    """Cherche un produit dans le catalogue NutriScope et renvoie ses fiches.

    À utiliser pour obtenir le Nutri-Score (A à E, ou null si inconnu) et les
    nutriments pour 100 g d'un produit. Seule source autorisée pour toute
    information sur un produit. Donner nom ou code (au moins l'un des deux).

    Ne pas utiliser pour proposer des alternatives (utiliser ``substitute``)
    ni pour une question générale de nutrition (utiliser ``answer_source``).

    Args:
        name: Nom ou partie du nom du produit, sans les mots de la question.
        code: Code-barres exact, en texte (ex. "3017620422003"). Prime sur
            name si les deux sont donnés.
        limit: Nombre maximal de fiches renvoyées, entier de 1 à 5.
            Facultatif, 3 par défaut.

    Returns:
        Enveloppe ``FindProductResponse`` avec :
        - ``status`` : "ok" (un seul résultat), "ambiguous" (plusieurs),
          ou "introuvable" (aucun).
        - ``total`` : nombre de fiches trouvées.
        - ``results`` : liste de ``ProductResult``.

    Raises:
        ValueError: Si ``name`` et ``code`` sont tous les deux absents,
            ou si ``limit`` est hors de l'intervalle [1, 5].
    """
    print("-"*10, " Outil appelé ", "-"*10)
    if name is None and code is None:
        raise ValueError("Au moins un critère requis : name ou code.")
    if not (1 <= limit <= 5):
        raise ValueError(f"limit doit être entre 1 et 5, reçu {limit}.")

    where_statement = _build_filter(name, code)

    struct_fields = ", ".join(
        f'{k} := CASE WHEN "{col}_empty" THEN NULL ELSE "{col}" END'
        for k, col in NUTRI_COLS.items()
    )
    any_missing = " OR ".join(f'"{col}_empty"' for col in NUTRI_COLS.values())

    con = duckdb.connect()
    response = con.execute(
        f"""
        SELECT code::VARCHAR as code,
        product_name as name,
        CASE WHEN
            lower(nutriscore_grade) IN ('a','b','c','d','e')
            THEN upper(nutriscore_grade) END AS nutriscore ,
            struct_pack({struct_fields}) AS nutrients,
            (nutriscore IS NULL OR {any_missing}) AS incomplete_data
        FROM read_parquet('{PARQUET_CLEAN_DATASET}')
        where {where_statement}
        limit {limit}
        """
    ).df()

    total = len(response)

    if total == 0:
        return FindProductResponse(status="introuvable", total=0, results=[])

    status: Status = "ok" if total == 1 else "ambiguous"
    results: list[ProductResult] = [
        ProductResult(
            code=row[0],
            name=row[1],
            nutriscore=row[2],
            nutrients=row[3],
            incomplete_data=row[4],
        )
        for row in response.values
    ]
    return FindProductResponse(status=status, total=total, results=results)


@tool(parse_docstring=True)
def substitute(
    code: str,
    required_labels: list[str] | None = None,
    max_results: int = 3,
) -> SubstituteResponse:
    """Propose des produits alternatifs mieux notés qu'un produit donné.

    À utiliser quand l'utilisateur demande une meilleure alternative à un
    produit déjà identifié (« propose mieux », « et en bio ? »). Les
    alternatives viennent du même rayon et sont classées par Nutri-Score,
    puis par proximité nutritionnelle avec le produit de départ.

    Ne pas utiliser pour obtenir la fiche d'un produit (utiliser
    ``find_product``) ni pour une question générale de nutrition
    (utiliser ``answer_source``).

    Args:
        code: Code-barres du produit de départ, sous forme de texte
            (ex. "3017620422003"). Ne jamais le convertir en nombre : les
            zéros de tête comptent.
        required_labels: Labels à privilégier, au format Open Food Facts
            (ex. ["en:organic"] pour du bio). Si aucun label n'est donné,
            aucun filtre n'est appliqué.
        max_results: Nombre maximal d'alternatives à renvoyer, entre 1 et 5.

    Returns:
        Enveloppe ``SubstituteResponse`` avec :
        - ``status`` : "ok" (au moins une alternative trouvée) ou
          "introuvable" (aucune alternative, ou produit de départ inconnu).
        - ``total`` : nombre d'alternatives trouvées.
        - ``results`` : liste de ``SubstituteResult``, triée de la meilleure
          à la moins bonne.

    Raises:
        ValueError: Si ``code`` est vide ou si ``max_results`` est hors
            de l'intervalle [1, 5].
    """
    if not code:
        raise ValueError("code ne peut pas être vide.")
    if not (1 <= max_results <= 5):
        raise ValueError(
            f"max_results doit être entre 1 et 5, reçu {max_results}."
        )
    raise NotImplementedError("Branché à src/substitution.py (TP 16)")


@tool(parse_docstring=True)
def answer_source(
    question: str,
    top_k: int = 5,
) -> AnswerSourceResponse:
    """Répond à une question de nutrition en citant des sources.

    À utiliser pour les questions de connaissance : explication du
    Nutri-Score, repères nutritionnels (PNNS), signification d'un additif,
    etc. La réponse s'appuie uniquement sur le corpus indexé (fiches produits
    et documents publics de référence). Toujours citer les sources renvoyées
    dans la réponse finale à l'utilisateur.

    Ne pas utiliser pour retrouver un produit précis (utiliser
    ``find_product``) ni pour proposer des alternatives (utiliser
    ``substitute``). Ne répond pas aux questions médicales ni hors
    alimentation.

    Args:
        question: Question de l'utilisateur, en français et en langage
            naturel (ex. « Pourquoi ce produit est-il noté D ? »).
        top_k: Nombre de passages du corpus à récupérer, entre 1 et 10.

    Returns:
        Enveloppe ``AnswerSourceResponse`` avec :
        - ``status`` : "ok" (réponse trouvée) ou "introuvable" (le corpus
          ne contient pas de réponse fiable).
        - ``total`` : nombre de résultats (0 ou 1).
        - ``results`` : liste d'un ``SourceResult`` (réponse + sources).

    Raises:
        ValueError: Si ``question`` est vide ou si ``top_k`` est hors
            de l'intervalle [1, 10].
    """
    if not question or not question.strip():
        raise ValueError("question ne peut pas être vide.")
    if not (1 <= top_k <= 10):
        raise ValueError(f"top_k doit être entre 1 et 10, reçu {top_k}.")
    raise NotImplementedError("Branché au RAG (TP 19-20)")

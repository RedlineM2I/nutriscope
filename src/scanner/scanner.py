import base64
import json
import mimetypes
import time
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from openai import APIError, OpenAI

from src.scanner.validation import (
    check_invented_values,
    check_nutritional_coherence,
    validate_with_pydantic,
)

# Contract keys (statut, produit, nutriments...) stay in French: the contract imposes them.
NUTRIENT_KEYS: tuple[str, ...] = (
    "kj", "kcal", "lipides", "satures", "glucides", "sucres",
    "fibres", "proteines", "sel",
)
VALID_BASES: tuple[str, ...] = ("100 g", "100 ml")


def empty_result(
        model_calls: int = 0,
        latency_s: float = 0.0,
        input_tokens: int = 0,
        output_tokens: int = 0,
) -> dict[str, Any]:
    """Résultat conforme au contrat, sans rien de lu. Filet de sécurité."""
    return {
        "statut": "illisible",
        "produit": {"nom": None, "marque": None, "code_barres": None},
        "base": None,
        "nutriments": {key: None for key in NUTRIENT_KEYS},
        "inferieur_a": [],
        "ingredients": None,
        "fiche_catalogue": None,
        "ecarts": [],
        "alertes": [],
        "mesures": {
            "appels_modele": model_calls,
            "latence_s": latency_s,
            "tokens_entree": input_tokens,
            "tokens_sortie": output_tokens,
        },
    }


def _text_or_none(value: Any) -> str | None:
    """Renvoie le texte nettoyé, ou None si la valeur n'est pas un texte non vide."""
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def normalize(res_json: Any, result: dict[str, Any]) -> dict[str, Any]:
    """Remplit `result` (issu de empty_result) avec la lecture du modèle validée.

    Passe par :
    1. Validation Pydantic (Étape A : types, bornes, isolation des erreurs).
    2. Contrôles de cohérence nutritionnelle (Étape B : sous-totaux, somme, ratio kJ/kcal).
    3. Détection des valeurs inventées (Étape C : faux 0, cohérence inferieur_a).
    """
    cleaned_data, pydantic_alerts = validate_with_pydantic(res_json)
    result["alertes"].extend(pydantic_alerts)

    result["produit"] = cleaned_data["produit"]
    result["base"] = cleaned_data["base"]
    result["nutriments"] = cleaned_data["nutriments"]
    result["inferieur_a"] = cleaned_data["inferieur_a"]
    result["ingredients"] = cleaned_data["ingredients"]

    # Contrôles de cohérence nutritionnelle (Étape B)
    coherence_alerts = check_nutritional_coherence(
        result["nutriments"], base=result["base"]
    )
    result["alertes"].extend(coherence_alerts)

    # Détection des valeurs inventées (Étape C)
    invented_alerts = check_invented_values(
        result["nutriments"], inferieur_a=result["inferieur_a"]
    )
    result["alertes"].extend(invented_alerts)

    # Statut : est-ce que quelque chose a été lu ?
    product_read = any(v is not None for v in result["produit"].values())
    value_read = any(v is not None for v in result["nutriments"].values())
    if product_read or value_read:
        result["statut"] = "non_verifie"
    else:
        result["alertes"].append("Aucun produit identifié et aucune valeur lue")

    return result


def _call_model(url_image, client: OpenAI, message) -> tuple[str | None, int, int]:
    system_prompt = Path(__file__).with_name("system_prompt.md").read_text(encoding="utf-8")
    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user", "content": [
            {"type": "text", "text": message},
            {"type": "image_url", "image_url": {"url": url_image}}, ]
        }
    ]

    response = client.chat.completions.create(
        model="qwen3-vl:8b-instruct", messages=messages, temperature=0
    )

    return response.choices[0].message.content, response.usage.prompt_tokens, response.usage.completion_tokens


def _extract_json(text: str) -> dict | None:
    i_start = text.find("{")
    i_end = text.rfind("}")
    if i_start == -1 or i_end == -1 or i_end < i_start:
        return None
    json_text = text[i_start:i_end + 1]
    try:
        resp_json = json.loads(json_text)
        if isinstance(resp_json, dict):
            return resp_json
        return None
    except JSONDecodeError as e:
        return None


def load_image(image: Path | bytes | str) -> tuple[bytes, str | None]:
    mime = None
    img_bytes = image
    if isinstance(image, (str, Path)):
        tmp_img = Path(image)
        mime = mimetypes.guess_type(tmp_img)[0]
        img_bytes = tmp_img.read_bytes()
    elif isinstance(image, bytes):
        if image.startswith(b"\xff\xd8\xff") :
            mime = "image/jpeg"
        elif image.startswith(b"\x89PNG") :
            mime = "image/png"
    if mime is None : raise Exception(f"Image type not supported: {type(image)}")
    return img_bytes, mime

def scan_label(image: Path | bytes | str):
    empty_json = empty_result()
    try:
        img_bytes, mime = load_image(image)
        image_b64 = base64.b64encode(img_bytes).decode("ascii")
        url_image = f"data:{mime};base64,{image_b64}"
    except Exception:
        empty_json["alertes"].append("Impossible de lire l'image fournie")
        return empty_json

    nb_try = 3
    model_calls = 0
    message = "Recopie le tableau nutritionnel de cette photo."
    for i in range(nb_try) :
        try:
            start = time.perf_counter()
            response, prompt_tokens, completion_tokens = _call_model(
                url_image,
                client=OpenAI(base_url="http://localhost:11434/v1", api_key="ollama"), message=message
            )
            perf = time.perf_counter() - start
        except APIError as e:
            empty_json["alertes"].append(f"Erreur API du modèle : {e}")
            return empty_json
        except Exception as e:
            empty_json["alertes"].append(f"Impossible de contacter le modèle : {e}")
            return empty_json
        model_calls += 1
        empty_json = empty_result(model_calls, perf, prompt_tokens, completion_tokens)
        res_json = _extract_json(response)
        res = normalize(res_json, empty_json)
    return res


# Alias imposé par les outils de l'atelier
scanner_etiquette = scan_label


if __name__ == '__main__':
    image = Path("data/photos/10_3608580065340_etiquette.jpg")
    print(scan_label(image))

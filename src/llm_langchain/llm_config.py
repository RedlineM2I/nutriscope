import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from langchain_ollama import ChatOllama

SYSTEM_PROMPT = Path(__file__).with_name("system_prompt.md").read_text(encoding="utf-8")

SUMMARIZE_PROMPT = (
    "Résume cette conversation entre l'utilisateur et l'assistant de NutriScope en trois phrases au plus, en français."
    "Garde les code-barres et les noms de produits cités.\n\n{messages}")


def create_model(temperature=0, num_predict=5000):
    if (os.getenv("LLM_PROVIDER") or "ollama") == "ollama":
        return ChatOllama(
            model=os.getenv("OLLAMA_MODEL", "qwen3:8b"),
            base_url=os.getenv("OLLAMA_URL", "http://localhost:11434"),
            temperature=temperature,  # 0 pour des réponses déterministes/factuelles
            reasoning=False,  # Désactive la réflexion préalable si non nécessaire
            num_predict=num_predict  # Plafond de tokens générés
        )
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model=os.environ["LLM_MODEL"],
        base_url=os.environ["LLM_BASE_URL"],
        api_key=os.environ["LLM_API_KEY"],
        temperature=temperature,
        max_tokens=num_predict
    )

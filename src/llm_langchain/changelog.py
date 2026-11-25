"""Journal d'exécution d'un agent LangChain : durée et tokens de chaque étape."""

import time
from typing import Any
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult


class Changelog(BaseCallbackHandler):
    """Note chaque étape de l'agent : type, nom, durée et tokens.

    Le texte des messages n'est jamais enregistré (confidentialité).

    Attributes:
        rows: Une ligne par étape terminée.
        start_times: Heure de début de chaque étape en cours, indexée par
            l'identifiant d'exécution (run_id).
    """

    def __init__(self) -> None:
        self.rows: list[dict[str, Any]] = []
        self.start_times: dict[UUID, float] = {}

    def on_chat_model_start(
            self,
            serialized: dict[str, Any],
            messages: list[list[Any]],
            *,
            run_id: UUID,
            **kwargs: Any,
    ) -> None:
        """Note l'heure de début d'un appel au modèle.

        Args:
            serialized: Description sérialisée du modèle (non utilisée).
            messages: Messages envoyés au modèle (non utilisés, jamais stockés).
            run_id: Identifiant unique de cette exécution.
            **kwargs: Arguments supplémentaires fournis par LangChain.
        """
        self.start_times[run_id] = time.perf_counter()

    def on_llm_end(
            self, response: LLMResult, *, run_id: UUID, **kwargs: Any
    ) -> None:
        """Écrit la ligne du journal à la fin d'un appel au modèle.

        Le nom de l'étape est la liste des outils demandés par le modèle,
        ou « réponse » s'il répond directement.

        Args:
            response: Résultat du modèle.
            run_id: Identifiant unique de cette exécution.
            **kwargs: Arguments supplémentaires fournis par LangChain.

        Raises:
            KeyError: Si on_chat_model_start n'a pas été appelé pour ce run_id.
        """
        duration = time.perf_counter() - self.start_times.pop(run_id)
        message = response.generations[0][0].message  # message rendu par le modèle

        # Noms des outils demandés par le modèle
        requested_tools = [call["name"] for call in message.tool_calls]
        name = ", ".join(requested_tools) if requested_tools else "réponse"

        usage = message.usage_metadata
        self.rows.append(
            {
                "étape": "modèle",
                "nom": name,
                "durée (s)": round(duration, 2),
                "tokens entrée": usage["input_tokens"],
                "tokens sortie": usage["output_tokens"],
            }
        )

    def on_tool_start(
            self,
            serialized: dict[str, Any],
            input_str: str,
            *,
            run_id: UUID,
            **kwargs: Any,
    ) -> None:
        """Note l'heure de début d'un appel d'outil.

        Args:
            serialized: Description sérialisée de l'outil (non utilisée).
            input_str: Entrée de l'outil (non utilisée, jamais stockée).
            run_id: Identifiant unique de cette exécution.
            **kwargs: Arguments supplémentaires fournis par LangChain.
        """
        self.start_times[run_id] = time.perf_counter()

    def on_tool_end(self, output: Any, *, run_id: UUID, **kwargs: Any) -> None:
        """Écrit la ligne du journal à la fin d'un outil.

        Args:
            output: Résultat de l'outil ; son attribut `name` donne le nom
                de l'outil.
            run_id: Identifiant unique de cette exécution.
            **kwargs: Arguments supplémentaires fournis par LangChain.

        Raises:
            KeyError: Si on_tool_start n'a pas été appelé pour ce run_id.
        """
        duration = time.perf_counter() - self.start_times.pop(run_id)
        self.rows.append(
            {
                "étape": "outil",
                "nom": output.name,
                "durée (s)": round(duration, 2),
                "tokens entrée": 0,
                "tokens sortie": 0,
            }
        )
# src/ai_research_assistant/core/unified_llm_factory.py
import logging
from typing import Any, Dict, Optional

from . import llm_provider
from .env_manager import env_manager

logger = logging.getLogger(__name__)


class UnifiedLLMFactory:
    """
    Centralized factory for creating pydantic-ai Model instances.
    """

    def __init__(self) -> None:
        self.env_manager = env_manager
        self._llm_cache: Dict[str, Any] = {}

    def create_llm_from_config(self, config: Dict[str, Any]) -> Any:
        """
        Create a pydantic-ai Model instance from a configuration dictionary.
        """
        provider = config.get("provider")
        model_name = config.get("model_name")

        if not provider or not model_name:
            raise ValueError(
                f"Invalid LLM config: provider={provider}, model_name={model_name}"
            )

        cache_key = f"{provider}:{model_name}"
        if cache_key in self._llm_cache:
            logger.debug(f"Returning cached pydantic-ai Model: {cache_key}")
            return self._llm_cache[cache_key]

        logger.info(
            f"Creating new pydantic-ai Model: Provider={provider}, Model={model_name}"
        )

        try:
            api_key = self.env_manager.get_api_key(provider)
            endpoint = self.env_manager.get_endpoint(provider)

            # The llm_provider now returns a pydantic-ai Model object
            llm_model_instance = llm_provider.get_llm_model(
                provider=provider,
                api_key=api_key,
                model_name=model_name,
                base_url=endpoint,
            )

            if llm_model_instance is None:
                raise RuntimeError(
                    f"Failed to create pydantic-ai Model for '{provider}'"
                )

            self._llm_cache[cache_key] = llm_model_instance
            logger.info(
                f"✅ Successfully created pydantic-ai Model: {provider}:{model_name}"
            )
            return llm_model_instance

        except Exception as e:
            error_msg = f"Failed to initialize pydantic-ai Model '{model_name}' for provider '{provider}': {e}"
            logger.error(error_msg, exc_info=True)
            raise RuntimeError(error_msg) from e

    def clear_cache(self) -> None:
        self._llm_cache.clear()
        logger.info("LLM cache cleared")


# --- Singleton Management ---
_llm_factory_instance: Optional[UnifiedLLMFactory] = None


def get_llm_factory() -> UnifiedLLMFactory:
    global _llm_factory_instance
    if _llm_factory_instance is None:
        _llm_factory_instance = UnifiedLLMFactory()
    return _llm_factory_instance

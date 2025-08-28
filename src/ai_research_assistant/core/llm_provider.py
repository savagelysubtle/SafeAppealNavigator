# src/ai_research_assistant/core/llm_provider.py
import logging
from typing import Any, Optional

# --- DEFINITIVE FIX: Import the correct Model and Provider classes from pydantic-ai ---
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider

from .env_manager import env_manager

# Import other pydantic-ai models as you add support for them
# from pydantic_ai.models.openai import OpenAIModel, OpenAIProvider

logger = logging.getLogger(__name__)


def _create_google_model(
    api_key: Optional[str], model_name: str, **kwargs
) -> GoogleModel:
    """Creates a pydantic-ai GoogleModel instance as per the official documentation."""
    if not api_key:
        api_key = env_manager.get_api_key("google")
    if not api_key:
        raise ValueError(env_manager.create_error_message("google"))

    # As per docs, create a provider and then the model
    provider = GoogleProvider(api_key=api_key)
    return GoogleModel(model_name, provider=provider)


# Add other provider functions here if needed, for example:
# def _create_openai_model(api_key: Optional[str], model_name: str, base_url: Optional[str], **kwargs) -> OpenAIModel:
#     ...

# Provider factory mapping now points to functions that create pydantic-ai Model objects
PROVIDER_FACTORIES = {
    "google": _create_google_model,
    # "openai": _create_openai_model,
}


def get_llm_model(
    provider: str,
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
    **kwargs,
) -> Any:
    """
    Get a pydantic-ai Model instance for the specified provider.
    """
    if provider not in PROVIDER_FACTORIES:
        supported_providers = ", ".join(PROVIDER_FACTORIES.keys())
        raise ValueError(
            f"Unsupported provider: {provider}. Supported: {supported_providers}"
        )

    factory = PROVIDER_FACTORIES[provider]

    if not model_name:
        # Define a default model if not provided
        default_models = {"google": "gemini-2.5-flash-preview-05-20"}
        model_name = default_models.get(provider)
        if not model_name:
            raise ValueError(
                f"No default model name configured for provider: {provider}"
            )

    try:
        logger.info(f"Creating pydantic-ai Model for {provider}:{model_name}")
        return factory(api_key=api_key, model_name=model_name, **kwargs)
    except Exception as e:
        logger.error(
            f"Failed to create pydantic-ai Model for {provider}: {e}", exc_info=True
        )
        raise ValueError(f"Failed to create {provider} model: {e}") from e

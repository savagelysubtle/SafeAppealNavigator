"""
LLM Provider Management for AI Research Assistant

Provides unified interface for creating and managing different LLM providers
with proper API key validation and configuration handling.
"""

import logging
from typing import Any, Dict, Optional

from .env_manager import env_manager

logger = logging.getLogger(__name__)


def _create_google_provider(
    api_key: Optional[str] = None,
    model_name: str = "gemini-2.5-flash-preview-04-17",
    temperature: float = 0.0,
    max_tokens: Optional[int] = None,
    top_p: Optional[float] = None,
    top_k: Optional[int] = None,
    safety_settings: Optional[Dict[str, str]] = None,
    **kwargs,
) -> Any:
    """
    Create Google GenerativeAI provider with enhanced configuration support

    Args:
        api_key: Google API key (if not provided, will get from environment)
        model_name: Model to use (default: gemini-2.5-flash-preview-04-17)
        temperature: Generation temperature (0.0-1.0)
        max_tokens: Maximum output tokens
        top_p: Top-p sampling parameter
        top_k: Top-k sampling parameter
        safety_settings: Safety settings for content filtering
        **kwargs: Additional parameters

    Returns:
        ChatGoogleGenerativeAI instance

    Raises:
        ValueError: If API key is not available
        ImportError: If langchain-google-genai is not installed
    """
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except ImportError as e:
        raise ImportError(
            "langchain-google-genai not installed. "
            "Install with: uv add langchain-google-genai"
        ) from e

    # Get API key from parameter or environment
    if not api_key:
        api_key = env_manager.get_api_key("google")

    if not api_key:
        error_msg = env_manager.create_error_message("google")
        raise ValueError(error_msg)

    # Start with basic configuration
    config = {
        "model": model_name,
        "temperature": temperature,
        "api_key": api_key,
    }

    # Add project ID if available
    provider_config = env_manager.get_provider_config("google")
    if "project_id" in provider_config:
        config["project_id"] = provider_config["project_id"]

    # Add generation configuration if parameters provided
    generation_config = {}
    if max_tokens is not None:
        generation_config["max_output_tokens"] = max_tokens
    if top_p is not None:
        generation_config["top_p"] = top_p
    if top_k is not None:
        generation_config["top_k"] = top_k

    if generation_config:
        config["generation_config"] = generation_config

    # Add safety settings if provided
    if safety_settings:
        config["safety_settings"] = safety_settings

    # Add any additional kwargs
    config.update(kwargs)

    logger.info(f"Creating Google provider with model: {model_name}")

    try:
        return ChatGoogleGenerativeAI(**config)
    except Exception as e:
        logger.error(f"Failed to create Google provider: {e}")
        raise ValueError(f"Failed to initialize Google provider: {e}") from e


def _create_openai_provider(
    api_key: Optional[str] = None,
    model_name: str = "gpt-4",
    temperature: float = 0.0,
    base_url: Optional[str] = None,
    **kwargs,
) -> Any:
    """Create OpenAI provider"""
    try:
        from langchain_openai import ChatOpenAI
    except ImportError as e:
        raise ImportError(
            "langchain-openai not installed. Install with: uv add langchain-openai"
        ) from e

    if not api_key:
        api_key = env_manager.get_api_key("openai")

    if not api_key:
        error_msg = env_manager.create_error_message("openai")
        raise ValueError(error_msg)

    config = {
        "model": model_name,
        "temperature": temperature,
        "api_key": api_key,
    }

    if base_url:
        config["base_url"] = base_url
    else:
        endpoint = env_manager.get_endpoint("openai")
        if endpoint:
            config["base_url"] = endpoint

    config.update(kwargs)

    logger.info(f"Creating OpenAI provider with model: {model_name}")
    return ChatOpenAI(**config)


def _create_anthropic_provider(
    api_key: Optional[str] = None,
    model_name: str = "claude-3-5-sonnet-20241022",
    temperature: float = 0.0,
    **kwargs,
) -> Any:
    """Create Anthropic provider"""
    try:
        from langchain_anthropic import ChatAnthropic
    except ImportError as e:
        raise ImportError(
            "langchain-anthropic not installed. "
            "Install with: uv add langchain-anthropic"
        ) from e

    if not api_key:
        api_key = env_manager.get_api_key("anthropic")

    if not api_key:
        error_msg = env_manager.create_error_message("anthropic")
        raise ValueError(error_msg)

    config = {
        "model": model_name,
        "temperature": temperature,
        "api_key": api_key,
    }

    config.update(kwargs)

    logger.info(f"Creating Anthropic provider with model: {model_name}")
    return ChatAnthropic(**config)


def _create_mistral_provider(
    api_key: Optional[str] = None,
    model_name: str = "mistral-large-latest",
    temperature: float = 0.0,
    **kwargs,
) -> Any:
    """Create Mistral provider"""
    try:
        from langchain_mistralai import ChatMistralAI
    except ImportError as e:
        raise ImportError(
            "langchain-mistralai not installed. "
            "Install with: uv add langchain-mistralai"
        ) from e

    if not api_key:
        api_key = env_manager.get_api_key("mistral")

    if not api_key:
        error_msg = env_manager.create_error_message("mistral")
        raise ValueError(error_msg)

    config = {
        "model": model_name,
        "temperature": temperature,
        "api_key": api_key,
    }

    endpoint = env_manager.get_endpoint("mistral")
    if endpoint:
        config["endpoint"] = endpoint

    config.update(kwargs)

    logger.info(f"Creating Mistral provider with model: {model_name}")
    return ChatMistralAI(**config)


def _create_ollama_provider(
    model_name: str = "llama2",
    temperature: float = 0.0,
    base_url: Optional[str] = None,
    **kwargs,
) -> Any:
    """Create Ollama provider"""
    try:
        from langchain_ollama import ChatOllama
    except ImportError as e:
        raise ImportError(
            "langchain-ollama not installed. Install with: uv add langchain-ollama"
        ) from e

    config = {
        "model": model_name,
        "temperature": temperature,
    }

    if base_url:
        config["base_url"] = base_url
    else:
        endpoint = env_manager.get_endpoint("ollama")
        if endpoint:
            config["base_url"] = endpoint
        else:
            config["base_url"] = "http://localhost:11434"  # Default Ollama URL

    config.update(kwargs)

    logger.info(f"Creating Ollama provider with model: {model_name}")
    return ChatOllama(**config)


def _create_deepseek_provider(
    api_key: Optional[str] = None,
    model_name: str = "deepseek-chat",
    temperature: float = 0.0,
    **kwargs,
) -> Any:
    """Create DeepSeek provider"""
    try:
        from langchain_deepseek import ChatDeepSeek
    except ImportError as e:
        raise ImportError(
            "langchain-deepseek not installed. Install with: uv add langchain-deepseek"
        ) from e

    if not api_key:
        api_key = env_manager.get_api_key("deepseek")

    if not api_key:
        error_msg = env_manager.create_error_message("deepseek")
        raise ValueError(error_msg)

    config = {
        "model": model_name,
        "temperature": temperature,
        "api_key": api_key,
    }

    base_url = env_manager.get_endpoint("deepseek")
    if base_url:
        config["base_url"] = base_url

    config.update(kwargs)

    logger.info(f"Creating DeepSeek provider with model: {model_name}")
    return ChatDeepSeek(**config)


def _create_watsonx_provider(
    api_key: Optional[str] = None,
    model_name: str = "meta-llama/llama-3-70b-instruct",
    temperature: float = 0.0,
    **kwargs,
) -> Any:
    """Create IBM WatsonX provider"""
    try:
        from langchain_ibm import ChatWatsonx
    except ImportError as e:
        raise ImportError(
            "langchain-ibm not installed. Install with: uv add langchain-ibm"
        ) from e

    if not api_key:
        api_key = env_manager.get_api_key("watsonx")

    if not api_key:
        error_msg = env_manager.create_error_message("watsonx")
        raise ValueError(error_msg)

    provider_config = env_manager.get_provider_config("watsonx")

    config = {
        "model_id": model_name,
        "temperature": temperature,
        "apikey": api_key,
    }

    if "url" in provider_config:
        config["url"] = provider_config["url"]

    if "project_id" in provider_config:
        config["project_id"] = provider_config["project_id"]

    config.update(kwargs)

    logger.info(f"Creating WatsonX provider with model: {model_name}")
    return ChatWatsonx(**config)


# Provider factory mapping
PROVIDER_FACTORIES = {
    "google": _create_google_provider,
    "openai": _create_openai_provider,
    "anthropic": _create_anthropic_provider,
    "mistral": _create_mistral_provider,
    "ollama": _create_ollama_provider,
    "deepseek": _create_deepseek_provider,
    "watsonx": _create_watsonx_provider,
}


def get_llm_model(
    provider: str,
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
    temperature: float = 0.0,
    **kwargs,
) -> Any:
    """
    Get LLM model instance for specified provider

    Args:
        provider: Provider name (google, openai, anthropic, etc.)
        api_key: API key (if not provided, will get from environment)
        model_name: Model name (uses provider default if not specified)
        temperature: Generation temperature (0.0-1.0)
        **kwargs: Additional provider-specific parameters

    Returns:
        LLM model instance

    Raises:
        ValueError: If provider is not supported or configuration is invalid
    """
    if provider not in PROVIDER_FACTORIES:
        supported_providers = ", ".join(PROVIDER_FACTORIES.keys())
        raise ValueError(
            f"Unsupported provider: {provider}. "
            f"Supported providers: {supported_providers}"
        )

    factory = PROVIDER_FACTORIES[provider]

    # Prepare arguments
    factory_kwargs = {"temperature": temperature, **kwargs}

    if api_key:
        factory_kwargs["api_key"] = api_key

    if model_name:
        factory_kwargs["model_name"] = model_name

    try:
        logger.info(f"Creating {provider} provider")
        return factory(**factory_kwargs)
    except Exception as e:
        logger.error(f"Failed to create {provider} provider: {e}")
        raise ValueError(f"Failed to create {provider} provider: {e}") from e


def get_available_providers() -> list[str]:
    """Get list of available LLM providers"""
    return list(PROVIDER_FACTORIES.keys())


def get_configured_providers() -> list[str]:
    """Get list of providers that have valid configuration"""
    return env_manager.get_all_configured_providers()


def validate_provider_config(provider: str) -> bool:
    """Validate that a provider has proper configuration"""
    return env_manager.validate_provider(provider)

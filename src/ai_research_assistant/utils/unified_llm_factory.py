"""
Unified LLM Factory for AI Research Assistant

This module provides a centralized factory for creating LLM instances,
eliminating the duplicate _initialize_llm functions scattered across the codebase.

Following the Factory Pattern and Browser-Use documentation guidelines.
"""

import logging
from typing import TYPE_CHECKING, Any, Dict, Optional

from src.ai_research_assistant.utils import llm_provider
from src.ai_research_assistant.utils.env_manager import EnvironmentManager

if TYPE_CHECKING:
    from src.ai_research_assistant.webui.components.global_settings_panel import (
        GlobalSettingsManager,
    )

logger = logging.getLogger(__name__)


class UnifiedLLMFactory:
    """
    Centralized LLM creation factory following the Factory Pattern.
    This eliminates duplicate LLM initialization code across components.
    """

    def __init__(self):
        self.env_manager = EnvironmentManager()
        self._llm_cache = {}  # Cache for reusing LLM instances

    def create_llm_from_global_settings(
        self, settings_manager: "GlobalSettingsManager", llm_type: str = "primary"
    ) -> Any:
        """
        Create LLM instance from global settings manager.

        Args:
            settings_manager: The global settings manager instance
            llm_type: "primary" or "planner"

        Returns:
            Configured LLM instance ready for use
        """
        if llm_type == "primary":
            config = settings_manager.get_primary_llm_config()
        elif llm_type == "planner":
            config = settings_manager.get_planner_llm_config()
            if config is None:
                # Fall back to primary if planner not enabled
                config = settings_manager.get_primary_llm_config()
        else:
            raise ValueError(f"Unknown LLM type: {llm_type}")

        return self.create_llm_from_config(config)

    def create_llm_from_config(self, config: Dict[str, Any]) -> Any:
        """
        Create LLM instance from configuration dictionary.

        Args:
            config: Dictionary with provider, model_name, temperature, etc.

        Returns:
            Configured LLM instance
        """
        provider = config.get("provider")
        model_name = config.get("model_name")
        temperature = config.get("temperature", 0.7)
        max_tokens = config.get("max_tokens", 2048)
        use_vision = config.get("use_vision", False)

        if not provider or not model_name:
            raise ValueError(
                f"Invalid LLM config: provider={provider}, model_name={model_name}"
            )

        # Create cache key
        cache_key = f"{provider}:{model_name}:{temperature}:{max_tokens}:{use_vision}"

        # Return cached instance if available
        if cache_key in self._llm_cache:
            logger.debug(f"Returning cached LLM: {cache_key}")
            return self._llm_cache[cache_key]

        logger.info(
            f"Creating new LLM: Provider={provider}, Model={model_name}, Temp={temperature}"
        )

        try:
            # Get API key and endpoint from environment
            api_key = self.env_manager.get_api_key(provider)
            endpoint = self.env_manager.get_endpoint(provider)

            # Create LLM using unified provider
            llm = llm_provider.get_llm_model(
                provider=provider,
                api_key=api_key,
                model_name=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
                base_url=endpoint,
            )

            if llm is None:
                raise RuntimeError(f"Failed to create LLM for provider '{provider}'")

            # Cache the instance
            self._llm_cache[cache_key] = llm

            logger.info(f"✅ Successfully created LLM: {provider}:{model_name}")
            return llm

        except Exception as e:
            error_msg = f"Failed to initialize LLM '{model_name}' for provider '{provider}': {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def create_llm_for_browser_agent(
        self,
        provider: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: float = 0.7,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        use_vision: bool = True,
    ) -> Any:
        """
        Create LLM specifically configured for Browser-Use agents.
        Follows Browser-Use documentation patterns.

        Args:
            provider: LLM provider (e.g., "openai", "google")
            model_name: Model name (e.g., "gpt-4", "gemini-2.0-flash-exp")
            temperature: Generation temperature
            base_url: Custom API endpoint
            api_key: Custom API key
            use_vision: Enable vision capabilities

        Returns:
            LLM instance configured for browser automation
        """
        config = {
            "provider": provider,
            "model_name": model_name,
            "temperature": temperature,
            "max_tokens": 8192,  # Larger context for browser tasks
            "use_vision": use_vision,
        }

        # Add custom API settings if provided
        if base_url:
            config["base_url"] = base_url
        if api_key:
            config["api_key"] = api_key

        return self.create_llm_from_config(config)

    def create_llm_for_research_agent(
        self,
        provider: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: float = 0.5,  # Lower temp for research accuracy
    ) -> Any:
        """
        Create LLM optimized for research tasks.

        Args:
            provider: LLM provider
            model_name: Model name
            temperature: Generation temperature (lower for accuracy)

        Returns:
            LLM instance configured for research tasks
        """
        config = {
            "provider": provider,
            "model_name": model_name,
            "temperature": temperature,
            "max_tokens": 4096,  # Good context for research
            "use_vision": False,  # Research typically text-focused
        }

        return self.create_llm_from_config(config)

    def create_llm_for_legal_agent(
        self,
        provider: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: float = 0.3,  # Very low temp for legal accuracy
    ) -> Any:
        """
        Create LLM optimized for legal analysis tasks.

        Args:
            provider: LLM provider
            model_name: Model name
            temperature: Generation temperature (very low for legal accuracy)

        Returns:
            LLM instance configured for legal tasks
        """
        config = {
            "provider": provider,
            "model_name": model_name,
            "temperature": temperature,
            "max_tokens": 8192,  # Large context for legal documents
            "use_vision": False,  # Legal work typically text-focused
        }

        return self.create_llm_from_config(config)

    def validate_provider_config(self, provider: str) -> bool:
        """
        Validate that a provider is properly configured.

        Args:
            provider: Provider name to validate

        Returns:
            True if provider is properly configured
        """
        try:
            return self.env_manager.validate_provider(provider)
        except Exception as e:
            logger.error(f"Provider validation failed for {provider}: {e}")
            return False

    def get_available_providers(self) -> list[str]:
        """
        Get list of properly configured providers.

        Returns:
            List of available provider names
        """
        return self.env_manager.get_all_configured_providers()

    def clear_cache(self) -> None:
        """Clear the LLM instance cache."""
        self._llm_cache.clear()
        logger.info("LLM cache cleared")

    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get information about cached LLM instances.

        Returns:
            Dictionary with cache statistics
        """
        return {
            "cached_instances": len(self._llm_cache),
            "cache_keys": list(self._llm_cache.keys()),
        }


# Global factory instance (Singleton pattern)
_llm_factory = None


def get_llm_factory() -> UnifiedLLMFactory:
    """
    Get the global LLM factory instance (Singleton).

    Returns:
        The unified LLM factory instance
    """
    global _llm_factory
    if _llm_factory is None:
        _llm_factory = UnifiedLLMFactory()
    return _llm_factory


def create_llm_from_settings(
    settings_manager: "GlobalSettingsManager", llm_type: str = "primary"
) -> Any:
    """
    Convenience function to create LLM from global settings.

    Args:
        settings_manager: Global settings manager instance
        llm_type: "primary" or "planner"

    Returns:
        Configured LLM instance
    """
    factory = get_llm_factory()
    return factory.create_llm_from_global_settings(settings_manager, llm_type)


def create_browser_llm(
    provider: Optional[str] = None,
    model_name: Optional[str] = None,
    temperature: float = 0.7,
    **kwargs,
) -> Any:
    """
    Convenience function to create LLM for browser automation.
    Follows Browser-Use documentation guidelines.

    Args:
        provider: LLM provider
        model_name: Model name
        temperature: Generation temperature
        **kwargs: Additional configuration

    Returns:
        LLM instance optimized for browser automation
    """
    factory = get_llm_factory()
    return factory.create_llm_for_browser_agent(
        provider=provider, model_name=model_name, temperature=temperature, **kwargs
    )

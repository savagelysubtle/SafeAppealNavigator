"""
Environment Variable Manager

Centralized management for environment variables with validation and error handling.
Provides standardized API key retrieval and environment setup.
"""

import logging
import os
from typing import Dict, List, Optional

from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class EnvironmentManager:
    """
    Centralized environment variable manager with validation and standardized API key handling.
    """

    # Mapping of provider names to their environment variable names
    PROVIDER_ENV_MAPPING = {
        "openai": {"api_key": "OPENAI_API_KEY", "endpoint": "OPENAI_ENDPOINT"},
        "anthropic": {"api_key": "ANTHROPIC_API_KEY", "endpoint": "ANTHROPIC_ENDPOINT"},
        "google": {
            "api_key": "GOOGLE_API_KEY",
            "project_id": "GOOGLE_PROJECT_ID",
            "endpoint": "GOOGLE_ENDPOINT",
        },
        "azure_openai": {
            "api_key": "AZURE_OPENAI_API_KEY",
            "endpoint": "AZURE_OPENAI_ENDPOINT",
            "api_version": "AZURE_OPENAI_API_VERSION",
        },
        "deepseek": {"api_key": "DEEPSEEK_API_KEY", "endpoint": "DEEPSEEK_ENDPOINT"},
        "mistral": {"api_key": "MISTRAL_API_KEY", "endpoint": "MISTRAL_ENDPOINT"},
        "alibaba": {"api_key": "ALIBABA_API_KEY", "endpoint": "ALIBABA_ENDPOINT"},
        "moonshot": {"api_key": "MOONSHOT_API_KEY", "endpoint": "MOONSHOT_ENDPOINT"},
        "unbound": {"api_key": "UNBOUND_API_KEY", "endpoint": "UNBOUND_ENDPOINT"},
        "siliconflow": {
            "api_key": "SiliconFLOW_API_KEY",
            "endpoint": "SiliconFLOW_ENDPOINT",
        },
        "ibm": {
            "api_key": "IBM_API_KEY",
            "endpoint": "IBM_ENDPOINT",
            "project_id": "IBM_PROJECT_ID",
        },
        "grok": {"api_key": "GROK_API_KEY", "endpoint": "GROK_ENDPOINT"},
        "modelscope": {
            "api_key": "MODELSCOPE_API_KEY",
            "endpoint": "MODELSCOPE_ENDPOINT",
        },
        "ollama": {"endpoint": "OLLAMA_ENDPOINT"},  # Ollama doesn't require API key
    }

    def __init__(self, env_file: str = ".env", validate_required: bool = False):
        """
        Initialize the environment manager.

        Args:
            env_file: Path to the .env file to load
            validate_required: Whether to validate required variables on init
        """
        self.env_file = env_file
        self.load_environment()

        if validate_required:
            self.validate_required_vars()

    def load_environment(self) -> None:
        """Load environment variables from the .env file."""
        try:
            load_dotenv(self.env_file)
            logger.info(f"Successfully loaded environment from {self.env_file}")
        except Exception as e:
            logger.warning(f"Could not load environment from {self.env_file}: {e}")

    def get_api_key(self, provider: str) -> Optional[str]:
        """
        Get API key for a specific provider.

        Args:
            provider: Provider name (e.g., 'openai', 'anthropic', 'google')

        Returns:
            API key string or None if not found

        Raises:
            ValueError: If provider is not supported
        """
        if provider not in self.PROVIDER_ENV_MAPPING:
            raise ValueError(f"Unsupported provider: {provider}")

        env_vars = self.PROVIDER_ENV_MAPPING[provider]
        if "api_key" not in env_vars:
            return None  # Provider doesn't require API key (e.g., Ollama)

        api_key = os.getenv(env_vars["api_key"], "").strip()
        return api_key if api_key else None

    def get_endpoint(self, provider: str) -> Optional[str]:
        """
        Get endpoint URL for a specific provider.

        Args:
            provider: Provider name

        Returns:
            Endpoint URL or None if not found
        """
        if provider not in self.PROVIDER_ENV_MAPPING:
            raise ValueError(f"Unsupported provider: {provider}")

        env_vars = self.PROVIDER_ENV_MAPPING[provider]
        if "endpoint" not in env_vars:
            return None

        endpoint = os.getenv(env_vars["endpoint"], "").strip()
        return endpoint if endpoint else None

    def get_provider_config(self, provider: str) -> Dict[str, Optional[str]]:
        """
        Get all configuration for a provider.

        Args:
            provider: Provider name

        Returns:
            Dictionary with all provider configuration
        """
        if provider not in self.PROVIDER_ENV_MAPPING:
            raise ValueError(f"Unsupported provider: {provider}")

        config = {}
        env_vars = self.PROVIDER_ENV_MAPPING[provider]

        for key, env_var in env_vars.items():
            value = os.getenv(env_var, "").strip()
            config[key] = value if value else None

        return config

    def validate_provider(self, provider: str) -> bool:
        """
        Validate that a provider has its required configuration.

        Args:
            provider: Provider name to validate

        Returns:
            True if provider is properly configured, False otherwise
        """
        try:
            config = self.get_provider_config(provider)

            # For providers that require API keys
            if "api_key" in self.PROVIDER_ENV_MAPPING[provider]:
                if not config.get("api_key"):
                    logger.error(f"Missing API key for provider: {provider}")
                    return False

            # Special validation for specific providers
            if provider == "ibm" and not config.get("project_id"):
                logger.error("Missing project_id for IBM provider")
                return False

            return True

        except Exception as e:
            logger.error(f"Error validating provider {provider}: {e}")
            return False

    def validate_required_vars(
        self, required_providers: Optional[List[str]] = None
    ) -> Dict[str, bool]:
        """
        Validate required environment variables for specified providers.

        Args:
            required_providers: List of providers to validate. If None, validates all.

        Returns:
            Dictionary mapping provider names to their validation status
        """
        if required_providers is None:
            required_providers = list(self.PROVIDER_ENV_MAPPING.keys())

        validation_results = {}

        for provider in required_providers:
            validation_results[provider] = self.validate_provider(provider)

        return validation_results

    def get_browser_config(self) -> Dict[str, Optional[str]]:
        """Get browser-related configuration."""
        return {
            "browser_path": os.getenv("BROWSER_PATH"),
            "browser_user_data": os.getenv("BROWSER_USER_DATA"),
            "browser_cdp": os.getenv("BROWSER_CDP"),
            "browser_wss": os.getenv("BROWSER_WSS"),
            "keep_browser_open": os.getenv("KEEP_BROWSER_OPEN", "true"),
            "use_own_browser": os.getenv("USE_OWN_BROWSER", "false"),
        }

    def get_logging_config(self) -> Dict[str, str]:
        """Get logging-related configuration."""
        return {
            "level": os.getenv("BROWSER_USE_LOGGING_LEVEL", "info"),
            "anonymized_telemetry": os.getenv("ANONYMIZED_TELEMETRY", "false"),
        }

    def get_default_llm(self) -> str:
        """Get the default LLM provider."""
        return os.getenv("DEFAULT_LLM", "openai")

    def get_legal_research_config(self) -> Dict[str, Optional[str]]:
        """Get legal research specific configuration."""
        return {
            "wcat_database_path": os.getenv("WCAT_DATABASE_PATH"),
        }

    def get_all_missing_vars(self) -> List[str]:
        """
        Get a list of all missing required environment variables.

        Returns:
            List of missing environment variable names
        """
        missing_vars = []

        for provider, env_vars in self.PROVIDER_ENV_MAPPING.items():
            for key, env_var in env_vars.items():
                if key == "api_key" and not os.getenv(env_var):
                    missing_vars.append(env_var)

        return missing_vars

    def create_error_message(self, provider: str) -> str:
        """
        Create a user-friendly error message for missing provider configuration.

        Args:
            provider: Provider name

        Returns:
            Formatted error message
        """
        if provider not in self.PROVIDER_ENV_MAPPING:
            return f"Unsupported provider: {provider}"

        env_vars = self.PROVIDER_ENV_MAPPING[provider]

        if "api_key" in env_vars:
            api_key_var = env_vars["api_key"]
            return (
                f"💥 {provider.upper()} API key not found! 🔑\n"
                f"Please set the `{api_key_var}` environment variable in your .env file "
                f"or provide it in the UI."
            )
        else:
            return f"Provider {provider} does not require an API key."


# Global instance for easy access
env_manager = EnvironmentManager()

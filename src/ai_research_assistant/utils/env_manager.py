"""
Environment Management for AI Research Assistant

Provides centralized environment variable management, API key validation,
and configuration handling for all LLM providers and services.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

from ai_research_assistant.config.mcp_config import ServerConfig # MCP Server config model
import json

logger = logging.getLogger(__name__)


class EnvironmentManager:
    """Centralized environment variable management for AI Research Assistant"""

    def __init__(self, env_file: str = ".env"):
        """Initialize environment manager with optional custom .env file"""
        self.env_file = env_file
        self.load_environment()

    # Provider-specific environment variable mappings
    PROVIDER_ENV_MAPPING = {
        "openai": {
            "api_key": "OPENAI_API_KEY",
            "base_url": "OPENAI_BASE_URL",
            "organization": "OPENAI_ORG_ID",
        },
        "anthropic": {"api_key": "ANTHROPIC_API_KEY", "base_url": "ANTHROPIC_BASE_URL"},
        "google": {
            "api_key": "GOOGLE_API_KEY",
            "project_id": "GOOGLE_PROJECT_ID",
            "endpoint": "GOOGLE_ENDPOINT",
        },
        "mistral": {"api_key": "MISTRAL_API_KEY", "endpoint": "MISTRAL_ENDPOINT"},
        "ollama": {"base_url": "OLLAMA_BASE_URL", "host": "OLLAMA_HOST"},
        "deepseek": {"api_key": "DEEPSEEK_API_KEY", "base_url": "DEEPSEEK_BASE_URL"},
        "watsonx": {
            "api_key": "WATSONX_API_KEY",
            "url": "WATSONX_URL",
            "project_id": "WATSONX_PROJECT_ID",
        },
    }

    def load_environment(self) -> None:
        """Load environment variables from .env file"""
        try:
            env_path = Path(self.env_file)
            if env_path.exists():
                load_dotenv(env_path)
                logger.info(f"Loaded environment variables from {self.env_file}")
            else:
                logger.warning(
                    f"Environment file {self.env_file} not found, using system environment"
                )
        except Exception as e:
            logger.error(f"Failed to load environment file {self.env_file}: {e}")

    def get_api_key(self, provider: str) -> Optional[str]:
        """Get API key for specified provider"""
        if provider not in self.PROVIDER_ENV_MAPPING:
            logger.warning(f"Unknown provider: {provider}")
            return None

        provider_config = self.PROVIDER_ENV_MAPPING[provider]
        if "api_key" not in provider_config:
            # Some providers (like Ollama) might not need API keys
            return None

        api_key_var = provider_config["api_key"]
        api_key = os.getenv(api_key_var)

        if api_key:
            logger.debug(f"API key found for {provider}")
        else:
            logger.warning(f"API key not found for {provider} (expected {api_key_var})")

        return api_key

    def get_endpoint(self, provider: str) -> Optional[str]:
        """Get endpoint/base URL for specified provider"""
        if provider not in self.PROVIDER_ENV_MAPPING:
            return None

        provider_config = self.PROVIDER_ENV_MAPPING[provider]

        # Try different endpoint key names based on provider
        endpoint_keys = ["base_url", "endpoint", "url", "host"]

        for key in endpoint_keys:
            if key in provider_config:
                endpoint_var = provider_config[key]
                endpoint = os.getenv(endpoint_var)
                if endpoint:
                    return endpoint

        return None

    def get_provider_config(self, provider: str) -> Dict[str, Any]:
        """Get complete configuration for specified provider"""
        if provider not in self.PROVIDER_ENV_MAPPING:
            logger.warning(f"Unknown provider: {provider}")
            return {}

        provider_config = self.PROVIDER_ENV_MAPPING[provider]
        config = {}

        # Get all configured environment variables for this provider
        for config_key, env_var in provider_config.items():
            value = os.getenv(env_var)
            if value:
                config[config_key] = value

        return config

    def validate_provider(self, provider: str) -> bool:
        """Validate that a provider has required configuration"""
        if provider not in self.PROVIDER_ENV_MAPPING:
            return False

        provider_config = self.PROVIDER_ENV_MAPPING[provider]

        # Check if API key is required and available
        if "api_key" in provider_config:
            api_key = self.get_api_key(provider)
            if not api_key:
                logger.error(f"Required API key missing for {provider}")
                return False

        logger.debug(f"Provider {provider} validation successful")
        return True

    def create_error_message(self, provider: str) -> str:
        """Create user-friendly error message for missing configuration"""
        if provider not in self.PROVIDER_ENV_MAPPING:
            return f"Unknown provider: {provider}"

        provider_config = self.PROVIDER_ENV_MAPPING[provider]

        if "api_key" in provider_config:
            api_key_var = provider_config["api_key"]
            return (
                f"API key not found for {provider.upper()} provider. "
                f"Please set the {api_key_var} environment variable in your .env file."
            )
        else:
            return f"Configuration missing for {provider.upper()} provider."

    def get_browser_config(self) -> Dict[str, Any]:
        """Get browser-specific configuration"""
        return {
            "headless": os.getenv("BROWSER_HEADLESS", "true").lower() == "true",
            "viewport_width": int(os.getenv("BROWSER_VIEWPORT_WIDTH", "1920")),
            "viewport_height": int(os.getenv("BROWSER_VIEWPORT_HEIGHT", "1080")),
            "user_agent": os.getenv("BROWSER_USER_AGENT"),
            "timeout": int(os.getenv("BROWSER_TIMEOUT", "30")),
        }

    def get_legal_research_config(self) -> Dict[str, Any]:
        """Get legal research specific configuration"""
        return {
            "database_path": os.getenv("LEGAL_DATABASE_PATH", "./legal_research_db"),
            "max_document_size_mb": int(os.getenv("LEGAL_MAX_DOC_SIZE_MB", "50")),
            "citation_format": os.getenv("LEGAL_CITATION_FORMAT", "bluebook"),
            "jurisdiction": os.getenv("LEGAL_JURISDICTION", "federal"),
            "wcat_database_path": os.getenv("WCAT_DATABASE_PATH"),
        }

    def get_all_configured_providers(self) -> list[str]:
        """Get list of all providers that have valid configuration"""
        configured_providers = []

        for provider in self.PROVIDER_ENV_MAPPING.keys():
            if self.validate_provider(provider):
                configured_providers.append(provider)

        return configured_providers

    def load_mcp_server_configs(self, mcp_config_path: Optional[Path] = None) -> List[ServerConfig]:
        """Load MCP server configurations from a JSON file."""
        if mcp_config_path is None:
            # Default to project_root/config/mcp_servers.json
            # Assuming env_manager.py is in src/ai_research_assistant/utils/
            # Project root is 3 levels up from this file's parent
            # Project root is 3 levels up from this file's parent (utils -> ai_research_assistant -> src)
            project_root = Path(__file__).resolve().parent.parent.parent
            mcp_config_path = project_root / "src" / "ai_research_assistant" / "config" / "mcp_servers.json"

        if not mcp_config_path.exists():
            logger.warning(f"MCP server configuration file not found: {mcp_config_path}")
            return []

        try:
            with open(mcp_config_path, "r") as f:
                data = json.load(f)
            
            server_configs_data = data.get("mcp_server_configs", [])
            
            parsed_configs = []
            for i, config_data in enumerate(server_configs_data):
                try:
                    parsed_configs.append(ServerConfig(**config_data))
                except Exception as e:
                    logger.error(f"Error parsing MCP server config #{i+1} at {mcp_config_path}: {e}\nData: {config_data}")
            
            logger.info(f"Successfully loaded {len(parsed_configs)} MCP server configurations from {mcp_config_path}")
            return parsed_configs
        except Exception as e:
            logger.error(f"Failed to load or parse MCP server configurations from {mcp_config_path}: {e}")
            return []


# Global environment manager instance
env_manager = EnvironmentManager()

def get_mcp_server_configs(custom_path: Optional[str] = None) -> List[ServerConfig]:
    """Helper function to get loaded MCP server configurations."""
    path_obj = Path(custom_path) if custom_path else None
    return env_manager.load_mcp_server_configs(mcp_config_path=path_obj)

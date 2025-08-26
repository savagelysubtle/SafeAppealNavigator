"""
Test suite for core.env_manager module.

This module contains comprehensive tests for environment variable management,
API key validation, provider configuration, and error handling in the
EnvironmentManager class.
"""

import os
from unittest.mock import Mock, patch

import pytest

from ai_research_assistant.core.env_manager import EnvironmentManager, env_manager


class TestEnvironmentManagerInitialization:
    """Test cases for EnvironmentManager initialization."""

    @patch("ai_research_assistant.core.env_manager.load_dotenv")
    @patch("ai_research_assistant.core.env_manager.Path")
    def test_init_with_default_env_file(self, mock_path, mock_load_dotenv):
        """Test initialization with default .env file."""
        # Setup mocks
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path.return_value = mock_path_instance

        env_mgr = EnvironmentManager()

        assert env_mgr.env_file == ".env"
        mock_load_dotenv.assert_called_once_with(mock_path_instance)

    @patch("ai_research_assistant.core.env_manager.load_dotenv")
    @patch("ai_research_assistant.core.env_manager.Path")
    def test_init_with_custom_env_file(self, mock_path, mock_load_dotenv):
        """Test initialization with custom .env file."""
        # Setup mocks
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path.return_value = mock_path_instance

        custom_file = "custom.env"
        env_mgr = EnvironmentManager(custom_file)

        assert env_mgr.env_file == custom_file
        mock_path.assert_called_with(custom_file)

    @patch("ai_research_assistant.core.env_manager.load_dotenv")
    @patch("ai_research_assistant.core.env_manager.Path")
    def test_init_env_file_not_exists(self, mock_path, mock_load_dotenv, caplog):
        """Test initialization when .env file doesn't exist."""
        # Setup mocks
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = False
        mock_path.return_value = mock_path_instance

        env_mgr = EnvironmentManager()

        # Should not call load_dotenv but should log warning
        mock_load_dotenv.assert_not_called()
        assert any("not found" in record.message for record in caplog.records)

    @patch("ai_research_assistant.core.env_manager.load_dotenv")
    @patch("ai_research_assistant.core.env_manager.Path")
    def test_init_load_dotenv_exception(self, mock_path, mock_load_dotenv, caplog):
        """Test initialization when load_dotenv raises exception."""
        # Setup mocks
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path.return_value = mock_path_instance
        mock_load_dotenv.side_effect = Exception("Load error")

        env_mgr = EnvironmentManager()

        # Should handle exception and log error
        assert any("Failed to load" in record.message for record in caplog.records)


class TestProviderEnvironmentMapping:
    """Test cases for provider environment variable mappings."""

    def test_provider_mapping_completeness(self):
        """Test that all expected providers have environment mappings."""
        env_mgr = EnvironmentManager()

        expected_providers = [
            "openai",
            "anthropic",
            "google",
            "mistral",
            "ollama",
            "deepseek",
            "watsonx",
        ]

        for provider in expected_providers:
            assert provider in env_mgr.PROVIDER_ENV_MAPPING
            assert isinstance(env_mgr.PROVIDER_ENV_MAPPING[provider], dict)

    def test_provider_mapping_structure(self):
        """Test provider mapping structure and expected keys."""
        env_mgr = EnvironmentManager()

        # Test specific provider mappings
        openai_mapping = env_mgr.PROVIDER_ENV_MAPPING["openai"]
        assert "api_key" in openai_mapping
        assert "base_url" in openai_mapping
        assert "organization" in openai_mapping

        google_mapping = env_mgr.PROVIDER_ENV_MAPPING["google"]
        assert "api_key" in google_mapping
        assert "project_id" in google_mapping
        assert "endpoint" in google_mapping

        ollama_mapping = env_mgr.PROVIDER_ENV_MAPPING["ollama"]
        assert "base_url" in ollama_mapping
        assert "host" in ollama_mapping
        # Ollama shouldn't have api_key
        assert "api_key" not in ollama_mapping

    def test_environment_variable_naming_convention(self):
        """Test that environment variable names follow conventions."""
        env_mgr = EnvironmentManager()

        for provider, mapping in env_mgr.PROVIDER_ENV_MAPPING.items():
            for key, env_var in mapping.items():
                # Environment variables should be uppercase
                assert env_var.isupper()
                # Should contain provider name (in most cases)
                assert provider.upper() in env_var or key.upper() in env_var


class TestGetApiKey:
    """Test cases for get_api_key method."""

    def test_get_api_key_valid_provider_with_key(self):
        """Test getting API key for valid provider with key set."""
        env_mgr = EnvironmentManager()

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-openai-key"}):
            api_key = env_mgr.get_api_key("openai")
            assert api_key == "test-openai-key"

    def test_get_api_key_valid_provider_without_key(self, caplog):
        """Test getting API key for valid provider without key set."""
        env_mgr = EnvironmentManager()

        with patch.dict(os.environ, {}, clear=True):
            api_key = env_mgr.get_api_key("openai")
            assert api_key is None
            assert any("not found" in record.message for record in caplog.records)

    def test_get_api_key_invalid_provider(self, caplog):
        """Test getting API key for invalid provider."""
        env_mgr = EnvironmentManager()

        api_key = env_mgr.get_api_key("nonexistent")
        assert api_key is None
        assert any("Unknown provider" in record.message for record in caplog.records)

    def test_get_api_key_provider_without_api_key_field(self):
        """Test getting API key for provider that doesn't use API keys (like Ollama)."""
        env_mgr = EnvironmentManager()

        api_key = env_mgr.get_api_key("ollama")
        assert api_key is None  # Ollama doesn't use API keys

    def test_get_api_key_multiple_providers(self):
        """Test getting API keys for multiple providers."""
        env_mgr = EnvironmentManager()

        test_env = {
            "OPENAI_API_KEY": "openai-key",
            "ANTHROPIC_API_KEY": "anthropic-key",
            "GOOGLE_API_KEY": "google-key",
        }

        with patch.dict(os.environ, test_env):
            assert env_mgr.get_api_key("openai") == "openai-key"
            assert env_mgr.get_api_key("anthropic") == "anthropic-key"
            assert env_mgr.get_api_key("google") == "google-key"


class TestGetEndpoint:
    """Test cases for get_endpoint method."""

    def test_get_endpoint_openai_base_url(self):
        """Test getting endpoint for OpenAI provider."""
        env_mgr = EnvironmentManager()

        with patch.dict(os.environ, {"OPENAI_BASE_URL": "https://api.openai.com/v1"}):
            endpoint = env_mgr.get_endpoint("openai")
            assert endpoint == "https://api.openai.com/v1"

    def test_get_endpoint_google_endpoint(self):
        """Test getting endpoint for Google provider."""
        env_mgr = EnvironmentManager()

        with patch.dict(
            os.environ, {"GOOGLE_ENDPOINT": "https://generativelanguage.googleapis.com"}
        ):
            endpoint = env_mgr.get_endpoint("google")
            assert endpoint == "https://generativelanguage.googleapis.com"

    def test_get_endpoint_ollama_host(self):
        """Test getting endpoint for Ollama provider using host variable."""
        env_mgr = EnvironmentManager()

        with patch.dict(os.environ, {"OLLAMA_HOST": "localhost:11434"}):
            endpoint = env_mgr.get_endpoint("ollama")
            assert endpoint == "localhost:11434"

    def test_get_endpoint_ollama_base_url_priority(self):
        """Test that base_url takes priority over host for Ollama."""
        env_mgr = EnvironmentManager()

        test_env = {
            "OLLAMA_BASE_URL": "http://custom:8080",
            "OLLAMA_HOST": "localhost:11434",
        }

        with patch.dict(os.environ, test_env):
            endpoint = env_mgr.get_endpoint("ollama")
            assert endpoint == "http://custom:8080"

    def test_get_endpoint_invalid_provider(self):
        """Test getting endpoint for invalid provider."""
        env_mgr = EnvironmentManager()

        endpoint = env_mgr.get_endpoint("nonexistent")
        assert endpoint is None

    def test_get_endpoint_no_env_vars_set(self):
        """Test getting endpoint when no environment variables are set."""
        env_mgr = EnvironmentManager()

        with patch.dict(os.environ, {}, clear=True):
            endpoint = env_mgr.get_endpoint("openai")
            assert endpoint is None


class TestGetProviderConfig:
    """Test cases for get_provider_config method."""

    def test_get_provider_config_complete(self):
        """Test getting complete provider configuration."""
        env_mgr = EnvironmentManager()

        test_env = {
            "OPENAI_API_KEY": "test-key",
            "OPENAI_BASE_URL": "https://api.openai.com/v1",
            "OPENAI_ORG_ID": "org-123",
        }

        with patch.dict(os.environ, test_env):
            config = env_mgr.get_provider_config("openai")

            assert config["api_key"] == "test-key"
            assert config["base_url"] == "https://api.openai.com/v1"
            assert config["organization"] == "org-123"

    def test_get_provider_config_partial(self):
        """Test getting partial provider configuration."""
        env_mgr = EnvironmentManager()

        test_env = {
            "OPENAI_API_KEY": "test-key"
            # Missing OPENAI_BASE_URL and OPENAI_ORG_ID
        }

        with patch.dict(os.environ, test_env):
            config = env_mgr.get_provider_config("openai")

            assert config["api_key"] == "test-key"
            assert "base_url" not in config
            assert "organization" not in config

    def test_get_provider_config_invalid_provider(self, caplog):
        """Test getting configuration for invalid provider."""
        env_mgr = EnvironmentManager()

        config = env_mgr.get_provider_config("nonexistent")
        assert config == {}
        assert any("Unknown provider" in record.message for record in caplog.records)

    def test_get_provider_config_empty_env(self):
        """Test getting provider configuration with empty environment."""
        env_mgr = EnvironmentManager()

        with patch.dict(os.environ, {}, clear=True):
            config = env_mgr.get_provider_config("openai")
            assert config == {}


class TestValidateProvider:
    """Test cases for validate_provider method."""

    def test_validate_provider_with_api_key_present(self):
        """Test validating provider with required API key present."""
        env_mgr = EnvironmentManager()

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            is_valid = env_mgr.validate_provider("openai")
            assert is_valid is True

    def test_validate_provider_with_api_key_missing(self, caplog):
        """Test validating provider with required API key missing."""
        env_mgr = EnvironmentManager()

        with patch.dict(os.environ, {}, clear=True):
            is_valid = env_mgr.validate_provider("openai")
            assert is_valid is False
            assert any(
                "Required API key missing" in record.message
                for record in caplog.records
            )

    def test_validate_provider_without_api_key_requirement(self):
        """Test validating provider that doesn't require API key (Ollama)."""
        env_mgr = EnvironmentManager()

        with patch.dict(os.environ, {}, clear=True):
            is_valid = env_mgr.validate_provider("ollama")
            assert is_valid is True

    def test_validate_provider_invalid_provider(self):
        """Test validating invalid provider."""
        env_mgr = EnvironmentManager()

        is_valid = env_mgr.validate_provider("nonexistent")
        assert is_valid is False

    def test_validate_provider_multiple_scenarios(self):
        """Test validating multiple providers in different scenarios."""
        env_mgr = EnvironmentManager()

        test_env = {
            "OPENAI_API_KEY": "openai-key",
            "GOOGLE_API_KEY": "google-key",
            # Missing ANTHROPIC_API_KEY
        }

        with patch.dict(os.environ, test_env):
            assert env_mgr.validate_provider("openai") is True
            assert env_mgr.validate_provider("google") is True
            assert env_mgr.validate_provider("anthropic") is False
            assert env_mgr.validate_provider("ollama") is True  # No API key required


class TestCreateErrorMessage:
    """Test cases for create_error_message method."""

    def test_create_error_message_provider_with_api_key(self):
        """Test creating error message for provider with API key requirement."""
        env_mgr = EnvironmentManager()

        error_msg = env_mgr.create_error_message("openai")
        assert "OPENAI" in error_msg
        assert "OPENAI_API_KEY" in error_msg
        assert ".env file" in error_msg

    def test_create_error_message_provider_without_api_key(self):
        """Test creating error message for provider without API key requirement."""
        env_mgr = EnvironmentManager()

        error_msg = env_mgr.create_error_message("ollama")
        assert "OLLAMA" in error_msg
        assert "Configuration missing" in error_msg

    def test_create_error_message_invalid_provider(self):
        """Test creating error message for invalid provider."""
        env_mgr = EnvironmentManager()

        error_msg = env_mgr.create_error_message("nonexistent")
        assert "Unknown provider: nonexistent" in error_msg

    def test_create_error_message_formatting(self):
        """Test error message formatting and content."""
        env_mgr = EnvironmentManager()

        error_msg = env_mgr.create_error_message("anthropic")

        # Should be user-friendly
        assert len(error_msg) > 20  # Reasonable length
        assert error_msg.endswith(".")  # Proper sentence
        assert "ANTHROPIC" in error_msg.upper()


class TestBrowserConfiguration:
    """Test cases for get_browser_config method."""

    def test_get_browser_config_defaults(self):
        """Test getting browser configuration with defaults."""
        env_mgr = EnvironmentManager()

        with patch.dict(os.environ, {}, clear=True):
            config = env_mgr.get_browser_config()

            assert config["headless"] is True
            assert config["viewport_width"] == 1920
            assert config["viewport_height"] == 1080
            assert config["user_agent"] is None
            assert config["timeout"] == 30

    def test_get_browser_config_custom_values(self):
        """Test getting browser configuration with custom values."""
        env_mgr = EnvironmentManager()

        test_env = {
            "BROWSER_HEADLESS": "false",
            "BROWSER_VIEWPORT_WIDTH": "1024",
            "BROWSER_VIEWPORT_HEIGHT": "768",
            "BROWSER_USER_AGENT": "CustomAgent/1.0",
            "BROWSER_TIMEOUT": "60",
        }

        with patch.dict(os.environ, test_env):
            config = env_mgr.get_browser_config()

            assert config["headless"] is False
            assert config["viewport_width"] == 1024
            assert config["viewport_height"] == 768
            assert config["user_agent"] == "CustomAgent/1.0"
            assert config["timeout"] == 60

    def test_get_browser_config_headless_variations(self):
        """Test browser headless configuration with different values."""
        env_mgr = EnvironmentManager()

        test_cases = [
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("false", False),
            ("False", False),
            ("FALSE", False),
            ("0", False),
            ("1", True),
        ]

        for env_value, expected in test_cases:
            with patch.dict(os.environ, {"BROWSER_HEADLESS": env_value}):
                config = env_mgr.get_browser_config()
                assert config["headless"] is expected

    def test_get_browser_config_invalid_integer_values(self):
        """Test browser configuration with invalid integer values."""
        env_mgr = EnvironmentManager()

        test_env = {
            "BROWSER_VIEWPORT_WIDTH": "invalid",
            "BROWSER_VIEWPORT_HEIGHT": "also_invalid",
            "BROWSER_TIMEOUT": "not_a_number",
        }

        with patch.dict(os.environ, test_env):
            # Should handle ValueError and use defaults
            with pytest.raises(ValueError):
                env_mgr.get_browser_config()


class TestLegalResearchConfiguration:
    """Test cases for get_legal_research_config method."""

    def test_get_legal_research_config_defaults(self):
        """Test getting legal research configuration with defaults."""
        env_mgr = EnvironmentManager()

        with patch.dict(os.environ, {}, clear=True):
            config = env_mgr.get_legal_research_config()

            assert config["database_path"] == "./legal_research_db"
            assert config["max_document_size_mb"] == 50
            assert config["citation_format"] == "bluebook"
            assert config["jurisdiction"] == "federal"
            assert config["wcat_database_path"] is None

    def test_get_legal_research_config_custom_values(self):
        """Test getting legal research configuration with custom values."""
        env_mgr = EnvironmentManager()

        test_env = {
            "LEGAL_DATABASE_PATH": "/custom/legal/db",
            "LEGAL_MAX_DOC_SIZE_MB": "100",
            "LEGAL_CITATION_FORMAT": "chicago",
            "LEGAL_JURISDICTION": "provincial",
            "WCAT_DATABASE_PATH": "/path/to/wcat/db",
        }

        with patch.dict(os.environ, test_env):
            config = env_mgr.get_legal_research_config()

            assert config["database_path"] == "/custom/legal/db"
            assert config["max_document_size_mb"] == 100
            assert config["citation_format"] == "chicago"
            assert config["jurisdiction"] == "provincial"
            assert config["wcat_database_path"] == "/path/to/wcat/db"

    def test_get_legal_research_config_invalid_integer(self):
        """Test legal research configuration with invalid integer value."""
        env_mgr = EnvironmentManager()

        test_env = {"LEGAL_MAX_DOC_SIZE_MB": "not_a_number"}

        with patch.dict(os.environ, test_env):
            with pytest.raises(ValueError):
                env_mgr.get_legal_research_config()


class TestGetAllConfiguredProviders:
    """Test cases for get_all_configured_providers method."""

    def test_get_all_configured_providers_none_configured(self):
        """Test getting all configured providers when none are configured."""
        env_mgr = EnvironmentManager()

        with patch.dict(os.environ, {}, clear=True):
            providers = env_mgr.get_all_configured_providers()

            # Should only include providers that don't require API keys
            assert "ollama" in providers
            assert "openai" not in providers
            assert "anthropic" not in providers
            assert "google" not in providers

    def test_get_all_configured_providers_some_configured(self):
        """Test getting all configured providers when some are configured."""
        env_mgr = EnvironmentManager()

        test_env = {
            "OPENAI_API_KEY": "openai-key",
            "GOOGLE_API_KEY": "google-key",
            # Missing ANTHROPIC_API_KEY, MISTRAL_API_KEY, etc.
        }

        with patch.dict(os.environ, test_env):
            providers = env_mgr.get_all_configured_providers()

            assert "openai" in providers
            assert "google" in providers
            assert "ollama" in providers  # No API key required
            assert "anthropic" not in providers  # Missing API key
            assert "mistral" not in providers  # Missing API key

    def test_get_all_configured_providers_all_configured(self):
        """Test getting all configured providers when all are configured."""
        env_mgr = EnvironmentManager()

        test_env = {
            "OPENAI_API_KEY": "openai-key",
            "ANTHROPIC_API_KEY": "anthropic-key",
            "GOOGLE_API_KEY": "google-key",
            "MISTRAL_API_KEY": "mistral-key",
            "DEEPSEEK_API_KEY": "deepseek-key",
            "WATSONX_API_KEY": "watsonx-key",
        }

        with patch.dict(os.environ, test_env):
            providers = env_mgr.get_all_configured_providers()

            expected_providers = [
                "openai",
                "anthropic",
                "google",
                "mistral",
                "ollama",
                "deepseek",
                "watsonx",
            ]

            for provider in expected_providers:
                assert provider in providers

    def test_get_all_configured_providers_return_type(self):
        """Test that get_all_configured_providers returns correct type."""
        env_mgr = EnvironmentManager()

        providers = env_mgr.get_all_configured_providers()
        assert isinstance(providers, list)

        # All items should be strings
        for provider in providers:
            assert isinstance(provider, str)
            assert len(provider) > 0


class TestGlobalEnvironmentManagerInstance:
    """Test cases for the global env_manager instance."""

    def test_global_env_manager_instance_exists(self):
        """Test that global env_manager instance exists."""
        assert env_manager is not None
        assert isinstance(env_manager, EnvironmentManager)

    def test_global_env_manager_functionality(self):
        """Test that global env_manager instance is functional."""
        # Should be able to call methods without errors
        providers = env_manager.get_all_configured_providers()
        assert isinstance(providers, list)

        # Should handle invalid provider gracefully
        api_key = env_manager.get_api_key("nonexistent")
        assert api_key is None

    def test_global_env_manager_is_singleton(self):
        """Test that global env_manager behaves like a singleton."""
        # Multiple imports should reference the same instance
        from ai_research_assistant.core.env_manager import env_manager as env_mgr2

        assert env_manager is env_mgr2


class TestEnvironmentManagerEdgeCases:
    """Test cases for edge cases and error scenarios."""

    def test_env_file_with_special_characters(self):
        """Test env file path with special characters."""
        special_path = "test-env.local"

        with patch("ai_research_assistant.core.env_manager.load_dotenv") as mock_load:
            with patch("ai_research_assistant.core.env_manager.Path") as mock_path:
                mock_path_instance = Mock()
                mock_path_instance.exists.return_value = True
                mock_path.return_value = mock_path_instance

                env_mgr = EnvironmentManager(special_path)
                assert env_mgr.env_file == special_path

    def test_empty_environment_variables(self):
        """Test handling of empty environment variables."""
        env_mgr = EnvironmentManager()

        test_env = {
            "OPENAI_API_KEY": "",  # Empty string
            "OPENAI_BASE_URL": "   ",  # Whitespace
        }

        with patch.dict(os.environ, test_env):
            config = env_mgr.get_provider_config("openai")

            # Empty strings should still be included
            assert "api_key" in config
            assert config["api_key"] == ""
            assert "base_url" in config
            assert config["base_url"] == "   "

    def test_case_sensitivity_of_environment_variables(self):
        """Test that environment variable lookup is case-sensitive."""
        env_mgr = EnvironmentManager()

        test_env = {
            "openai_api_key": "lowercase-key",  # Wrong case
            "OPENAI_API_KEY": "correct-key",  # Correct case
        }

        with patch.dict(os.environ, test_env):
            api_key = env_mgr.get_api_key("openai")
            assert api_key == "correct-key"  # Should use correct case

    @patch("ai_research_assistant.core.env_manager.logger")
    def test_logging_calls(self, mock_logger):
        """Test that appropriate logging calls are made."""
        env_mgr = EnvironmentManager()

        # Test successful API key retrieval
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            env_mgr.get_api_key("openai")
            mock_logger.debug.assert_called()

        # Test missing API key
        with patch.dict(os.environ, {}, clear=True):
            env_mgr.get_api_key("openai")
            mock_logger.warning.assert_called()

    def test_provider_config_with_none_values(self):
        """Test provider configuration handling of None values."""
        env_mgr = EnvironmentManager()

        # Mock os.getenv to return None for some values
        with patch("os.getenv") as mock_getenv:

            def side_effect(var_name, default=None):
                if var_name == "OPENAI_API_KEY":
                    return "test-key"
                return None

            mock_getenv.side_effect = side_effect

            config = env_mgr.get_provider_config("openai")

            # Should only include non-None values
            assert "api_key" in config
            assert config["api_key"] == "test-key"
            assert "base_url" not in config
            assert "organization" not in config

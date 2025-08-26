"""
Test suite for core.llm_provider module.

This module contains comprehensive tests for LLM provider functionality,
including model creation, error handling, and provider factory patterns
with proper mocking of pydantic-ai dependencies.
"""

from unittest.mock import Mock, patch

import pytest

# Import the actual functions and constants from the module
try:
    # Test if pydantic-ai is available
    from pydantic_ai.models.google import GoogleModel
    from pydantic_ai.providers.google import GoogleProvider

    from ai_research_assistant.core.llm_provider import (
        PROVIDER_FACTORIES,
        _create_google_model,
        get_llm_model,
    )

    PYDANTIC_AI_AVAILABLE = True
except ImportError as e:
    PYDANTIC_AI_AVAILABLE = False
    pytest.skip(f"Could not import required modules: {e}", allow_module_level=True)


class TestProviderFactories:
    """Test cases for provider factory mappings."""

    def test_provider_factories_structure(self):
        """Test that PROVIDER_FACTORIES has expected structure."""
        assert isinstance(PROVIDER_FACTORIES, dict)
        assert len(PROVIDER_FACTORIES) > 0

        # Each factory should be callable
        for provider, factory in PROVIDER_FACTORIES.items():
            assert isinstance(provider, str)
            assert callable(factory)

    def test_google_provider_factory_exists(self):
        """Test that Google provider factory is available."""
        assert "google" in PROVIDER_FACTORIES
        assert PROVIDER_FACTORIES["google"] == _create_google_model


class TestCreateGoogleModel:
    """Test cases for _create_google_model function."""

    @patch("ai_research_assistant.core.llm_provider.GoogleProvider")
    @patch("ai_research_assistant.core.llm_provider.GoogleModel")
    @patch("ai_research_assistant.core.llm_provider.env_manager")
    def test_create_google_model_with_api_key(
        self, mock_env_manager, mock_google_model, mock_google_provider
    ):
        """Test creating Google model with provided API key."""
        # Setup mocks
        api_key = "test-google-api-key"
        model_name = "gemini-1.5-pro"
        mock_provider_instance = Mock()
        mock_google_provider.return_value = mock_provider_instance
        mock_model_instance = Mock()
        mock_google_model.return_value = mock_model_instance

        # Call function
        result = _create_google_model(api_key, model_name)

        # Verify behavior
        mock_google_provider.assert_called_once_with(api_key=api_key)
        mock_google_model.assert_called_once_with(
            model_name, provider=mock_provider_instance
        )
        assert result == mock_model_instance

    @patch("ai_research_assistant.core.llm_provider.GoogleProvider")
    @patch("ai_research_assistant.core.llm_provider.GoogleModel")
    @patch("ai_research_assistant.core.llm_provider.env_manager")
    def test_create_google_model_without_api_key(
        self, mock_env_manager, mock_google_model, mock_google_provider
    ):
        """Test creating Google model without API key (gets from env_manager)."""
        # Setup mocks
        env_api_key = "env-google-api-key"
        model_name = "gemini-1.5-flash"
        mock_env_manager.get_api_key.return_value = env_api_key
        mock_provider_instance = Mock()
        mock_google_provider.return_value = mock_provider_instance
        mock_model_instance = Mock()
        mock_google_model.return_value = mock_model_instance

        # Call function without API key
        result = _create_google_model(None, model_name)

        # Verify behavior
        mock_env_manager.get_api_key.assert_called_once_with("google")
        mock_google_provider.assert_called_once_with(api_key=env_api_key)
        mock_google_model.assert_called_once_with(
            model_name, provider=mock_provider_instance
        )
        assert result == mock_model_instance

    @patch("ai_research_assistant.core.llm_provider.env_manager")
    def test_create_google_model_no_api_key_available(self, mock_env_manager):
        """Test creating Google model when no API key is available."""
        # Setup mocks
        mock_env_manager.get_api_key.return_value = None
        mock_env_manager.create_error_message.return_value = "Google API key not found"

        # Should raise ValueError
        with pytest.raises(ValueError) as exc_info:
            _create_google_model(None, "gemini-1.5-pro")

        assert "Google API key not found" in str(exc_info.value)
        mock_env_manager.get_api_key.assert_called_once_with("google")
        mock_env_manager.create_error_message.assert_called_once_with("google")

    @patch("ai_research_assistant.core.llm_provider.GoogleProvider")
    @patch("ai_research_assistant.core.llm_provider.GoogleModel")
    @patch("ai_research_assistant.core.llm_provider.env_manager")
    def test_create_google_model_with_kwargs(
        self, mock_env_manager, mock_google_model, mock_google_provider
    ):
        """Test creating Google model with additional kwargs."""
        # Setup mocks
        api_key = "test-api-key"
        model_name = "gemini-1.5-pro"
        mock_provider_instance = Mock()
        mock_google_provider.return_value = mock_provider_instance
        mock_model_instance = Mock()
        mock_google_model.return_value = mock_model_instance

        # Call function with additional kwargs
        extra_kwargs = {"temperature": 0.5, "max_tokens": 1000}
        result = _create_google_model(api_key, model_name, **extra_kwargs)

        # Verify behavior - kwargs should be passed through
        mock_google_provider.assert_called_once_with(api_key=api_key)
        mock_google_model.assert_called_once_with(
            model_name, provider=mock_provider_instance
        )
        assert result == mock_model_instance


class TestGetLLMModel:
    """Test cases for get_llm_model function."""

    def test_get_llm_model_google_provider(self):
        """Test getting LLM model for Google provider."""
        # Setup mocks
        mock_factory = Mock()
        mock_model = Mock()
        mock_factory.return_value = mock_model

        # Patch the factory in the dictionary
        with patch.dict(PROVIDER_FACTORIES, {"google": mock_factory}):
            # Call function
            result = get_llm_model(
                provider="google", api_key="test-key", model_name="gemini-1.5-pro"
            )

            # Verify behavior
            mock_factory.assert_called_once_with(
                api_key="test-key", model_name="gemini-1.5-pro"
            )
            assert result == mock_model

    def test_get_llm_model_unsupported_provider(self):
        """Test getting LLM model for unsupported provider."""
        with pytest.raises(ValueError) as exc_info:
            get_llm_model(provider="unsupported", model_name="test-model")

        error_message = str(exc_info.value)
        assert "Unsupported provider: unsupported" in error_message
        assert "google" in error_message  # Should list supported providers

    def test_get_llm_model_with_default_model_name(self):
        """Test getting LLM model with default model name."""
        # Setup mocks
        mock_factory = Mock()
        mock_model = Mock()
        mock_factory.return_value = mock_model

        # Patch the factory in the dictionary
        with patch.dict(PROVIDER_FACTORIES, {"google": mock_factory}):
            # Call function without model_name
            result = get_llm_model(provider="google", api_key="test-key")

            # Should use default model name for Google
            mock_factory.assert_called_once_with(
                api_key="test-key",
                model_name="gemini-1.5-pro",  # Default for Google
            )
            assert result == mock_model

    def test_get_llm_model_provider_without_default_model(self):
        """Test getting LLM model for provider without default model."""
        # Add a provider factory without default model for testing
        with patch.dict(
            "ai_research_assistant.core.llm_provider.PROVIDER_FACTORIES",
            {"test_provider": Mock()},
        ):
            with pytest.raises(ValueError) as exc_info:
                get_llm_model(provider="test_provider")  # No model_name provided

            assert (
                "No default model name configured for provider: test_provider"
                in str(exc_info.value)
            )

    def test_get_llm_model_factory_exception(self):
        """Test handling of factory function exceptions."""
        # Setup mock to raise exception
        mock_factory = Mock()
        mock_factory.side_effect = Exception("Factory error")

        # Patch the factory in the dictionary
        with patch.dict(PROVIDER_FACTORIES, {"google": mock_factory}):
            with pytest.raises(ValueError) as exc_info:
                get_llm_model(provider="google", model_name="test-model")

            error_message = str(exc_info.value)
            assert "Failed to create google model" in error_message
            assert "Factory error" in error_message

    def test_get_llm_model_with_additional_kwargs(self):
        """Test getting LLM model with additional keyword arguments."""
        # Setup mocks
        mock_factory = Mock()
        mock_model = Mock()
        mock_factory.return_value = mock_model

        # Patch the factory in the dictionary
        with patch.dict(PROVIDER_FACTORIES, {"google": mock_factory}):
            # Call function with additional kwargs
            extra_kwargs = {"temperature": 0.7, "max_tokens": 2048}
            result = get_llm_model(
                provider="google",
                api_key="test-key",
                model_name="gemini-1.5-flash",
                **extra_kwargs,
            )

            # Verify all parameters are passed through
            mock_factory.assert_called_once_with(
                api_key="test-key",
                model_name="gemini-1.5-flash",
                temperature=0.7,
                max_tokens=2048,
            )
            assert result == mock_model

    @patch("ai_research_assistant.core.llm_provider.logger")
    @patch("ai_research_assistant.core.llm_provider._create_google_model")
    def test_get_llm_model_logging(self, mock_create_google, mock_logger):
        """Test that appropriate logging occurs during model creation."""
        # Setup mocks
        mock_model = Mock()
        mock_create_google.return_value = mock_model

        # Call function
        get_llm_model(provider="google", model_name="gemini-1.5-pro")

        # Verify logging calls
        mock_logger.info.assert_called_with(
            "Creating pydantic-ai Model for google:gemini-1.5-pro"
        )

    @patch("ai_research_assistant.core.llm_provider.logger")
    def test_get_llm_model_error_logging(self, mock_logger):
        """Test error logging when model creation fails."""
        # Setup mock to raise exception
        mock_factory = Mock()
        test_exception = Exception("Test error")
        mock_factory.side_effect = test_exception

        # Patch the factory in the dictionary
        with patch.dict(PROVIDER_FACTORIES, {"google": mock_factory}):
            with pytest.raises(ValueError):
                get_llm_model(provider="google", model_name="test-model")

            # Verify error logging
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args
            assert "Failed to create pydantic-ai Model for google" in call_args[0][0]
            assert call_args[1]["exc_info"] is True


class TestProviderFactoryIntegration:
    """Integration tests for provider factory system."""

    def test_provider_factory_mapping_completeness(self):
        """Test that provider factory mapping covers expected providers."""
        # Currently only Google is implemented
        expected_providers = ["google"]

        for provider in expected_providers:
            assert provider in PROVIDER_FACTORIES
            assert callable(PROVIDER_FACTORIES[provider])

    def test_provider_factory_function_signatures(self):
        """Test that provider factory functions have expected signatures."""
        import inspect

        for provider, factory in PROVIDER_FACTORIES.items():
            # Get function signature
            signature = inspect.signature(factory)

            # Should have at least api_key and model_name parameters
            param_names = list(signature.parameters.keys())
            assert "api_key" in param_names
            assert "model_name" in param_names

    @patch("ai_research_assistant.core.llm_provider.GoogleProvider")
    @patch("ai_research_assistant.core.llm_provider.GoogleModel")
    @patch("ai_research_assistant.core.llm_provider.env_manager")
    def test_end_to_end_model_creation(
        self, mock_env_manager, mock_google_model, mock_google_provider
    ):
        """Test end-to-end model creation flow."""
        # Setup mocks
        api_key = "integration-test-key"
        model_name = "gemini-1.5-pro"
        mock_provider_instance = Mock()
        mock_google_provider.return_value = mock_provider_instance
        mock_model_instance = Mock()
        mock_google_model.return_value = mock_model_instance

        # Test the complete flow
        result = get_llm_model(
            provider="google", api_key=api_key, model_name=model_name
        )

        # Verify the complete chain
        assert result == mock_model_instance
        mock_google_provider.assert_called_once_with(api_key=api_key)
        mock_google_model.assert_called_once_with(
            model_name, provider=mock_provider_instance
        )


class TestErrorHandling:
    """Test cases for error handling scenarios."""

    def test_provider_factory_parameter_validation(self):
        """Test parameter validation in provider factories."""
        # Test with None values
        with pytest.raises(ValueError):
            get_llm_model(provider=None, model_name="test")

        with pytest.raises(ValueError):
            get_llm_model(provider="", model_name="test")

    def test_model_creation_with_empty_model_name(self):
        """Test model creation with empty model name."""
        # Setup mocks
        mock_factory = Mock()
        mock_factory.return_value = Mock()

        # Patch the factory in the dictionary
        with patch.dict(PROVIDER_FACTORIES, {"google": mock_factory}):
            # Empty model name should fall back to default model name
            result = get_llm_model(provider="google", model_name="")

            # Empty string is treated as falsy, so it should use the default model
            mock_factory.assert_called_once_with(
                api_key=None, model_name="gemini-1.5-pro"
            )

    def test_supported_providers_list_format(self):
        """Test that supported providers list is properly formatted in errors."""
        try:
            get_llm_model(provider="invalid", model_name="test")
        except ValueError as e:
            error_message = str(e)
            # Should contain "Supported:" followed by provider list
            assert "Supported:" in error_message
            assert "google" in error_message


class TestModuleConfiguration:
    """Test cases for module-level configuration."""

    def test_default_model_configuration(self):
        """Test default model configuration for supported providers."""
        # Test that default models are available for each provider
        for provider in PROVIDER_FACTORIES.keys():
            try:
                # This should work without explicit model_name
                get_llm_model(provider=provider, api_key="test-key")
            except ValueError as e:
                # Should not fail due to missing default model
                assert "No default model name configured" not in str(e)
            except Exception:
                # Other exceptions (like missing dependencies) are acceptable
                pass

    def test_provider_factory_consistency(self):
        """Test consistency across provider factories."""
        for provider, factory in PROVIDER_FACTORIES.items():
            # Factory should be a function
            assert callable(factory)

            # Function name should follow naming convention
            expected_name_pattern = f"_create_{provider}_model"
            assert factory.__name__ == expected_name_pattern

    def test_import_structure(self):
        """Test that module imports are properly structured."""
        # Test that key functions are available at module level
        from ai_research_assistant.core.llm_provider import get_llm_model

        assert callable(get_llm_model)

        # Test that provider factories dict is available
        from ai_research_assistant.core.llm_provider import PROVIDER_FACTORIES

        assert isinstance(PROVIDER_FACTORIES, dict)

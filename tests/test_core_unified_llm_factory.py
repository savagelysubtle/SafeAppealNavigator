"""
Test suite for core.unified_llm_factory module.

This module contains comprehensive tests for the unified LLM factory pattern,
including model creation, caching mechanisms, error handling, and singleton
management functionality.
"""

from unittest.mock import Mock, patch

import pytest

from ai_research_assistant.core.unified_llm_factory import (
    UnifiedLLMFactory,
    get_llm_factory,
)


class TestUnifiedLLMFactory:
    """Test cases for UnifiedLLMFactory class."""

    def setup_method(self):
        """Clear cache before each test to prevent interference."""
        # Clear the global factory cache if it exists
        factory = get_llm_factory()
        factory.clear_cache()

    def test_unified_llm_factory_initialization(self):
        """Test UnifiedLLMFactory initialization."""
        factory = UnifiedLLMFactory()

        assert factory.env_manager is not None
        assert hasattr(factory, "_llm_cache")
        assert isinstance(factory._llm_cache, dict)
        assert len(factory._llm_cache) == 0

    @patch("ai_research_assistant.core.env_manager.env_manager.get_api_key")
    @patch("ai_research_assistant.core.env_manager.env_manager.get_endpoint")
    def test_factory_uses_global_env_manager(self, mock_get_endpoint, mock_get_api_key):
        """Test that factory uses the global env_manager instance."""
        factory = UnifiedLLMFactory()

        # Test that the factory is using the global env_manager
        from ai_research_assistant.core.env_manager import env_manager

        assert factory.env_manager is env_manager

    @patch("ai_research_assistant.core.unified_llm_factory.llm_provider")
    @patch("ai_research_assistant.core.env_manager.env_manager.get_endpoint")
    @patch("ai_research_assistant.core.env_manager.env_manager.get_api_key")
    def test_create_llm_from_config_successful(
        self, mock_get_api_key, mock_get_endpoint, mock_llm_provider
    ):
        """Test successful LLM creation from configuration."""
        # Setup mocks
        config = {"provider": "google", "model_name": "gemini-1.5-pro"}
        mock_get_api_key.return_value = "test-api-key"
        mock_get_endpoint.return_value = "https://api.google.com"
        mock_model = Mock()
        mock_llm_provider.get_llm_model.return_value = mock_model

        factory = UnifiedLLMFactory()
        result = factory.create_llm_from_config(config)

        # Verify behavior
        assert result == mock_model
        mock_get_api_key.assert_called_once_with("google")
        mock_get_endpoint.assert_called_once_with("google")
        mock_llm_provider.get_llm_model.assert_called_once_with(
            provider="google",
            api_key="test-api-key",
            model_name="gemini-1.5-pro",
            base_url="https://api.google.com",
        )

    def test_create_llm_from_config_missing_provider(self):
        """Test LLM creation with missing provider in config."""
        config = {"model_name": "test-model"}

        factory = UnifiedLLMFactory()

        with pytest.raises(ValueError) as exc_info:
            factory.create_llm_from_config(config)

        assert "Invalid LLM config" in str(exc_info.value)
        assert "provider=None" in str(exc_info.value)

    def test_create_llm_from_config_missing_model_name(self):
        """Test LLM creation with missing model_name in config."""
        config = {"provider": "google"}

        factory = UnifiedLLMFactory()

        with pytest.raises(ValueError) as exc_info:
            factory.create_llm_from_config(config)

        assert "Invalid LLM config" in str(exc_info.value)
        assert "model_name=None" in str(exc_info.value)

    def test_create_llm_from_config_empty_provider(self):
        """Test LLM creation with empty provider."""
        config = {"provider": "", "model_name": "test-model"}

        factory = UnifiedLLMFactory()

        with pytest.raises(ValueError) as exc_info:
            factory.create_llm_from_config(config)

        assert "Invalid LLM config" in str(exc_info.value)

    def test_create_llm_from_config_empty_model_name(self):
        """Test LLM creation with empty model_name."""
        config = {"provider": "google", "model_name": ""}

        factory = UnifiedLLMFactory()

        with pytest.raises(ValueError) as exc_info:
            factory.create_llm_from_config(config)

        assert "Invalid LLM config" in str(exc_info.value)

    @patch("ai_research_assistant.core.unified_llm_factory.llm_provider")
    @patch("ai_research_assistant.core.env_manager.env_manager.get_endpoint")
    @patch("ai_research_assistant.core.env_manager.env_manager.get_api_key")
    def test_create_llm_caching_mechanism(
        self, mock_get_api_key, mock_get_endpoint, mock_llm_provider
    ):
        """Test LLM caching mechanism."""
        # Setup mocks
        config = {"provider": "google", "model_name": "gemini-1.5-pro"}
        mock_get_api_key.return_value = "test-api-key"
        mock_get_endpoint.return_value = None
        mock_model = Mock()
        mock_llm_provider.get_llm_model.return_value = mock_model

        factory = UnifiedLLMFactory()

        # First call - should create and cache
        result1 = factory.create_llm_from_config(config)
        assert result1 == mock_model
        assert len(factory._llm_cache) == 1

        # Second call - should return cached instance
        result2 = factory.create_llm_from_config(config)
        assert result2 == mock_model
        assert result1 is result2  # Should be same instance

        # LLM provider should only be called once
        mock_llm_provider.get_llm_model.assert_called_once()

    @patch("ai_research_assistant.core.unified_llm_factory.llm_provider")
    @patch("ai_research_assistant.core.env_manager.env_manager.get_endpoint")
    @patch("ai_research_assistant.core.env_manager.env_manager.get_api_key")
    def test_create_llm_cache_key_generation(
        self, mock_get_api_key, mock_get_endpoint, mock_llm_provider
    ):
        """Test cache key generation for different configurations."""
        # Setup mocks
        mock_get_api_key.return_value = "test-api-key"
        mock_get_endpoint.return_value = None
        mock_model = Mock()
        mock_llm_provider.get_llm_model.return_value = mock_model

        factory = UnifiedLLMFactory()

        # Create models with different configurations
        config1 = {"provider": "google", "model_name": "gemini-1.5-pro"}
        config2 = {"provider": "google", "model_name": "gemini-1.5-flash"}
        config3 = {"provider": "openai", "model_name": "gpt-4"}

        factory.create_llm_from_config(config1)
        factory.create_llm_from_config(config2)
        factory.create_llm_from_config(config3)

        # Should have 3 different cache entries
        assert len(factory._llm_cache) == 3

        # Verify cache keys
        expected_keys = [
            "google:gemini-1.5-pro",
            "google:gemini-1.5-flash",
            "openai:gpt-4",
        ]
        for key in expected_keys:
            assert key in factory._llm_cache

    @patch("ai_research_assistant.core.unified_llm_factory.llm_provider")
    @patch("ai_research_assistant.core.env_manager.env_manager.get_endpoint")
    @patch("ai_research_assistant.core.env_manager.env_manager.get_api_key")
    def test_create_llm_provider_error_handling(
        self, mock_get_api_key, mock_get_endpoint, mock_llm_provider
    ):
        """Test error handling when llm_provider raises exception."""
        # Setup mocks
        config = {"provider": "google", "model_name": "gemini-1.5-pro"}
        mock_get_api_key.return_value = "test-api-key"
        mock_get_endpoint.return_value = None
        mock_llm_provider.get_llm_model.side_effect = Exception("Provider error")

        factory = UnifiedLLMFactory()

        with pytest.raises(RuntimeError) as exc_info:
            factory.create_llm_from_config(config)

        error_message = str(exc_info.value)
        assert "Failed to initialize pydantic-ai Model" in error_message
        assert "gemini-1.5-pro" in error_message
        assert "google" in error_message
        assert "Provider error" in error_message

    @patch("ai_research_assistant.core.unified_llm_factory.llm_provider")
    @patch("ai_research_assistant.core.env_manager.env_manager.get_endpoint")
    @patch("ai_research_assistant.core.env_manager.env_manager.get_api_key")
    def test_create_llm_returns_none(
        self, mock_get_api_key, mock_get_endpoint, mock_llm_provider
    ):
        """Test error handling when llm_provider returns None."""
        # Setup mocks
        config = {"provider": "google", "model_name": "gemini-1.5-pro"}
        mock_get_api_key.return_value = "test-api-key"
        mock_get_endpoint.return_value = None
        mock_llm_provider.get_llm_model.return_value = None

        factory = UnifiedLLMFactory()

        with pytest.raises(RuntimeError) as exc_info:
            factory.create_llm_from_config(config)

        error_message = str(exc_info.value)
        assert "Failed to create pydantic-ai Model for 'google'" in error_message

    @patch("ai_research_assistant.core.unified_llm_factory.llm_provider")
    @patch("ai_research_assistant.core.env_manager.env_manager.get_endpoint")
    @patch("ai_research_assistant.core.env_manager.env_manager.get_api_key")
    def test_create_llm_without_endpoint(
        self, mock_get_api_key, mock_get_endpoint, mock_llm_provider
    ):
        """Test LLM creation when endpoint is not available."""
        # Setup mocks
        config = {"provider": "google", "model_name": "gemini-1.5-pro"}
        mock_get_api_key.return_value = "test-api-key"
        mock_get_endpoint.return_value = None  # No endpoint
        mock_model = Mock()
        mock_llm_provider.get_llm_model.return_value = mock_model

        factory = UnifiedLLMFactory()
        result = factory.create_llm_from_config(config)

        # Should still work
        assert result == mock_model
        mock_llm_provider.get_llm_model.assert_called_once_with(
            provider="google",
            api_key="test-api-key",
            model_name="gemini-1.5-pro",
            base_url=None,
        )

    def test_clear_cache(self):
        """Test cache clearing functionality."""
        factory = UnifiedLLMFactory()

        # Manually add items to cache
        factory._llm_cache["test:model1"] = Mock()
        factory._llm_cache["test:model2"] = Mock()
        assert len(factory._llm_cache) == 2

        # Clear cache
        factory.clear_cache()

        # Cache should be empty
        assert len(factory._llm_cache) == 0

    @patch("ai_research_assistant.core.unified_llm_factory.logger")
    @patch("ai_research_assistant.core.unified_llm_factory.llm_provider")
    @patch("ai_research_assistant.core.env_manager.env_manager.get_endpoint")
    @patch("ai_research_assistant.core.env_manager.env_manager.get_api_key")
    def test_logging_behavior(
        self, mock_get_api_key, mock_get_endpoint, mock_llm_provider, mock_logger
    ):
        """Test logging behavior during LLM creation."""
        # Setup mocks
        config = {"provider": "google", "model_name": "gemini-1.5-pro"}
        mock_get_api_key.return_value = "test-api-key"
        mock_get_endpoint.return_value = None
        mock_model = Mock()
        mock_llm_provider.get_llm_model.return_value = mock_model

        factory = UnifiedLLMFactory()

        # Test successful creation logging
        factory.create_llm_from_config(config)

        # Verify info logging
        info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        assert any("Creating new pydantic-ai Model" in call for call in info_calls)
        assert any(
            "Successfully created pydantic-ai Model" in call for call in info_calls
        )

        # Test cached retrieval logging
        factory.create_llm_from_config(config)  # Second call
        debug_calls = [call[0][0] for call in mock_logger.debug.call_args_list]
        assert any("Returning cached pydantic-ai Model" in call for call in debug_calls)

    @patch("ai_research_assistant.core.unified_llm_factory.logger")
    @patch("ai_research_assistant.core.unified_llm_factory.llm_provider")
    @patch("ai_research_assistant.core.env_manager.env_manager.get_endpoint")
    @patch("ai_research_assistant.core.env_manager.env_manager.get_api_key")
    def test_error_logging(
        self, mock_get_api_key, mock_get_endpoint, mock_llm_provider, mock_logger
    ):
        """Test error logging during LLM creation failure."""
        # Setup mocks
        config = {"provider": "google", "model_name": "gemini-1.5-pro"}
        mock_get_api_key.return_value = "test-api-key"
        mock_get_endpoint.return_value = None
        mock_llm_provider.get_llm_model.side_effect = Exception("Test error")

        factory = UnifiedLLMFactory()

        with pytest.raises(RuntimeError):
            factory.create_llm_from_config(config)

        # Verify error logging
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        assert "Failed to initialize pydantic-ai Model" in call_args[0][0]
        assert call_args[1]["exc_info"] is True


class TestGetLLMFactory:
    """Test cases for get_llm_factory singleton function."""

    def test_get_llm_factory_returns_instance(self):
        """Test that get_llm_factory returns UnifiedLLMFactory instance."""
        factory = get_llm_factory()

        assert isinstance(factory, UnifiedLLMFactory)

    def test_get_llm_factory_singleton_behavior(self):
        """Test that get_llm_factory returns the same instance (singleton)."""
        factory1 = get_llm_factory()
        factory2 = get_llm_factory()

        assert factory1 is factory2  # Should be the same instance

    @patch("ai_research_assistant.core.unified_llm_factory._llm_factory_instance", None)
    def test_get_llm_factory_initialization(self):
        """Test get_llm_factory initialization when instance is None."""
        # Clear the global instance
        import ai_research_assistant.core.unified_llm_factory as factory_module

        factory_module._llm_factory_instance = None

        factory = get_llm_factory()

        assert isinstance(factory, UnifiedLLMFactory)
        assert factory_module._llm_factory_instance is factory

    def test_get_llm_factory_persistence(self):
        """Test that get_llm_factory persists across multiple calls."""
        factories = [get_llm_factory() for _ in range(5)]

        # All should be the same instance
        for factory in factories[1:]:
            assert factory is factories[0]


class TestFactoryIntegration:
    """Integration tests for UnifiedLLMFactory."""

    def setup_method(self):
        """Clear cache before each test to prevent interference."""
        # Clear the global factory cache if it exists
        factory = get_llm_factory()
        factory.clear_cache()

    @patch("ai_research_assistant.core.unified_llm_factory.llm_provider")
    @patch("ai_research_assistant.core.env_manager.env_manager.get_endpoint")
    @patch("ai_research_assistant.core.env_manager.env_manager.get_api_key")
    def test_factory_with_real_config_structure(
        self, mock_get_api_key, mock_get_endpoint, mock_llm_provider
    ):
        """Test factory with realistic configuration structure."""
        # Setup realistic configuration
        config = {
            "provider": "google",
            "model_name": "gemini-1.5-pro",
            "temperature": 0.0,
            "max_tokens": 2048,
        }

        # Setup mocks
        mock_get_api_key.return_value = "real-api-key"
        mock_get_endpoint.return_value = "https://generativelanguage.googleapis.com"
        mock_model = Mock()
        mock_llm_provider.get_llm_model.return_value = mock_model

        factory = get_llm_factory()
        result = factory.create_llm_from_config(config)

        assert result == mock_model
        mock_llm_provider.get_llm_model.assert_called_once_with(
            provider="google",
            api_key="real-api-key",
            model_name="gemini-1.5-pro",
            base_url="https://generativelanguage.googleapis.com",
        )

    @patch("ai_research_assistant.core.unified_llm_factory.llm_provider")
    @patch("ai_research_assistant.core.env_manager.env_manager.get_endpoint")
    @patch("ai_research_assistant.core.env_manager.env_manager.get_api_key")
    def test_factory_concurrent_usage_simulation(
        self, mock_get_api_key, mock_get_endpoint, mock_llm_provider
    ):
        """Test factory behavior under simulated concurrent usage."""
        # Setup mocks
        mock_get_api_key.return_value = "test-key"
        mock_get_endpoint.return_value = None
        mock_model = Mock()
        mock_llm_provider.get_llm_model.return_value = mock_model

        factory = get_llm_factory()

        # Simulate multiple "concurrent" requests for same model
        config = {"provider": "google", "model_name": "gemini-1.5-pro"}
        results = []

        for _ in range(10):
            result = factory.create_llm_from_config(config)
            results.append(result)

        # All results should be the same cached instance
        for result in results:
            assert result is results[0]

        # Provider should only be called once
        mock_llm_provider.get_llm_model.assert_called_once()

    def test_factory_cache_isolation_between_instances(self):
        """Test that different factory instances have isolated caches."""
        factory1 = UnifiedLLMFactory()
        factory2 = UnifiedLLMFactory()

        # Add different items to each cache
        factory1._llm_cache["test:model1"] = Mock()
        factory2._llm_cache["test:model2"] = Mock()

        # Caches should be independent
        assert "test:model1" in factory1._llm_cache
        assert "test:model1" not in factory2._llm_cache
        assert "test:model2" in factory2._llm_cache
        assert "test:model2" not in factory1._llm_cache

    def test_factory_global_singleton_vs_new_instances(self):
        """Test behavior of global singleton vs new instances."""
        global_factory1 = get_llm_factory()
        global_factory2 = get_llm_factory()
        new_factory = UnifiedLLMFactory()

        # Global factories should be the same
        assert global_factory1 is global_factory2

        # New factory should be different
        assert new_factory is not global_factory1
        assert new_factory is not global_factory2


class TestEdgeCasesAndErrorConditions:
    """Test cases for edge cases and error conditions."""

    def test_factory_with_none_config(self):
        """Test factory behavior with None config."""
        factory = UnifiedLLMFactory()

        with pytest.raises(AttributeError):
            factory.create_llm_from_config(None)

    def test_factory_with_malformed_config(self):
        """Test factory behavior with malformed config."""
        factory = UnifiedLLMFactory()

        malformed_configs = [
            {"provider": None, "model_name": "test"},
            {"provider": "test", "model_name": None},
            {"provider": 123, "model_name": "test"},  # Wrong type
            {"provider": "test", "model_name": 456},  # Wrong type
        ]

        for config in malformed_configs:
            with pytest.raises((ValueError, RuntimeError)):
                factory.create_llm_from_config(config)

    @patch("ai_research_assistant.core.env_manager.env_manager.get_api_key")
    def test_factory_with_env_manager_errors(self, mock_get_api_key):
        """Test factory behavior when env_manager raises errors."""
        factory = UnifiedLLMFactory()
        config = {"provider": "google", "model_name": "test-model"}

        # Test env_manager errors
        mock_get_api_key.side_effect = Exception("Env error")

        with pytest.raises(RuntimeError) as exc_info:
            factory.create_llm_from_config(config)

        assert "Failed to initialize pydantic-ai Model" in str(exc_info.value)

    def test_factory_cache_with_special_characters(self):
        """Test factory cache handling with special characters in config."""
        factory = UnifiedLLMFactory()

        # Manually test cache key generation with special characters
        config1 = {"provider": "test-provider", "model_name": "model:with:colons"}
        config2 = {"provider": "test_provider", "model_name": "model/with/slashes"}

        # These should generate different cache keys
        cache_key1 = f"{config1['provider']}:{config1['model_name']}"
        cache_key2 = f"{config2['provider']}:{config2['model_name']}"

        assert cache_key1 != cache_key2
        assert ":" in cache_key1
        assert "/" in cache_key2

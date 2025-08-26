"""
Test suite for BasePydanticAgentConfig class.

This module contains comprehensive tests for the configuration class that serves
as the foundation for all agent configurations in the system.
"""

import pytest
from pydantic import ValidationError

from ai_research_assistant.agents.base_pydantic_agent_config import (
    BasePydanticAgentConfig,
)


class TestBasePydanticAgentConfig:
    """Test cases for BasePydanticAgentConfig class."""

    def test_config_default_values(self):
        """Test that default configuration values are set correctly."""
        config = BasePydanticAgentConfig(
            agent_id="test_agent_001", agent_name="TestAgent"
        )

        assert config.agent_id == "test_agent_001"
        assert config.agent_name == "TestAgent"
        assert config.llm_provider == "google"
        assert config.llm_model_name == "gemini-1.5-flash"
        assert config.llm_temperature == 0.7
        assert config.llm_max_tokens == 4096
        assert config.pydantic_ai_instructions is None
        assert config.pydantic_ai_system_prompt is None
        assert config.pydantic_ai_retries == 1
        assert config.custom_settings == {}

    def test_config_with_all_fields(self):
        """Test configuration creation with all fields specified."""
        custom_settings = {"feature_flag": True, "debug_mode": False}

        config = BasePydanticAgentConfig(
            agent_id="agent_002",
            agent_name="FullAgent",
            llm_provider="openai",
            llm_model_name="gpt-4",
            llm_temperature=0.3,
            llm_max_tokens=8192,
            pydantic_ai_instructions="Custom instructions",
            pydantic_ai_system_prompt="You are a helpful agent",
            pydantic_ai_retries=3,
            custom_settings=custom_settings,
        )

        assert config.agent_id == "agent_002"
        assert config.agent_name == "FullAgent"
        assert config.llm_provider == "openai"
        assert config.llm_model_name == "gpt-4"
        assert config.llm_temperature == 0.3
        assert config.llm_max_tokens == 8192
        assert config.pydantic_ai_instructions == "Custom instructions"
        assert config.pydantic_ai_system_prompt == "You are a helpful agent"
        assert config.pydantic_ai_retries == 3
        assert config.custom_settings == custom_settings

    def test_config_field_validation_required_fields(self):
        """Test that required fields raise validation errors when missing."""
        with pytest.raises(ValidationError) as exc_info:
            BasePydanticAgentConfig()

        errors = exc_info.value.errors()
        required_fields = [error["loc"][0] for error in errors]
        assert "agent_id" in required_fields
        assert "agent_name" in required_fields

    @pytest.mark.parametrize("temperature", [-0.1, 1.1, 2.0, -1.0])
    def test_config_temperature_validation(self, temperature):
        """Test temperature validation with invalid values."""
        # Note: Pydantic doesn't enforce temperature bounds by default
        # This test documents current behavior
        config = BasePydanticAgentConfig(
            agent_id="temp_test", agent_name="TempTest", llm_temperature=temperature
        )
        assert config.llm_temperature == temperature

    @pytest.mark.parametrize("max_tokens", [0, -1, -100])
    def test_config_max_tokens_validation(self, max_tokens):
        """Test max_tokens validation with invalid values."""
        # Note: Pydantic doesn't enforce positive integers by default
        # This test documents current behavior
        config = BasePydanticAgentConfig(
            agent_id="tokens_test", agent_name="TokensTest", llm_max_tokens=max_tokens
        )
        assert config.llm_max_tokens == max_tokens

    @pytest.mark.parametrize("retries", [0, -1, 100])
    def test_config_retries_validation(self, retries):
        """Test retries validation with various values."""
        config = BasePydanticAgentConfig(
            agent_id="retries_test",
            agent_name="RetriesTest",
            pydantic_ai_retries=retries,
        )
        assert config.pydantic_ai_retries == retries

    def test_config_serialization(self):
        """Test configuration serialization to dict and JSON."""
        custom_settings = {"nested": {"value": 42}}

        config = BasePydanticAgentConfig(
            agent_id="serialize_test",
            agent_name="SerializeTest",
            llm_provider="anthropic",
            llm_model_name="claude-3",
            custom_settings=custom_settings,
        )

        # Test dict serialization
        config_dict = config.model_dump()
        assert isinstance(config_dict, dict)
        assert config_dict["agent_id"] == "serialize_test"
        assert config_dict["custom_settings"] == custom_settings

        # Test JSON serialization
        config_json = config.model_dump_json()
        assert isinstance(config_json, str)
        assert "serialize_test" in config_json

    def test_config_deserialization(self):
        """Test configuration deserialization from dict."""
        config_data = {
            "agent_id": "deserialize_test",
            "agent_name": "DeserializeTest",
            "llm_provider": "google",
            "llm_model_name": "gemini-pro",
            "llm_temperature": 0.5,
            "custom_settings": {"mode": "test"},
        }

        config = BasePydanticAgentConfig(**config_data)
        assert config.agent_id == "deserialize_test"
        assert config.agent_name == "DeserializeTest"
        assert config.llm_provider == "google"
        assert config.custom_settings["mode"] == "test"

    def test_config_extra_fields_allowed(self):
        """Test that extra fields are allowed due to Config.extra = 'allow'."""
        config = BasePydanticAgentConfig(
            agent_id="extra_test",
            agent_name="ExtraTest",
            extra_field="extra_value",
            another_field=123,
        )

        assert config.agent_id == "extra_test"
        # Extra fields should be accessible
        assert hasattr(config, "extra_field")
        assert getattr(config, "extra_field") == "extra_value"

    @pytest.mark.parametrize("provider", ["openai", "google", "anthropic", "custom"])
    def test_config_various_providers(self, provider):
        """Test configuration with various LLM providers."""
        config = BasePydanticAgentConfig(
            agent_id=f"provider_test_{provider}",
            agent_name="ProviderTest",
            llm_provider=provider,
        )
        assert config.llm_provider == provider

    def test_config_custom_settings_deep_copy(self):
        """Test that custom_settings maintains proper references."""
        original_settings = {"list": [1, 2, 3], "dict": {"key": "value"}}

        config = BasePydanticAgentConfig(
            agent_id="deep_copy_test",
            agent_name="DeepCopyTest",
            custom_settings=original_settings,
        )

        # Verify settings are properly stored
        assert config.custom_settings["list"] == [1, 2, 3]
        assert config.custom_settings["dict"]["key"] == "value"

        # Modify original to test if it affects config
        original_settings["list"].append(4)
        # Config should be unaffected if proper copying is done
        # Note: This test documents current behavior

    def test_config_model_validation_types(self):
        """Test type validation for various fields."""
        # Test with incorrect types
        with pytest.raises(ValidationError):
            BasePydanticAgentConfig(
                agent_id=123,  # Should be string
                agent_name="TypeError",
            )

        with pytest.raises(ValidationError):
            BasePydanticAgentConfig(
                agent_id="type_test",
                agent_name=None,  # Should be string
            )

    def test_config_empty_strings(self):
        """Test configuration with empty string values."""
        config = BasePydanticAgentConfig(
            agent_id="", agent_name="", llm_provider="", llm_model_name=""
        )

        assert config.agent_id == ""
        assert config.agent_name == ""
        assert config.llm_provider == ""
        assert config.llm_model_name == ""

    def test_config_none_values_for_optional_fields(self):
        """Test that None values work for optional fields."""
        config = BasePydanticAgentConfig(
            agent_id="none_test",
            agent_name="NoneTest",
            llm_model_name=None,
            pydantic_ai_instructions=None,
            pydantic_ai_system_prompt=None,
        )

        assert config.llm_model_name is None
        assert config.pydantic_ai_instructions is None
        assert config.pydantic_ai_system_prompt is None


@pytest.fixture
def sample_config():
    """Fixture providing a standard configuration for testing."""
    return BasePydanticAgentConfig(
        agent_id="sample_agent_001",
        agent_name="SampleAgent",
        llm_provider="google",
        llm_model_name="gemini-1.5-flash",
        llm_temperature=0.7,
        custom_settings={"test_mode": True},
    )


@pytest.fixture
def config_factory():
    """Factory fixture for creating test configurations."""

    def _create_config(**kwargs):
        defaults = {"agent_id": "factory_agent", "agent_name": "FactoryAgent"}
        defaults.update(kwargs)
        return BasePydanticAgentConfig(**defaults)

    return _create_config


class TestBasePydanticAgentConfigWithFixtures:
    """Test cases using fixtures for configuration testing."""

    def test_sample_config_fixture(self, sample_config):
        """Test using the sample config fixture."""
        assert sample_config.agent_id == "sample_agent_001"
        assert sample_config.custom_settings["test_mode"] is True

    def test_config_factory_fixture(self, config_factory):
        """Test using the config factory fixture."""
        config1 = config_factory(agent_id="factory_1")
        config2 = config_factory(agent_id="factory_2", llm_provider="openai")

        assert config1.agent_id == "factory_1"
        assert config2.agent_id == "factory_2"
        assert config2.llm_provider == "openai"

    def test_config_modification(self, sample_config):
        """Test modifying configuration after creation."""
        # Pydantic models are immutable by default, but custom_settings dict can be modified
        original_settings = sample_config.custom_settings
        original_settings["new_key"] = "new_value"

        assert sample_config.custom_settings["new_key"] == "new_value"

"""
Test suite for core.config module.

This module contains comprehensive tests for configuration constants,
provider settings, Google model configurations, and utility functions
in the core.config module.
"""

from ai_research_assistant.core.config import (
    AGENT_DEFAULTS,
    # Constants
    APP_SETTINGS,
    BROWSER_DEFAULTS,
    DEFAULT_MODELS,
    GOOGLE_MODEL_OPTIONS,
    LEGAL_RESEARCH_DEFAULTS,
    PROVIDER_DISPLAY_NAMES,
    SUPPORTED_FILE_TYPES,
    # Utility Functions
    get_google_model_display_name,
    get_google_model_info,
    get_google_model_options,
    get_google_models_by_category,
    get_google_models_with_capability,
    get_provider_config,
    get_provider_display_name,
    get_recommended_google_models,
    get_supported_providers,
    is_google_model_compatible_with_mcp,
    print_google_model_summary,
    validate_google_model_config,
)


class TestProviderConfiguration:
    """Test cases for provider configuration constants."""

    def test_provider_display_names_completeness(self):
        """Test that all expected providers have display names."""
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
            assert provider in PROVIDER_DISPLAY_NAMES
            assert isinstance(PROVIDER_DISPLAY_NAMES[provider], str)
            assert len(PROVIDER_DISPLAY_NAMES[provider]) > 0

    def test_default_models_structure(self):
        """Test that DEFAULT_MODELS has proper structure."""
        required_fields = ["model", "temperature", "max_tokens"]

        for provider, config in DEFAULT_MODELS.items():
            assert isinstance(config, dict)
            for field in required_fields:
                assert field in config

            # Validate specific field types
            assert isinstance(config["model"], str)
            assert isinstance(config["temperature"], (int, float))
            assert isinstance(config["max_tokens"], int)
            assert config["temperature"] >= 0
            assert config["max_tokens"] > 0

    def test_default_models_providers_match_display_names(self):
        """Test that DEFAULT_MODELS keys match PROVIDER_DISPLAY_NAMES keys."""
        assert set(DEFAULT_MODELS.keys()) == set(PROVIDER_DISPLAY_NAMES.keys())

    def test_browser_defaults_structure(self):
        """Test BROWSER_DEFAULTS configuration structure."""
        assert isinstance(BROWSER_DEFAULTS["headless"], bool)
        assert isinstance(BROWSER_DEFAULTS["viewport_width"], int)
        assert isinstance(BROWSER_DEFAULTS["viewport_height"], int)
        assert isinstance(BROWSER_DEFAULTS["timeout"], int)
        assert BROWSER_DEFAULTS["user_agent"] is None

        # Validate reasonable values
        assert BROWSER_DEFAULTS["viewport_width"] > 0
        assert BROWSER_DEFAULTS["viewport_height"] > 0
        assert BROWSER_DEFAULTS["timeout"] > 0

    def test_legal_research_defaults_structure(self):
        """Test LEGAL_RESEARCH_DEFAULTS configuration structure."""
        assert isinstance(LEGAL_RESEARCH_DEFAULTS["max_document_size_mb"], int)
        assert isinstance(LEGAL_RESEARCH_DEFAULTS["citation_format"], str)
        assert isinstance(LEGAL_RESEARCH_DEFAULTS["jurisdiction"], str)
        assert isinstance(LEGAL_RESEARCH_DEFAULTS["database_path"], str)

        assert LEGAL_RESEARCH_DEFAULTS["max_document_size_mb"] > 0
        assert len(LEGAL_RESEARCH_DEFAULTS["citation_format"]) > 0
        assert len(LEGAL_RESEARCH_DEFAULTS["jurisdiction"]) > 0

    def test_agent_defaults_structure(self):
        """Test AGENT_DEFAULTS configuration structure."""
        assert isinstance(AGENT_DEFAULTS["timeout_seconds"], int)
        assert isinstance(AGENT_DEFAULTS["retry_attempts"], int)
        assert isinstance(AGENT_DEFAULTS["batch_size"], int)

        assert AGENT_DEFAULTS["timeout_seconds"] > 0
        assert AGENT_DEFAULTS["retry_attempts"] >= 0
        assert AGENT_DEFAULTS["batch_size"] > 0

    def test_supported_file_types_structure(self):
        """Test SUPPORTED_FILE_TYPES configuration structure."""
        expected_categories = ["documents", "images", "web"]

        for category in expected_categories:
            assert category in SUPPORTED_FILE_TYPES
            assert isinstance(SUPPORTED_FILE_TYPES[category], list)

            # Each file type should start with a dot
            for file_type in SUPPORTED_FILE_TYPES[category]:
                assert isinstance(file_type, str)
                assert file_type.startswith(".")
                assert len(file_type) > 1

    def test_app_settings_structure(self):
        """Test APP_SETTINGS configuration structure."""
        assert isinstance(APP_SETTINGS["name"], str)
        assert isinstance(APP_SETTINGS["version"], str)
        assert isinstance(APP_SETTINGS["debug"], bool)
        assert isinstance(APP_SETTINGS["log_level"], str)

        assert len(APP_SETTINGS["name"]) > 0
        assert len(APP_SETTINGS["version"]) > 0
        assert APP_SETTINGS["log_level"] in [
            "DEBUG",
            "INFO",
            "WARNING",
            "ERROR",
            "CRITICAL",
        ]


class TestGoogleModelConfiguration:
    """Test cases for Google model configuration."""

    def test_google_model_options_structure(self):
        """Test that all Google models have required fields."""
        required_fields = [
            "name",
            "description",
            "context_window",
            "max_output_tokens",
            "capabilities",
        ]

        for model_id, model_info in GOOGLE_MODEL_OPTIONS.items():
            assert isinstance(model_id, str)
            assert isinstance(model_info, dict)

            for field in required_fields:
                assert field in model_info, f"Model {model_id} missing field {field}"

            # Validate field types
            assert isinstance(model_info["name"], str)
            assert isinstance(model_info["description"], str)
            assert isinstance(model_info["context_window"], int)
            assert isinstance(model_info["max_output_tokens"], int)
            assert isinstance(model_info["capabilities"], list)

            # Validate reasonable values
            assert model_info["context_window"] > 0
            assert model_info["max_output_tokens"] > 0
            assert len(model_info["capabilities"]) > 0

    def test_google_model_capabilities_consistency(self):
        """Test that model capabilities are consistent."""
        valid_capabilities = {
            "thinking",
            "code_execution",
            "multimodal",
            "function_calling",
            "audio_generation",
            "tts",
            "live_api",
            "image_generation",
        }

        for model_id, model_info in GOOGLE_MODEL_OPTIONS.items():
            for capability in model_info["capabilities"]:
                assert isinstance(capability, str)
                assert capability in valid_capabilities, (
                    f"Invalid capability '{capability}' in model {model_id}"
                )

    def test_google_model_audio_models_have_io_types(self):
        """Test that audio models have input/output type specifications."""
        for model_id, model_info in GOOGLE_MODEL_OPTIONS.items():
            if (
                "audio_generation" in model_info["capabilities"]
                or "tts" in model_info["capabilities"]
            ):
                assert "input_types" in model_info, (
                    f"Audio model {model_id} missing input_types"
                )
                assert "output_types" in model_info, (
                    f"Audio model {model_id} missing output_types"
                )
                assert isinstance(model_info["input_types"], list)
                assert isinstance(model_info["output_types"], list)

    def test_google_model_generations_are_categorized(self):
        """Test that models are properly categorized by generation."""
        generations = {"1.5", "2.0", "2.5"}

        for model_id in GOOGLE_MODEL_OPTIONS.keys():
            has_generation = any(gen in model_id for gen in generations)
            assert has_generation, (
                f"Model {model_id} doesn't have recognizable generation"
            )


class TestProviderUtilityFunctions:
    """Test cases for provider utility functions."""

    def test_get_provider_config_valid_provider(self):
        """Test get_provider_config with valid provider."""
        config = get_provider_config("openai")
        assert isinstance(config, dict)
        assert "model" in config
        assert "temperature" in config
        assert "max_tokens" in config

    def test_get_provider_config_invalid_provider(self):
        """Test get_provider_config with invalid provider."""
        config = get_provider_config("nonexistent")
        assert config == {}

    def test_get_supported_providers(self):
        """Test get_supported_providers returns correct list."""
        providers = get_supported_providers()
        assert isinstance(providers, list)
        assert len(providers) > 0

        expected_providers = list(PROVIDER_DISPLAY_NAMES.keys())
        assert set(providers) == set(expected_providers)

    def test_get_provider_display_name_valid(self):
        """Test get_provider_display_name with valid provider."""
        display_name = get_provider_display_name("openai")
        assert display_name == "OpenAI"

    def test_get_provider_display_name_invalid(self):
        """Test get_provider_display_name with invalid provider."""
        display_name = get_provider_display_name("nonexistent")
        assert display_name == "Nonexistent"  # Title case fallback


class TestGoogleModelUtilityFunctions:
    """Test cases for Google model utility functions."""

    def test_get_google_model_options(self):
        """Test get_google_model_options returns complete options."""
        options = get_google_model_options()
        assert options == GOOGLE_MODEL_OPTIONS
        assert isinstance(options, dict)
        assert len(options) > 0

    def test_get_google_model_info_valid_model(self):
        """Test get_google_model_info with valid model."""
        # Use a model we know exists
        model_id = list(GOOGLE_MODEL_OPTIONS.keys())[0]
        info = get_google_model_info(model_id)

        assert isinstance(info, dict)
        assert "name" in info
        assert "description" in info
        assert info == GOOGLE_MODEL_OPTIONS[model_id]

    def test_get_google_model_info_invalid_model(self):
        """Test get_google_model_info with invalid model."""
        info = get_google_model_info("nonexistent-model")
        assert info == {}

    def test_get_google_models_by_category(self):
        """Test get_google_models_by_category structure."""
        categories = get_google_models_by_category()
        assert isinstance(categories, dict)

        # Check that all models in categories exist in GOOGLE_MODEL_OPTIONS
        all_categorized_models = []
        for category, models in categories.items():
            assert isinstance(category, str)
            assert isinstance(models, list)
            all_categorized_models.extend(models)

            for model in models:
                assert model in GOOGLE_MODEL_OPTIONS, (
                    f"Model {model} not found in GOOGLE_MODEL_OPTIONS"
                )

    def test_get_recommended_google_models(self):
        """Test get_recommended_google_models structure."""
        recommendations = get_recommended_google_models()
        assert isinstance(recommendations, dict)

        expected_use_cases = {
            "general_use",
            "reasoning_heavy",
            "cost_efficient",
            "multimodal",
            "coding",
            "audio_generation",
            "conversational",
            "stable_production",
            "high_context",
            "image_generation",
        }

        assert set(recommendations.keys()) == expected_use_cases

        # Check that all recommended models exist
        for use_case, model_id in recommendations.items():
            assert isinstance(model_id, str)
            assert model_id in GOOGLE_MODEL_OPTIONS, (
                f"Recommended model {model_id} for {use_case} not found"
            )

    def test_get_google_models_with_capability(self):
        """Test get_google_models_with_capability functionality."""
        # Test with a capability we know exists
        thinking_models = get_google_models_with_capability("thinking")
        assert isinstance(thinking_models, list)

        # Verify all returned models actually have the capability
        for model_id in thinking_models:
            assert model_id in GOOGLE_MODEL_OPTIONS
            assert "thinking" in GOOGLE_MODEL_OPTIONS[model_id]["capabilities"]

    def test_get_google_models_with_capability_nonexistent(self):
        """Test get_google_models_with_capability with nonexistent capability."""
        models = get_google_models_with_capability("nonexistent_capability")
        assert models == []

    def test_is_google_model_compatible_with_mcp_known_incompatible(self):
        """Test MCP compatibility check with known incompatible model."""
        # Test the known problematic model
        is_compatible = is_google_model_compatible_with_mcp(
            "gemini-2.5-flash-preview-05-20"
        )
        assert is_compatible is False

    def test_is_google_model_compatible_with_mcp_compatible_model(self):
        """Test MCP compatibility check with compatible model."""
        # Use a model that should be compatible
        is_compatible = is_google_model_compatible_with_mcp(
            "gemini-2.5-flash-preview-04-17"
        )
        assert is_compatible is True

    def test_get_google_model_display_name_valid(self):
        """Test get_google_model_display_name with valid model."""
        # Use first available model
        model_id = list(GOOGLE_MODEL_OPTIONS.keys())[0]
        display_name = get_google_model_display_name(model_id)

        assert isinstance(display_name, str)
        assert display_name == GOOGLE_MODEL_OPTIONS[model_id]["name"]

    def test_get_google_model_display_name_invalid(self):
        """Test get_google_model_display_name with invalid model."""
        display_name = get_google_model_display_name("nonexistent-model")
        assert display_name == "nonexistent-model"  # Fallback to model ID


class TestGoogleModelValidation:
    """Test cases for Google model validation functions."""

    def test_validate_google_model_config_structure(self):
        """Test validate_google_model_config returns proper structure."""
        validation = validate_google_model_config()

        expected_keys = {
            "total_models",
            "models_by_generation",
            "capabilities_count",
            "issues",
            "categorized_models",
            "uncategorized_models",
        }

        assert isinstance(validation, dict)
        assert set(validation.keys()) >= expected_keys

        # Check types
        assert isinstance(validation["total_models"], int)
        assert isinstance(validation["models_by_generation"], dict)
        assert isinstance(validation["capabilities_count"], dict)
        assert isinstance(validation["issues"], list)
        assert isinstance(validation["categorized_models"], int)
        assert isinstance(validation["uncategorized_models"], list)

    def test_validate_google_model_config_counts(self):
        """Test that validation counts are consistent."""
        validation = validate_google_model_config()

        # Total models should match actual count
        assert validation["total_models"] == len(GOOGLE_MODEL_OPTIONS)

        # Generation counts should add up reasonably
        total_by_generation = sum(validation["models_by_generation"].values())
        assert total_by_generation == validation["total_models"]

        # Capability counts should be reasonable
        for capability, count in validation["capabilities_count"].items():
            assert isinstance(capability, str)
            assert isinstance(count, int)
            assert count > 0

    def test_validate_google_model_config_no_critical_issues(self):
        """Test that validation doesn't find critical configuration issues."""
        validation = validate_google_model_config()

        # Should not have issues with recommended models
        critical_issues = [
            issue
            for issue in validation["issues"]
            if "Recommended model" in issue and "not found" in issue
        ]
        assert len(critical_issues) == 0, f"Critical issues found: {critical_issues}"

    def test_print_google_model_summary_runs_without_error(self, capsys):
        """Test that print_google_model_summary executes without errors."""
        # This function prints to stdout, so we capture output
        print_google_model_summary()

        captured = capsys.readouterr()
        assert "GOOGLE GEMINI MODELS SUMMARY" in captured.out
        assert "Total Models:" in captured.out
        assert "Model Categories:" in captured.out


class TestConfigurationIntegrity:
    """Test cases for overall configuration integrity."""

    def test_all_google_models_have_unique_names(self):
        """Test that all Google models have unique display names."""
        display_names = []
        for model_info in GOOGLE_MODEL_OPTIONS.values():
            display_names.append(model_info["name"])

        # Check for duplicates
        assert len(display_names) == len(set(display_names)), (
            "Duplicate display names found"
        )

    def test_recommended_models_cover_all_use_cases(self):
        """Test that recommended models are available for all expected use cases."""
        recommendations = get_recommended_google_models()

        # These are the use cases we expect to have recommendations for
        expected_use_cases = {
            "general_use",
            "reasoning_heavy",
            "cost_efficient",
            "multimodal",
            "coding",
            "audio_generation",
            "conversational",
            "stable_production",
            "high_context",
            "image_generation",
        }

        missing_use_cases = expected_use_cases - set(recommendations.keys())
        assert len(missing_use_cases) == 0, (
            f"Missing recommendations for: {missing_use_cases}"
        )

    def test_model_categories_are_comprehensive(self):
        """Test that model categorization covers most models."""
        categories = get_google_models_by_category()
        all_categorized = set()

        for models in categories.values():
            all_categorized.update(models)

        all_models = set(GOOGLE_MODEL_OPTIONS.keys())
        uncategorized = all_models - all_categorized

        # Allow some models to be uncategorized, but not too many
        uncategorized_percentage = len(uncategorized) / len(all_models)
        assert uncategorized_percentage < 0.1, (
            f"Too many uncategorized models: {uncategorized}"
        )

    def test_mcp_compatibility_annotation_exists(self):
        """Test that MCP compatibility is properly annotated."""
        # The default model should be MCP compatible
        default_model = DEFAULT_MODELS["google"]["model"]
        is_compatible = is_google_model_compatible_with_mcp(default_model)

        # If the default model is not compatible, it should be documented
        if not is_compatible:
            # Check that there's a note in the configuration
            model_info = GOOGLE_MODEL_OPTIONS.get(default_model, {})
            note = model_info.get("note", "")
            assert "MCP" in note or "tool" in note, (
                f"Incompatible default model {default_model} should be documented"
            )

    def test_configuration_constants_are_immutable_types(self):
        """Test that configuration constants use immutable types where appropriate."""
        # These should be tuples or immutable collections where possible
        # This is more of a code quality test

        # File type lists could be tuples for immutability
        for category, file_types in SUPPORTED_FILE_TYPES.items():
            assert isinstance(
                file_types, list
            )  # Currently lists, documenting current state

            # Verify no empty extensions
            for ext in file_types:
                assert len(ext) > 1, f"Invalid file extension: {ext}"

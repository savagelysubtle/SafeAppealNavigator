"""
Configuration constants and settings for AI Research Assistant

Provides centralized configuration for provider display names,
default settings, and other application constants.
"""

from typing import Any, Dict, List

# Provider display names for UI
PROVIDER_DISPLAY_NAMES = {
    "openai": "OpenAI",
    "anthropic": "Anthropic (Claude)",
    "google": "Google Gemini",
    "mistral": "Mistral AI",
    "ollama": "Ollama (Local)",
    "deepseek": "DeepSeek",
    "watsonx": "IBM WatsonX",
}

# Default model configurations
DEFAULT_MODELS = {
    "openai": {"model": "gpt-4", "temperature": 0.0, "max_tokens": 2048},
    "anthropic": {
        "model": "claude-3-5-sonnet-20241022",
        "temperature": 0.0,
        "max_tokens": 2048,
    },
    "google": {
        "model": "gemini-2.5-flash-preview-04-17",
        "temperature": 0.0,
        "max_tokens": 2048,
        "note": "Using April version due to MCP tool compatibility issues with 05-20 version",
    },
    "mistral": {
        "model": "mistral-large-latest",
        "temperature": 0.0,
        "max_tokens": 2048,
    },
    "ollama": {"model": "llama2", "temperature": 0.0, "max_tokens": 2048},
    "deepseek": {"model": "deepseek-chat", "temperature": 0.0, "max_tokens": 2048},
    "watsonx": {
        "model": "meta-llama/llama-3-70b-instruct",
        "temperature": 0.0,
        "max_tokens": 2048,
    },
}

# Google model options for UI selection
GOOGLE_MODEL_OPTIONS = {
    # Gemini 2.5 Pro models (Most Advanced)
    "gemini-2.5-pro-preview-05-06": {
        "name": "Gemini 2.5 Pro Preview (Latest)",
        "description": "Most advanced reasoning model with maximum response accuracy",
        "context_window": 1048576,
        "max_output_tokens": 65536,
        "capabilities": [
            "thinking",
            "code_execution",
            "multimodal",
            "function_calling",
        ],
    },
    "gemini-2.5-pro-preview-03-25": {
        "name": "Gemini 2.5 Pro Preview (March)",
        "description": "Previous version of the advanced reasoning model",
        "context_window": 1048576,
        "max_output_tokens": 65536,
        "capabilities": [
            "thinking",
            "code_execution",
            "multimodal",
            "function_calling",
        ],
    },
    # Gemini 2.5 Pro TTS models
    "gemini-2.5-pro-preview-tts": {
        "name": "Gemini 2.5 Pro Preview TTS",
        "description": "Most powerful text-to-speech model with high control and transparency",
        "context_window": 8000,
        "max_output_tokens": 16000,
        "capabilities": ["audio_generation", "tts"],
        "input_types": ["text"],
        "output_types": ["audio"],
    },
    # Gemini 2.5 Flash models (Best Price-Performance)
    "gemini-2.5-flash-preview-05-20": {
        "name": "Gemini 2.5 Flash Preview (Latest)",
        "description": "Best price-performance with adaptive thinking capabilities - note: may have MCP tool issues",
        "context_window": 1048576,
        "max_output_tokens": 65536,
        "capabilities": [
            "thinking",
            "code_execution",
            "multimodal",
            "function_calling",
        ],
    },
    "gemini-2.5-flash-preview-04-17": {
        "name": "Gemini 2.5 Flash Preview (April)",
        "description": "Previous version of Flash with adaptive thinking capabilities",
        "context_window": 1048576,
        "max_output_tokens": 65536,
        "capabilities": [
            "thinking",
            "code_execution",
            "multimodal",
            "function_calling",
        ],
    },
    # Gemini 2.5 Flash TTS model
    "gemini-2.5-flash-preview-tts": {
        "name": "Gemini 2.5 Flash Preview TTS",
        "description": "Price-performant text-to-speech model with high control and transparency",
        "context_window": 8000,
        "max_output_tokens": 16000,
        "capabilities": ["audio_generation", "tts"],
        "input_types": ["text"],
        "output_types": ["audio"],
    },
    # Gemini 2.5 Flash Native Audio models
    "gemini-2.5-flash-preview-native-audio-dialog": {
        "name": "Gemini 2.5 Flash Native Audio Dialog",
        "description": "Native audio dialog model for conversational experiences",
        "context_window": 128000,
        "max_output_tokens": 8000,
        "capabilities": ["audio_generation", "function_calling", "live_api"],
        "input_types": ["audio", "video", "text"],
        "output_types": ["text", "audio"],
    },
    "gemini-2.5-flash-exp-native-audio-thinking-dialog": {
        "name": "Gemini 2.5 Flash Native Audio Thinking",
        "description": "Native audio dialog model with thinking capabilities for complex conversations",
        "context_window": 128000,
        "max_output_tokens": 8000,
        "capabilities": [
            "audio_generation",
            "function_calling",
            "thinking",
            "live_api",
        ],
        "input_types": ["audio", "video", "text"],
        "output_types": ["text", "audio"],
    },
    # Gemini 2.0 models (Production Ready)
    "gemini-2.0-flash": {
        "name": "Gemini 2.0 Flash",
        "description": "Next-gen features with speed and enhanced performance",
        "context_window": 1048576,
        "max_output_tokens": 8192,
        "capabilities": ["multimodal", "function_calling", "code_execution"],
    },
    "gemini-2.0-flash-exp": {
        "name": "Gemini 2.0 Flash Experimental",
        "description": "Experimental version with latest features",
        "context_window": 1048576,
        "max_output_tokens": 8192,
        "capabilities": ["multimodal", "function_calling", "thinking"],
    },
    "gemini-2.0-flash-lite": {
        "name": "Gemini 2.0 Flash-Lite",
        "description": "Cost-efficient model optimized for low latency",
        "context_window": 1048576,
        "max_output_tokens": 8192,
        "capabilities": ["multimodal", "function_calling"],
    },
    "gemini-2.0-flash-preview-image-generation": {
        "name": "Gemini 2.0 Flash Preview Image Generation",
        "description": "Conversational image generation and editing",
        "context_window": 32000,
        "max_output_tokens": 8192,
        "capabilities": ["image_generation", "multimodal", "function_calling"],
    },
    "gemini-2.0-flash-live-001": {
        "name": "Gemini 2.0 Flash Live",
        "description": "Low-latency bidirectional voice and video interactions",
        "context_window": 1048576,
        "max_output_tokens": 8192,
        "capabilities": ["live_api", "audio_generation", "function_calling"],
    },
    # Gemini 1.5 models (Stable)
    "gemini-1.5-pro": {
        "name": "Gemini 1.5 Pro",
        "description": "Mid-size multimodal model optimized for complex reasoning",
        "context_window": 2097152,
        "max_output_tokens": 8192,
        "capabilities": ["multimodal", "function_calling", "code_execution"],
    },
    "gemini-1.5-flash": {
        "name": "Gemini 1.5 Flash",
        "description": "Fast and versatile multimodal model for diverse tasks",
        "context_window": 1048576,
        "max_output_tokens": 8192,
        "capabilities": ["multimodal", "function_calling", "code_execution"],
    },
    "gemini-1.5-flash-8b": {
        "name": "Gemini 1.5 Flash-8B",
        "description": "Small model designed for lower intelligence tasks",
        "context_window": 1048576,
        "max_output_tokens": 8192,
        "capabilities": ["multimodal", "function_calling", "code_execution"],
    },
}

# Browser configuration defaults
BROWSER_DEFAULTS = {
    "headless": True,
    "viewport_width": 1920,
    "viewport_height": 1080,
    "timeout": 30,
    "user_agent": None,
}

# Legal research configuration defaults
LEGAL_RESEARCH_DEFAULTS = {
    "max_document_size_mb": 50,
    "citation_format": "bluebook",
    "jurisdiction": "federal",
    "database_path": "./legal_research_db",
}

# Agent configuration defaults
AGENT_DEFAULTS = {"timeout_seconds": 300, "retry_attempts": 3, "batch_size": 10}

# Supported file types for document processing
SUPPORTED_FILE_TYPES = {
    "documents": [".pdf", ".docx", ".txt", ".md"],
    "images": [".png", ".jpg", ".jpeg", ".gif", ".bmp"],
    "web": [".html", ".htm", ".xml"],
}

# Application settings
APP_SETTINGS = {
    "name": "AI Research Assistant",
    "version": "1.0.0",
    "debug": False,
    "log_level": "INFO",
}


def get_provider_config(provider: str) -> Dict[str, Any]:
    """Get configuration for a specific provider"""
    return DEFAULT_MODELS.get(provider, {})


def get_supported_providers() -> List[str]:
    """Get list of all supported providers"""
    return list(PROVIDER_DISPLAY_NAMES.keys())


def get_provider_display_name(provider: str) -> str:
    """Get display name for a provider"""
    return PROVIDER_DISPLAY_NAMES.get(provider, provider.title())


def get_google_model_options() -> Dict[str, Any]:
    """Get all available Google model options with their details"""
    return GOOGLE_MODEL_OPTIONS


def get_google_model_info(model_id: str) -> Dict[str, Any]:
    """Get detailed information about a specific Google model"""
    return GOOGLE_MODEL_OPTIONS.get(model_id, {})


def get_google_models_by_category() -> Dict[str, List[str]]:
    """Get Google models organized by category"""
    return {
        "Gemini 2.5 Pro (Most Advanced)": [
            "gemini-2.5-pro-preview-05-06",
            "gemini-2.5-pro-preview-03-25",
        ],
        "Gemini 2.5 Flash (Best Price-Performance)": [
            "gemini-2.5-flash-preview-05-20",
            "gemini-2.5-flash-preview-04-17",
        ],
        "Gemini 2.5 Text-to-Speech": [
            "gemini-2.5-pro-preview-tts",
            "gemini-2.5-flash-preview-tts",
        ],
        "Gemini 2.5 Native Audio": [
            "gemini-2.5-flash-preview-native-audio-dialog",
            "gemini-2.5-flash-exp-native-audio-thinking-dialog",
        ],
        "Gemini 2.0 Production": [
            "gemini-2.0-flash",
            "gemini-2.0-flash-exp",
            "gemini-2.0-flash-lite",
        ],
        "Gemini 2.0 Specialized": [
            "gemini-2.0-flash-preview-image-generation",
            "gemini-2.0-flash-live-001",
        ],
        "Gemini 1.5 Stable": [
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "gemini-1.5-flash-8b",
        ],
    }


def get_recommended_google_models() -> Dict[str, str]:
    """Get recommended Google models for different use cases"""
    return {
        "general_use": "gemini-2.5-flash-preview-04-17",
        "reasoning_heavy": "gemini-2.5-pro-preview-05-06",
        "cost_efficient": "gemini-2.0-flash-lite",
        "multimodal": "gemini-2.5-flash-preview-04-17",
        "coding": "gemini-2.5-pro-preview-05-06",
        "audio_generation": "gemini-2.5-flash-preview-tts",
        "conversational": "gemini-2.5-flash-preview-native-audio-dialog",
        "stable_production": "gemini-1.5-flash",
        "high_context": "gemini-1.5-pro",
        "image_generation": "gemini-2.0-flash-preview-image-generation",
    }


def get_google_models_with_capability(capability: str) -> List[str]:
    """Get all Google models that support a specific capability"""
    models_with_capability = []
    for model_id, model_info in GOOGLE_MODEL_OPTIONS.items():
        if capability in model_info.get("capabilities", []):
            models_with_capability.append(model_id)
    return models_with_capability


def is_google_model_compatible_with_mcp(model_id: str) -> bool:
    """Check if a Google model is compatible with MCP tools"""
    # Known issue with gemini-2.5-flash-preview-05-20 and MCP tools
    problematic_models = ["gemini-2.5-flash-preview-05-20"]
    return model_id not in problematic_models


def get_google_model_display_name(model_id: str) -> str:
    """Get the display name for a Google model"""
    model_info = GOOGLE_MODEL_OPTIONS.get(model_id, {})
    return model_info.get("name", model_id)


def validate_google_model_config() -> Dict[str, Any]:
    """Validate Google model configuration and return summary"""
    validation_results = {
        "total_models": len(GOOGLE_MODEL_OPTIONS),
        "models_by_generation": {},
        "capabilities_count": {},
        "issues": [],
        "categorized_models": 0,
        "uncategorized_models": [],
    }

    # Count models by generation
    for model_id in GOOGLE_MODEL_OPTIONS.keys():
        if "2.5" in model_id:
            generation = "Gemini 2.5"
        elif "2.0" in model_id:
            generation = "Gemini 2.0"
        elif "1.5" in model_id:
            generation = "Gemini 1.5"
        else:
            generation = "Other"

        validation_results["models_by_generation"][generation] = (
            validation_results["models_by_generation"].get(generation, 0) + 1
        )

    # Count capabilities
    for model_info in GOOGLE_MODEL_OPTIONS.values():
        for capability in model_info.get("capabilities", []):
            validation_results["capabilities_count"][capability] = (
                validation_results["capabilities_count"].get(capability, 0) + 1
            )

    # Check categorization
    categories = get_google_models_by_category()
    categorized_ids = set()
    for models in categories.values():
        categorized_ids.update(models)
        validation_results["categorized_models"] += len(models)

    # Find uncategorized models
    all_model_ids = set(GOOGLE_MODEL_OPTIONS.keys())
    uncategorized = all_model_ids - categorized_ids
    validation_results["uncategorized_models"] = list(uncategorized)

    # Check for issues
    recommended = get_recommended_google_models()
    for use_case, model_id in recommended.items():
        if model_id not in GOOGLE_MODEL_OPTIONS:
            validation_results["issues"].append(
                f"Recommended model for {use_case} ({model_id}) not found in GOOGLE_MODEL_OPTIONS"
            )

    # Check MCP compatibility warnings
    mcp_incompatible = [
        model_id
        for model_id in GOOGLE_MODEL_OPTIONS.keys()
        if not is_google_model_compatible_with_mcp(model_id)
    ]
    if mcp_incompatible:
        validation_results["mcp_incompatible"] = mcp_incompatible

    return validation_results


def print_google_model_summary():
    """Print a summary of all Google models for debugging"""
    print("=" * 60)
    print("GOOGLE GEMINI MODELS SUMMARY")
    print("=" * 60)

    validation = validate_google_model_config()

    print(f"Total Models: {validation['total_models']}")
    print(f"Categorized Models: {validation['categorized_models']}")

    print("\nModels by Generation:")
    for generation, count in validation["models_by_generation"].items():
        print(f"  {generation}: {count} models")

    print("\nCapabilities Distribution:")
    for capability, count in sorted(validation["capabilities_count"].items()):
        print(f"  {capability}: {count} models")

    print("\nModel Categories:")
    categories = get_google_models_by_category()
    for category, models in categories.items():
        print(f"  {category}: {len(models)} models")
        for model in models:
            model_info = GOOGLE_MODEL_OPTIONS.get(model, {})
            name = model_info.get("name", model)
            print(f"    - {name} ({model})")

    if validation["uncategorized_models"]:
        print(f"\nUncategorized Models: {len(validation['uncategorized_models'])}")
        for model in validation["uncategorized_models"]:
            print(f"  - {model}")

    if validation["issues"]:
        print(f"\nIssues Found: {len(validation['issues'])}")
        for issue in validation["issues"]:
            print(f"  - {issue}")

    if "mcp_incompatible" in validation:
        print(f"\nMCP Incompatible Models: {len(validation['mcp_incompatible'])}")
        for model in validation["mcp_incompatible"]:
            print(f"  - {model}")

    print("=" * 60)

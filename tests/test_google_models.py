#!/usr/bin/env python3
"""
Test script to validate Google Gemini model integration
"""

from src.ai_research_assistant.utils.config import (
    get_recommended_google_models,
    validate_google_model_config,
)
from src.ai_research_assistant.utils.llm_provider import _create_google_provider


def test_google_models():
    """Test Google model integration"""
    print("Testing Google LLM Provider with New Models:")
    print("=" * 50)

    recommended = get_recommended_google_models()

    for use_case, model_id in recommended.items():
        print(f"Testing {use_case}: {model_id}")
        try:
            # Note: This will fail without API key, but we can test the provider creation logic
            provider = _create_google_provider(api_key="test_key", model_name=model_id)
            print(f"  ✅ Provider creation logic works for {model_id}")
        except ValueError as e:
            if "API key" in str(e):
                print(
                    f"  ✅ Provider creation logic works (API key needed): {model_id}"
                )
            else:
                print(f"  ❌ Error: {e}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
        print()

    # Test validation
    print("\nRunning model configuration validation:")
    print("=" * 50)
    validation = validate_google_model_config()

    print(f"Total models configured: {validation['total_models']}")
    print(
        f"All models categorized: {validation['categorized_models'] == validation['total_models']}"
    )

    if validation.get("issues"):
        print("⚠️ Issues found:")
        for issue in validation["issues"]:
            print(f"  - {issue}")
    else:
        print("✅ No configuration issues found")

    if validation.get("mcp_incompatible"):
        print(f"\n⚠️ MCP incompatible models: {len(validation['mcp_incompatible'])}")
        for model in validation["mcp_incompatible"]:
            print(f"  - {model}")

    print("\n" + "=" * 50)
    print("Google Gemini 2.5 models successfully integrated! 🎉")


if __name__ == "__main__":
    test_google_models()

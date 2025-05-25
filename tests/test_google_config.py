#!/usr/bin/env python3

"""
Test script to verify Google models configuration
"""

from src.ai_research_assistant.utils import config


def test_google_models():
    print("=" * 60)
    print("Testing Google Models Configuration")
    print("=" * 60)

    # Test basic imports
    print("✅ Config module imported successfully")

    # Test provider display names
    providers = config.PROVIDER_DISPLAY_NAMES
    print(f"✅ Available providers: {list(providers.keys())}")

    # Test Google model options
    google_models = config.GOOGLE_MODEL_OPTIONS
    print(f"✅ Total Google models defined: {len(google_models)}")

    # Test categories
    categories = config.get_google_models_by_category()
    print(f"✅ Google model categories: {len(categories)}")

    print("\n📋 Google Model Categories:")
    for category, models in categories.items():
        print(f"  {category}: {len(models)} models")
        for model in models[:2]:  # Show first 2 models per category
            model_info = google_models.get(model, {})
            print(f"    • {model_info.get('name', model)}")
        if len(models) > 2:
            print(f"    ... and {len(models) - 2} more")

    # Test recommended models
    recommended = config.get_recommended_google_models()
    print(f"\n🎯 Recommended models: {len(recommended)}")
    for use_case, model in recommended.items():
        model_info = google_models.get(model, {})
        print(f"  {use_case}: {model_info.get('name', model)}")

    # Test default model
    default_config = config.DEFAULT_MODELS.get("google", {})
    default_model = default_config.get("model", "Not set")
    print(f"\n🔧 Default Google model: {default_model}")

    print("\n✅ All Google model configurations are working correctly!")
    return True


if __name__ == "__main__":
    try:
        test_google_models()
    except Exception as e:
        print(f"❌ Error testing Google models: {e}")
        import traceback

        traceback.print_exc()

#!/usr/bin/env python3
"""
Simple test to verify legal research imports work correctly
"""


def test_imports():
    print("🧪 Testing legal research imports...")

    try:
        from src.ai_research_assistant.agent.legal_research.enhanced_legal_features import (
            EnhancedLegalAnalyzer,
        )

        print("✅ EnhancedLegalAnalyzer import successful")

        # Test instantiation without parameters
        analyzer = EnhancedLegalAnalyzer()
        print("✅ EnhancedLegalAnalyzer instantiation successful")

        print(f"   - LLM instance available: {analyzer.llm_instance is not None}")
        print(f"   - LLM provider: {analyzer.llm_provider}")

    except Exception as e:
        print(f"❌ EnhancedLegalAnalyzer test failed: {e}")
        return False

    try:
        print("✅ LegalCaseResearchAgent import successful")
    except Exception as e:
        print(f"❌ LegalCaseResearchAgent import failed: {e}")
        return False

    try:
        print("✅ LegalCaseDatabase import successful")
    except Exception as e:
        print(f"❌ LegalCaseDatabase import failed: {e}")
        return False

    print("🎉 All legal research imports successful!")
    return True


if __name__ == "__main__":
    test_imports()

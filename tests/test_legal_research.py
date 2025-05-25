#!/usr/bin/env python3
"""
Test script to verify the updated legal research functionality works with Google models.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv

from src.ai_research_assistant.agent.legal_research.enhanced_legal_features import (
    EnhancedLegalAnalyzer,
)
from src.ai_research_assistant.utils.unified_llm_factory import get_llm_factory

# Load environment variables
load_dotenv()


def test_legal_research():
    """Test the updated legal research functionality"""

    print("🧪 Testing Legal Research with Google Models")
    print("=" * 50)

    try:
        # Create LLM instance using unified factory
        factory = get_llm_factory()

        # Create Google LLM for legal research (lower temperature for accuracy)
        llm = factory.create_llm_for_legal_agent(
            provider="google",
            model_name="gemini-2.5-flash-preview-05-20",
            temperature=0.3,
        )

        print("✅ Created Google LLM instance for legal research")

        # Create enhanced legal analyzer with the LLM instance
        analyzer = EnhancedLegalAnalyzer(llm_instance=llm)
        print("✅ Created EnhancedLegalAnalyzer with Google LLM")

        # Test case data
        user_case = {
            "summary": "Worker injured their back while lifting heavy boxes at warehouse. WorkSafeBC denied claim stating injury was pre-existing condition.",
            "keywords": [
                "back injury",
                "lifting",
                "warehouse",
                "pre-existing condition",
                "denied claim",
            ],
            "appellant_name": "John Doe",
            "appellant_address": "123 Main St, Vancouver, BC",
        }

        similar_cases = [
            {
                "appeal_number": "WCAT-2023-001",
                "date": "2023-01-15",
                "issues": "Back injury during lifting operations, dispute over pre-existing condition",
                "outcome": "Appeal allowed - injury found to be work-related",
                "similarity_score": 0.85,
            },
            {
                "appeal_number": "WCAT-2022-045",
                "date": "2022-11-20",
                "issues": "Warehouse worker back strain, employer disputed work-relatedness",
                "outcome": "Appeal partially allowed - benefits awarded",
                "similarity_score": 0.78,
            },
        ]

        print("\n🔍 Testing legal strategy generation...")

        # Generate legal strategy
        strategy = analyzer.generate_legal_strategy(user_case, similar_cases)

        if "error" in strategy:
            print(f"❌ Error: {strategy['error']}")
            return False

        print("✅ Legal strategy generated successfully!")
        print("\n📄 Strategy Preview:")
        raw_analysis = strategy.get("raw_analysis", "")
        preview = (
            raw_analysis[:300] + "..." if len(raw_analysis) > 300 else raw_analysis
        )
        print(f"{preview}")

        print("\n📊 Strategy Details:")
        print(f"   • Generated at: {strategy.get('generated_at')}")
        print(f"   • Confidence: {strategy.get('confidence')}")
        print(f"   • Key points found: {len(strategy.get('key_points', []))}")

        # Show some key points if available
        key_points = strategy.get("key_points", [])
        if key_points:
            print("\n🎯 Key Strategic Points:")
            for i, point in enumerate(key_points[:3], 1):
                print(f"   {i}. {point[:100]}...")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_legal_research()

    if success:
        print("\n🎉 Legal Research Test PASSED!")
        print("✅ Google models are working correctly with legal research")
        print("✅ The WebUI legal research tab should now work properly")
    else:
        print("\n💥 Legal Research Test FAILED!")
        print("❌ There may still be issues with the legal research integration")

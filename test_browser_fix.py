#!/usr/bin/env python3
"""Quick test to verify browser agent fix works."""

import os
import sys

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from ai_research_assistant.core.models import ConductComprehensiveResearchInput


def test_pydantic_model():
    """Test that the Pydantic model works with case_context field."""
    try:
        # This should work - correct field name
        input_data = ConductComprehensiveResearchInput(
            search_keywords=["test", "keywords"],
            case_context="Test case context",
            research_depth="moderate",
            sources_to_include=["example.com"],
        )
        print("✓ Pydantic model validation passed with case_context")
        print(f"  Field value: {input_data.case_context}")
        return True
    except Exception as e:
        print(f"✗ Pydantic model validation failed: {e}")
        return False


def test_old_field_name():
    """Test that the old field name fails (as expected)."""
    try:
        # This should fail - incorrect field name
        input_data = ConductComprehensiveResearchInput(
            search_keywords=["test", "keywords"],
            case_context_summary="Test case context",  # Wrong field name
            research_depth="moderate",
            sources_to_include=["example.com"],
        )
        print("✗ Old field name should have failed but didn't")
        return False
    except Exception:
        print("✓ Old field name correctly failed validation")
        return True


if __name__ == "__main__":
    print("Testing browser agent Pydantic model fix...")

    test1 = test_pydantic_model()
    test2 = test_old_field_name()

    if test1 and test2:
        print("\n✓ All tests passed! The fix should work correctly.")
    else:
        print("\n✗ Some tests failed. The fix may need more work.")

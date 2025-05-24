#!/usr/bin/env python3
"""
Test script to verify the legal research fixes

This script tests:
1. LLM client initialization
2. Enhanced legal workflow
3. Database functionality
"""

import os
import tempfile
from pathlib import Path


def test_llm_clients():
    """Test LLM client initialization"""
    print("🧠 Testing LLM Client Initialization...")

    try:
        from .enhanced_legal_features import EnhancedLegalAnalyzer

        # Test OpenAI client (if API key available)
        if os.getenv("OPENAI_API_KEY"):
            print("  ✅ Testing OpenAI client...")
            analyzer = EnhancedLegalAnalyzer("openai")
            print(f"     OpenAI client initialized: {analyzer.client is not None}")
        else:
            print("  ⚠️  OpenAI API key not found - skipping OpenAI test")

        # Test Anthropic client (if API key available)
        if os.getenv("ANTHROPIC_API_KEY"):
            print("  ✅ Testing Anthropic client...")
            analyzer = EnhancedLegalAnalyzer("anthropic")
            print(f"     Anthropic client initialized: {analyzer.client is not None}")
        else:
            print("  ⚠️  Anthropic API key not found - skipping Anthropic test")

    except Exception as e:
        print(f"  ❌ Error testing LLM clients: {e}")


def test_database():
    """Test database functionality"""
    print("\n🗄️ Testing Database Functionality...")

    try:
        from .legal_case_database import LegalCaseDatabase

        # Create temporary database
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name

        print(f"  📍 Using temporary database: {db_path}")

        # Initialize database
        db = LegalCaseDatabase(db_path)
        print("  ✅ Database initialized successfully")

        # Test adding a case
        test_case = {
            "appeal_number": "TEST001",
            "date": "2024-01-01",
            "appeal_type": "Compensation",
            "decision_type": "Merit",
            "issues": "Test case for spinal stenosis from warehouse work",
            "case_summary": "Worker developed spinal stenosis from repetitive lifting",
            "outcome": "Appeal allowed - condition deemed work-related",
            "pdf_url": "https://example.com/test.pdf",
            "pdf_path": None,
            "full_text": "Full case text...",
            "keywords": ["stenosis", "warehouse", "lifting", "work-related"],
        }

        case_id = db.add_case(test_case)
        print(f"  ✅ Test case added with ID: {case_id}")

        # Test search
        results = db.search_cases("stenosis", limit=5)
        print(f"  ✅ Search found {len(results)} cases")

        # Test similarity search
        similar = db.find_similar_cases(
            user_keywords=["stenosis", "warehouse"],
            user_case_summary="I have spinal stenosis from warehouse work",
            min_similarity=0.1,
        )
        print(f"  ✅ Similarity search found {len(similar)} similar cases")

        # Get statistics
        stats = db.get_case_statistics()
        print(f"  ✅ Database statistics: {stats['total_cases']} total cases")

        # Clean up
        Path(db_path).unlink(missing_ok=True)
        print("  🧹 Temporary database cleaned up")

    except Exception as e:
        print(f"  ❌ Error testing database: {e}")


def test_enhanced_workflow():
    """Test enhanced legal workflow"""
    print("\n🔬 Testing Enhanced Legal Workflow...")

    try:
        from .enhanced_legal_features import create_enhanced_legal_workflow

        # Test case data
        user_case = {
            "summary": "Warehouse worker with spinal stenosis from repetitive lifting",
            "keywords": ["stenosis", "warehouse", "lifting"],
            "appellant_name": "Test User",
            "appellant_address": "123 Test St, Test City, TC",
        }

        existing_cases = [
            {
                "appeal_number": "A2024001",
                "issues": "Spinal stenosis from warehouse work",
                "outcome": "Appeal allowed",
                "similarity_score": 0.9,
            }
        ]

        # Run workflow
        results = create_enhanced_legal_workflow(user_case, existing_cases)
        print("  ✅ Enhanced workflow completed successfully")
        print(f"     Workflow ID: {results.get('workflow_id', 'N/A')}")
        print(f"     Created: {results.get('created_at', 'N/A')}")

        if results.get("enhanced_strategy"):
            print("  ✅ Enhanced strategy generated")

        if results.get("generated_documents"):
            print("  ✅ Documents generated")

    except Exception as e:
        print(f"  ❌ Error testing enhanced workflow: {e}")


def main():
    """Run all tests"""
    print("🧪 Legal Research System - Fix Verification Tests")
    print("=" * 60)

    test_llm_clients()
    test_database()
    test_enhanced_workflow()

    print("\n" + "=" * 60)
    print("✅ Test suite completed!")
    print("\n💡 Next steps:")
    print("   1. Set API keys: OPENAI_API_KEY or ANTHROPIC_API_KEY")
    print("   2. Set database path: WCAT_DATABASE_PATH")
    print("   3. Test the web UI legal research tab")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Enhanced Legal Research Demo

This script demonstrates the advanced features of the enhanced legal research system:
1. LLM-powered case analysis and strategy generation
2. Automated legal document generation
3. Multi-jurisdictional research capabilities
4. Case progress tracking
5. Database integration with enhanced search
"""

import logging
import os
from datetime import datetime
from pathlib import Path

from .enhanced_legal_features import (
    CaseProgressTracker,
    EnhancedLegalAnalyzer,
    LegalDocumentGenerator,
    MultiJurisdictionalResearcher,
    create_enhanced_legal_workflow,
)
from .legal_case_database import LegalCaseDatabase

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def demo_enhanced_legal_analyzer():
    """Demonstrate the enhanced LLM-powered legal analyzer"""
    print("🧠 Enhanced Legal Analyzer Demo")
    print("=" * 50)

    # Sample user case
    user_case = {
        "summary": """
        I worked as a warehouse employee for 3 years, performing repetitive heavy lifting of packages
        weighing 40-60 pounds. Over time, I developed spinal stenosis at L4-L5 with associated
        radiculopathy causing pain and numbness in my right leg. The condition has been diagnosed
        through MRI and confirmed by a specialist. I believe this is work-related due to the
        repetitive nature of my job and the gradual onset of symptoms during my employment.
        """,
        "keywords": ["stenosis", "warehouse", "lifting", "employment", "radiculopathy"],
        "appellant_name": "John Smith",
        "appellant_address": "123 Main St, Vancouver, BC V5K 1A1",
    }

    # Sample similar cases (would normally come from database)
    similar_cases = [
        {
            "appeal_number": "A2024001",
            "date": "2024-01-15",
            "issues": "Worker developed spinal stenosis from repetitive lifting in warehouse environment",
            "outcome": "Appeal allowed - condition deemed work-related",
            "similarity_score": 0.95,
        },
        {
            "appeal_number": "A2023045",
            "date": "2023-08-20",
            "issues": "Disc herniation at L4-L5 from warehouse work involving heavy lifting",
            "outcome": "Appeal allowed - employment causation established",
            "similarity_score": 0.88,
        },
        {
            "appeal_number": "A2023012",
            "date": "2023-03-10",
            "issues": "Radiculopathy claimed as workplace injury from repetitive lifting",
            "outcome": "Appeal dismissed - insufficient evidence of workplace causation",
            "similarity_score": 0.72,
        },
    ]

    try:
        # Initialize enhanced analyzer
        print("🔧 Initializing Enhanced Legal Analyzer...")
        analyzer = EnhancedLegalAnalyzer("openai")  # or "anthropic"

        # Generate legal strategy
        print("⚖️ Generating AI-powered legal strategy...")
        strategy = analyzer.generate_legal_strategy(user_case, similar_cases)

        if strategy.get("error"):
            print(f"❌ Error: {strategy['error']}")
            print(
                "💡 Note: Make sure to set your OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable"
            )
        else:
            print("✅ Legal Strategy Generated!")
            print("\n📋 Strategy Analysis:")
            print(strategy.get("raw_analysis", "No analysis available")[:500] + "...")

            if strategy.get("key_points"):
                print("\n🎯 Key Strategic Points:")
                for i, point in enumerate(strategy["key_points"][:5], 1):
                    print(f"   {i}. {point}")

    except Exception as e:
        print(f"❌ Error in legal analyzer demo: {e}")
        print("💡 This may be due to missing API keys or network issues")


def demo_document_generator():
    """Demonstrate the legal document generator"""
    print("\n📄 Legal Document Generator Demo")
    print("=" * 50)

    try:
        # Initialize document generator
        doc_generator = LegalDocumentGenerator()

        # Sample case details
        case_details = {
            "appellant_name": "John Smith",
            "appellant_address": "123 Main St\nVancouver, BC V5K 1A1",
            "grounds": "Developed spinal stenosis from repetitive heavy lifting in warehouse employment",
            "remedy": "Appeal decision and grant compensation for work-related spinal injury",
            "precedents": [
                {
                    "appeal_number": "A2024001",
                    "outcome": "Appeal allowed - condition deemed work-related",
                },
                {
                    "appeal_number": "A2023045",
                    "outcome": "Appeal allowed - employment causation established",
                },
            ],
        }

        # Generate appeal notice
        print("📝 Generating Notice of Appeal...")
        appeal_notice = doc_generator.generate_appeal_notice(case_details)

        print("✅ Appeal Notice Generated!")
        print("\n📋 Generated Document (Preview):")
        print("-" * 40)
        print(
            appeal_notice[:800] + "\n..." if len(appeal_notice) > 800 else appeal_notice
        )
        print("-" * 40)

        # Save document
        output_dir = Path("./tmp/enhanced_demo/documents")
        output_dir.mkdir(parents=True, exist_ok=True)

        doc_file = (
            output_dir
            / f"appeal_notice_demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        with open(doc_file, "w", encoding="utf-8") as f:
            f.write(appeal_notice)

        print(f"💾 Document saved to: {doc_file}")

    except Exception as e:
        print(f"❌ Error in document generator demo: {e}")


def demo_case_progress_tracker():
    """Demonstrate the case progress tracker"""
    print("\n📅 Case Progress Tracker Demo")
    print("=" * 50)

    try:
        # Initialize case tracker
        tracker_db = "./tmp/enhanced_demo/case_tracking_demo.db"
        case_tracker = CaseProgressTracker(tracker_db)

        # Add sample milestones
        case_id = "demo_case_001"

        print("📌 Adding case milestones...")
        case_tracker.add_case_milestone(
            case_id,
            "Initial Research",
            "2025-01-31",
            "Completed initial case research and similar case analysis",
        )

        case_tracker.add_case_milestone(
            case_id,
            "Evidence Gathering",
            "2025-02-15",
            "Collect medical reports and employment records",
        )

        case_tracker.add_case_milestone(
            case_id, "Appeal Filed", "2025-02-28", "Submit appeal notice to WCAT"
        )

        # Get upcoming deadlines
        print("⏰ Checking upcoming deadlines...")
        deadlines = case_tracker.get_upcoming_deadlines(60)  # Next 60 days

        if deadlines:
            print("✅ Upcoming Deadlines:")
            for deadline in deadlines:
                print(f"   📋 {deadline['case_stage']} - {deadline['next_deadline']}")
                print(f"      Notes: {deadline.get('notes', 'No notes')}")
        else:
            print("📝 No upcoming deadlines found (this is expected for demo data)")

        print(f"💾 Case tracking database: {tracker_db}")

    except Exception as e:
        print(f"❌ Error in case progress tracker demo: {e}")


def demo_multi_jurisdictional_search():
    """Demonstrate multi-jurisdictional search capabilities"""
    print("\n🌐 Multi-Jurisdictional Research Demo")
    print("=" * 50)

    try:
        # Initialize multi-jurisdictional researcher
        multi_researcher = MultiJurisdictionalResearcher()

        # Sample search
        query = "spinal stenosis workplace injury"
        jurisdictions = ["bc_wcat", "canlii"]

        print(f"🔍 Searching multiple jurisdictions for: '{query}'")
        print(f"📚 Jurisdictions: {', '.join(jurisdictions)}")

        # Perform search (note: this is a placeholder implementation)
        results = multi_researcher.search_multiple_jurisdictions(query, jurisdictions)

        print("✅ Multi-jurisdictional search completed!")
        print("\n📊 Results by Jurisdiction:")

        for jurisdiction, cases in results.items():
            print(f"   🏛️ {jurisdiction.upper()}: {len(cases)} cases found")
            if cases:
                # Show first few results (if any)
                for i, case in enumerate(cases[:2], 1):
                    print(f"      {i}. Sample case result")

        print("\n💡 Note: This is a placeholder implementation.")
        print("   In production, this would search actual legal databases.")

    except Exception as e:
        print(f"❌ Error in multi-jurisdictional search demo: {e}")


async def demo_enhanced_workflow():
    """Demonstrate the complete enhanced legal workflow"""
    print("\n🔬 Enhanced Legal Workflow Demo")
    print("=" * 50)

    try:
        # Sample user case
        user_case = {
            "summary": "Warehouse worker with spinal stenosis from repetitive lifting",
            "keywords": ["stenosis", "warehouse", "lifting", "employment"],
            "appellant_name": "Jane Doe",
            "appellant_address": "456 Oak St, Vancouver, BC V6B 2M1",
        }

        # Sample existing cases (would come from database in real scenario)
        existing_cases = [
            {
                "appeal_number": "A2024001",
                "issues": "Spinal stenosis from warehouse lifting",
                "outcome": "Appeal allowed",
                "similarity_score": 0.9,
            }
        ]

        print("🚀 Running complete enhanced legal workflow...")

        # Run the enhanced workflow
        results = create_enhanced_legal_workflow(user_case, existing_cases)

        print("✅ Enhanced workflow completed!")
        print("\n📊 Workflow Results:")
        print(f"   🆔 Workflow ID: {results.get('workflow_id', 'N/A')}")
        print(f"   📅 Created: {results.get('created_at', 'N/A')}")

        if results.get("enhanced_strategy"):
            print("   🧠 Enhanced Strategy: Generated")

        if results.get("additional_cases"):
            print("   🔍 Additional Cases: Found")

        if results.get("generated_documents"):
            print("   📄 Documents: Generated")

        # Save workflow results
        output_dir = Path("./tmp/enhanced_demo/workflows")
        output_dir.mkdir(parents=True, exist_ok=True)

        import json

        results_file = (
            output_dir
            / f"workflow_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"💾 Workflow results saved to: {results_file}")

    except Exception as e:
        print(f"❌ Error in enhanced workflow demo: {e}")


def demo_database_integration():
    """Demonstrate enhanced database integration"""
    print("\n🗄️ Enhanced Database Integration Demo")
    print("=" * 50)

    try:
        # Get database path from environment or use default
        db_path = os.getenv(
            "WCAT_DATABASE_PATH", "./tmp/enhanced_demo/enhanced_cases.db"
        )
        database = LegalCaseDatabase(db_path)

        print(f"📊 Database location: {db_path}")

        # Get database statistics
        stats = database.get_case_statistics()
        print("\n📈 Database Statistics:")
        print(f"   📚 Total cases: {stats['total_cases']}")

        if stats.get("common_keywords"):
            print("   🔤 Most common keywords:")
            for keyword in stats["common_keywords"][:5]:
                print(f"      - {keyword['keyword']} ({keyword['frequency']} times)")

        # Demo enhanced search
        print("\n🔍 Testing enhanced database search...")
        search_results = database.search_cases(
            query="stenosis warehouse",
            filters={"keywords": ["stenosis", "employment"]},
            limit=5,
        )

        print(f"✅ Found {len(search_results)} matching cases")

        for i, case in enumerate(search_results[:3], 1):
            print(f"   {i}. {case['appeal_number']} - {case['date']}")
            print(f"      Issues: {case['issues'][:60]}...")

        # Demo similarity search
        print("\n🔗 Testing case similarity search...")
        similar_cases = database.find_similar_cases(
            user_keywords=["stenosis", "warehouse", "lifting"],
            user_case_summary="Warehouse worker with spinal stenosis",
            min_similarity=0.1,
            limit=3,
        )

        print(f"✅ Found {len(similar_cases)} similar cases")

        for i, case in enumerate(similar_cases, 1):
            similarity = case.get("similarity_score", 0)
            print(f"   {i}. {case['appeal_number']} (Similarity: {similarity:.2f})")

    except Exception as e:
        print(f"❌ Error in database integration demo: {e}")


async def main():
    """Run the complete enhanced legal research demo"""
    print("🏛️ Enhanced Legal Research System Demo")
    print("=" * 60)
    print(
        "This demo showcases the advanced features of the enhanced legal research system."
    )
    print("=" * 60)

    # Create demo output directory
    output_dir = Path("./tmp/enhanced_demo")
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Run all demos
        await demo_enhanced_legal_analyzer()
        demo_document_generator()
        demo_case_progress_tracker()
        demo_multi_jurisdictional_search()
        await demo_enhanced_workflow()
        demo_database_integration()

        print("\n" + "=" * 60)
        print("✅ Enhanced Legal Research Demo Completed Successfully!")
        print("=" * 60)
        print(f"📁 Demo files saved to: {output_dir.absolute()}")
        print("\n💡 Next Steps:")
        print(
            "   1. Set up API keys for LLM providers (OPENAI_API_KEY or ANTHROPIC_API_KEY)"
        )
        print("   2. Configure WCAT_DATABASE_PATH environment variable")
        print("   3. Use the enhanced legal research tab in the web UI")
        print("   4. Explore the generated documents and workflow results")

    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        logger.error(f"Demo error: {e}", exc_info=True)


if __name__ == "__main__":
    print("Starting Enhanced Legal Research Demo...")

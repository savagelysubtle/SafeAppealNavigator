#!/usr/bin/env python3
"""
Command-line demo for the Legal Case Research Agent

This script demonstrates the full functionality of the legal research agent
including searching WCAT cases, building a database, and generating legal arguments.
"""

import asyncio
import logging
from datetime import datetime

from .legal_case_agent import run_legal_research_task
from .legal_case_database import LegalCaseDatabase

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def demo_legal_research():
    """Demonstrate the legal research agent"""
    print("🏛️ Legal Case Research Agent Demo")
    print("=" * 50)

    # Sample user case
    user_case_summary = """
    I worked as a warehouse employee for 3 years, performing repetitive heavy lifting of packages
    weighing 40-60 pounds. Over time, I developed spinal stenosis at L4-L5 with associated
    radiculopathy causing pain and numbness in my right leg. The condition has been diagnosed
    through MRI and confirmed by a specialist. I believe this is work-related due to the
    repetitive nature of my job and the gradual onset of symptoms during my employment.
    """

    # Search queries
    search_queries = [
        "stenosis",
        "spinal injury warehouse",
        "repetitive lifting back injury",
    ]

    # Date range (last 5 years)
    date_range = {"start_date": "2019-01-01", "end_date": "2024-12-31"}

    # Browser configuration
    browser_config = {
        "headless": True,
        "window_width": 1280,
        "window_height": 1100,
        "disable_security": False,
    }

    task_id = f"demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    print(f"Task ID: {task_id}")
    print(f"User Case: {user_case_summary.strip()}")
    print(f"Search Queries: {search_queries}")
    print(f"Date Range: {date_range['start_date']} to {date_range['end_date']}")
    print("\nStarting research...\n")

    try:
        # Run the legal research
        results = await run_legal_research_task(
            search_queries=search_queries,
            user_case_summary=user_case_summary,
            task_id=task_id,
            browser_config=browser_config,
            date_range=date_range,
            max_cases_per_query=10,  # Smaller number for demo
            download_dir="./tmp/legal_research_demo",
        )

        print("✅ Research completed!")
        print_results(results)

        # Demonstrate database functionality
        print("\n" + "=" * 50)
        print("📊 Database Functionality Demo")
        print("=" * 50)

        db_path = "./tmp/legal_research_demo/cases.db"
        db = LegalCaseDatabase(db_path)

        # Show database statistics
        stats = db.get_case_statistics()
        print(f"Total cases in database: {stats['total_cases']}")
        print(f"Database path: {stats['database_path']}")

        # Demonstrate search functionality
        print("\n🔍 Searching database for 'stenosis':")
        search_results = db.search_cases(query="stenosis", limit=5)

        for i, case in enumerate(search_results[:3], 1):
            print(f"\n{i}. Case {case['appeal_number']} ({case['date']})")
            print(f"   Issues: {case['issues'][:100]}...")
            if case["outcome"]:
                print(f"   Outcome: {case['outcome'][:100]}...")

        # Find similar cases
        print("\n🔗 Finding cases similar to user's case:")
        user_keywords = ["stenosis", "warehouse", "lifting", "employment", "spinal"]
        similar_cases = db.find_similar_cases(
            user_keywords=user_keywords,
            user_case_summary=user_case_summary,
            min_similarity=0.1,
            limit=3,
        )

        for i, case in enumerate(similar_cases, 1):
            similarity = case.get("similarity_score", 0)
            print(f"\n{i}. Case {case['appeal_number']} (Similarity: {similarity:.2f})")
            print(f"   Issues: {case['issues'][:100]}...")

        return results

    except Exception as e:
        logger.error(f"Error during demo: {e}", exc_info=True)
        return None


def print_results(results):
    """Print formatted results"""
    print("\n📊 Research Results:")
    print(f"   Task ID: {results.get('task_id')}")
    print(f"   Status: {results.get('status')}")
    print(f"   Total cases found: {results.get('total_cases_found', 0)}")
    print(f"   Similar cases: {len(results.get('similar_cases', []))}")
    print(f"   Confidence score: {results.get('confidence_score', 0):.2f}")

    # Legal arguments
    legal_args = results.get("legal_arguments", {})
    if legal_args:
        print("\n⚖️ Legal Arguments:")
        print(f"   Favorable precedents: {legal_args.get('favorable_precedents', 0)}")
        print(
            f"   Unfavorable precedents: {legal_args.get('unfavorable_precedents', 0)}"
        )

        key_args = legal_args.get("key_arguments", [])
        if key_args:
            print("\n🎯 Key Arguments:")
            for i, arg in enumerate(key_args, 1):
                print(f"   {i}. {arg}")

        recommendations = legal_args.get("recommendations", [])
        if recommendations:
            print("\n💡 Recommendations:")
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. {rec}")

    # Similar cases
    similar_cases = results.get("similar_cases", [])
    if similar_cases:
        print("\n📚 Most Similar Cases:")
        for i, case in enumerate(similar_cases[:3], 1):
            similarity = case.get("similarity_score", 0)
            print(
                f"\n   {i}. Case {case['appeal_number']} (Similarity: {similarity:.2f})"
            )
            print(f"      Date: {case['date']}")
            print(f"      Issues: {case['issues'][:100]}...")
            if case.get("outcome"):
                print(f"      Outcome: {case['outcome'][:100]}...")


async def quick_database_demo():
    """Quick demonstration of database functionality without web scraping"""
    print("📊 Quick Database Demo (No Web Scraping)")
    print("=" * 50)

    db_path = "./tmp/legal_research_demo/cases_demo.db"
    db = LegalCaseDatabase(db_path)

    # Add sample cases
    sample_cases = [
        {
            "appeal_number": "A2024001",
            "date": "2024-01-15",
            "appeal_type": "Compensation",
            "decision_type": "Merit",
            "issues": "Worker developed spinal stenosis from repetitive lifting in warehouse environment",
            "case_summary": "The worker claimed spinal stenosis developed due to workplace duties involving heavy lifting",
            "outcome": "Appeal allowed - condition deemed work-related",
            "pdf_url": "https://example.com/case1.pdf",
            "pdf_path": None,
            "full_text": "Full decision text about spinal stenosis and workplace causation...",
            "keywords": ["stenosis", "warehouse", "lifting", "employment", "causation"],
        },
        {
            "appeal_number": "A2024002",
            "date": "2024-02-20",
            "appeal_type": "Compensation",
            "decision_type": "Merit",
            "issues": "Disc herniation claimed as workplace injury from construction work",
            "case_summary": "Construction worker claimed disc herniation from workplace activities",
            "outcome": "Appeal dismissed - insufficient evidence of workplace causation",
            "pdf_url": "https://example.com/case2.pdf",
            "pdf_path": None,
            "full_text": "Full decision text about disc herniation and workplace evidence...",
            "keywords": ["disc herniation", "construction", "workplace", "evidence"],
        },
    ]

    print("Adding sample cases to database...")
    for case in sample_cases:
        case_id = db.add_case(case)
        print(f"Added case {case['appeal_number']} with ID {case_id}")

    # Demonstrate search
    print("\n🔍 Searching for 'stenosis':")
    results = db.search_cases(query="stenosis", limit=5)
    for result in results:
        print(f"- {result['appeal_number']}: {result['issues']}")

    # Demonstrate similarity search
    print("\n🔗 Finding similar cases:")
    similar = db.find_similar_cases(
        user_keywords=["stenosis", "warehouse", "lifting"],
        user_case_summary="I have spinal stenosis from warehouse work",
        min_similarity=0.1,
    )

    for case in similar:
        similarity = case.get("similarity_score", 0)
        print(f"- {case['appeal_number']} (Similarity: {similarity:.2f})")

    # Show statistics
    stats = db.get_case_statistics()
    print("\n📊 Database Statistics:")
    print(f"Total cases: {stats['total_cases']}")
    print(f"Database path: {stats['database_path']}")


if __name__ == "__main__":
    print("Legal Case Research Agent Demo")
    print("Choose demo mode:")
    print("1. Quick database demo (no web scraping)")
    print("2. Full research demo (includes web scraping)")

    choice = input("Enter choice (1 or 2): ").strip()

    if choice == "1":
        asyncio.run(quick_database_demo())
    elif choice == "2":
        asyncio.run(demo_legal_research())
    else:
        print("Invalid choice. Running quick demo...")
        asyncio.run(quick_database_demo())

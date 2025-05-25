"""
WCB Legal Intake Workflow Example

This example demonstrates how to use the Enhanced Legal Intake Agent
to process large WCB file dumps and prepare them for legal research.

Usage:
    python wcb_workflow_example.py --dump_dir "/path/to/wcb/files" --case_id "WCB_CASE_2024_001"
"""

import argparse
import asyncio
import json
import logging
from pathlib import Path

from enhanced_legal_intake import EnhancedLegalIntakeAgent

from ..core import AgentTask, TaskPriority

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WCBWorkflowManager:
    """
    Manager for orchestrating the complete WCB legal intake workflow.

    This demonstrates the full pipeline from file dump to legal research preparation.
    """

    def __init__(self, output_dir: str = "./tmp/wcb_processing"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize the enhanced legal intake agent
        self.legal_intake_agent = EnhancedLegalIntakeAgent(
            case_organization_directory=str(self.output_dir / "organized_cases"),
            intake_directory=str(self.output_dir / "intake"),
            processed_directory=str(self.output_dir / "processed"),
        )

        logger.info(
            f"WCB Workflow Manager initialized with output directory: {self.output_dir}"
        )

    async def process_wcb_dump(self, dump_directory: str, case_id: str = None) -> dict:
        """
        Complete workflow for processing a WCB file dump.

        Args:
            dump_directory: Path to the directory containing WCB files
            case_id: Optional case identifier

        Returns:
            Complete results of the processing workflow
        """
        logger.info(f"🚀 Starting WCB dump processing for: {dump_directory}")

        # Create task for the main processing workflow
        task = AgentTask(
            task_type="process_legal_dump",
            parameters={"dump_directory": dump_directory, "case_id": case_id},
            priority=TaskPriority.HIGH,
        )

        # Execute the main workflow
        result = await self.legal_intake_agent.execute_task(task)

        if result["success"]:
            logger.info("✅ WCB dump processing completed successfully")
            await self._print_workflow_summary(result)
        else:
            logger.error(f"❌ WCB dump processing failed: {result.get('error')}")

        return result

    async def _print_workflow_summary(self, result: dict):
        """Print a comprehensive summary of the workflow results."""
        print("\n" + "=" * 80)
        print("🎯 WCB LEGAL INTAKE WORKFLOW SUMMARY")
        print("=" * 80)

        print(f"📁 Case ID: {result['case_id']}")
        print(f"📂 Case Directory: {result['case_directory']}")
        print(f"⏱️  Processing Time: {result['start_time']} → {result['end_time']}")

        print("\n📊 PROCESSING STATISTICS:")
        print(f"   • Total Files Processed: {result['total_files_processed']}")
        print(f"   • Documents Organized: {result['documents_organized']}")
        print(f"   • Search Points Generated: {result['search_points_generated']}")
        print(f"   • Timeline Events: {result['timeline_events']}")

        # Stage-by-stage breakdown
        print("\n🔍 STAGE BREAKDOWN:")
        for stage_name, stage_result in result.get("stages", {}).items():
            if isinstance(stage_result, dict) and stage_result.get("success"):
                print(f"   ✅ {stage_name.title()}: Success")
            else:
                print(f"   ❌ {stage_name.title()}: Failed")

        # Document organization summary
        if "processing" in result.get("stages", {}):
            categorized = result["stages"]["processing"].get("categorized_files", {})
            if categorized:
                print("\n📋 DOCUMENT CATEGORIZATION:")
                for doc_type, files in categorized.items():
                    print(
                        f"   • {doc_type.replace('_', ' ').title()}: {len(files)} files"
                    )

        # Search points preview
        if "search_points" in result.get("stages", {}):
            search_points = result["stages"]["search_points"].get("search_points", [])
            if search_points:
                print("\n🔎 SEARCH POINTS GENERATED:")
                for i, sp in enumerate(search_points[:3], 1):  # Show first 3
                    print(
                        f"   {i}. {sp['search_type']}: {', '.join(sp['keywords'][:3])}"
                    )
                if len(search_points) > 3:
                    print(f"   ... and {len(search_points) - 3} more search points")

        print("\n🚀 NEXT STEPS:")
        print(f"   1. Review organized documents in: {result['case_directory']}")
        print("   2. Execute legal research using generated search points")
        print("   3. Analyze case timeline for key events")
        print("   4. Prepare legal arguments based on categorized evidence")

        print("=" * 80 + "\n")

    async def demonstrate_document_types(self, sample_dir: str):
        """
        Demonstrate WCB document type identification on sample files.
        """
        print("\n🔍 DEMONSTRATING WCB DOCUMENT TYPE IDENTIFICATION")
        print("-" * 60)

        sample_path = Path(sample_dir)
        if not sample_path.exists():
            print(f"❌ Sample directory not found: {sample_dir}")
            return

        for file_path in sample_path.glob("*"):
            if file_path.is_file() and file_path.suffix.lower() in {
                ".pdf",
                ".docx",
                ".txt",
            }:
                print(f"\n📄 Analyzing: {file_path.name}")

                # Extract content
                content_result = await self.legal_intake_agent._extract_text_content(
                    file_path
                )
                if content_result["success"]:
                    # Identify document type
                    type_result = (
                        await self.legal_intake_agent._identify_wcb_document_type(
                            {
                                "content": content_result["content"][
                                    :1000
                                ],  # First 1000 chars
                                "file_path": str(file_path),
                            }
                        )
                    )

                    doc_type = type_result.get("wcb_document_type", "unknown")
                    confidence = type_result.get("confidence", 0.0)
                    method = type_result.get("method", "unknown")

                    print(f"   📋 Document Type: {doc_type}")
                    print(f"   🎯 Confidence: {confidence:.2f}")
                    print(f"   🔧 Method: {method}")

                    # Extract key entities
                    entities_result = (
                        await self.legal_intake_agent._extract_legal_entities(
                            {
                                "content": content_result["content"][:2000],
                                "document_type": doc_type,
                            }
                        )
                    )

                    if entities_result["success"]:
                        entities = entities_result["entities"]
                        print("   🏷️  Key Entities:")
                        for entity_type, values in entities.items():
                            if values:
                                print(f"      • {entity_type}: {', '.join(values[:3])}")

    async def batch_process_multiple_cases(self, dump_directories: list):
        """
        Demonstrate batch processing of multiple WCB case dumps.
        """
        print(f"\n⚡ BATCH PROCESSING {len(dump_directories)} WCB CASE DUMPS")
        print("-" * 60)

        task = AgentTask(
            task_type="batch_legal_organize",
            parameters={"dump_directories": dump_directories},
            priority=TaskPriority.HIGH,
        )

        result = await self.legal_intake_agent.execute_task(task)

        if result["success"]:
            print("✅ Batch processing completed!")
            print(f"   • Total dumps processed: {result['total_dumps_processed']}")
            print(f"   • Successful cases: {result['successful_cases']}")

            for batch_result in result["batch_results"]:
                case_id = batch_result.get("case_id", "unknown")
                success = batch_result.get("result", {}).get("success", False)
                status = "✅" if success else "❌"
                print(f"   {status} {case_id}: {'Success' if success else 'Failed'}")
        else:
            print(f"❌ Batch processing failed: {result.get('error')}")

    async def generate_case_report(self, case_id: str):
        """
        Generate a comprehensive case report after processing.
        """
        print(f"\n📊 GENERATING CASE REPORT FOR: {case_id}")
        print("-" * 60)

        summary = await self.legal_intake_agent.get_case_summary(case_id)

        if summary["success"]:
            print(f"📁 Case Directory: {summary['case_directory']}")
            print(f"📋 Total Documents: {summary['total_documents']}")
            print(
                f"🏷️  Organization Status: {summary.get('organization_complete', 'Unknown')}"
            )

            print("\n📂 Document Distribution:")
            for doc_type, count in summary.get("document_counts", {}).items():
                print(f"   • {doc_type.replace('_', ' ').title()}: {count} files")

            # Load and display search points if available
            case_dir = Path(summary["case_directory"])
            search_points_file = case_dir / "search_points" / "legal_search_points.json"

            if search_points_file.exists():
                with open(search_points_file, "r") as f:
                    search_points = json.load(f)

                print("\n🔍 Search Points Summary:")
                priority_counts = {}
                for sp in search_points:
                    priority = sp.get("priority", "unknown")
                    priority_counts[priority] = priority_counts.get(priority, 0) + 1

                for priority, count in priority_counts.items():
                    print(f"   • {priority.title()} Priority: {count} search points")
        else:
            print(f"❌ Could not generate report: {summary.get('error')}")


async def main():
    """Main example execution."""
    parser = argparse.ArgumentParser(description="WCB Legal Intake Workflow Example")
    parser.add_argument(
        "--dump_dir", required=True, help="Path to WCB file dump directory"
    )
    parser.add_argument("--case_id", help="Optional case identifier")
    parser.add_argument(
        "--demo_types", help="Path to sample files for document type demo"
    )
    parser.add_argument(
        "--batch_dirs", nargs="+", help="Multiple directories for batch processing"
    )

    args = parser.parse_args()

    # Initialize workflow manager
    workflow_manager = WCBWorkflowManager()

    try:
        # Main processing workflow
        if args.dump_dir:
            print("🏥 STARTING WCB LEGAL INTAKE WORKFLOW")
            print("=" * 80)

            result = await workflow_manager.process_wcb_dump(
                dump_directory=args.dump_dir, case_id=args.case_id
            )

            # Generate case report
            if result["success"]:
                await workflow_manager.generate_case_report(result["case_id"])

        # Optional demonstrations
        if args.demo_types:
            await workflow_manager.demonstrate_document_types(args.demo_types)

        if args.batch_dirs:
            await workflow_manager.batch_process_multiple_cases(args.batch_dirs)

    except Exception as e:
        logger.error(f"Workflow execution failed: {e}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))

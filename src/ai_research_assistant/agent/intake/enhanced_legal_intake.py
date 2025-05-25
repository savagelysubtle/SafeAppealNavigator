"""
Enhanced Legal Intake Agent for WCB Case Processing

This module extends the base IntakeAgent with specialized workflows for:
- Mass WCB legal file processing
- Automatic document organization and categorization
- Legal document type identification
- Search point generation for Legal Research Agent
- Case timeline reconstruction
"""

import json
import logging
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core import AgentTask
from ..legal_research.legal_case_database import LegalCaseDatabase
from .intake_agent import IntakeAgent

logger = logging.getLogger(__name__)


class WCBDocumentType:
    """WCB-specific document classifications"""

    # Primary Categories
    DECISION = "decision"
    LETTER = "letter"
    CASE_FILE = "case_file"
    REVIEW_FILE = "review_file"
    MEDICAL_REPORT = "medical_report"
    EMPLOYMENT_RECORD = "employment_record"
    FORM = "form"
    CORRESPONDENCE = "correspondence"

    # Sub-categories
    TRIBUNAL_DECISION = "tribunal_decision"
    BOARD_DECISION = "board_decision"
    APPEAL_DECISION = "appeal_decision"
    INITIAL_DECISION = "initial_decision"

    CLAIM_LETTER = "claim_letter"
    DENIAL_LETTER = "denial_letter"
    APPROVAL_LETTER = "approval_letter"
    REQUEST_LETTER = "request_letter"

    UNKNOWN = "unknown"


class LegalSearchPoint:
    """Structure for legal research search points"""

    def __init__(
        self,
        search_type: str,
        keywords: List[str],
        context: str,
        priority: str = "medium",
        document_refs: Optional[List[str]] = None,
    ):
        self.search_type = search_type
        self.keywords = keywords
        self.context = context
        self.priority = priority
        self.document_refs = document_refs or []
        self.created_at = datetime.now().isoformat()


class EnhancedLegalIntakeAgent(IntakeAgent):
    """
    Enhanced intake agent specialized for WCB legal case processing.

    Capabilities:
    - Mass file dump processing with intelligent organization
    - WCB-specific document type identification
    - Legal timeline reconstruction
    - Automatic case file organization
    - Search point generation for legal research
    - Integration with legal case database
    """

    def __init__(
        self,
        legal_case_db: Optional[LegalCaseDatabase] = None,
        case_organization_directory: str = "./tmp/organized_cases",
        **kwargs,
    ):
        super().__init__(**kwargs)

        # Legal-specific configuration
        self.legal_db = legal_case_db or LegalCaseDatabase()
        self.case_org_dir = Path(case_organization_directory)
        self.case_org_dir.mkdir(parents=True, exist_ok=True)

        # WCB document patterns for classification
        self.wcb_patterns = self._initialize_wcb_patterns()

        # Case processing state
        self.current_case_id: Optional[str] = None
        self.current_case_files: List[Path] = []
        self.case_timeline: List[Dict[str, Any]] = []
        self.search_points: List[LegalSearchPoint] = []
        self.case_entities: Dict[str, List[str]] = {}

        logger.info(f"Enhanced Legal Intake Agent initialized: {self.agent_id}")

    def get_supported_task_types(self) -> List[str]:
        """Return enhanced task types including legal-specific operations."""
        base_tasks = super().get_supported_task_types()
        legal_tasks = [
            "process_legal_dump",
            "organize_case_files",
            "identify_wcb_document_type",
            "extract_legal_entities",
            "generate_search_points",
            "reconstruct_case_timeline",
            "prepare_legal_research",
            "batch_legal_organize",
        ]
        return base_tasks + legal_tasks

    async def execute_task(self, task: AgentTask) -> Dict[str, Any]:
        """Execute legal-specific tasks or delegate to base agent."""
        task_type = task.task_type
        params = task.parameters

        # Handle legal-specific tasks
        legal_tasks = {
            "process_legal_dump": self._process_legal_dump,
            "organize_case_files": self._organize_case_files,
            "identify_wcb_document_type": self._identify_wcb_document_type,
            "extract_legal_entities": self._extract_legal_entities,
            "generate_search_points": self._generate_search_points,
            "reconstruct_case_timeline": self._reconstruct_case_timeline,
            "prepare_legal_research": self._prepare_legal_research,
            "batch_legal_organize": self._batch_legal_organize,
        }

        if task_type in legal_tasks:
            try:
                return await legal_tasks[task_type](params)
            except Exception as e:
                logger.error(
                    f"Legal task execution failed for {task_type}: {e}", exc_info=True
                )
                return {
                    "success": False,
                    "error": str(e),
                    "task_id": task.id,
                    "task_type": task_type,
                }
        else:
            # Delegate to base agent
            return await super().execute_task(task)

    async def _process_legal_dump(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main workflow for processing large legal file dumps.

        Steps:
        1. Validate and scan dump directory
        2. Create case organization structure
        3. Process and categorize all files
        4. Extract legal entities and metadata
        5. Reconstruct case timeline
        6. Generate search points for legal research
        7. Prepare database entries
        """
        dump_directory = params.get("dump_directory")
        case_id = (
            params.get("case_id") or f"case_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )

        if not dump_directory:
            return {"success": False, "error": "dump_directory parameter required"}

        dump_path = Path(dump_directory)
        if not dump_path.exists():
            return {
                "success": False,
                "error": f"Dump directory not found: {dump_directory}",
            }

        logger.info(f"Processing legal dump: {dump_directory} for case: {case_id}")

        # Initialize case processing
        self.current_case_id = case_id
        self.current_case_files = []
        self.case_timeline = []
        self.search_points = []

        results = {
            "success": True,
            "case_id": case_id,
            "dump_directory": str(dump_directory),
            "start_time": datetime.now().isoformat(),
            "stages": {},
        }

        try:
            # Stage 1: Scan and validate files
            scan_result = await self._scan_dump_directory(dump_path)
            results["stages"]["scan"] = scan_result

            if not scan_result["success"]:
                return scan_result

            # Stage 2: Create organized case structure
            org_result = await self._create_case_organization(case_id)
            results["stages"]["organization"] = org_result

            # Stage 3: Process and categorize files
            process_result = await self._batch_process_legal_files(
                dump_path, scan_result["files"]
            )
            results["stages"]["processing"] = process_result

            # Stage 4: Extract legal entities and metadata
            entities_result = await self._extract_case_entities()
            results["stages"]["entities"] = entities_result

            # Stage 5: Reconstruct timeline
            timeline_result = await self._reconstruct_case_timeline({})
            results["stages"]["timeline"] = timeline_result

            # Stage 6: Generate search points
            search_result = await self._generate_search_points({})
            results["stages"]["search_points"] = search_result

            # Stage 7: Prepare legal research
            research_result = await self._prepare_legal_research({})
            results["stages"]["legal_research"] = research_result

            # Final summary
            results.update(
                {
                    "end_time": datetime.now().isoformat(),
                    "total_files_processed": len(self.current_case_files),
                    "documents_organized": process_result.get("documents_processed", 0),
                    "search_points_generated": len(self.search_points),
                    "timeline_events": len(self.case_timeline),
                    "case_directory": str(self.case_org_dir / case_id),
                }
            )

        except Exception as e:
            logger.error(f"Legal dump processing failed: {e}", exc_info=True)
            results.update(
                {
                    "success": False,
                    "error": str(e),
                    "end_time": datetime.now().isoformat(),
                }
            )

        return results

    async def _scan_dump_directory(self, dump_path: Path) -> Dict[str, Any]:
        """Scan dump directory and catalog all files."""
        logger.info(f"Scanning dump directory: {dump_path}")

        supported_extensions = {".pdf", ".docx", ".doc", ".txt", ".html", ".json"}
        files_found = []
        total_size = 0

        try:
            for file_path in dump_path.rglob("*"):
                if (
                    file_path.is_file()
                    and file_path.suffix.lower() in supported_extensions
                ):
                    file_info = {
                        "path": str(file_path),
                        "name": file_path.name,
                        "size_mb": round(file_path.stat().st_size / 1024 / 1024, 2),
                        "extension": file_path.suffix.lower(),
                        "modified": datetime.fromtimestamp(
                            file_path.stat().st_mtime
                        ).isoformat(),
                    }
                    files_found.append(file_info)
                    total_size += file_info["size_mb"]

            return {
                "success": True,
                "files": files_found,
                "total_files": len(files_found),
                "total_size_mb": round(total_size, 2),
                "file_types": self._analyze_file_types(files_found),
            }

        except Exception as e:
            return {"success": False, "error": f"Failed to scan directory: {e}"}

    def _analyze_file_types(self, files: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze distribution of file types."""
        type_counts = {}
        for file_info in files:
            ext = file_info["extension"]
            type_counts[ext] = type_counts.get(ext, 0) + 1
        return type_counts

    async def _create_case_organization(self, case_id: str) -> Dict[str, Any]:
        """Create organized directory structure for the case."""
        case_dir = self.case_org_dir / case_id

        # Create subdirectories for different document types
        subdirs = [
            "decisions",
            "letters",
            "case_files",
            "review_files",
            "medical_reports",
            "employment_records",
            "forms",
            "correspondence",
            "timeline",
            "search_points",
            "unknown",
        ]

        created_dirs = []
        try:
            for subdir in subdirs:
                dir_path = case_dir / subdir
                dir_path.mkdir(parents=True, exist_ok=True)
                created_dirs.append(str(dir_path))

            # Create metadata file
            metadata_file = case_dir / "case_metadata.json"
            metadata = {
                "case_id": case_id,
                "created_at": datetime.now().isoformat(),
                "processing_agent": self.agent_id,
                "organization_structure": subdirs,
                "status": "processing",
            }

            with open(metadata_file, "w") as f:
                json.dump(metadata, f, indent=2)

            return {
                "success": True,
                "case_directory": str(case_dir),
                "subdirectories": created_dirs,
                "metadata_file": str(metadata_file),
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create case organization: {e}",
            }

    async def _batch_process_legal_files(
        self, dump_path: Path, files: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Process and organize all files from the dump."""
        processed_count = 0
        failed_count = 0
        categorized_files = {}

        for file_info in files:
            try:
                file_path = Path(file_info["path"])

                # Process the document
                process_result = await self._process_single_legal_document(file_path)

                if process_result["success"]:
                    processed_count += 1
                    doc_type = process_result["wcb_document_type"]

                    if doc_type not in categorized_files:
                        categorized_files[doc_type] = []
                    categorized_files[doc_type].append(
                        {
                            "original_path": str(file_path),
                            "organized_path": process_result["organized_path"],
                            "metadata": process_result["metadata"],
                        }
                    )

                    # Add to case files list
                    self.current_case_files.append(file_path)

                else:
                    failed_count += 1
                    logger.warning(
                        f"Failed to process {file_path}: {process_result.get('error')}"
                    )

            except Exception as e:
                failed_count += 1
                logger.error(f"Error processing {file_info['path']}: {e}")

        return {
            "success": True,
            "documents_processed": processed_count,
            "documents_failed": failed_count,
            "categorized_files": categorized_files,
            "total_files": len(files),
        }

    async def _process_single_legal_document(self, file_path: Path) -> Dict[str, Any]:
        """Process a single document and organize it."""
        try:
            # Extract content
            content_result = await self._extract_text_content(file_path)
            if not content_result["success"]:
                return content_result

            content = content_result["content"]

            # Identify WCB document type
            wcb_type_result = await self._identify_wcb_document_type(
                {"content": content, "file_path": str(file_path)}
            )

            wcb_doc_type = wcb_type_result.get(
                "wcb_document_type", WCBDocumentType.UNKNOWN
            )

            # Extract metadata
            metadata_result = await self._extract_metadata(file_path)

            # Extract legal entities
            entities_result = await self._extract_legal_entities(
                {"content": content, "document_type": wcb_doc_type}
            )

            # Organize file
            organized_path = await self._organize_file_by_type(
                file_path, wcb_doc_type, entities_result.get("entities", {})
            )

            return {
                "success": True,
                "wcb_document_type": wcb_doc_type,
                "organized_path": organized_path,
                "metadata": {
                    "original_path": str(file_path),
                    "content_length": len(content),
                    "file_metadata": metadata_result,
                    "legal_entities": entities_result.get("entities", {}),
                    "classification_confidence": wcb_type_result.get("confidence", 0.0),
                },
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _organize_file_by_type(
        self, file_path: Path, wcb_type: str, entities: Dict[str, Any]
    ) -> str:
        """Organize file into appropriate directory based on type."""
        if not self.current_case_id:
            raise ValueError("No current case ID set")

        case_dir = self.case_org_dir / self.current_case_id

        # Map WCB types to directories
        type_dir_map = {
            WCBDocumentType.DECISION: "decisions",
            WCBDocumentType.TRIBUNAL_DECISION: "decisions",
            WCBDocumentType.BOARD_DECISION: "decisions",
            WCBDocumentType.APPEAL_DECISION: "decisions",
            WCBDocumentType.INITIAL_DECISION: "decisions",
            WCBDocumentType.LETTER: "letters",
            WCBDocumentType.CLAIM_LETTER: "letters",
            WCBDocumentType.DENIAL_LETTER: "letters",
            WCBDocumentType.APPROVAL_LETTER: "letters",
            WCBDocumentType.REQUEST_LETTER: "letters",
            WCBDocumentType.CASE_FILE: "case_files",
            WCBDocumentType.REVIEW_FILE: "review_files",
            WCBDocumentType.MEDICAL_REPORT: "medical_reports",
            WCBDocumentType.EMPLOYMENT_RECORD: "employment_records",
            WCBDocumentType.FORM: "forms",
            WCBDocumentType.CORRESPONDENCE: "correspondence",
            WCBDocumentType.UNKNOWN: "unknown",
        }

        target_dir = case_dir / type_dir_map.get(wcb_type, "unknown")

        # Create meaningful filename with metadata
        date_prefix = ""
        if "dates" in entities and entities["dates"]:
            # Use the earliest date found
            earliest_date = min(entities["dates"])
            date_prefix = f"{earliest_date.replace('-', '')}_"

        # Sanitize filename
        base_name = file_path.stem
        sanitized_name = re.sub(r"[^\w\-_\.]", "_", base_name)
        new_filename = f"{date_prefix}{sanitized_name}{file_path.suffix}"

        target_path = target_dir / new_filename

        # Copy file to organized location
        shutil.copy2(file_path, target_path)

        return str(target_path)

    def _initialize_wcb_patterns(self) -> Dict[str, List[str]]:
        """Initialize patterns for WCB document type identification."""
        return {
            WCBDocumentType.DECISION: [
                r"tribunal decision",
                r"board decision",
                r"appeal decision",
                r"workers.*compensation.*decision",
                r"wcb.*decision",
                r"wcat.*decision",
                r"decision.*no\.",
                r"reasons.*for.*decision",
            ],
            WCBDocumentType.LETTER: [
                r"dear.*claimant",
                r"dear.*sir.*madam",
                r"re:.*claim.*no",
                r"workers.*compensation.*letter",
                r"notification.*letter",
                r"correspondence.*dated",
            ],
            WCBDocumentType.MEDICAL_REPORT: [
                r"medical.*report",
                r"physician.*report",
                r"clinical.*assessment",
                r"medical.*examination",
                r"doctor.*report",
                r"medical.*opinion",
            ],
            WCBDocumentType.FORM: [
                r"form.*\d+",
                r"application.*form",
                r"claim.*form",
                r"medical.*form",
                r"wcb.*form",
            ],
        }

    async def _identify_wcb_document_type(
        self, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Identify WCB-specific document type using patterns and LLM."""
        content = params.get("content", "")
        file_path = params.get("file_path", "")

        # First, try pattern matching
        pattern_result = self._pattern_match_wcb_type(content, file_path)
        if pattern_result["confidence"] > 0.8:
            return pattern_result

        # Then use LLM for more sophisticated classification
        llm_result = await self._llm_classify_wcb_type(content, file_path)

        # Combine results
        if llm_result["confidence"] > pattern_result["confidence"]:
            return llm_result
        else:
            return pattern_result

    def _pattern_match_wcb_type(self, content: str, file_path: str) -> Dict[str, Any]:
        """Use pattern matching to identify WCB document type."""
        content_lower = content.lower()
        filename_lower = Path(file_path).name.lower()

        # Check each pattern category
        for doc_type, patterns in self.wcb_patterns.items():
            matches = 0
            for pattern in patterns:
                if re.search(pattern, content_lower) or re.search(
                    pattern, filename_lower
                ):
                    matches += 1

            if matches > 0:
                confidence = min(matches / len(patterns), 1.0)
                return {
                    "wcb_document_type": doc_type,
                    "confidence": confidence,
                    "method": "pattern_matching",
                    "matches_found": matches,
                }

        return {
            "wcb_document_type": WCBDocumentType.UNKNOWN,
            "confidence": 0.0,
            "method": "pattern_matching",
            "matches_found": 0,
        }

    async def _llm_classify_wcb_type(
        self, content: str, file_path: str
    ) -> Dict[str, Any]:
        """Use LLM to classify WCB document type."""
        try:
            # Create a classification prompt
            prompt = f"""
            Analyze this WCB/Workers' Compensation document and classify its type.

            Document filename: {Path(file_path).name}
            Content preview: {content[:2000]}...

            Classify as one of:
            - decision (tribunal/board/appeal decisions)
            - letter (correspondence, notifications)
            - case_file (main case documentation)
            - review_file (case review documents)
            - medical_report (medical assessments)
            - employment_record (employment history)
            - form (application forms, claim forms)
            - correspondence (general correspondence)
            - unknown (if unclear)

            Respond with JSON: {{"type": "...", "confidence": 0.0-1.0, "reasoning": "..."}}
            """

            llm = await self._get_llm_instance()
            if not llm:
                return {
                    "wcb_document_type": WCBDocumentType.UNKNOWN,
                    "confidence": 0.0,
                    "method": "llm_unavailable",
                }

            response = await llm.ainvoke(prompt)

            # Parse JSON response
            try:
                result = json.loads(response.content)
                return {
                    "wcb_document_type": result.get("type", WCBDocumentType.UNKNOWN),
                    "confidence": result.get("confidence", 0.0),
                    "method": "llm_classification",
                    "reasoning": result.get("reasoning", ""),
                }
            except json.JSONDecodeError:
                # Fallback to text parsing
                response_text = response.content.lower()
                for doc_type in [
                    WCBDocumentType.DECISION,
                    WCBDocumentType.LETTER,
                    WCBDocumentType.MEDICAL_REPORT,
                    WCBDocumentType.FORM,
                ]:
                    if doc_type in response_text:
                        return {
                            "wcb_document_type": doc_type,
                            "confidence": 0.7,
                            "method": "llm_text_parsing",
                        }

                return {
                    "wcb_document_type": WCBDocumentType.UNKNOWN,
                    "confidence": 0.0,
                    "method": "llm_parse_failed",
                }

        except Exception as e:
            logger.error(f"LLM classification failed: {e}")
            return {
                "wcb_document_type": WCBDocumentType.UNKNOWN,
                "confidence": 0.0,
                "method": "llm_error",
            }

    async def _extract_legal_entities(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Extract legal entities from document content."""
        content = params.get("content", "")
        doc_type = params.get("document_type", "")

        entities = {
            "claim_numbers": [],
            "dates": [],
            "names": [],
            "medical_conditions": [],
            "employers": [],
            "case_references": [],
            "decision_outcomes": [],
            "appeal_numbers": [],
        }

        # Extract claim numbers
        claim_patterns = [
            r"claim.*no\.?\s*:?\s*([A-Z0-9\-]+)",
            r"file.*no\.?\s*:?\s*([A-Z0-9\-]+)",
            r"reference.*no\.?\s*:?\s*([A-Z0-9\-]+)",
        ]

        for pattern in claim_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            entities["claim_numbers"].extend(matches)

        # Extract dates
        date_patterns = [
            r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            r"(\d{4}[/-]\d{1,2}[/-]\d{1,2})",
            r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}",
        ]

        for pattern in date_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            entities["dates"].extend(matches)

        # Extract medical conditions (common WCB conditions)
        medical_conditions = [
            r"herniat(ed|ion)",
            r"stenosis",
            r"radiculopathy",
            r"carpal tunnel",
            r"back injury",
            r"repetitive strain",
            r"chronic pain",
            r"disc.*degeneration",
        ]

        for condition in medical_conditions:
            if re.search(condition, content, re.IGNORECASE):
                entities["medical_conditions"].append(condition)

        # Use LLM for more sophisticated entity extraction
        llm_entities = await self._llm_extract_entities(content, doc_type)

        # Merge LLM results
        for key, values in llm_entities.items():
            if key in entities and values:
                entities[key].extend(values)

        # Clean and deduplicate
        for key in entities:
            entities[key] = list(set(entities[key]))  # Remove duplicates

        return {
            "success": True,
            "entities": entities,
            "extraction_methods": ["pattern_matching", "llm_extraction"],
        }

    async def _llm_extract_entities(
        self, content: str, doc_type: str
    ) -> Dict[str, List[str]]:
        """Use LLM to extract legal entities."""
        try:
            prompt = f"""
            Extract key legal entities from this WCB document of type: {doc_type}

            Content: {content[:3000]}...

            Extract and return as JSON:
            {{
                "claim_numbers": [...],
                "dates": [...],
                "names": [...],
                "medical_conditions": [...],
                "employers": [...],
                "decision_outcomes": [...],
                "appeal_numbers": [...]
            }}
            """

            llm = await self._get_llm_instance()
            if not llm:
                return {}

            response = await llm.ainvoke(prompt)

            try:
                return json.loads(response.content)
            except json.JSONDecodeError:
                return {}

        except Exception as e:
            logger.error(f"LLM entity extraction failed: {e}")
            return {}

    async def _generate_search_points(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate structured search points for the Legal Research Agent."""

        # Analyze processed documents to create search strategies
        search_points = []

        # Ensure we have a valid case ID before proceeding
        if not self.current_case_id:
            logger.warning("⚠️ No current case ID set for search point generation")
            return {
                "success": False,
                "error": "No current case ID available for search point generation",
                "search_points_generated": 0,
                "search_points": [],
            }

        # Generate search points based on case documents
        for file_path in self.current_case_files:
            try:
                # Read organized file metadata
                case_dir = self.case_org_dir / self.current_case_id
                metadata_file = case_dir / "case_metadata.json"

                # Create search points based on document types and entities
                if "decisions" in str(file_path):
                    search_points.append(
                        LegalSearchPoint(
                            search_type="precedent_search",
                            keywords=["similar decisions", "comparable cases"],
                            context="Find similar WCB decisions for precedent analysis",
                            priority="high",
                            document_refs=[str(file_path)],
                        )
                    )

                if "medical_reports" in str(file_path):
                    search_points.append(
                        LegalSearchPoint(
                            search_type="medical_precedent",
                            keywords=["medical evidence", "similar conditions"],
                            context="Find cases with similar medical evidence",
                            priority="medium",
                        )
                    )

            except Exception as e:
                logger.warning(f"Error generating search points for {file_path}: {e}")

        # Generate entity-based search points
        for condition in self.case_entities.get("medical_conditions", []):
            search_points.append(
                LegalSearchPoint(
                    search_type="condition_precedent",
                    keywords=[condition, "case law", "precedent"],
                    context=f"Find precedent cases involving {condition}",
                    priority="high",
                )
            )

        # Save search points
        self.search_points = search_points
        await self._save_search_points()

        return {
            "success": True,
            "search_points_generated": len(search_points),
            "search_points": [
                {
                    "search_type": sp.search_type,
                    "keywords": sp.keywords,
                    "context": sp.context,
                    "priority": sp.priority,
                }
                for sp in search_points
            ],
        }

    async def _save_search_points(self):
        """Save search points to case directory."""
        if not self.current_case_id:
            return

        case_dir = self.case_org_dir / self.current_case_id
        search_points_file = case_dir / "search_points" / "legal_search_points.json"
        search_points_file.parent.mkdir(exist_ok=True)

        search_points_data = [
            {
                "search_type": sp.search_type,
                "keywords": sp.keywords,
                "context": sp.context,
                "priority": sp.priority,
                "document_refs": sp.document_refs,
                "created_at": sp.created_at,
            }
            for sp in self.search_points
        ]

        with open(search_points_file, "w") as f:
            json.dump(search_points_data, f, indent=2)

    async def _reconstruct_case_timeline(
        self, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Reconstruct chronological timeline of case events."""
        timeline_events = []

        # Extract dates and events from all processed documents
        for file_path in self.current_case_files:
            try:
                # This would be enhanced to extract actual timeline events
                # For now, we'll create a basic timeline structure
                timeline_events.append(
                    {
                        "date": datetime.now().isoformat(),
                        "event_type": "document_processed",
                        "description": f"Processed document: {Path(file_path).name}",
                        "document_reference": str(file_path),
                    }
                )
            except Exception as e:
                logger.warning(f"Error processing timeline for {file_path}: {e}")

        # Sort timeline by date
        timeline_events.sort(key=lambda x: x["date"])
        self.case_timeline = timeline_events

        # Save timeline
        await self._save_case_timeline()

        return {
            "success": True,
            "timeline_events": len(timeline_events),
            "timeline": timeline_events,
        }

    async def _save_case_timeline(self):
        """Save case timeline to case directory."""
        if not self.current_case_id:
            return

        case_dir = self.case_org_dir / self.current_case_id
        timeline_file = case_dir / "timeline" / "case_timeline.json"
        timeline_file.parent.mkdir(exist_ok=True)

        with open(timeline_file, "w") as f:
            json.dump(self.case_timeline, f, indent=2)

    async def _prepare_legal_research(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare structured data package for Legal Research Agent."""

        if not self.current_case_id:
            return {"success": False, "error": "No active case to prepare"}

        case_dir = self.case_org_dir / self.current_case_id

        # Create research package
        research_package = {
            "case_id": self.current_case_id,
            "prepared_at": datetime.now().isoformat(),
            "case_directory": str(case_dir),
            "search_points": [
                {
                    "search_type": sp.search_type,
                    "keywords": sp.keywords,
                    "context": sp.context,
                    "priority": sp.priority,
                }
                for sp in self.search_points
            ],
            "document_summary": {
                "total_documents": len(self.current_case_files),
                "organized_structure": list(case_dir.iterdir()),
                "timeline_events": len(self.case_timeline),
            },
            "next_steps": [
                "Execute precedent searches using search points",
                "Analyze similar cases in database",
                "Generate legal research report",
                "Identify key legal arguments",
            ],
        }

        # Save research package
        research_file = case_dir / "legal_research_package.json"
        with open(research_file, "w") as f:
            json.dump(research_package, f, indent=2)

        return {
            "success": True,
            "research_package": research_package,
            "package_file": str(research_file),
            "ready_for_legal_research": True,
        }

    async def _batch_legal_organize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Batch organize multiple case dumps."""
        dump_directories = params.get("dump_directories", [])

        if not dump_directories:
            return {"success": False, "error": "No dump directories provided"}

        results = []

        for dump_dir in dump_directories:
            try:
                # Process each dump as a separate case
                case_id = f"batch_case_{len(results) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

                result = await self._process_legal_dump(
                    {"dump_directory": dump_dir, "case_id": case_id}
                )

                results.append(
                    {"dump_directory": dump_dir, "case_id": case_id, "result": result}
                )

            except Exception as e:
                results.append(
                    {"dump_directory": dump_dir, "error": str(e), "success": False}
                )

        return {
            "success": True,
            "batch_results": results,
            "total_dumps_processed": len(results),
            "successful_cases": len(
                [r for r in results if r.get("result", {}).get("success", False)]
            ),
        }

    async def get_case_summary(self, case_id: str) -> Dict[str, Any]:
        """Get comprehensive summary of processed case."""
        case_dir = self.case_org_dir / case_id

        if not case_dir.exists():
            return {"success": False, "error": f"Case {case_id} not found"}

        # Load case metadata
        metadata_file = case_dir / "case_metadata.json"
        metadata = {}
        if metadata_file.exists():
            with open(metadata_file, "r") as f:
                metadata = json.load(f)

        # Count organized documents
        doc_counts = {}
        for subdir in case_dir.iterdir():
            if subdir.is_dir():
                doc_counts[subdir.name] = len(list(subdir.glob("*")))

        return {
            "success": True,
            "case_id": case_id,
            "case_directory": str(case_dir),
            "metadata": metadata,
            "document_counts": doc_counts,
            "total_documents": sum(doc_counts.values()),
            "organization_complete": metadata.get("status") == "completed",
        }

    async def _organize_case_files(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Organize case files into structured directories."""
        case_id = params.get("case_id", self.current_case_id)
        if not case_id:
            return {"success": False, "error": "No case ID provided"}

        return await self._create_case_organization(case_id)

    async def _extract_case_entities(self) -> Dict[str, Any]:
        """Extract entities from all processed case files."""
        all_entities = {
            "claim_numbers": [],
            "dates": [],
            "names": [],
            "medical_conditions": [],
            "employers": [],
            "case_references": [],
            "decision_outcomes": [],
            "appeal_numbers": [],
        }

        for file_path in self.current_case_files:
            try:
                # Read file content
                content_result = await self._extract_text_content(file_path)
                if content_result["success"]:
                    # Extract entities from this file
                    entities_result = await self._extract_legal_entities(
                        {
                            "content": content_result["content"],
                            "document_type": "unknown",
                        }
                    )

                    # Merge entities
                    if entities_result["success"]:
                        for key, values in entities_result["entities"].items():
                            if key in all_entities:
                                all_entities[key].extend(values)

            except Exception as e:
                logger.warning(f"Error extracting entities from {file_path}: {e}")

        # Remove duplicates
        for key in all_entities:
            all_entities[key] = list(set(all_entities[key]))

        # Store for later use
        self.case_entities = all_entities

        return {
            "success": True,
            "entities": all_entities,
            "files_processed": len(self.current_case_files),
        }

    async def _get_llm_instance(self):
        """Get LLM instance from the unified factory using global settings."""
        try:
            from ...utils.unified_llm_factory import get_llm_factory

            factory = get_llm_factory()

            # Use global settings manager if available
            if (
                hasattr(self, "global_settings_manager")
                and self.global_settings_manager
            ):
                # Get primary LLM configuration from global settings
                llm_config = self.global_settings_manager.get_primary_llm_config()
                provider = llm_config.get("provider", "google")
                model_name = llm_config.get(
                    "model_name", "gemini-2.5-flash-preview-04-17"
                )

                logger.info(
                    f"🤖 Using LLM from global settings: {provider} - {model_name}"
                )
                return factory.create_llm_for_legal_agent(provider, model_name)
            else:
                # Fallback to default settings if no global settings manager
                logger.warning(
                    "⚠️ No global settings manager found, using default OpenAI configuration"
                )
                return factory.create_llm_for_legal_agent("openai", "gpt-4")

        except Exception as e:
            logger.warning(f"Could not get LLM instance: {e}")
            return None

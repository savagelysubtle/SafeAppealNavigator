"""
Enhanced Legal Intake Agent for WCB Case Processing

This module extends the base IntakeAgent with specialized workflows for:
- Mass WCB legal file processing
- Automatic document organization and categorization
- Legal document type identification
- Search point generation for Legal Research Agent
- Case timeline reconstruction
- Insurance company and medical provider tracking
- OCR capabilities for scanned documents
- Comprehensive document sorting and tracking
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

    # Insurance and medical tracking
    INSURANCE_DOCUMENT = "insurance_document"
    MEDICAL_PROVIDER_DOCUMENT = "medical_provider_document"
    USER_SUBMISSION = "user_submission"

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


class DocumentTracker:
    """Track document submissions and sources"""

    def __init__(self):
        self.insurance_companies = {}
        self.medical_providers = {}
        self.user_submissions = []
        self.submission_timeline = []

    def add_insurance_document(self, company_name: str, document_info: Dict[str, Any]):
        """Track insurance company documents"""
        if company_name not in self.insurance_companies:
            self.insurance_companies[company_name] = []
        self.insurance_companies[company_name].append(document_info)

    def add_medical_provider(self, provider_name: str, document_info: Dict[str, Any]):
        """Track medical provider documents"""
        if provider_name not in self.medical_providers:
            self.medical_providers[provider_name] = []
        self.medical_providers[provider_name].append(document_info)

    def add_user_submission(self, document_info: Dict[str, Any]):
        """Track user-submitted documents"""
        self.user_submissions.append(document_info)

    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive tracking summary"""
        return {
            "insurance_companies": {
                name: len(docs) for name, docs in self.insurance_companies.items()
            },
            "medical_providers": {
                name: len(docs) for name, docs in self.medical_providers.items()
            },
            "user_submissions": len(self.user_submissions),
            "total_documents": (
                sum(len(docs) for docs in self.insurance_companies.values())
                + sum(len(docs) for docs in self.medical_providers.values())
                + len(self.user_submissions)
            ),
        }


class EnhancedLegalIntakeAgent(IntakeAgent):
    """
    Enhanced intake agent specialized for comprehensive legal case processing.

    Capabilities:
    - Mass file dump processing with intelligent organization
    - WCB-specific document type identification
    - Legal timeline reconstruction
    - Automatic case file organization
    - Search point generation for legal research
    - Integration with legal case database
    - Insurance company and medical provider tracking
    - OCR capabilities for scanned documents
    - Comprehensive document sorting and submission tracking
    """

    def __init__(
        self,
        legal_case_db: Optional[LegalCaseDatabase] = None,
        case_organization_directory: str = "./tmp/organized_cases",
        enable_ocr: bool = True,
        **kwargs,
    ):
        super().__init__(**kwargs)

        # Legal-specific configuration
        self.legal_db = legal_case_db or LegalCaseDatabase()
        self.case_org_dir = Path(case_organization_directory)
        self.case_org_dir.mkdir(parents=True, exist_ok=True)
        self.enable_ocr = enable_ocr

        # WCB document patterns for classification
        self.wcb_patterns = self._initialize_wcb_patterns()

        # Case processing state
        self.current_case_id: Optional[str] = None
        self.current_case_files: List[Path] = []
        self.case_timeline: List[Dict[str, Any]] = []
        self.search_points: List[LegalSearchPoint] = []
        self.case_entities: Dict[str, List[str]] = {}

        # Document tracking
        self.document_tracker = DocumentTracker()

        # Insurance and medical provider patterns
        self.insurance_patterns = self._initialize_insurance_patterns()
        self.medical_provider_patterns = self._initialize_medical_provider_patterns()

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
            "track_document_sources",
            "analyze_submission_patterns",
            "generate_tracking_report",
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
            "track_document_sources": self._track_document_sources,
            "analyze_submission_patterns": self._analyze_submission_patterns,
            "generate_tracking_report": self._generate_tracking_report,
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
        3. Process and categorize all files (OCR last for efficiency)
        4. Extract legal entities and metadata
        5. Track document sources and submissions
        6. Reconstruct case timeline
        7. Generate search points for legal research
        8. Prepare database entries
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
        self.document_tracker = DocumentTracker()

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

            # Stage 3: Process and categorize files (OCR-optimized order)
            process_result = await self._batch_process_legal_files(
                dump_path, scan_result["files"]
            )
            results["stages"]["processing"] = process_result

            # Stage 4: Extract legal entities and metadata
            entities_result = await self._extract_case_entities()
            results["stages"]["entities"] = entities_result

            # Stage 5: Track document sources
            tracking_result = await self._track_document_sources({})
            results["stages"]["document_tracking"] = tracking_result

            # Stage 6: Reconstruct timeline
            timeline_result = await self._reconstruct_case_timeline({})
            results["stages"]["timeline"] = timeline_result

            # Stage 7: Generate search points
            search_result = await self._generate_search_points({})
            results["stages"]["search_points"] = search_result

            # Stage 8: Prepare legal research
            research_result = await self._prepare_legal_research({})
            results["stages"]["legal_research"] = research_result

            # Final summary
            tracking_summary = self.document_tracker.get_summary()
            results.update(
                {
                    "end_time": datetime.now().isoformat(),
                    "total_files_processed": len(self.current_case_files),
                    "documents_organized": process_result.get("documents_processed", 0),
                    "search_points_generated": len(self.search_points),
                    "timeline_events": len(self.case_timeline),
                    "case_directory": str(self.case_org_dir / case_id),
                    "document_tracking": tracking_summary,
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
        """Scan dump directory and catalog all files with OCR optimization."""
        logger.info(f"Scanning dump directory: {dump_path}")

        supported_extensions = {
            ".pdf",
            ".docx",
            ".doc",
            ".txt",
            ".html",
            ".json",
            ".png",
            ".jpg",
            ".jpeg",
            ".tiff",
            ".bmp",
        }
        files_found = []
        total_size = 0

        # Categorize files for processing order (non-OCR first)
        text_files = []
        ocr_files = []

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

                    # Categorize for processing order
                    if file_path.suffix.lower() in {
                        ".png",
                        ".jpg",
                        ".jpeg",
                        ".tiff",
                        ".bmp",
                    }:
                        ocr_files.append(file_info)
                    else:
                        text_files.append(file_info)

                    files_found.append(file_info)
                    total_size += file_info["size_mb"]

            # Reorder for efficient processing (text files first, OCR last)
            files_found = text_files + ocr_files

            return {
                "success": True,
                "files": files_found,
                "total_files": len(files_found),
                "total_size_mb": round(total_size, 2),
                "file_types": self._analyze_file_types(files_found),
                "text_files": len(text_files),
                "ocr_files": len(ocr_files),
                "processing_order": "text_first_ocr_last",
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
            "insurance_documents",
            "medical_providers",
            "user_submissions",
            "timeline",
            "search_points",
            "tracking_reports",
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
                "ocr_enabled": self.enable_ocr,
                "features": [
                    "document_classification",
                    "entity_extraction",
                    "timeline_reconstruction",
                    "search_point_generation",
                    "source_tracking",
                    "submission_analysis",
                ],
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
        """Process and organize all files from the dump with OCR optimization."""
        processed_count = 0
        failed_count = 0
        categorized_files = {}
        ocr_processed = 0

        for file_info in files:
            try:
                file_path = Path(file_info["path"])

                # Process the document
                process_result = await self._process_single_legal_document(file_path)

                if process_result["success"]:
                    processed_count += 1
                    doc_type = process_result["wcb_document_type"]

                    if process_result.get("ocr_used", False):
                        ocr_processed += 1

                    if doc_type not in categorized_files:
                        categorized_files[doc_type] = []
                    categorized_files[doc_type].append(
                        {
                            "original_path": str(file_path),
                            "organized_path": process_result["organized_path"],
                            "metadata": process_result["metadata"],
                            "document_source": process_result.get("document_source"),
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
            "ocr_documents_processed": ocr_processed,
            "categorized_files": categorized_files,
            "total_files": len(files),
        }

    async def _process_single_legal_document(self, file_path: Path) -> Dict[str, Any]:
        """Process a single document and organize it with enhanced source tracking."""
        try:
            # Extract content (with OCR if needed)
            content_result = await self._extract_text_content_with_ocr(file_path)
            if not content_result["success"]:
                return content_result

            content = content_result["content"]
            ocr_used = content_result.get("ocr_used", False)

            # Identify WCB document type
            wcb_type_result = await self._identify_wcb_document_type(
                {"content": content, "file_path": str(file_path)}
            )

            wcb_doc_type = wcb_type_result.get(
                "wcb_document_type", WCBDocumentType.UNKNOWN
            )

            # Identify document source (insurance, medical provider, user)
            source_result = await self._identify_document_source(content, file_path)

            # Extract metadata
            metadata_result = await self._extract_metadata(file_path)

            # Extract legal entities
            entities_result = await self._extract_legal_entities(
                {"content": content, "document_type": wcb_doc_type}
            )

            # Organize file
            organized_path = await self._organize_file_by_type(
                file_path,
                wcb_doc_type,
                entities_result.get("entities", {}),
                source_result,
            )

            return {
                "success": True,
                "wcb_document_type": wcb_doc_type,
                "organized_path": organized_path,
                "document_source": source_result,
                "ocr_used": ocr_used,
                "metadata": {
                    "original_path": str(file_path),
                    "content_length": len(content),
                    "file_metadata": metadata_result,
                    "legal_entities": entities_result.get("entities", {}),
                    "classification_confidence": wcb_type_result.get("confidence", 0.0),
                    "source_confidence": source_result.get("confidence", 0.0),
                    "ocr_used": ocr_used,
                },
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _extract_text_content_with_ocr(self, file_path: Path) -> Dict[str, Any]:
        """Extract text content with OCR support for image files."""
        try:
            # Check if it's an image file that needs OCR
            image_extensions = {".png", ".jpg", ".jpeg", ".tiff", ".bmp"}

            if file_path.suffix.lower() in image_extensions:
                if self.enable_ocr:
                    return await self._extract_ocr_content(file_path)
                else:
                    return {
                        "success": False,
                        "error": f"OCR disabled for image file: {file_path}",
                    }
            else:
                # Use regular text extraction
                result = await self._extract_text_content(file_path)
                result["ocr_used"] = False
                return result

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _extract_ocr_content(self, file_path: Path) -> Dict[str, Any]:
        """Extract text from image files using OCR."""
        try:
            import pytesseract
            from PIL import Image

            # Open and process image
            image = Image.open(file_path)

            # Extract text using OCR
            text = pytesseract.image_to_string(image)

            return {
                "success": True,
                "content": text,
                "ocr_used": True,
                "extraction_method": "pytesseract",
                "content_length": len(text),
            }

        except ImportError:
            return {
                "success": False,
                "error": "OCR dependencies not installed (pytesseract, PIL)",
                "ocr_used": False,
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"OCR extraction failed: {e}",
                "ocr_used": False,
            }

    async def _identify_document_source(
        self, content: str, file_path: Path
    ) -> Dict[str, Any]:
        """Identify if document is from insurance company, medical provider, or user."""
        content_lower = content.lower()
        filename_lower = file_path.name.lower()

        # Check for insurance company indicators
        insurance_score = 0
        matched_companies = []
        for company, patterns in self.insurance_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content_lower) or re.search(
                    pattern, filename_lower
                ):
                    insurance_score += 1
                    if company not in matched_companies:
                        matched_companies.append(company)

        # Check for medical provider indicators
        medical_score = 0
        matched_providers = []
        for provider_type, patterns in self.medical_provider_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content_lower) or re.search(
                    pattern, filename_lower
                ):
                    medical_score += 1
                    if provider_type not in matched_providers:
                        matched_providers.append(provider_type)

        # Determine source type
        if insurance_score > medical_score and insurance_score > 0:
            return {
                "source_type": "insurance_company",
                "confidence": min(insurance_score / 3.0, 1.0),
                "matched_entities": matched_companies,
                "details": f"Identified {len(matched_companies)} insurance company indicators",
            }
        elif medical_score > 0:
            return {
                "source_type": "medical_provider",
                "confidence": min(medical_score / 3.0, 1.0),
                "matched_entities": matched_providers,
                "details": f"Identified {len(matched_providers)} medical provider indicators",
            }
        else:
            return {
                "source_type": "user_submission",
                "confidence": 0.5,
                "matched_entities": [],
                "details": "No clear insurance or medical provider indicators found",
            }

    async def _organize_file_by_type(
        self,
        file_path: Path,
        wcb_type: str,
        entities: Dict[str, Any],
        source_info: Dict[str, Any],
    ) -> str:
        """Organize file into appropriate directory based on type and source."""
        if not self.current_case_id:
            raise ValueError("No current case ID set")

        case_dir = self.case_org_dir / self.current_case_id

        # Map WCB types to directories with source consideration
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

        # Override directory based on source if it's insurance or medical
        source_type = source_info.get("source_type", "unknown")
        if source_type == "insurance_company":
            target_dir = case_dir / "insurance_documents"
        elif source_type == "medical_provider":
            target_dir = case_dir / "medical_providers"
        elif source_type == "user_submission":
            target_dir = case_dir / "user_submissions"
        else:
            target_dir = case_dir / type_dir_map.get(wcb_type, "unknown")

        # Create meaningful filename with metadata
        date_prefix = ""
        if "dates" in entities and entities["dates"]:
            # Use the earliest date found
            earliest_date = min(entities["dates"])
            date_prefix = f"{earliest_date.replace('-', '')}_"

        # Add source prefix
        source_prefix = ""
        if source_type == "insurance_company" and source_info.get("matched_entities"):
            source_prefix = f"INS_{source_info['matched_entities'][0][:10]}_"
        elif source_type == "medical_provider" and source_info.get("matched_entities"):
            source_prefix = f"MED_{source_info['matched_entities'][0][:10]}_"
        elif source_type == "user_submission":
            source_prefix = "USER_"

        # Sanitize filename
        base_name = file_path.stem
        sanitized_name = re.sub(r"[^\w\-_\.]", "_", base_name)
        new_filename = f"{source_prefix}{date_prefix}{sanitized_name}{file_path.suffix}"

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

    def _initialize_insurance_patterns(self) -> Dict[str, List[str]]:
        """Initialize patterns for insurance company identification."""
        return {
            "general_insurance": [
                r"insurance.*company",
                r"insurance.*corp",
                r"insurance.*ltd",
                r"claims.*department",
                r"policy.*number",
                r"claim.*number.*\d+",
                r"adjuster",
                r"underwriter",
            ],
            "specific_companies": [
                r"icbc",
                r"cooperators",
                r"state.*farm",
                r"intact.*insurance",
                r"aviva",
                r"rbc.*insurance",
                r"td.*insurance",
                r"wawanesa",
            ],
        }

    def _initialize_medical_provider_patterns(self) -> Dict[str, List[str]]:
        """Initialize patterns for medical provider identification."""
        return {
            "hospitals": [
                r"hospital",
                r"medical.*center",
                r"health.*center",
                r"clinic",
                r"emergency.*department",
                r"radiology.*department",
            ],
            "doctors": [
                r"dr\.\s+[a-z]+",
                r"doctor",
                r"physician",
                r"specialist",
                r"consultant",
                r"medical.*director",
            ],
            "practices": [
                r"medical.*practice",
                r"family.*practice",
                r"orthopedic.*clinic",
                r"physiotherapy",
                r"chiropractic",
                r"rehabilitation.*center",
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

            llm = self._get_llm_instance()
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
            "insurance_companies": [],
            "medical_providers": [],
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

        # Extract insurance companies and medical providers
        for company, patterns in self.insurance_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    entities["insurance_companies"].append(company)

        for provider, patterns in self.medical_provider_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    entities["medical_providers"].append(provider)

        # Use LLM for more sophisticated entity extraction
        llm_entities = await self._llm_extract_entities(content, doc_type)

        # Merge LLM results
        for key, values in llm_entities.items():
            if key in entities and values:
                entities[key].extend(values)

        # Clean and deduplicate
        for key in entities:
            entities[key] = list(set(entities[key]))  # Remove duplicates

        # Store for later use
        self.case_entities = entities

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
                "appeal_numbers": [...],
                "insurance_companies": [...],
                "medical_providers": [...]
            }}
            """

            llm = self._get_llm_instance()
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

    async def _track_document_sources(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Track and categorize document sources for submission analysis."""

        for file_path in self.current_case_files:
            try:
                # Read organized file metadata to get source information
                # This would typically be stored during processing
                # For now, we'll re-analyze the file
                content_result = await self._extract_text_content_with_ocr(file_path)
                if content_result["success"]:
                    source_info = await self._identify_document_source(
                        content_result["content"], file_path
                    )

                    document_info = {
                        "file_path": str(file_path),
                        "file_name": file_path.name,
                        "source_type": source_info["source_type"],
                        "confidence": source_info["confidence"],
                        "matched_entities": source_info.get("matched_entities", []),
                        "processed_at": datetime.now().isoformat(),
                    }

                    # Add to appropriate tracker
                    if source_info["source_type"] == "insurance_company":
                        for company in source_info.get("matched_entities", ["unknown"]):
                            self.document_tracker.add_insurance_document(
                                company, document_info
                            )
                    elif source_info["source_type"] == "medical_provider":
                        for provider in source_info.get(
                            "matched_entities", ["unknown"]
                        ):
                            self.document_tracker.add_medical_provider(
                                provider, document_info
                            )
                    else:
                        self.document_tracker.add_user_submission(document_info)

            except Exception as e:
                logger.warning(f"Error tracking source for {file_path}: {e}")

        # Save tracking data
        await self._save_tracking_data()

        return {
            "success": True,
            "tracking_summary": self.document_tracker.get_summary(),
            "detailed_tracking": {
                "insurance_companies": len(self.document_tracker.insurance_companies),
                "medical_providers": len(self.document_tracker.medical_providers),
                "user_submissions": len(self.document_tracker.user_submissions),
            },
        }

    async def _save_tracking_data(self):
        """Save document tracking data to case directory."""
        if not self.current_case_id:
            return

        case_dir = self.case_org_dir / self.current_case_id
        tracking_file = case_dir / "tracking_reports" / "document_tracking.json"
        tracking_file.parent.mkdir(exist_ok=True)

        tracking_data = {
            "case_id": self.current_case_id,
            "generated_at": datetime.now().isoformat(),
            "summary": self.document_tracker.get_summary(),
            "insurance_companies": self.document_tracker.insurance_companies,
            "medical_providers": self.document_tracker.medical_providers,
            "user_submissions": self.document_tracker.user_submissions,
        }

        with open(tracking_file, "w") as f:
            json.dump(tracking_data, f, indent=2)

    async def _analyze_submission_patterns(
        self, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze patterns in document submissions."""
        analysis = {
            "submission_timeline": [],
            "source_analysis": {},
            "document_types": {},
            "recommendations": [],
        }

        # Analyze submission patterns
        summary = self.document_tracker.get_summary()

        # Source distribution analysis
        total_docs = summary["total_documents"]
        if total_docs > 0:
            analysis["source_analysis"] = {
                "insurance_percentage": (summary["user_submissions"] / total_docs)
                * 100,
                "medical_percentage": (
                    len(self.document_tracker.medical_providers) / total_docs
                )
                * 100,
                "user_percentage": (summary["user_submissions"] / total_docs) * 100,
            }

        # Generate recommendations
        if summary["insurance_companies"] > 3:
            analysis["recommendations"].append(
                "High number of insurance companies involved - consider consolidation review"
            )

        if summary["medical_providers"] > 5:
            analysis["recommendations"].append(
                "Multiple medical providers - ensure all reports are current and relevant"
            )

        if summary["user_submissions"] < (total_docs * 0.3):
            analysis["recommendations"].append(
                "Low user submission rate - may need to request additional documentation"
            )

        return {
            "success": True,
            "analysis": analysis,
            "total_documents_analyzed": total_docs,
        }

    async def _generate_tracking_report(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive tracking and submission report."""

        report = {
            "case_id": self.current_case_id,
            "report_generated": datetime.now().isoformat(),
            "executive_summary": {},
            "detailed_breakdown": {},
            "recommendations": [],
            "action_items": [],
        }

        # Get tracking summary
        summary = self.document_tracker.get_summary()

        # Executive summary
        report["executive_summary"] = {
            "total_documents_processed": summary["total_documents"],
            "insurance_companies_identified": len(summary["insurance_companies"]),
            "medical_providers_identified": len(summary["medical_providers"]),
            "user_submissions": summary["user_submissions"],
            "case_complexity": self._assess_case_complexity(summary),
        }

        # Detailed breakdown
        report["detailed_breakdown"] = {
            "insurance_companies": summary["insurance_companies"],
            "medical_providers": summary["medical_providers"],
            "document_distribution": self._calculate_document_distribution(summary),
            "timeline_analysis": len(self.case_timeline),
            "search_points_generated": len(self.search_points),
        }

        # Generate recommendations
        report["recommendations"] = await self._generate_case_recommendations(summary)

        # Save report
        if self.current_case_id:
            await self._save_tracking_report(report)

        return {
            "success": True,
            "report": report,
            "report_file": f"case_{self.current_case_id}_tracking_report.json",
        }

    def _assess_case_complexity(self, summary: Dict[str, Any]) -> str:
        """Assess case complexity based on document and source counts."""
        total_docs = summary["total_documents"]
        total_sources = len(summary["insurance_companies"]) + len(
            summary["medical_providers"]
        )

        if total_docs > 50 and total_sources > 10:
            return "High"
        elif total_docs > 20 and total_sources > 5:
            return "Medium"
        else:
            return "Low"

    def _calculate_document_distribution(
        self, summary: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate percentage distribution of document sources."""
        total = summary["total_documents"]
        if total == 0:
            return {"insurance": 0, "medical": 0, "user": 0}

        return {
            "insurance_percentage": (
                sum(summary["insurance_companies"].values()) / total
            )
            * 100,
            "medical_percentage": (sum(summary["medical_providers"].values()) / total)
            * 100,
            "user_percentage": (summary["user_submissions"] / total) * 100,
        }

    async def _generate_case_recommendations(
        self, summary: Dict[str, Any]
    ) -> List[str]:
        """Generate case-specific recommendations."""
        recommendations = []

        # Insurance-related recommendations
        if len(summary["insurance_companies"]) > 3:
            recommendations.append(
                "Multiple insurance companies involved - verify coverage periods and responsibilities"
            )

        # Medical provider recommendations
        if len(summary["medical_providers"]) > 5:
            recommendations.append(
                "High number of medical providers - ensure continuity of care documentation"
            )

        # Document volume recommendations
        if summary["total_documents"] > 100:
            recommendations.append(
                "Large document volume - consider digital organization and indexing"
            )

        # User submission recommendations
        user_ratio = summary["user_submissions"] / max(summary["total_documents"], 1)
        if user_ratio < 0.2:
            recommendations.append(
                "Low user submission rate - may need to request additional personal documentation"
            )

        return recommendations

    async def _save_tracking_report(self, report: Dict[str, Any]):
        """Save comprehensive tracking report."""
        if not self.current_case_id:
            return

        case_dir = self.case_org_dir / self.current_case_id
        report_file = (
            case_dir
            / "tracking_reports"
            / f"comprehensive_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        report_file.parent.mkdir(exist_ok=True)

        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

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

                if "medical_reports" in str(file_path) or "medical_providers" in str(
                    file_path
                ):
                    search_points.append(
                        LegalSearchPoint(
                            search_type="medical_precedent",
                            keywords=["medical evidence", "similar conditions"],
                            context="Find cases with similar medical evidence",
                            priority="medium",
                        )
                    )

                if "insurance_documents" in str(file_path):
                    search_points.append(
                        LegalSearchPoint(
                            search_type="insurance_dispute",
                            keywords=["insurance coverage", "policy interpretation"],
                            context="Find cases involving similar insurance disputes",
                            priority="high",
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

        # Generate source-based search points
        for company in self.document_tracker.insurance_companies.keys():
            search_points.append(
                LegalSearchPoint(
                    search_type="insurance_company_precedent",
                    keywords=[company, "similar disputes", "coverage decisions"],
                    context=f"Find cases involving {company}",
                    priority="medium",
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
                # Enhanced timeline reconstruction with source tracking
                file_stat = file_path.stat()
                timeline_events.append(
                    {
                        "date": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                        "event_type": "document_processed",
                        "description": f"Processed document: {Path(file_path).name}",
                        "document_reference": str(file_path),
                        "file_size": file_stat.st_size,
                    }
                )
            except Exception as e:
                logger.warning(f"Error processing timeline for {file_path}: {e}")

        # Add source-based timeline events
        for company, docs in self.document_tracker.insurance_companies.items():
            timeline_events.append(
                {
                    "date": datetime.now().isoformat(),
                    "event_type": "insurance_documentation",
                    "description": f"Processed {len(docs)} documents from {company}",
                    "source": company,
                    "document_count": len(docs),
                }
            )

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
                "organized_structure": [
                    d.name for d in case_dir.iterdir() if d.is_dir()
                ],
                "timeline_events": len(self.case_timeline),
                "tracking_summary": self.document_tracker.get_summary(),
            },
            "next_steps": [
                "Execute precedent searches using search points",
                "Analyze similar cases in database",
                "Review insurance company patterns",
                "Analyze medical provider documentation",
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

        # Load tracking data if available
        tracking_file = case_dir / "tracking_reports" / "document_tracking.json"
        tracking_data = {}
        if tracking_file.exists():
            with open(tracking_file, "r") as f:
                tracking_data = json.load(f)

        return {
            "success": True,
            "case_id": case_id,
            "case_directory": str(case_dir),
            "metadata": metadata,
            "document_counts": doc_counts,
            "total_documents": sum(doc_counts.values()),
            "organization_complete": metadata.get("status") == "completed",
            "tracking_data": tracking_data.get("summary", {}),
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
            "insurance_companies": [],
            "medical_providers": [],
        }

        for file_path in self.current_case_files:
            try:
                # Read file content
                content_result = await self._extract_text_content_with_ocr(file_path)
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

    def _get_llm_instance(self):
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
                    "⚠️ No global settings manager found, using default Google configuration"
                )
                return factory.create_llm_for_legal_agent(
                    "google", "gemini-2.5-flash-preview-04-17"
                )

        except Exception as e:
            logger.warning(f"Could not get LLM instance: {e}")
            return None

"""
Legal Case Research Agent for Workers' Compensation Appeal Tribunal (WCAT) Cases

This agent specializes in:
1. Searching WCAT database for similar cases
2. Downloading and analyzing legal decision PDFs
3. Extracting case metadata and key details
4. Building arguments based on favorable precedents
5. Generating comprehensive case analysis reports
6. Persistent storage and cross-referencing of cases
7. Enhanced LLM-powered legal analysis and strategy generation
8. Multi-jurisdictional research capabilities
9. Automated legal document generation
"""

import logging
import os
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, TypedDict
from urllib.parse import urljoin

from playwright.async_api import Page

# Try to import PyPDF2 for PDF analysis
try:
    from PyPDF2 import PdfReader

    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False
    PdfReader = None

from src.ai_research_assistant.browser.custom_browser import CustomBrowser
from src.ai_research_assistant.browser.custom_context import CustomBrowserContext

from .enhanced_legal_features import (
    CaseProgressTracker,
    EnhancedLegalAnalyzer,
    LegalDocumentGenerator,
    MultiJurisdictionalResearcher,
)
from .legal_case_database import LegalCaseDatabase

logger = logging.getLogger(__name__)

# Global registries
_LEGAL_AGENT_STOP_FLAGS = {}
_LEGAL_AGENT_INSTANCES = {}


class CaseInfo(TypedDict):
    """Structure for storing case information"""

    appeal_number: str
    date: str
    appeal_type: str
    decision_type: str
    issues: str
    pdf_url: str
    pdf_path: Optional[str]
    case_summary: Optional[str]
    keywords: List[str]
    outcome: Optional[str]
    similarity_score: Optional[float]
    database_id: Optional[int]


class LegalCaseResearchAgent:
    """
    Specialized agent for researching WCAT legal cases and building legal arguments.

    Enhanced with persistent database storage for:
    - Cross-referencing similar cases
    - Building comprehensive case knowledge base
    - Advanced search and filtering capabilities
    - Historical analysis tracking

    Workflow:
    1. Search WCAT database with specific parameters
    2. Parse search results and extract case metadata
    3. Download PDF decisions for detailed analysis
    4. Store cases in persistent database with full-text search
    5. Extract key information from PDFs (issues, decisions, reasoning)
    6. Compare cases with user's situation using database search
    7. Generate argument summaries based on favorable precedents
    """

    def __init__(
        self,
        browser: CustomBrowser,
        context: CustomBrowserContext,
        download_dir: str = "./tmp/legal_research",
        task_id: Optional[str] = None,
        db_path: Optional[str] = None,
        enable_llm_analysis: bool = True,
        llm_provider: str = "openai",
        enable_document_generation: bool = True,
        enable_multi_jurisdictional: bool = False,
    ):
        self.browser = browser
        self.context = context
        self.download_dir = Path(download_dir)
        self.task_id = task_id or str(uuid.uuid4())

        # Initialize database with environment variable support
        if db_path is None:
            env_path = os.getenv("WCAT_DATABASE_PATH")
            if env_path:
                db_path = env_path
            else:
                db_path = str(self.download_dir / "cases.db")
        self.database = LegalCaseDatabase(db_path)

        # Enhanced features configuration
        self.enable_llm_analysis = enable_llm_analysis
        self.enable_document_generation = enable_document_generation
        self.enable_multi_jurisdictional = enable_multi_jurisdictional

        # Initialize enhanced components
        self.legal_analyzer = None
        self.document_generator = None
        self.multi_researcher = None
        self.case_tracker = None

        if self.enable_llm_analysis:
            try:
                self.legal_analyzer = EnhancedLegalAnalyzer(llm_provider)
                logger.info(
                    f"[LegalAgent {self.task_id}] Initialized LLM analyzer with {llm_provider}"
                )
            except Exception as e:
                logger.warning(
                    f"[LegalAgent {self.task_id}] Failed to initialize LLM analyzer: {e}"
                )

        if self.enable_document_generation:
            try:
                self.document_generator = LegalDocumentGenerator()
                logger.info(
                    f"[LegalAgent {self.task_id}] Initialized document generator"
                )
            except Exception as e:
                logger.warning(
                    f"[LegalAgent {self.task_id}] Failed to initialize document generator: {e}"
                )

        if self.enable_multi_jurisdictional:
            try:
                self.multi_researcher = MultiJurisdictionalResearcher()
                logger.info(
                    f"[LegalAgent {self.task_id}] Initialized multi-jurisdictional researcher"
                )
            except Exception as e:
                logger.warning(
                    f"[LegalAgent {self.task_id}] Failed to initialize multi-jurisdictional researcher: {e}"
                )

        # Initialize case progress tracker
        try:
            tracker_db_path = str(self.download_dir / "case_tracking.db")
            self.case_tracker = CaseProgressTracker(tracker_db_path)
            logger.info(
                f"[LegalAgent {self.task_id}] Initialized case progress tracker"
            )
        except Exception as e:
            logger.warning(
                f"[LegalAgent {self.task_id}] Failed to initialize case tracker: {e}"
            )

        # Create organized directory structure
        self.download_dir.mkdir(parents=True, exist_ok=True)
        (self.download_dir / "pdfs").mkdir(exist_ok=True)
        (self.download_dir / "analysis").mkdir(exist_ok=True)
        (self.download_dir / "documents").mkdir(exist_ok=True)

        self.research_page: Optional[Page] = None
        self.cases_found: List[CaseInfo] = []
        self.user_case_details: Dict[str, Any] = {}

    async def run_legal_research(
        self,
        search_queries: List[str],
        user_case_summary: str,
        date_range: Optional[Dict[str, str]] = None,
        max_cases_per_query: int = 20,
        use_database_search: bool = True,
    ) -> Dict[str, Any]:
        """
        Enhanced main entry point for legal case research with database integration.

        Args:
            search_queries: List of search terms (e.g., ["stenosis", "spinal injury"])
            user_case_summary: Description of the user's case for comparison
            date_range: {"start_date": "2020-01-01", "end_date": "2025-05-17"}
            max_cases_per_query: Maximum number of cases to analyze per query
            use_database_search: Whether to search existing database first

        Returns:
            Dictionary with research results and argument analysis
        """
        stop_event = _LEGAL_AGENT_STOP_FLAGS.get(self.task_id)

        try:
            # Store this instance for potential stop calls
            _LEGAL_AGENT_INSTANCES[self.task_id] = self

            # Store user case details for comparison
            self.user_case_details = {
                "summary": user_case_summary,
                "keywords": self._extract_keywords(user_case_summary),
            }

            logger.info(f"[LegalAgent {self.task_id}] Starting legal case research")
            logger.info(
                f"[LegalAgent {self.task_id}] Database statistics: {self.database.get_case_statistics()}"
            )

            all_cases = []

            # First, search existing database for similar cases
            if use_database_search:
                logger.info(f"[LegalAgent {self.task_id}] Searching existing database")
                db_similar_cases = self.database.find_similar_cases(
                    user_keywords=self.user_case_details["keywords"],
                    user_case_summary=user_case_summary,
                    min_similarity=0.2,
                    limit=50,
                )
                logger.info(
                    f"[LegalAgent {self.task_id}] Found {len(db_similar_cases)} similar cases in database"
                )
                all_cases.extend(self._convert_db_cases_to_case_info(db_similar_cases))

            # Create research page for new searches
            self.research_page = await self.context.create_new_page()

            # Search WCAT website for new cases
            for query in search_queries:
                if stop_event and stop_event.is_set():
                    logger.info(f"[LegalAgent {self.task_id}] Stop requested")
                    break

                logger.info(f"[LegalAgent {self.task_id}] Searching WCAT for: {query}")

                # Search WCAT database
                new_cases = await self._search_wcat_cases(
                    query, date_range, max_cases_per_query
                )

                # Download, analyze, and store new cases
                for case in new_cases:
                    if stop_event and stop_event.is_set():
                        break

                    # Download and analyze PDF
                    await self._download_and_analyze_case(case)

                    # Store in database with full PDF text
                    case_data = self._convert_case_info_to_db_format(case)
                    try:
                        case_id = self.database.add_case(case_data)
                        case["database_id"] = case_id
                        logger.info(
                            f"[LegalAgent {self.task_id}] Stored case {case['appeal_number']} in database"
                        )
                    except Exception as e:
                        logger.error(f"Error storing case {case['appeal_number']}: {e}")

                all_cases.extend(new_cases)

            # Enhanced similarity analysis using database
            similar_cases = self._find_similar_cases_enhanced(all_cases)

            # Build legal arguments with database cross-referencing
            legal_arguments = await self._build_legal_arguments_enhanced(similar_cases)

            # Enhanced LLM-powered strategy generation
            enhanced_strategy = None
            if self.legal_analyzer:
                enhanced_strategy = await self.generate_enhanced_strategy(
                    self.user_case_details, similar_cases
                )
                if enhanced_strategy:
                    legal_arguments["enhanced_strategy"] = enhanced_strategy

            # Multi-jurisdictional search if enabled
            multi_jurisdictional_results = {}
            if self.enable_multi_jurisdictional:
                multi_jurisdictional_results = (
                    await self.perform_multi_jurisdictional_search(
                        self.user_case_details["keywords"]
                    )
                )
                if multi_jurisdictional_results:
                    legal_arguments["multi_jurisdictional_results"] = (
                        multi_jurisdictional_results
                    )

            # Generate legal documents if enabled
            generated_documents = {}
            if self.enable_document_generation and similar_cases:
                generated_documents = await self.generate_legal_documents(
                    self.user_case_details, similar_cases
                )
                if generated_documents:
                    legal_arguments["generated_documents"] = generated_documents

            # Generate comprehensive report
            report = await self._generate_legal_report_enhanced(
                similar_cases, legal_arguments
            )

            # Save analysis results in database
            confidence_score = self._calculate_confidence_score(
                similar_cases, legal_arguments
            )
            analysis_id = self.database.save_analysis_results(
                user_case_summary=user_case_summary,
                similar_cases_found=len(similar_cases),
                favorable_precedents=legal_arguments.get("favorable_precedents", 0),
                unfavorable_precedents=legal_arguments.get("unfavorable_precedents", 0),
                recommendations=legal_arguments.get("recommendations", []),
                confidence_score=confidence_score,
            )

            return {
                "task_id": self.task_id,
                "analysis_id": analysis_id,
                "total_cases_found": len(all_cases),
                "similar_cases": similar_cases,
                "legal_arguments": legal_arguments,
                "report": report,
                "confidence_score": confidence_score,
                "database_statistics": self.database.get_case_statistics(),
                "status": "completed",
            }

        except Exception as e:
            logger.error(f"[LegalAgent {self.task_id}] Error: {e}", exc_info=True)
            return {"task_id": self.task_id, "error": str(e), "status": "failed"}

        finally:
            if self.research_page:
                try:
                    await self.research_page.close()
                except Exception as e:
                    logger.error(f"Error closing research page: {e}")

            if self.task_id in _LEGAL_AGENT_INSTANCES:
                del _LEGAL_AGENT_INSTANCES[self.task_id]

    def _convert_db_cases_to_case_info(
        self, db_cases: List[Dict[str, Any]]
    ) -> List[CaseInfo]:
        """Convert database cases to CaseInfo format"""
        case_info_list = []
        for db_case in db_cases:
            case_info: CaseInfo = {
                "appeal_number": db_case.get("appeal_number", ""),
                "date": db_case.get("date", ""),
                "appeal_type": db_case.get("appeal_type", ""),
                "decision_type": db_case.get("decision_type", ""),
                "issues": db_case.get("issues", ""),
                "pdf_url": db_case.get("pdf_url", ""),
                "pdf_path": db_case.get("pdf_path"),
                "case_summary": db_case.get("case_summary"),
                "keywords": db_case.get("keywords", []),
                "outcome": db_case.get("outcome"),
                "similarity_score": db_case.get("similarity_score"),
                "database_id": db_case.get("database_id"),
            }
            case_info_list.append(case_info)
        return case_info_list

    def _convert_case_info_to_db_format(self, case: CaseInfo) -> Dict[str, Any]:
        """Convert CaseInfo to database format"""
        # Read full text from PDF if available
        full_text = ""
        pdf_path = case.get("pdf_path")
        if pdf_path and Path(pdf_path).exists():
            try:
                pdf_analysis = self._analyze_pdf_content(Path(pdf_path))
                full_text = pdf_analysis.get("full_text", "")
            except Exception as e:
                logger.warning(f"Could not extract full text from {pdf_path}: {e}")

        return {
            "appeal_number": case["appeal_number"],
            "date": case["date"],
            "appeal_type": case["appeal_type"],
            "decision_type": case["decision_type"],
            "issues": case["issues"],
            "case_summary": case.get("case_summary"),
            "outcome": case.get("outcome"),
            "pdf_url": case["pdf_url"],
            "pdf_path": case.get("pdf_path"),
            "full_text": full_text,
            "keywords": case["keywords"],
        }

    async def _search_wcat_cases(
        self,
        query: str,
        date_range: Optional[Dict[str, str]] = None,
        max_cases: int = 20,
    ) -> List[CaseInfo]:
        """Search WCAT database and extract case information"""
        if not self.research_page:
            logger.error("Research page not available")
            return []

        base_url = "https://www.wcat.bc.ca/home/search-past-decisions/"

        # Build search URL with parameters
        params = {
            "q": query,
            "start_date": date_range.get("start_date", "2020-01-01")
            if date_range
            else "2020-01-01",
            "end_date": date_range.get("end_date", "2025-05-17")
            if date_range
            else "2025-05-17",
            "appeal_number": "",
            "application_type": "",
            "document_type": "",
            "classification": "",
            "sortby": "relevant",
        }

        # Construct URL
        search_url = base_url + "?" + "&".join([f"{k}={v}" for k, v in params.items()])

        try:
            await self.research_page.goto(search_url, wait_until="networkidle")
            logger.info(
                f"[LegalAgent {self.task_id}] Loaded search results for: {query}"
            )

            # Wait for results to load
            await self.research_page.wait_for_selector(
                ".search-result, .result-item, ul li", timeout=10000
            )

            cases = []
            case_count = 0

            # Extract case information from search results
            # WCAT uses a list structure for results
            result_items = await self.research_page.query_selector_all("ul li")

            for item in result_items:
                if case_count >= max_cases:
                    break

                try:
                    case_info = await self._extract_case_info_from_element(item)
                    if case_info:
                        cases.append(case_info)
                        case_count += 1
                        logger.info(
                            f"[LegalAgent {self.task_id}] Found case: {case_info['appeal_number']}"
                        )

                except Exception as e:
                    logger.warning(f"Error extracting case info: {e}")
                    continue

            logger.info(
                f"[LegalAgent {self.task_id}] Found {len(cases)} cases for query: {query}"
            )
            return cases

        except Exception as e:
            logger.error(f"[LegalAgent {self.task_id}] Error searching WCAT: {e}")
            return []

    async def _extract_case_info_from_element(self, element) -> Optional[CaseInfo]:
        """Extract case information from a search result element"""
        try:
            # Look for appeal number
            appeal_number_elem = await element.query_selector("strong, .appeal-number")
            appeal_number = (
                await appeal_number_elem.text_content()
                if appeal_number_elem
                else "Unknown"
            )

            # Look for date
            date_elem = await element.query_selector(".date, time")
            date = await date_elem.text_content() if date_elem else "Unknown"

            # Look for appeal type and decision type
            type_elems = await element.query_selector_all(
                ".type, .appeal-type, .decision-type"
            )
            appeal_type = "Compensation"  # Default for WCAT
            decision_type = "Merit"  # Default

            # Extract issues description
            issues_elem = await element.query_selector(".issues, .description")
            issues = await issues_elem.text_content() if issues_elem else ""

            # Look for PDF download link
            pdf_link_elem = await element.query_selector(
                'a[href*=".pdf"], a[href*="download"]'
            )
            pdf_url = ""
            if pdf_link_elem:
                href = await pdf_link_elem.get_attribute("href")
                if href:
                    pdf_url = urljoin("https://www.wcat.bc.ca", href)

            # Extract keywords from issues
            keywords = self._extract_keywords(issues)

            case_info: CaseInfo = {
                "appeal_number": appeal_number.strip(),
                "date": date.strip(),
                "appeal_type": appeal_type,
                "decision_type": decision_type,
                "issues": issues.strip(),
                "pdf_url": pdf_url,
                "pdf_path": None,
                "case_summary": None,
                "keywords": keywords,
                "outcome": None,
                "similarity_score": None,
                "database_id": None,
            }

            return case_info

        except Exception as e:
            logger.warning(f"Error extracting case info from element: {e}")
            return None

    async def _download_and_analyze_case(self, case: CaseInfo):
        """Download PDF and extract detailed case information"""
        if not case["pdf_url"]:
            logger.warning(f"No PDF URL for case {case['appeal_number']}")
            return

        try:
            # Download PDF
            pdf_path = await self._download_pdf(case["pdf_url"], case["appeal_number"])
            case["pdf_path"] = str(pdf_path)

            # Extract text and analyze
            if HAS_PYPDF2 and pdf_path.exists():
                case_analysis = self._analyze_pdf_content(pdf_path)
                case["case_summary"] = case_analysis.get("summary")
                case["outcome"] = case_analysis.get("outcome")
                case["keywords"].extend(case_analysis.get("additional_keywords", []))

            # Calculate similarity to user's case
            case["similarity_score"] = self._calculate_similarity(case)

        except Exception as e:
            logger.error(
                f"Error downloading/analyzing case {case['appeal_number']}: {e}"
            )

    async def _download_pdf(self, pdf_url: str, case_number: str) -> Path:
        """Download PDF file"""
        if not self.research_page:
            logger.error("Research page not available for PDF download")
            download_path = self.download_dir / "pdfs" / f"{case_number}.pdf"
            download_path.touch()
            return download_path

        try:
            # Navigate to PDF URL and trigger download
            await self.research_page.goto(pdf_url)

            # Set up download handling
            download_path = self.download_dir / "pdfs" / f"{case_number}.pdf"

            # Wait for download to complete
            async with self.research_page.expect_download() as download_info:
                # The navigation should trigger the download
                pass

            download = await download_info.value
            await download.save_as(download_path)

            logger.info(f"[LegalAgent {self.task_id}] Downloaded PDF: {download_path}")
            return download_path

        except Exception as e:
            logger.warning(f"Could not download PDF for {case_number}: {e}")
            # Create empty file as placeholder
            download_path = self.download_dir / "pdfs" / f"{case_number}.pdf"
            download_path.touch()
            return download_path

    def _analyze_pdf_content(self, pdf_path: Path) -> Dict[str, Any]:
        """Extract and analyze content from PDF"""
        if not HAS_PYPDF2 or PdfReader is None:
            return {
                "summary": "PDF analysis not available",
                "outcome": "Unknown",
                "additional_keywords": [],
            }

        try:
            with open(pdf_path, "rb") as file:
                pdf_reader = PdfReader(file)

                # Extract text from all pages
                full_text = ""
                for page in pdf_reader.pages:
                    text = page.extract_text()
                    if text:
                        full_text += text + "\n"

                # Analyze content for key information
                analysis = {
                    "summary": self._extract_case_summary(full_text),
                    "outcome": self._extract_outcome(full_text),
                    "additional_keywords": self._extract_keywords(full_text),
                }

                return analysis

        except Exception as e:
            logger.error(f"Error analyzing PDF {pdf_path}: {e}")
            return {
                "summary": "Error analyzing PDF",
                "outcome": "Unknown",
                "additional_keywords": [],
            }

    def _extract_case_summary(self, text: str) -> str:
        """Extract case summary from PDF text"""
        # Look for common legal document patterns
        summary_patterns = [
            r"ISSUES?:\s*(.{100,500})",
            r"SUMMARY:\s*(.{100,500})",
            r"BACKGROUND:\s*(.{100,500})",
            r"The issues? (?:on appeal|under appeal) (?:is|are):\s*(.{100,500})",
        ]

        for pattern in summary_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                summary = match.group(1).strip()
                # Clean up the summary
                summary = re.sub(r"\s+", " ", summary)
                return summary[:500] + "..." if len(summary) > 500 else summary

        # Fallback: take first substantial paragraph
        paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 100]
        if paragraphs:
            return (
                paragraphs[0][:500] + "..."
                if len(paragraphs[0]) > 500
                else paragraphs[0]
            )

        return "Summary not available"

    def _extract_outcome(self, text: str) -> str:
        """Extract case outcome from PDF text"""
        outcome_patterns = [
            r"(?:DECISION|CONCLUSION|ORDER):\s*(.{50,200})",
            r"The appeal is (allowed|dismissed|granted|denied)",
            r"(?:I|We) (?:find|conclude|decide) that (.{50,200})",
        ]

        for pattern in outcome_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                outcome = match.group(1).strip()
                outcome = re.sub(r"\s+", " ", outcome)
                return outcome[:200] + "..." if len(outcome) > 200 else outcome

        return "Outcome not determined"

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords from text"""
        if not text:
            return []

        # Common WCAT/medical/legal terms
        keyword_patterns = [
            r"\b(?:stenosis|disc\s+herniation|radiculopathy|spondylosis|neuropathy)\b",
            r"\b(?:L\d-\d|C\d-\d|T\d-\d)\b",  # Spinal levels
            r"\b(?:permanent|temporary|aggravation|causation|employment)\b",
            r"\b(?:compensable|workplace|injury|accident)\b",
            r"\b(?:medical|surgical|treatment|therapy)\b",
        ]

        keywords = []
        text_lower = text.lower()

        for pattern in keyword_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            keywords.extend(matches)

        # Remove duplicates and return
        return list(set(keywords))

    def _calculate_similarity(self, case: CaseInfo) -> float:
        """Calculate similarity score between case and user's case"""
        if not self.user_case_details:
            return 0.0

        user_keywords = set(self.user_case_details.get("keywords", []))
        case_keywords = set(case["keywords"])

        # Simple keyword overlap similarity
        if not user_keywords and not case_keywords:
            return 0.0

        intersection = user_keywords.intersection(case_keywords)
        union = user_keywords.union(case_keywords)

        similarity = len(intersection) / len(union) if union else 0.0

        # Boost score for specific medical terms
        medical_terms = {"stenosis", "disc herniation", "radiculopathy", "spinal"}
        if intersection.intersection(medical_terms):
            similarity += 0.2

        return min(similarity, 1.0)

    def _find_similar_cases_enhanced(self, all_cases: List[CaseInfo]) -> List[CaseInfo]:
        """Find cases most similar to user's case"""
        # Sort by similarity score, ensuring we handle None values properly
        similar_cases = []
        for case in all_cases:
            similarity_score = case.get("similarity_score")
            if similarity_score is not None and similarity_score > 0.3:
                similar_cases.append(case)

        # Sort with proper handling of None values
        similar_cases.sort(key=lambda x: x.get("similarity_score") or 0.0, reverse=True)

        return similar_cases[:10]  # Return top 10 most similar

    async def _build_legal_arguments_enhanced(
        self, similar_cases: List[CaseInfo]
    ) -> Dict[str, Any]:
        """Build legal arguments based on similar cases"""
        if not similar_cases:
            return {"arguments": [], "precedents": [], "recommendations": []}

        # Group cases by outcome
        favorable_cases = []
        unfavorable_cases = []

        for case in similar_cases:
            outcome = case.get("outcome") or ""
            outcome_lower = outcome.lower()
            if any(
                word in outcome_lower
                for word in ["allowed", "granted", "accepted", "compensable"]
            ):
                favorable_cases.append(case)
            else:
                unfavorable_cases.append(case)

        arguments = {
            "favorable_precedents": len(favorable_cases),
            "unfavorable_precedents": len(unfavorable_cases),
            "key_arguments": self._extract_key_arguments(favorable_cases),
            "precedent_cases": [
                {
                    "appeal_number": case["appeal_number"],
                    "date": case["date"],
                    "issues": case["issues"],
                    "outcome": case.get("outcome") or "Unknown",
                    "similarity_score": case.get("similarity_score") or 0.0,
                }
                for case in favorable_cases[:5]
            ],
            "recommendations": self._generate_recommendations(
                favorable_cases, unfavorable_cases
            ),
        }

        return arguments

    def _extract_key_arguments(self, favorable_cases: List[CaseInfo]) -> List[str]:
        """Extract key legal arguments from favorable cases"""
        arguments = []

        for case in favorable_cases:
            case_summary = case.get("case_summary") or ""
            outcome = case.get("outcome") or ""

            case_summary_lower = case_summary.lower()
            outcome_lower = outcome.lower()

            # Extract argument patterns
            if (
                "employment" in case_summary_lower
                and "aggravation" in case_summary_lower
            ):
                arguments.append(
                    f"Employment-related aggravation precedent (Case {case['appeal_number']})"
                )

            if "causation" in case_summary_lower:
                arguments.append(
                    f"Causation established in similar circumstances (Case {case['appeal_number']})"
                )

            if "compensable" in outcome_lower:
                arguments.append(
                    f"Similar condition deemed compensable (Case {case['appeal_number']})"
                )

        return list(set(arguments))  # Remove duplicates

    def _generate_recommendations(
        self, favorable_cases: List[CaseInfo], unfavorable_cases: List[CaseInfo]
    ) -> List[str]:
        """Generate strategic recommendations"""
        recommendations = []

        if len(favorable_cases) > len(unfavorable_cases):
            recommendations.append("Strong precedent support exists for your case type")

        if favorable_cases:
            recommendations.append(
                "Focus on employment-related causation or aggravation"
            )
            recommendations.append(
                "Highlight medical evidence supporting work-related connection"
            )

        if unfavorable_cases:
            recommendations.append(
                "Address potential counter-arguments from unfavorable precedents"
            )

        recommendations.append(
            "Consider obtaining additional medical opinions if needed"
        )

        return recommendations

    async def _generate_legal_report_enhanced(
        self, similar_cases: List[CaseInfo], legal_arguments: Dict[str, Any]
    ) -> str:
        """Generate comprehensive legal research report"""
        report_path = self.download_dir / "analysis" / f"legal_report_{self.task_id}.md"

        report_content = f"""# Legal Case Research Report

## Research Summary
- **Task ID**: {self.task_id}
- **Date**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **Total Cases Analyzed**: {len(self.cases_found)}
- **Similar Cases Found**: {len(similar_cases)}

## User Case Summary
{self.user_case_details.get("summary", "Not provided")}

## Key Findings

### Favorable Precedents: {legal_arguments.get("favorable_precedents", 0)}
### Unfavorable Precedents: {legal_arguments.get("unfavorable_precedents", 0)}

## Most Relevant Cases

"""

        for i, case in enumerate(similar_cases[:5], 1):
            report_content += f"""
### {i}. Case {case["appeal_number"]} (Similarity: {case.get("similarity_score", 0):.2f})
- **Date**: {case["date"]}
- **Issues**: {case["issues"]}
- **Outcome**: {case.get("outcome", "Not determined")}
- **PDF**: {case["pdf_path"] if case["pdf_path"] else "Not available"}

"""

        report_content += """
## Legal Arguments

### Key Arguments to Pursue:
"""
        for arg in legal_arguments.get("key_arguments", []):
            report_content += f"- {arg}\n"

        report_content += """
### Strategic Recommendations:
"""
        for rec in legal_arguments.get("recommendations", []):
            report_content += f"- {rec}\n"

        # Save report
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)

        logger.info(f"[LegalAgent {self.task_id}] Generated report: {report_path}")
        return report_content

    def _calculate_confidence_score(
        self, similar_cases: List[CaseInfo], legal_arguments: Dict[str, Any]
    ) -> float:
        """Calculate confidence score based on similarity and legal arguments"""
        # Placeholder for confidence score calculation
        return 0.75  # Default value, actual implementation needed

    async def stop(self):
        """Stop the legal research agent"""
        self.stopped = True
        if self.task_id in _LEGAL_AGENT_STOP_FLAGS:
            _LEGAL_AGENT_STOP_FLAGS[self.task_id].set()

    async def generate_enhanced_strategy(
        self, user_case: Dict[str, Any], similar_cases: List[CaseInfo]
    ) -> Optional[Dict[str, Any]]:
        """Generate enhanced legal strategy using LLM analysis"""
        if not self.legal_analyzer:
            logger.warning(f"[LegalAgent {self.task_id}] LLM analyzer not available")
            return None

        try:
            # Convert CaseInfo to dict format for analyzer
            cases_for_analysis = []
            for case in similar_cases:
                case_dict = {
                    "appeal_number": case["appeal_number"],
                    "date": case["date"],
                    "issues": case["issues"],
                    "outcome": case.get("outcome", "Unknown"),
                    "similarity_score": case.get("similarity_score", 0.0),
                    "case_summary": case.get("case_summary", ""),
                }
                cases_for_analysis.append(case_dict)

            strategy = self.legal_analyzer.generate_legal_strategy(
                user_case,
                cases_for_analysis[:5],  # Limit to top 5 cases
            )

            logger.info(
                f"[LegalAgent {self.task_id}] Generated enhanced legal strategy"
            )
            return strategy

        except Exception as e:
            logger.error(
                f"[LegalAgent {self.task_id}] Error generating enhanced strategy: {e}"
            )
            return None

    async def generate_legal_documents(
        self, case_details: Dict[str, Any], precedent_cases: List[CaseInfo]
    ) -> Dict[str, str]:
        """Generate legal documents using the document generator"""
        if not self.document_generator:
            logger.warning(
                f"[LegalAgent {self.task_id}] Document generator not available"
            )
            return {}

        try:
            # Prepare precedent cases for document generation
            precedents_for_docs = []
            for case in precedent_cases[:5]:  # Top 5 precedents
                precedents_for_docs.append(
                    {
                        "appeal_number": case["appeal_number"],
                        "outcome": case.get("outcome", "Unknown"),
                    }
                )

            # Generate appeal notice
            doc_details = {
                "appellant_name": case_details.get(
                    "appellant_name", "[APPELLANT NAME]"
                ),
                "appellant_address": case_details.get(
                    "appellant_address", "[APPELLANT ADDRESS]"
                ),
                "grounds": case_details.get("summary", "")[0:200] + "...",
                "remedy": "Appeal decision and grant compensation for work-related injury",
                "precedents": precedents_for_docs,
            }

            appeal_notice = self.document_generator.generate_appeal_notice(doc_details)

            # Save the document
            docs_dir = self.download_dir / "documents"
            docs_dir.mkdir(exist_ok=True)

            appeal_file = docs_dir / f"appeal_notice_{self.task_id}.txt"
            with open(appeal_file, "w", encoding="utf-8") as f:
                f.write(appeal_notice)

            logger.info(f"[LegalAgent {self.task_id}] Generated legal documents")

            return {
                "appeal_notice": appeal_notice,
                "appeal_notice_path": str(appeal_file),
            }

        except Exception as e:
            logger.error(f"[LegalAgent {self.task_id}] Error generating documents: {e}")
            return {}

    async def perform_multi_jurisdictional_search(
        self, search_terms: List[str]
    ) -> Dict[str, List]:
        """Perform multi-jurisdictional search if enabled"""
        if not self.multi_researcher:
            logger.warning(
                f"[LegalAgent {self.task_id}] Multi-jurisdictional researcher not available"
            )
            return {}

        try:
            query = " ".join(search_terms)
            jurisdictions = ["bc_wcat", "canlii"]  # Default jurisdictions

            additional_results = self.multi_researcher.search_multiple_jurisdictions(
                query, jurisdictions
            )

            logger.info(
                f"[LegalAgent {self.task_id}] Performed multi-jurisdictional search"
            )
            return additional_results

        except Exception as e:
            logger.error(
                f"[LegalAgent {self.task_id}] Error in multi-jurisdictional search: {e}"
            )
            return {}

    async def track_case_progress(
        self, case_id: str, milestone: str, deadline: str, notes: str = ""
    ):
        """Track case progress and deadlines"""
        if not self.case_tracker:
            logger.warning(f"[LegalAgent {self.task_id}] Case tracker not available")
            return

        try:
            self.case_tracker.add_case_milestone(case_id, milestone, deadline, notes)
            logger.info(
                f"[LegalAgent {self.task_id}] Added case milestone: {milestone}"
            )

        except Exception as e:
            logger.error(
                f"[LegalAgent {self.task_id}] Error tracking case progress: {e}"
            )

    async def get_upcoming_deadlines(self, days_ahead: int = 30) -> List[Dict]:
        """Get upcoming case deadlines"""
        if not self.case_tracker:
            return []

        try:
            deadlines = self.case_tracker.get_upcoming_deadlines(days_ahead)
            return deadlines

        except Exception as e:
            logger.error(f"[LegalAgent {self.task_id}] Error getting deadlines: {e}")
            return []


# Utility functions for running legal research tasks


async def run_legal_research_task(
    search_queries: List[str],
    user_case_summary: str,
    task_id: str,
    browser_config: Dict[str, Any],
    date_range: Optional[Dict[str, str]] = None,
    max_cases_per_query: int = 20,
    download_dir: str = "./tmp/legal_research",
) -> Dict[str, Any]:
    """
    Run a single legal research task with proper browser management.
    """
    try:
        # Create browser and context
        browser = CustomBrowser()
        context = await browser.new_context()

        # Create legal research agent
        agent = LegalCaseResearchAgent(
            browser=browser, context=context, download_dir=download_dir, task_id=task_id
        )

        # Run research
        results = await agent.run_legal_research(
            search_queries=search_queries,
            user_case_summary=user_case_summary,
            date_range=date_range,
            max_cases_per_query=max_cases_per_query,
        )

        return results

    except Exception as e:
        logger.error(f"Error in legal research task {task_id}: {e}", exc_info=True)
        return {"task_id": task_id, "error": str(e), "status": "failed"}

    finally:
        try:
            if "context" in locals():
                await context.close()
            if "browser" in locals():
                await browser.close()
        except Exception as e:
            logger.error(f"Error cleaning up browser resources: {e}")


def run_legal_research_sync(
    search_queries: List[str],
    user_case_summary: str,
    task_id: str,
    browser_config: Dict[str, Any],
    date_range: Optional[Dict[str, str]] = None,
    max_cases_per_query: int = 20,
    download_dir: str = "./tmp/legal_research",
) -> Dict[str, Any]:
    """
    Synchronous wrapper for legal research task.
    This function can be called from Gradio event handlers.
    """
    import asyncio

    import nest_asyncio

    # Apply nest_asyncio to allow nested event loops
    nest_asyncio.apply()

    try:
        # Try to get existing event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If there's already a running loop, use nest_asyncio
            return loop.run_until_complete(
                run_legal_research_task(
                    search_queries=search_queries,
                    user_case_summary=user_case_summary,
                    task_id=task_id,
                    browser_config=browser_config,
                    date_range=date_range,
                    max_cases_per_query=max_cases_per_query,
                    download_dir=download_dir,
                )
            )
        else:
            # No running loop, create a new one
            return asyncio.run(
                run_legal_research_task(
                    search_queries=search_queries,
                    user_case_summary=user_case_summary,
                    task_id=task_id,
                    browser_config=browser_config,
                    date_range=date_range,
                    max_cases_per_query=max_cases_per_query,
                    download_dir=download_dir,
                )
            )
    except RuntimeError as e:
        if "no running event loop" in str(e):
            # Create new event loop
            return asyncio.run(
                run_legal_research_task(
                    search_queries=search_queries,
                    user_case_summary=user_case_summary,
                    task_id=task_id,
                    browser_config=browser_config,
                    date_range=date_range,
                    max_cases_per_query=max_cases_per_query,
                    download_dir=download_dir,
                )
            )
        else:
            raise e


async def stop_legal_research_agent(task_id: str):
    """Stop a running legal research agent"""
    if task_id in _LEGAL_AGENT_STOP_FLAGS:
        _LEGAL_AGENT_STOP_FLAGS[task_id].set()
        logger.info(f"Stop signal sent to legal research agent {task_id}")

    if task_id in _LEGAL_AGENT_INSTANCES:
        try:
            await _LEGAL_AGENT_INSTANCES[task_id].stop()
        except Exception as e:
            logger.error(f"Error stopping legal research agent {task_id}: {e}")

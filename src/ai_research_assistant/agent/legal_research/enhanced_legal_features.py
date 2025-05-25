"""
Enhanced Legal Research Features for WCAT Case Analysis

This module provides advanced features for legal case research:
1. LLM-powered case analysis and argument generation
2. Multi-jurisdictional legal research capabilities
3. Advanced legal reasoning and precedent analysis
4. Automated legal document generation
5. Case strategy optimization
"""

import logging
import re
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from ...utils.unified_llm_factory import UnifiedLLMFactory

logger = logging.getLogger(__name__)


class EnhancedLegalAnalyzer:
    """
    Enhanced legal analysis using unified LLM integration for deeper case insights
    """

    def __init__(
        self,
        llm_instance=None,
        llm_provider: str = "google",
        global_settings_manager=None,
    ):
        """Initialize with a pre-configured LLM instance or create one from provider/settings"""
        self.llm_instance = llm_instance
        self.llm_provider = llm_provider
        self.global_settings_manager = global_settings_manager

        # If no LLM instance provided, create one using unified factory
        if not self.llm_instance:
            try:
                self.llm_instance = self._initialize_llm()
                if self.llm_instance:
                    logger.info(
                        f"✅ Successfully initialized LLM for EnhancedLegalAnalyzer using {self.llm_provider}"
                    )
                else:
                    logger.warning(
                        "Failed to initialize LLM instance for EnhancedLegalAnalyzer"
                    )
            except Exception as e:
                logger.error(f"Error initializing LLM for EnhancedLegalAnalyzer: {e}")
                self.llm_instance = None

    def _initialize_llm(self):
        """Initialize LLM using unified factory with global settings support"""
        try:
            factory = UnifiedLLMFactory()

            # Try global settings first if available
            if self.global_settings_manager:
                try:
                    llm = factory.create_llm_from_global_settings(
                        self.global_settings_manager, "primary"
                    )
                    if llm:
                        logger.info(
                            "✅ Using global settings for EnhancedLegalAnalyzer LLM"
                        )
                        return llm
                except Exception as e:
                    logger.warning(
                        f"Failed to use global settings for EnhancedLegalAnalyzer LLM: {e}"
                    )

            # Fallback to provider-specific configuration
            logger.info(
                f"Using provider-specific LLM configuration for EnhancedLegalAnalyzer: {self.llm_provider}"
            )

            config = {
                "provider": self.llm_provider,
                "model_name": None,  # Will use default for provider
                "temperature": 0.7,  # Good for legal analysis
                "max_tokens": 2048,
            }

            return factory.create_llm_from_config(config)

        except Exception as e:
            logger.error(
                f"Failed to initialize LLM using unified factory for EnhancedLegalAnalyzer: {e}"
            )
            return None

    def generate_legal_strategy(
        self, user_case: Dict[str, Any], similar_cases: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive legal strategy using unified LLM analysis
        """
        if not self.llm_instance:
            return {"error": "LLM instance not available"}

        prompt = self._build_strategy_prompt(user_case, similar_cases)

        try:
            # Use the unified LLM interface (LangChain compatible)
            response = self.llm_instance.invoke(prompt)

            # Handle different response types
            if hasattr(response, "content"):
                strategy = response.content
            elif isinstance(response, str):
                strategy = response
            else:
                strategy = str(response)

            return self._parse_strategy_response(strategy)

        except Exception as e:
            logger.error(f"Error generating legal strategy: {e}")
            return {"error": str(e)}

    def _build_strategy_prompt(
        self, user_case: Dict[str, Any], similar_cases: List[Dict[str, Any]]
    ) -> str:
        """Build comprehensive prompt for legal strategy generation"""
        prompt = f"""You are an expert legal strategist specializing in Workers' Compensation law. Provide comprehensive legal analysis based on the case details and precedents below.

        LEGAL CASE ANALYSIS REQUEST

        USER'S CASE:
        {user_case.get("summary", "")}

        Key Issues: {", ".join(user_case.get("keywords", []))}

        SIMILAR PRECEDENT CASES:
        """

        for i, case in enumerate(similar_cases[:5], 1):
            prompt += f"""
        {i}. Case {case.get("appeal_number", "Unknown")}
           Date: {case.get("date", "Unknown")}
           Issues: {case.get("issues", "")[:200]}...
           Outcome: {case.get("outcome", "Unknown")}
           Similarity: {case.get("similarity_score", 0):.2f}
        """

        prompt += """

        ANALYSIS REQUIRED:
        1. Identify the strongest legal arguments based on precedents
        2. Highlight potential weaknesses and counter-arguments
        3. Suggest evidence gathering strategies
        4. Recommend expert witnesses or medical assessments
        5. Provide step-by-step litigation strategy
        6. Assess likelihood of success (percentage)

        Please provide a structured response with clear headings and actionable recommendations.
        """

        return prompt

    def _parse_strategy_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into structured strategy"""
        # Simple parsing - could be enhanced with more sophisticated NLP
        return {
            "raw_analysis": response,
            "generated_at": datetime.now().isoformat(),
            "confidence": "high",  # Could extract from response
            "key_points": self._extract_key_points(response),
        }

    def _extract_key_points(self, text: str) -> List[str]:
        """Extract key strategic points from analysis"""
        # Look for numbered lists or bullet points
        points = []
        lines = text.split("\n")
        for line in lines:
            line = line.strip()
            if (
                re.match(r"^[0-9]+\.", line)
                or line.startswith("•")
                or line.startswith("-")
            ):
                if len(line) > 10:  # Avoid short/empty bullets
                    points.append(line)
        return points[:10]  # Return top 10 points


class MultiJurisdictionalResearcher:
    """
    Research legal cases across multiple jurisdictions and legal databases
    """

    def __init__(self):
        self.supported_jurisdictions = {
            "bc_wcat": "https://www.wcat.bc.ca",
            "canlii": "https://www.canlii.org",
            "supreme_court": "https://www.scc-csc.ca",
            # Add more jurisdictions as needed
        }

    def search_multiple_jurisdictions(
        self, query: str, jurisdictions: Optional[List[str]] = None
    ) -> Dict[str, List]:
        """
        Search multiple legal databases simultaneously
        """
        if jurisdictions is None:
            jurisdictions = ["bc_wcat", "canlii"]

        results = {}
        for jurisdiction in jurisdictions:
            if jurisdiction in self.supported_jurisdictions:
                results[jurisdiction] = self._search_jurisdiction(jurisdiction, query)

        return results

    def _search_jurisdiction(self, jurisdiction: str, query: str) -> List[Dict]:
        """
        Search specific jurisdiction (placeholder for implementation)
        """
        # Implement specific search logic for each jurisdiction
        return []


class LegalDocumentGenerator:
    """
    Generate legal documents and forms based on case analysis
    """

    def __init__(self, template_dir: str = "./legal_templates"):
        self.template_dir = Path(template_dir)
        self.template_dir.mkdir(exist_ok=True)

    def generate_appeal_notice(self, case_details: Dict[str, Any]) -> str:
        """Generate Notice of Appeal document"""
        template = """
NOTICE OF APPEAL TO WORKERS' COMPENSATION APPEAL TRIBUNAL

Appeal Number: [TO BE ASSIGNED]
Date: {date}

APPELLANT INFORMATION:
Name: {appellant_name}
Address: {appellant_address}
Phone: {appellant_phone}

GROUNDS FOR APPEAL:
{grounds_for_appeal}

REMEDY SOUGHT:
{remedy_sought}

SUPPORTING PRECEDENTS:
{precedent_cases}

Respectfully submitted,
{signature}
        """

        return template.format(
            date=datetime.now().strftime("%Y-%m-%d"),
            appellant_name=case_details.get("appellant_name", "[APPELLANT NAME]"),
            appellant_address=case_details.get(
                "appellant_address", "[APPELLANT ADDRESS]"
            ),
            appellant_phone=case_details.get("appellant_phone", "[PHONE NUMBER]"),
            grounds_for_appeal=case_details.get("grounds", "[GROUNDS FOR APPEAL]"),
            remedy_sought=case_details.get("remedy", "[REMEDY SOUGHT]"),
            precedent_cases=self._format_precedents(case_details.get("precedents", [])),
            signature=case_details.get("signature", "[SIGNATURE]"),
        )

    def _format_precedents(self, precedents: List[Dict]) -> str:
        """Format precedent cases for legal document"""
        formatted = ""
        for i, case in enumerate(precedents, 1):
            formatted += f"{i}. {case.get('appeal_number', 'Unknown')} - {case.get('outcome', '')}\n"
        return formatted


class CaseProgressTracker:
    """
    Track case progress, deadlines, and important dates
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_tracking_db()

    def _init_tracking_db(self):
        """Initialize case tracking database"""
        import sqlite3

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS case_tracking (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    case_id TEXT UNIQUE,
                    case_stage TEXT,
                    next_deadline DATE,
                    important_dates TEXT, -- JSON
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def add_case_milestone(
        self, case_id: str, milestone: str, date: str, notes: str = ""
    ):
        """Add important milestone to case tracking"""
        import sqlite3

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO case_tracking
                (case_id, case_stage, next_deadline, notes, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
                (case_id, milestone, date, notes),
            )
            conn.commit()

    def get_upcoming_deadlines(self, days_ahead: int = 30) -> List[Dict]:
        """Get upcoming deadlines for all tracked cases"""
        import sqlite3

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT * FROM case_tracking
                WHERE next_deadline BETWEEN date('now') AND date('now', '+{} days')
                ORDER BY next_deadline
            """.format(days_ahead)
            )
            return [dict(row) for row in cursor.fetchall()]


class AutomatedResearchScheduler:
    """
    Automatically schedule and run research updates for ongoing cases
    """

    def __init__(self, agent_instance):
        self.agent = agent_instance
        self.scheduled_searches = {}

    def schedule_periodic_research(
        self, case_id: str, search_terms: List[str], frequency_days: int = 7
    ):
        """Schedule periodic research for new precedents"""
        self.scheduled_searches[case_id] = {
            "search_terms": search_terms,
            "frequency_days": frequency_days,
            "last_run": None,
            "next_run": datetime.now(),
        }

    def run_scheduled_research(self):
        """Execute all scheduled research tasks"""
        for case_id, schedule in self.scheduled_searches.items():
            if datetime.now() >= schedule["next_run"]:
                # Run research update
                logger.info(f"Running scheduled research for case {case_id}")
                # Implementation would call the research agent
                schedule["last_run"] = datetime.now()
                schedule["next_run"] = datetime.now() + timedelta(
                    days=schedule["frequency_days"]
                )


# Example usage functions
def create_enhanced_legal_workflow(
    user_case: Dict[str, Any], existing_cases: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Create a complete enhanced legal workflow
    """
    workflow_results = {
        "workflow_id": str(uuid.uuid4()),
        "created_at": datetime.now().isoformat(),
        "enhanced_strategy": None,
        "additional_cases": {},
        "generated_documents": {},
    }

    try:
        # Initialize enhanced components
        analyzer = EnhancedLegalAnalyzer()
        multi_researcher = MultiJurisdictionalResearcher()
        doc_generator = LegalDocumentGenerator()

        # Generate comprehensive strategy
        if analyzer.llm_instance:
            strategy = analyzer.generate_legal_strategy(user_case, existing_cases)
            workflow_results["enhanced_strategy"] = strategy
            logger.info("✅ Generated enhanced legal strategy")
        else:
            logger.warning("⚠️ LLM not available, skipping strategy generation")
            workflow_results["enhanced_strategy"] = {
                "error": "LLM not available for strategy generation"
            }

        # Search additional jurisdictions
        try:
            additional_cases = multi_researcher.search_multiple_jurisdictions(
                query=" ".join(user_case.get("keywords", [])),
                jurisdictions=["bc_wcat", "canlii"],
            )
            workflow_results["additional_cases"] = additional_cases
            logger.info("✅ Completed multi-jurisdictional search")
        except Exception as e:
            logger.warning(f"Multi-jurisdictional search failed: {e}")
            workflow_results["additional_cases"] = {"error": str(e)}

        # Generate appeal documents
        try:
            appeal_notice = doc_generator.generate_appeal_notice(user_case)
            workflow_results["generated_documents"] = {"appeal_notice": appeal_notice}
            logger.info("✅ Generated legal documents")
        except Exception as e:
            logger.warning(f"Document generation failed: {e}")
            workflow_results["generated_documents"] = {"error": str(e)}

    except Exception as e:
        logger.error(f"Enhanced legal workflow failed: {e}")
        workflow_results["error"] = str(e)

    return workflow_results

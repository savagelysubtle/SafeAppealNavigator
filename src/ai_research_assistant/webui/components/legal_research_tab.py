"""
Enhanced Legal Research Agent Web UI Tab for WCAT Case Analysis

This module provides an advanced web interface for:
1. WCAT case research and analysis
2. LLM-powered legal strategy generation
3. Legal document generation
4. Case progress tracking
5. Multi-jurisdictional research
6. Database search and management
"""

import logging
import os
import threading
import uuid
from datetime import datetime

import gradio as gr

from src.ai_research_assistant.agent.legal_research import (
    LegalCaseDatabase,
)
from src.ai_research_assistant.agent.legal_research.enhanced_legal_features import (
    EnhancedLegalAnalyzer,
    LegalDocumentGenerator,
    MultiJurisdictionalResearcher,
    create_enhanced_legal_workflow,
)
from src.ai_research_assistant.utils.unified_llm_factory import UnifiedLLMFactory
from src.ai_research_assistant.webui.webui_manager import WebuiManager

logger = logging.getLogger(__name__)

# Global state management
_LEGAL_RESEARCH_TASKS = {}
_LEGAL_RESEARCH_STOP_FLAGS = {}


def _get_llm_from_global_settings(
    webui_manager: WebuiManager, llm_type: str = "primary"
):
    """
    Get LLM instance from global settings manager.
    This function provides a unified way to access LLMs across all components.
    """
    try:
        if (
            hasattr(webui_manager, "global_settings_manager")
            and webui_manager.global_settings_manager
        ):
            factory = UnifiedLLMFactory()
            llm = factory.create_llm_from_global_settings(
                webui_manager.global_settings_manager, llm_type=llm_type
            )
            if llm:
                logger.info(f"✅ Using global settings for {llm_type} LLM")
                return llm

        logger.warning("Global settings manager not available")
        return None
    except Exception as e:
        logger.error(f"Failed to get LLM from global settings: {e}")
        return None


def _get_llm_from_legacy_settings(
    webui_manager: WebuiManager,
    llm_provider_val: str,
    llm_temp: float,
):
    """
    Fallback to legacy LLM initialization for backward compatibility.
    This ensures the component continues working during the migration period.
    """
    try:
        from src.ai_research_assistant.utils.llm_provider import get_llm_model

        logger.info(
            f"Using legacy LLM settings: provider={llm_provider_val}, temp={llm_temp}"
        )

        llm = get_llm_model(
            provider=llm_provider_val,
            temperature=llm_temp,
            max_tokens=4096,  # Good for legal analysis
        )

        if llm:
            logger.info(f"✅ Created LLM using legacy settings: {llm_provider_val}")
            return llm
        else:
            raise RuntimeError(
                f"Failed to create LLM with provider '{llm_provider_val}'"
            )

    except Exception as e:
        logger.error(f"Legacy LLM initialization failed: {e}")
        raise RuntimeError(f"Failed to initialize LLM: {e}")


def create_legal_research_tab(ui_manager: WebuiManager) -> None:
    """
    Creates an enhanced legal research tab with advanced features
    """
    with gr.Column():
        gr.Markdown("# ⚖️ Enhanced Legal Research Assistant")
        gr.Markdown(
            "*Advanced WCAT case research with AI-powered analysis and document generation*"
        )

        # Quick Actions Section
        with gr.Group():
            gr.Markdown("## 🚀 Quick Actions")
            with gr.Row():
                quick_research_btn = gr.Button(
                    "🔍 Quick Case Search", variant="secondary"
                )
                generate_docs_btn = gr.Button(
                    "📄 Generate Documents", variant="secondary"
                )
                db_stats_btn = gr.Button("📊 Database Statistics", variant="secondary")

        # Main Research Section
        with gr.Group():
            gr.Markdown("## 🔬 Case Research & Analysis")

            with gr.Tab("🎯 Research Configuration"):
                with gr.Row():
                    with gr.Column():
                        case_summary = gr.Textbox(
                            label="📝 Your Case Summary",
                            placeholder="Describe your case in detail (injury, circumstances, work history, etc.)",
                            lines=6,
                            info="Provide comprehensive details about your case for better analysis",
                        )

                        search_terms = gr.Textbox(
                            label="🔍 Search Terms",
                            placeholder="stenosis, warehouse injury, repetitive strain",
                            info="Comma-separated keywords for case search",
                        )

                    with gr.Column():
                        with gr.Group():
                            gr.Markdown("### 📅 Date Range")
                            date_from = gr.Textbox(
                                label="From Date",
                                value="2019-01-01",
                                placeholder="YYYY-MM-DD",
                            )
                            date_to = gr.Textbox(
                                label="To Date",
                                value=datetime.now().strftime("%Y-%m-%d"),
                                placeholder="YYYY-MM-DD",
                            )

                        with gr.Group():
                            gr.Markdown("### ⚙️ Research Settings")
                            max_cases = gr.Slider(
                                minimum=5,
                                maximum=100,
                                value=20,
                                step=5,
                                label="Maximum Cases to Analyze",
                            )
                            use_database_search = gr.Checkbox(
                                label="🗄️ Search Existing Database First",
                                value=True,
                                info="Search local database before web scraping",
                            )
                            enable_llm_analysis = gr.Checkbox(
                                label="🧠 Enable LLM-Powered Analysis",
                                value=True,
                                info="Generate strategic legal analysis using AI",
                            )
                            multi_jurisdictional = gr.Checkbox(
                                label="🌐 Multi-Jurisdictional Search",
                                value=False,
                                info="Search across multiple legal databases",
                            )

            with gr.Tab("🎛️ Advanced Options"):
                with gr.Row():
                    with gr.Column():
                        # Note: LLM configuration moved to Global Settings panel
                        gr.Markdown("### 🤖 LLM Configuration")
                        gr.Markdown("""
                        **ℹ️ LLM settings are now managed in the Global Settings panel above.**

                        Configure your AI model preferences there for optimal legal analysis.
                        """)

                        # Legacy LLM configuration (hidden by default, for fallback compatibility)
                        with gr.Accordion(
                            "🔧 Legacy LLM Override (Advanced)", open=False
                        ):
                            llm_provider = gr.Dropdown(
                                choices=["openai", "anthropic", "google"],
                                value="openai",
                                label="LLM Provider Override",
                                info="Override global LLM settings for this session only",
                            )
                            llm_temperature = gr.Slider(
                                minimum=0.0,
                                maximum=1.0,
                                value=0.1,
                                step=0.1,
                                label="Analysis Temperature Override",
                                info="Lower = more focused analysis",
                            )

                    with gr.Column():
                        gr.Markdown("### 📋 Document Generation")
                        appellant_name = gr.Textbox(
                            label="Appellant Name", placeholder="Your full legal name"
                        )
                        appellant_address = gr.Textbox(
                            label="Appellant Address",
                            placeholder="Your mailing address",
                            lines=2,
                        )
                        auto_generate_docs = gr.Checkbox(
                            label="📄 Auto-Generate Legal Documents",
                            value=True,
                            info="Automatically create appeal notices and summaries",
                        )

        # Control Buttons
        with gr.Row():
            start_research_btn = gr.Button(
                "🚀 Start Enhanced Research", variant="primary", scale=2
            )
            stop_research_btn = gr.Button("⏹️ Stop Research", variant="stop", scale=1)
            clear_results_btn = gr.Button(
                "🗑️ Clear Results", variant="secondary", scale=1
            )

        # Results Section
        with gr.Group():
            gr.Markdown("## 📊 Research Results & Analysis")

            with gr.Tab("📈 Research Progress"):
                research_status = gr.Textbox(
                    label="🔄 Research Status",
                    value="Ready to start research",
                    lines=3,
                    interactive=False,
                )

                progress_bar = gr.Progress()

                research_log = gr.Textbox(
                    label="📋 Research Log",
                    lines=10,
                    interactive=False,
                    info="Detailed log of research activities",
                )

            with gr.Tab("⚖️ Legal Analysis"):
                strategy_analysis = gr.Textbox(
                    label="🧠 AI-Generated Legal Strategy",
                    lines=15,
                    interactive=False,
                    info="Comprehensive legal analysis and strategy recommendations",
                )

                with gr.Row():
                    favorable_cases = gr.Number(
                        label="✅ Favorable Precedents", value=0, interactive=False
                    )
                    unfavorable_cases = gr.Number(
                        label="❌ Unfavorable Precedents", value=0, interactive=False
                    )
                    confidence_score = gr.Number(
                        label="🎯 Confidence Score", value=0.0, interactive=False
                    )

            with gr.Tab("📄 Generated Documents"):
                appeal_notice = gr.Textbox(
                    label="📋 Notice of Appeal",
                    lines=20,
                    interactive=False,
                    info="Auto-generated appeal notice based on your case",
                )

                with gr.Row():
                    download_notice_btn = gr.Button(
                        "💾 Download Appeal Notice", variant="secondary"
                    )
                    download_summary_btn = gr.Button(
                        "💾 Download Case Summary", variant="secondary"
                    )

            with gr.Tab("🔍 Similar Cases"):
                similar_cases_display = gr.Dataframe(
                    headers=[
                        "Appeal Number",
                        "Date",
                        "Issues",
                        "Outcome",
                        "Similarity",
                    ],
                    datatype=["str", "str", "str", "str", "number"],
                    label="📚 Most Similar Cases",
                    interactive=False,
                )

        # Database Management Section
        with gr.Group():
            gr.Markdown("## 🗄️ Database Management")

            with gr.Tab("🔍 Database Search"):
                with gr.Row():
                    db_search_query = gr.Textbox(
                        label="Search Query", placeholder="Enter search terms..."
                    )
                    db_search_btn = gr.Button("🔍 Search Database", variant="secondary")

                with gr.Row():
                    db_keywords = gr.Textbox(
                        label="Keywords Filter",
                        placeholder="stenosis, injury, employment",
                    )
                    db_outcome_filter = gr.Dropdown(
                        choices=["All", "Favorable", "Unfavorable"],
                        value="All",
                        label="Outcome Filter",
                    )
                    db_search_limit = gr.Slider(
                        minimum=10,
                        maximum=100,
                        value=50,
                        step=10,
                        label="Results Limit",
                    )

                db_search_results = gr.Dataframe(
                    headers=["Appeal Number", "Date", "Issues", "Outcome"],
                    datatype=["str", "str", "str", "str"],
                    label="🗄️ Database Search Results",
                    interactive=False,
                )

            with gr.Tab("📊 Database Statistics"):
                db_stats_display = gr.JSON(label="📈 Database Statistics", value={})

                with gr.Row():
                    export_db_btn = gr.Button("📤 Export Database", variant="secondary")
                    refresh_stats_btn = gr.Button(
                        "🔄 Refresh Statistics", variant="secondary"
                    )

        # Case Progress Tracking
        with gr.Group():
            gr.Markdown("## 📅 Case Progress Tracking")

            with gr.Row():
                case_stage = gr.Dropdown(
                    choices=[
                        "Initial Research",
                        "Evidence Gathering",
                        "Appeal Filed",
                        "Hearing Scheduled",
                        "Decision Pending",
                    ],
                    label="Current Case Stage",
                    value="Initial Research",
                )
                next_deadline = gr.Textbox(
                    label="Next Deadline", placeholder="YYYY-MM-DD"
                )
                add_milestone_btn = gr.Button("➕ Add Milestone", variant="secondary")

            upcoming_deadlines = gr.Dataframe(
                headers=["Case ID", "Stage", "Deadline", "Notes"],
                datatype=["str", "str", "str", "str"],
                label="⏰ Upcoming Deadlines",
                interactive=False,
            )

    # Event Handlers

    def start_legal_research(
        case_summary: str,
        search_terms: str,
        date_from_str: str,
        date_to_str: str,
        max_cases_val: int,
        use_db_search: bool,
        enable_llm: bool,
        multi_juris: bool,
        llm_provider_val: str,
        llm_temp: float,
        appellant_name_val: str,
        appellant_address_val: str,
        auto_gen_docs: bool,
    ):
        """Enhanced research start function with new capabilities"""

        if not case_summary.strip():
            return (
                gr.update(value="❌ Please provide a case summary"),
                gr.update(value=""),
                gr.update(value=""),
                gr.update(value=0),
                gr.update(value=0),
                gr.update(value=0.0),
                gr.update(value=""),
                gr.update(value=[]),
            )

        task_id = str(uuid.uuid4())
        _LEGAL_RESEARCH_STOP_FLAGS[task_id] = threading.Event()

        # Enhanced research configuration
        research_config = {
            "case_summary": case_summary,
            "search_terms": [
                term.strip() for term in search_terms.split(",") if term.strip()
            ],
            "date_range": {"start_date": date_from_str, "end_date": date_to_str},
            "max_cases": max_cases_val,
            "use_database_search": use_db_search,
            "enable_llm_analysis": enable_llm,
            "multi_jurisdictional": multi_juris,
            "llm_config": {"provider": llm_provider_val, "temperature": llm_temp},
            "document_generation": {
                "enabled": auto_gen_docs,
                "appellant_name": appellant_name_val,
                "appellant_address": appellant_address_val,
            },
        }

        # Start enhanced research
        def run_enhanced_research():
            """Run enhanced research in a separate thread"""
            try:
                # Initialize LLM using global settings first, then fallback to legacy
                llm = None
                if enable_llm:
                    llm = _get_llm_from_global_settings(ui_manager, "primary")
                    if not llm:
                        logger.info(
                            "Global settings not available, using legacy LLM settings"
                        )
                        llm = _get_llm_from_legacy_settings(
                            ui_manager, llm_provider_val, llm_temp
                        )

                # Initialize enhanced components
                analyzer = None
                if enable_llm:
                    # Create analyzer with proper LLM instance and global settings support
                    analyzer = EnhancedLegalAnalyzer(
                        llm_instance=llm,  # Pass the actual LLM instance
                        llm_provider=llm_provider_val,
                        global_settings_manager=getattr(
                            ui_manager, "global_settings_manager", None
                        ),
                    )

                if auto_gen_docs:
                    doc_generator = LegalDocumentGenerator()

                if multi_juris:
                    multi_researcher = MultiJurisdictionalResearcher()

                # For now, just run the enhanced workflow without browser automation
                # TODO: Integrate with actual legal case research
                results = create_enhanced_legal_workflow(
                    user_case={
                        "summary": case_summary,
                        "keywords": research_config["search_terms"],
                        "appellant_name": appellant_name_val,
                        "appellant_address": appellant_address_val,
                    },
                    existing_cases=[],  # This would be populated from database
                )

                return {
                    "task_id": task_id,
                    "status": "completed",
                    "results": results,
                    "message": "Enhanced research workflow completed successfully",
                }

            except Exception as e:
                logger.error(f"Enhanced research error: {e}", exc_info=True)
                return {
                    "task_id": task_id,
                    "status": "failed",
                    "error": str(e),
                    "message": f"Research failed: {str(e)}",
                }

        # Run the research in a thread to avoid asyncio issues
        def threaded_research():
            try:
                results = run_enhanced_research()
                _LEGAL_RESEARCH_TASKS[task_id] = results
            except Exception as e:
                logger.error(f"Thread research error: {e}")
                _LEGAL_RESEARCH_TASKS[task_id] = {"error": str(e)}

        thread = threading.Thread(target=threaded_research)
        thread.start()
        _LEGAL_RESEARCH_TASKS[task_id] = {"status": "running", "thread": thread}

        return (
            gr.update(value=f"🚀 Started enhanced research (Task: {task_id[:8]})"),
            gr.update(value="Research in progress..."),
            gr.update(value="Initializing enhanced legal research workflow..."),
            gr.update(value=0),
            gr.update(value=0),
            gr.update(value=0.0),
            gr.update(value=""),
            gr.update(value=[]),
        )

    def stop_legal_research():
        """Stop all running legal research tasks"""
        for task_id, stop_event in _LEGAL_RESEARCH_STOP_FLAGS.items():
            stop_event.set()

        for task_id, task_data in _LEGAL_RESEARCH_TASKS.items():
            if isinstance(task_data, dict) and "thread" in task_data:
                # It's a thread-based task
                thread = task_data["thread"]
                if thread.is_alive():
                    # Set stop flag and wait briefly for thread to finish
                    if task_id in _LEGAL_RESEARCH_STOP_FLAGS:
                        _LEGAL_RESEARCH_STOP_FLAGS[task_id].set()
                    # Note: We can't force-kill threads in Python, so we rely on cooperative stopping
            elif hasattr(task_data, "cancel") and callable(
                getattr(task_data, "cancel", None)
            ):
                # It's an asyncio task (legacy)
                task_data.cancel()  # type: ignore

        _LEGAL_RESEARCH_TASKS.clear()
        _LEGAL_RESEARCH_STOP_FLAGS.clear()

        return gr.update(value="⏹️ All research tasks stopped")

    def search_database(
        query: str,
        keywords_str: str,
        outcome_filter_val: str,
        limit_val: int,
    ):
        """Enhanced database search with better filtering"""
        try:
            # Get database path from environment
            db_path = os.getenv("WCAT_DATABASE_PATH")
            if not db_path:
                return gr.update(value=[["No database configured", "", "", ""]])

            database = LegalCaseDatabase(db_path)

            # Build search filters
            filters = {}
            if keywords_str.strip():
                filters["keywords"] = [k.strip() for k in keywords_str.split(",")]

            if outcome_filter_val != "All":
                outcome_term = (
                    "allowed" if outcome_filter_val == "Favorable" else "dismissed"
                )
                filters["outcome_contains"] = outcome_term

            # Perform search
            results = database.search_cases(
                query=query, filters=filters, limit=limit_val
            )

            # Format results for display
            formatted_results = []
            for case in results:
                formatted_results.append(
                    [
                        case["appeal_number"],
                        case["date"],
                        case["issues"][:100] + "..."
                        if len(case["issues"]) > 100
                        else case["issues"],
                        case["outcome"][:50] + "..."
                        if case.get("outcome") and len(case["outcome"]) > 50
                        else case.get("outcome", ""),
                    ]
                )

            return gr.update(value=formatted_results)

        except Exception as e:
            logger.error(f"Database search error: {e}")
            return gr.update(value=[["Error", str(e), "", ""]])

    def load_database_stats():
        """Load and display database statistics"""
        try:
            db_path = os.getenv("WCAT_DATABASE_PATH")
            if not db_path:
                return gr.update(value={"error": "No database configured"})

            database = LegalCaseDatabase(db_path)
            stats = database.get_case_statistics()
            return gr.update(value=stats)

        except Exception as e:
            logger.error(f"Database stats error: {e}")
            return gr.update(value={"error": str(e)})

    def generate_quick_documents(
        case_summary: str, appellant_name: str, appellant_address: str
    ):
        """Quick document generation"""
        try:
            doc_generator = LegalDocumentGenerator()

            case_details = {
                "appellant_name": appellant_name,
                "appellant_address": appellant_address,
                "grounds": f"Based on case summary: {case_summary[:200]}...",
                "remedy": "Appeal decision and grant compensation",
                "precedents": [],  # Would be populated from research
            }

            appeal_notice = doc_generator.generate_appeal_notice(case_details)
            return gr.update(value=appeal_notice)

        except Exception as e:
            logger.error(f"Document generation error: {e}")
            return gr.update(value=f"Error generating document: {str(e)}")

    # Wire up event handlers
    start_research_btn.click(
        start_legal_research,
        inputs=[
            case_summary,
            search_terms,
            date_from,
            date_to,
            max_cases,
            use_database_search,
            enable_llm_analysis,
            multi_jurisdictional,
            llm_provider,
            llm_temperature,
            appellant_name,
            appellant_address,
            auto_generate_docs,
        ],
        outputs=[
            research_status,
            strategy_analysis,
            research_log,
            favorable_cases,
            unfavorable_cases,
            confidence_score,
            appeal_notice,
            similar_cases_display,
        ],
    )

    stop_research_btn.click(stop_legal_research, outputs=[research_status])

    db_search_btn.click(
        search_database,
        inputs=[db_search_query, db_keywords, db_outcome_filter, db_search_limit],
        outputs=[db_search_results],
    )

    db_stats_btn.click(load_database_stats, outputs=[db_stats_display])

    refresh_stats_btn.click(load_database_stats, outputs=[db_stats_display])

    generate_docs_btn.click(
        generate_quick_documents,
        inputs=[case_summary, appellant_name, appellant_address],
        outputs=[appeal_notice],
    )

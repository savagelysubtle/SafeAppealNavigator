"""
Cross Reference Agent WebUI Tab

Provides interface for cross-referencing documents, cases, and data across multiple sources,
including relationship analysis and correlation discovery.
"""

import asyncio
import logging
from typing import Any, AsyncGenerator, Dict

import gradio as gr
from gradio.components import Component

from src.ai_research_assistant.agent.core import AgentTask, TaskPriority
from src.ai_research_assistant.agent.cross_reference.cross_reference_agent import (
    CrossReferenceAgent,
)
from src.ai_research_assistant.webui.webui_manager import WebuiManager

logger = logging.getLogger(__name__)


async def run_cross_reference_operation(
    webui_manager: WebuiManager, components: Dict[Component, Any]
) -> AsyncGenerator[Dict[Component, Any], None]:
    """Execute the selected cross-reference operation."""

    # Get UI components
    reference_type_comp = webui_manager.get_component_by_id(
        "cross_reference_agent.reference_type"
    )
    primary_case_comp = webui_manager.get_component_by_id(
        "cross_reference_agent.primary_case"
    )
    comparison_scope_comp = webui_manager.get_component_by_id(
        "cross_reference_agent.comparison_scope"
    )
    analysis_depth_comp = webui_manager.get_component_by_id(
        "cross_reference_agent.analysis_depth"
    )
    start_button_comp = webui_manager.get_component_by_id(
        "cross_reference_agent.start_button"
    )
    stop_button_comp = webui_manager.get_component_by_id(
        "cross_reference_agent.stop_button"
    )
    progress_comp = webui_manager.get_component_by_id("cross_reference_agent.progress")
    status_comp = webui_manager.get_component_by_id("cross_reference_agent.status")
    results_comp = webui_manager.get_component_by_id("cross_reference_agent.results")

    # Get input values
    reference_type = components.get(reference_type_comp, "case_analysis")
    primary_case = components.get(primary_case_comp, "").strip()
    comparison_scope = components.get(comparison_scope_comp, ["similar_cases"])
    analysis_depth = components.get(analysis_depth_comp, "standard")

    # Validation
    if not primary_case:
        gr.Warning("Please enter a primary case or document identifier.")
        yield {start_button_comp: gr.update(interactive=True)}
        return

    # Initial UI update
    yield {
        start_button_comp: gr.update(
            value="⏳ Starting Analysis...", interactive=False
        ),
        stop_button_comp: gr.update(interactive=True),
        primary_case_comp: gr.update(interactive=False),
        reference_type_comp: gr.update(interactive=False),
        comparison_scope_comp: gr.update(interactive=False),
        analysis_depth_comp: gr.update(interactive=False),
        progress_comp: gr.update(value=10, visible=True),
        status_comp: gr.update(value="🔍 Initializing cross-reference analysis..."),
        results_comp: gr.update(
            value="**Analysis Starting...**\n\nInitializing Cross Reference Agent and preparing analysis parameters..."
        ),
    }

    try:
        # Initialize cross reference agent
        agent = CrossReferenceAgent()
        logger.info("Cross Reference Agent initialized")

        yield {
            progress_comp: gr.update(value=20),
            status_comp: gr.update(
                value="🤖 Agent initialized, starting cross-reference analysis..."
            ),
        }

        # Create and execute task
        task = AgentTask(
            task_type=reference_type,
            parameters={
                "primary_case": primary_case,
                "comparison_scope": comparison_scope,
                "analysis_depth": analysis_depth,
                "include_relationships": True,
                "include_correlations": True,
            },
            priority=TaskPriority.HIGH,
        )

        # Store task for stop functionality
        webui_manager.cr_current_task = asyncio.create_task(agent.execute_task(task))

        yield {
            progress_comp: gr.update(value=30),
            status_comp: gr.update(value="🔍 Executing cross-reference analysis..."),
        }

        # Monitor progress
        progress_value = 40
        while not webui_manager.cr_current_task.done():
            # Simulate progress updates
            progress_value = min(progress_value + 10, 90)
            yield {
                progress_comp: gr.update(value=progress_value),
                status_comp: gr.update(
                    value=f"📊 Analyzing relationships... {progress_value}%"
                ),
            }
            await asyncio.sleep(1.0)

        # Get results
        result = await webui_manager.cr_current_task

        # Format results
        if result.get("success"):
            analysis_data = result.get("analysis", {})
            relationships = analysis_data.get("relationships", [])
            correlations = analysis_data.get("correlations", [])
            similar_cases = analysis_data.get("similar_cases", [])

            results_text = f"""# 🔗 Cross-Reference Analysis Results

## ✅ Analysis Summary
- **Primary Case**: "{primary_case}"
- **Analysis Type**: {reference_type.replace("_", " ").title()}
- **Analysis Depth**: {analysis_depth.title()}
- **Scope**: {", ".join(comparison_scope)}

## 📊 Key Findings

### 🔗 Relationships Found: {len(relationships)}
"""

            for i, rel in enumerate(relationships[:10], 1):  # Show first 10
                rel_type = rel.get("type", "Unknown")
                target = rel.get("target", "Unknown")
                strength = rel.get("strength", 0)
                description = rel.get("description", "No description available")

                results_text += f"""
**{i}. {rel_type.title()} Relationship**
- **Target**: {target}
- **Strength**: {strength:.2f}/1.0
- **Description**: {description}
"""

            results_text += f"""

### 🎯 Similar Cases Found: {len(similar_cases)}
"""

            for i, case in enumerate(similar_cases[:5], 1):  # Show first 5
                case_id = case.get("case_id", f"Case {i}")
                similarity = case.get("similarity_score", 0)
                key_similarities = case.get("key_similarities", [])

                results_text += f"""
**{i}. {case_id}**
- **Similarity Score**: {similarity:.2f}/1.0
- **Key Similarities**: {", ".join(key_similarities[:3])}
"""

            results_text += f"""

### 🔍 Correlations Identified: {len(correlations)}
"""

            for i, corr in enumerate(correlations[:5], 1):  # Show first 5
                corr_type = corr.get("type", "Unknown")
                description = corr.get("description", "No description")
                confidence = corr.get("confidence", 0)

                results_text += f"""
**{i}. {corr_type.title()}**
- **Confidence**: {confidence:.2f}/1.0
- **Description**: {description}
"""

            results_text += """

## 🚀 Recommended Actions
1. **Review Similar Cases**: Examine the most similar cases for precedent analysis
2. **Investigate Relationships**: Follow up on high-strength relationships
3. **Export Analysis**: Save results for legal research preparation
4. **Expand Search**: Use findings to broaden research scope

## 📈 Analysis Insights
- Strong relationships suggest important connections to investigate
- High similarity scores indicate relevant precedents
- Correlations may reveal hidden patterns in case data
"""

        else:
            # Error handling
            error_msg = result.get("error", "Unknown error occurred")
            results_text = f"""# ❌ Analysis Failed

**Error**: {error_msg}

## 💡 Suggestions
- Verify the primary case identifier exists in the database
- Check that comparison scope includes valid data sources
- Try a simpler analysis depth setting
- Ensure the case has sufficient data for analysis
"""

        yield {
            progress_comp: gr.update(value=100),
            status_comp: gr.update(value="✅ Cross-reference analysis completed!"),
            results_comp: gr.update(value=results_text),
        }

    except Exception as e:
        logger.error(f"Error during cross-reference analysis: {e}", exc_info=True)
        yield {
            status_comp: gr.update(value=f"❌ Analysis failed: {str(e)[:100]}..."),
            results_comp: gr.update(
                value=f"# ❌ Error\n\n**Error Details:**\n```\n{e}\n```"
            ),
            progress_comp: gr.update(value=0),
        }

    finally:
        # Reset UI
        webui_manager.cr_current_task = None
        yield {
            start_button_comp: gr.update(value="🔗 Start Analysis", interactive=True),
            stop_button_comp: gr.update(interactive=False),
            primary_case_comp: gr.update(interactive=True),
            reference_type_comp: gr.update(interactive=True),
            comparison_scope_comp: gr.update(interactive=True),
            analysis_depth_comp: gr.update(interactive=True),
            progress_comp: gr.update(visible=False),
        }


async def stop_cross_reference_operation(
    webui_manager: WebuiManager,
) -> Dict[Component, Any]:
    """Stop the current cross-reference operation."""
    logger.info("Stop button clicked for Cross Reference Agent.")

    task = webui_manager.cr_current_task
    if task and not task.done():
        task.cancel()
        try:
            await asyncio.wait_for(task, timeout=2.0)
        except (asyncio.CancelledError, asyncio.TimeoutError):
            pass

    webui_manager.cr_current_task = None

    return {
        webui_manager.get_component_by_id(
            "cross_reference_agent.start_button"
        ): gr.update(value="🔗 Start Analysis", interactive=True),
        webui_manager.get_component_by_id(
            "cross_reference_agent.stop_button"
        ): gr.update(interactive=False),
        webui_manager.get_component_by_id("cross_reference_agent.status"): gr.update(
            value="⏹️ Analysis stopped by user"
        ),
    }


def create_cross_reference_agent_tab(webui_manager: WebuiManager):
    """Create the Cross Reference Agent tab for relationship analysis."""

    input_components = list(webui_manager.get_components())
    tab_components = {}

    with gr.Column():
        # Header
        gr.Markdown(
            """
        # 🔗 Cross Reference Agent
        *Intelligent cross-referencing and relationship analysis across legal documents and cases*
        """
        )

        with gr.Group():
            gr.Markdown("## 🎯 Analysis Configuration")

            reference_type = gr.Radio(
                choices=[
                    ("Case Analysis", "case_analysis"),
                    ("Document Cross-Reference", "document_cross_reference"),
                    ("Legal Precedent Mapping", "precedent_mapping"),
                    ("Timeline Correlation", "timeline_correlation"),
                    ("Entity Relationship Analysis", "entity_analysis"),
                ],
                value="case_analysis",
                label="🔍 Analysis Type",
                info="Choose the type of cross-reference analysis to perform",
                interactive=True,
            )

            primary_case = gr.Textbox(
                label="📝 Primary Case/Document",
                placeholder="Enter case ID, document reference, or search terms...",
                lines=2,
                interactive=True,
                info="The primary case or document to analyze and find relationships for",
            )

        with gr.Group():
            gr.Markdown("## 🎛️ Analysis Parameters")

            with gr.Row():
                comparison_scope = gr.CheckboxGroup(
                    choices=[
                        "similar_cases",
                        "related_documents",
                        "legal_precedents",
                        "medical_reports",
                        "employment_records",
                        "timeline_events",
                    ],
                    value=["similar_cases", "related_documents"],
                    label="📂 Comparison Scope",
                    info="Select what types of data to cross-reference against",
                    interactive=True,
                )

                analysis_depth = gr.Radio(
                    choices=[
                        ("Quick Scan", "quick"),
                        ("Standard Analysis", "standard"),
                        ("Deep Analysis", "deep"),
                        ("Comprehensive Review", "comprehensive"),
                    ],
                    value="standard",
                    label="🔬 Analysis Depth",
                    info="How thorough should the analysis be?",
                    interactive=True,
                )

            with gr.Accordion("💡 Analysis Examples & Tips", open=False):
                gr.Markdown(
                    """
                **Case Analysis Examples:**
                - Case ID: "WCB-2024-001234"
                - Claim number: "CL-789456"
                - Decision reference: "WCAT-2023-05678"

                **Document Cross-Reference Examples:**
                - Medical report filename or ID
                - Employment record reference
                - Letter or correspondence ID

                **Analysis Scope Guide:**
                - **Similar Cases**: Find cases with similar facts, injuries, or outcomes
                - **Related Documents**: Identify documents that reference this case
                - **Legal Precedents**: Find relevant legal precedents and citations
                - **Medical Reports**: Cross-reference medical evidence and assessments
                - **Employment Records**: Find related employment and workplace information
                - **Timeline Events**: Identify chronologically related events and decisions

                **Analysis Depth Guide:**
                - **Quick Scan**: Fast relationship identification (1-2 minutes)
                - **Standard Analysis**: Balanced speed and thoroughness (3-5 minutes)
                - **Deep Analysis**: Comprehensive relationship mapping (5-10 minutes)
                - **Comprehensive Review**: Exhaustive analysis with detailed correlations (10+ minutes)
                """
                )

        # Control buttons
        with gr.Row():
            stop_button = gr.Button(
                "⏹️ Stop Analysis",
                variant="stop",
                scale=2,
                interactive=False,
                size="lg",
            )
            start_button = gr.Button(
                "🔗 Start Analysis", variant="primary", scale=3, size="lg"
            )

        # Progress and results section
        with gr.Group():
            gr.Markdown("## 📊 Analysis Progress & Results")

            progress = gr.Slider(
                label="🔄 Analysis Progress",
                minimum=0,
                maximum=100,
                value=0,
                interactive=False,
                visible=False,
                info="Current analysis progress",
            )

            status = gr.Textbox(
                label="📈 Current Status",
                value="🎯 Ready to start cross-reference analysis...",
                lines=2,
                interactive=False,
                container=True,
            )

            results = gr.Markdown(
                label="📋 Analysis Results",
                value="""# 🔗 Cross Reference Agent

**Welcome to the Cross Reference Analysis System!**

This tool provides comprehensive relationship analysis and cross-referencing capabilities:

## 🔍 Available Analysis Types:

### **1. Case Analysis**
- Find relationships between cases, decisions, and outcomes
- Identify similar fact patterns and legal issues
- Map connections between related claims and appeals

### **2. Document Cross-Reference**
- Cross-reference documents across case files
- Find documents that reference each other
- Identify document chains and evidence trails

### **3. Legal Precedent Mapping**
- Map relationships between legal precedents and current cases
- Find applicable case law and citations
- Identify precedent hierarchies and authority chains

### **4. Timeline Correlation**
- Analyze temporal relationships between events
- Find chronologically related decisions and documents
- Identify patterns in case progression timelines

### **5. Entity Relationship Analysis**
- Map relationships between people, organizations, and entities
- Find connections through employers, medical providers, legal representatives
- Analyze network patterns in case participants

## 🎯 Analysis Scope Options:

- **Similar Cases**: Cases with comparable facts, injuries, or legal issues
- **Related Documents**: Documents that reference or relate to your primary case
- **Legal Precedents**: Relevant case law, citations, and legal authorities
- **Medical Reports**: Medical evidence and assessments from similar cases
- **Employment Records**: Related employment history and workplace information
- **Timeline Events**: Chronologically connected events and decisions

## 🚀 Getting Started:

1. **Choose analysis type** based on what relationships you want to explore
2. **Enter primary case/document** - the starting point for your analysis
3. **Select comparison scope** - what types of data to cross-reference
4. **Set analysis depth** - how thorough you want the analysis to be
5. **Start analysis** and review the relationship map

*Configure your analysis parameters above and click Start Analysis!*
""",
                container=True,
                height=500,
            )

    # Store components
    tab_components.update(
        {
            "reference_type": reference_type,
            "primary_case": primary_case,
            "comparison_scope": comparison_scope,
            "analysis_depth": analysis_depth,
            "start_button": start_button,
            "stop_button": stop_button,
            "progress": progress,
            "status": status,
            "results": results,
        }
    )

    webui_manager.add_components("cross_reference_agent", tab_components)
    webui_manager.init_cross_reference_agent()

    # Event handlers
    async def start_wrapper(
        *comps: Any,
    ) -> AsyncGenerator[Dict[Component, Any], None]:
        components_dict = dict(zip(input_components, comps))
        async for update in run_cross_reference_operation(
            webui_manager, components_dict
        ):
            yield update

    async def stop_wrapper() -> AsyncGenerator[Dict[Component, Any], None]:
        update_dict = await stop_cross_reference_operation(webui_manager)
        yield update_dict

    # Connect handlers
    start_button.click(
        fn=start_wrapper,
        inputs=input_components,
        outputs=list(tab_components.values()),
    )

    stop_button.click(
        fn=stop_wrapper, inputs=None, outputs=list(tab_components.values())
    )

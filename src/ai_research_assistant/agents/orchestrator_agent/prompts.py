# src/ai_research_assistant/agents/chief_legal_orchestrator/prompts.py

# Example prompts for the ChiefLegalOrchestrator's internal Pydantic AI agent,
# especially if it needs to make decisions within graph nodes.

DECIDE_NEXT_PHASE_PROMPT = """
Given the current workflow state and the user's original query, determine the next logical phase.
Workflow State:
{workflow_state_json}

User Query: {user_query}

Available Phases: DocumentIntake, LegalResearch, DataQuerySynthesis, ReportFinalization, ErrorHandling.
If an error is present in the state, the next phase should be ErrorHandling.
If document intake is not complete, choose DocumentIntake.
If research is not complete, choose LegalResearch.
If query/synthesis is not complete, choose DataQuerySynthesis.
If all main phases are complete, choose ReportFinalization.

Respond with only the name of the next phase (e.g., "LegalResearch").
"""

SYNTHESIZE_FINAL_REPORT_PROMPT = """
You are the ChiefLegalOrchestrator. You have received summaries from various coordinator agents.
Your task is to synthesize a final comprehensive report for the user based on these inputs.

User Query: {user_query}

Document Processing Summary:
{doc_processing_summary_json}

Legal Research Findings Summary:
{research_findings_summary_json}

Synthesized Data & Query Report (if available):
{data_query_report_json}

Combine these inputs into a coherent, well-structured final report.
The report should directly address the user's original query.
Start with an executive summary, followed by detailed sections for document intake, research findings, and data analysis, then conclude with key insights and recommendations.
"""

# Prompts for specific graph nodes could also live here.
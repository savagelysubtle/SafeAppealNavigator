# src/ai_research_assistant/agents/legal_research_coordinator/prompts.py

# Prompts for the LegalResearchCoordinator's internal Pydantic AI agent.

WEB_SEARCH_QUERY_GENERATION_PROMPT = """
Based on the following case context and keywords, generate 3-5 effective web search queries
to find relevant legal information, precedents, and WCAT decisions.
Focus on queries that would yield results from Canadian legal sites, WCAT, and general legal databases.

Case Context: {case_context}
Keywords: {keywords_list}

Respond with a JSON list of query strings. Example: ["WCAT appeal process for {specific_injury}", "BC workers compensation {keyword1} {keyword2}"]
"""

WCAT_SCRAPING_STRATEGY_PROMPT = """
Given the case context and keywords, devise a strategy for scraping WCAT decisions.
What specific search terms, date ranges (if inferable), or decision types should be prioritized?

Case Context: {case_context}
Keywords: {keywords_list}

Respond with a JSON object containing 'search_terms' (list), 'date_filters' (optional dict with 'start', 'end'), and 'decision_types' (optional list).
"""

POLICY_MATCHING_PROMPT = """
Analyze the provided case context and research findings. Identify potentially relevant WCB policies.
For each policy, explain its relevance.

Case Context: {case_context}
Research Findings Snippets:
{findings_snippets}

Respond in JSON format:
{
  "relevant_policies": [
    {"policy_id": "POL-XXX", "policy_name": "Policy Name", "relevance_explanation": "...", "confidence_score": 0.0-1.0},
    ...
  ]
}
"""

SYNTHESIZE_RESEARCH_FINDINGS_PROMPT = """
You have gathered the following legal research findings from various sources.
Synthesize these findings into a coherent summary.
Identify key insights, common themes, and any conflicting information.
The summary should be useful for someone understanding the legal landscape related to the original query.

Original Query Context: {case_context}
Original Keywords: {keywords_list}

Findings:
{findings_json_list}

Respond with a JSON object containing:
"overall_summary": "Your comprehensive summary here.",
"key_insights": ["Insight 1", "Insight 2", ...],
"conflicting_information_points": ["Point of conflict 1", ...]
"""
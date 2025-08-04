# src/ai_research_assistant/agents/document_processing_coordinator/prompts.py

# Prompts for the DocumentAgent's internal Pydantic AI agent.

EXTRACT_DOCUMENT_STRUCTURE_PROMPT = """
Analyze the following document and extract its structure and key components.
Focus on identifying the document's organization, main sections, and overall format.

Document Text:
{document_text_snippet}

Respond in JSON format with the following structure:
{{
  "document_type": "type of document (report, memo, brief, etc.)",
  "structure": {{
    "sections": ["list", "of", "main", "sections"],
    "has_table_of_contents": true/false,
    "has_executive_summary": true/false,
    "has_citations": true/false,
    "has_appendices": true/false
  }},
  "metadata": {{
    "title": "document title if found",
    "author": "author if found",
    "date": "date if found",
    "page_count": "estimated page count"
  }},
  "summary": "brief 2-3 sentence summary of the document"
}}
"""

CREATE_DOCUMENT_FROM_OUTLINE_PROMPT = """
Create a professional document based on the following outline and requirements.

Document Type: {document_type}
Title: {title}
Outline:
{outline}

Additional Requirements:
{requirements}

Generate a complete, well-formatted document following the provided outline.
Include appropriate headings, transitions between sections, and professional language.
Ensure the document flows logically and addresses all points in the outline.
"""

MERGE_DOCUMENTS_PROMPT = """
Merge the following document contents into a single, cohesive document.
Maintain logical flow and eliminate redundancy while preserving all unique information.

Documents to merge:
{documents_to_merge}

Target document type: {target_type}
Special instructions: {merge_instructions}

Create a unified document that combines all relevant information from the source documents.
Ensure smooth transitions between merged sections and maintain consistent formatting and tone.
"""

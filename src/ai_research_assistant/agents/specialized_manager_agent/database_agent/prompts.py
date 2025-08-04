# src/ai_research_assistant/agents/data_query_coordinator/prompts.py

# Prompts for the DatabaseAgent's internal Pydantic AI agent.

ORGANIZE_DOCUMENTS_INTO_COLLECTIONS_PROMPT = """
Based on the provided document metadata and content summaries, create a plan to organize
documents into appropriate Chroma collections for optimal retrieval and management.

Current documents:
{documents_summary}

Consider creating collections based on:
- Document type (legal briefs, medical records, contracts, etc.)
- Date ranges for temporal organization
- Subject matter or case association
- Access patterns and query requirements

Respond with a JSON object containing:
{{
  "collections": [
    {{
      "name": "collection_name",
      "description": "what this collection contains",
      "document_criteria": "criteria for documents in this collection",
      "embedding_function": "default",
      "estimated_document_count": 0
    }}
  ],
  "sorting_rules": [
    {{
      "source_collection": "unsorted",
      "target_collection": "collection_name",
      "filter_metadata": {{"key": "value"}}
    }}
  ]
}}
"""

OPTIMIZE_COLLECTION_PROMPT = """
Analyze the current state of the Chroma collection and suggest optimization parameters.

Collection: {collection_name}
Current document count: {document_count}
Current metadata schema: {metadata_schema}
Query patterns: {query_patterns}

Suggest optimal HNSW parameters and any reorganization needed for better performance.
Consider:
- Search speed vs accuracy tradeoffs
- Memory usage
- Expected query load
- Document similarity patterns

Respond with optimization recommendations including specific HNSW parameter values.
"""

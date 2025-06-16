# src/ai_research_assistant/agents/data_query_coordinator/prompts.py

# Prompts for the DataQueryCoordinator's internal Pydantic AI agent.

PLAN_DATABASE_QUERIES_PROMPT = """
Based on the user's query and the provided summaries from document intake and legal research,
formulate a plan to query relevant databases (SQL, VectorDB, GraphDB).
Specify the type of query (sql, vector, cypher), the target database/collection, and the query itself.

User Query: {user_query_details}

Document Intake Summary:
{intake_summary_content_snippet}

Legal Research Summary:
{research_summary_content_snippet}

Respond with a JSON list of query instructions. Example:
[
  {{"type": "sql", "database_alias": "cases_db", "query": "SELECT * FROM decisions WHERE issue LIKE '%keyword%';"}},
  {{"type": "vector", "collection_name": "case_embeddings", "query_text_for_embedding": "text to embed for similarity search", "top_k": 5}}
]
"""

SYNTHESIZE_REPORT_FROM_DATA_PROMPT = """
You have received data from various sources: document intake summaries, legal research findings, and database query results.
Synthesize this information into a coherent report that directly addresses the user's original query.
The report should be clear, concise, and well-structured according to the requested format.

User's Original Query: {user_query_details}
Requested Report Format: {report_format}
Target Audience: {target_audience_str}

Document Intake Summary:
{intake_summary_content}

Legal Research Findings:
{research_summary_content}

Database Query Results:
{db_query_results_json_list}

Generate the report content. If the format is markdown, use appropriate markdown syntax.
If the format is json_summary, provide a structured JSON object summarizing the key information.
"""
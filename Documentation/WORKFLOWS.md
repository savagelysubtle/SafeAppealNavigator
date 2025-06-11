# Key Workflows (Refactor v2)

## 1. Full Research Pipeline

1.  **CEO** receives user goal → passes to **Orchestrator**.
2.  **Orchestrator** parallel-fires:
    *   `document_agent.process()` → returns `ProcessingSummary`.
    *   `browser_agent.search()` → returns `ResearchHits`.
3.  Stores embeddings via `database_agent.upsert()`.
4.  (Phase-2) calls `legal_manager_agent.draft_memo()` for structured PDF/Markdown output.
5.  CEO returns answer & attaches artefact links.

## 2. Incremental Chat Clarification

*   Worker raises `NeedUserInputError` → Orchestrator surfaces to CEO → CEO asks user → result routed back down to the waiting worker → graph resumes.

## 3. Hot-swap plugin

*   Drop `analytics_agent/agent.py` into `specialized_manager_agent/`.
*   Declare `CAPABILITY="analytics.stats"` at module level.
*   Registry auto-imports and the Orchestrator can now route `analytics` tasks without redeploying CEO.
# Dev-Kickoff Plan (Refactor v2)

## Phase 0 – Setup

*   Python 3.11, Poetry, Docker.
*   Initialise new tree (`FILE_TREE.md`).

## Phase 1 – Core models + agent cards

*   `MessageEnvelope`, `CAPABILITY` enum.
*   JSON cards for CEO, Orchestrator, document/browser/database agents.

## Phase 2 – Worker MVP

1.  `document_agent` (Unstructured + Tesseract).
2.  `browser_agent` (Playwright headless + BeautifulSoup).
3.  `database_agent` (psycopg + pgvector).

## Phase 3 – Orchestrator

*   Build TaskGraph; add retry & timeout guards.
*   FastA2A wrapper with `/healthz` probe.

## Phase 4 – CEO

*   Tiny prompt: “You are the managing partner…”.
*   Link to UI via AG-UI backend.

## Phase 5 – End-to-end test

*   docker-compose up → ingest sample WCAT bundle → produce precedent memo.

## Phase 6 – Phase-2 agents

*   `legal_manager_agent` (draft & verify).
*   red_team & analytics plugins.

CI: `pytest -q && ruff . && ai-bandit`
CD: GH Actions → Docker Hub → fly.io (or k8s).

Happy coding!
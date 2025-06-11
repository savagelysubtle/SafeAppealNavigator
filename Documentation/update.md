Below is an **all-in-one refactor pack**: a fresh file-tree sketch, a ranked agent rollout plan (MVP → future), and **fully rewritten docs**—each in its own copy-paste-ready code block. The wording reflects the “single manager layer + one-level worker folders” convention we agreed on, while preserving the spirit of your original documentation.

* * *

📂 New top-level file tree (high-level view)
--------------------------------------------

`airesearchagent/
├── .env*                     # runtime secrets
├── README.md                 # ← rewritten below
├── FILE_TREE.md              # ← rewritten below
├── pyproject.toml
├── docker-compose.yml
│
├── agent_cards/              # JSON capabilities
│   ├── ceo_agent.json
│   ├── orchestrator_agent.json
│   ├── specialized_manager_agent.json
│   └── (autogen at build)
│
├── docs/
│   ├── ARCHITECTURE.md       # ← rewritten below
│   ├── WORKFLOWS.md          # ← rewritten below
│   ├── MEMORY_MODEL.md       # ← rewritten below
│   └── DEV_KICKOFF.md        # ← rewritten below
│
├── src/
│   └── ai_research_assistant/
│       ├── __init__.py
│       │
│       ├── agents/
│       │   ├── ceo_agent/
│       │   │   └── agent.py
│       │   ├── orchestrator_agent/
│       │   │   ├── agent.py
│       │   │   └── task_graph.py
│       │   └── specialized_manager_agent/
│       │       ├── __init__.py        # exports registry helpers
│       │       ├── browser_agent/
│       │       │   └── agent.py
│       │       ├── document_agent/
│       │       │   └── agent.py
│       │       ├── database_agent/
│       │       │   └── agent.py
│       │       └── legal_manager_agent/
│       │           └── agent.py
│       │
│       ├── a2a_services/             # FastA2A wrappers
│       │   └── startup.py
│       ├── mcp_integration/          # service-discovery + shared tools
│       ├── ag_ui_backend/
│       └── utils/
│
└── tests/`

* * *

🎯 Agent rollout & priority
---------------------------

Rank

Agent (folder)

MVP?

Rationale

1

`document_agent`

✅

Intake/OCR/tag/embeddings = foundation for every workflow.

2

`browser_agent`

✅

External search & scraping unlock precedent discovery quickly.

3

`database_agent`

✅

Persists vectors + metadata; unblocks retrieval & RAG.

4

`legal_manager_agent`

↗︎ Phase-2

Drafts memos, cross-checks citations once the above data flows exist.

5

(future) analytics\_agent

⏩

Stats, judge sentiment, etc.—nice-to-have after core works.

6

(future) red\_team\_agent

⏩

Hallucination/ethics QA once system is stable.

* * *

📄 Rewritten docs
-----------------

### README.md

`# AI-Research-Assistant 🧑‍⚖️🤖 **AI-Research-Assistant** is a modular, A2A-compliant multi-agent platform that automates legal-research workflows—from raw document dumps to polished precedent memos.
Built with **PydanticAI + TaskGraph**, orchestrated via **FastA2A**, and discoverable through a lightweight **MCP registry**, it keeps the **CEO agent** as the only human touch-point while specialist workers grind through intake, search, and drafting behind the scenes. ## Quick-start (dev) ```bash
git clone https://github.com/your-org/AI-Research-Assistant.git
cd AI-Research-Assistant
poetry install
cp .env.example .env  # add keys
docker-compose up -d  # spin up Chroma, Neo4j, etc.
uvicorn ai_research_assistant.a2a_services.startup:app --reload`

MVP scope
---------

Component

Purpose

**ceo\_agent**

Single user interface, summarises results.

**orchestrator\_agent**

TaskGraph supervisor & FastA2A endpoint.

**document\_agent**

OCR → tag → chunk → embed.

**browser\_agent**

Web + docket search.

**database\_agent**

pgvector/Chroma CRUD.

Roadmap
-------

*   Phase-2: `legal_manager_agent` (draft & verify)

*   Phase-3: Red-team & analytics plugins

*   Phase-4: Marketplace for external capability agents


License: MIT

yaml

 `--- ### FILE_TREE.md ```markdown # Project File Tree (2025-06-refactor) ```text airesearchagent/ ├── agent_cards/ # A2A capability descriptors ├── docs/ # architecture, memory, workflows ├── src/ │ └── ai_research_assistant/ │ ├── agents/ │ │ ├── ceo_agent/ │ │ ├── orchestrator_agent/ │ │ └── specialized_manager_agent/ │ │ ├── browser_agent/ │ │ ├── document_agent/ │ │ ├── database_agent/ │ │ └── legal_manager_agent/ │ ├── a2a_services/ │ ├── mcp_integration/ │ ├── ag_ui_backend/ │ └── utils/ └── tests/`

_Only one “manager” folder (`specialized_manager_agent`) sits between the orchestrator and worker agents—keeping FastA2A imports short while grouping domain workers logically._

shell

 ``---
 ### ARCHITECTURE.md ```markdown # System Architecture (Refactor v2) ![architecture_diagram](assets/architecture_overview_refactor_v2.mermaid)
 ## Layers 1. **UI** – Gradio ↔ AG-UI backend (FastAPI).
2. **CEO Agent** – Vorder-facing chatbot, no heavy lifting.
3. **Orchestrator Agent** – Runs TaskGraph, publishes A2A `/ask|/tell|/stream`.
4. **Specialized Manager Layer**
   * Exports a **registry helper** that maps `CAPABILITY` tags to import paths.
   * Discovers worker agents at start-up and attaches them to the Orchestrator graph.
5. **Worker Agents** (`*_agent`)
   * `document_agent` – intake pipeline.
   * `browser_agent` – web/docket scraping.
   * `database_agent` – pgvector queries + schema ops.
   * `legal_manager_agent` – memo composer & citation verifier (phase-2).
6. **Shared Services (MCP)**
   * File store (Rust), ChromaDB, Postgres, Neo4j, OpenTelemetry.
 ## A2A Flow ```mermaid
sequenceDiagram User->>CEO: Ask legal question CEO->>Orchestrator: /ask (goal, context) Orchestrator->>document_agent: /ask (ingest docs) document_agent-->>Orchestrator: processed docs Orchestrator->>browser_agent: /ask (search precedents) browser_agent-->>Orchestrator: findings Orchestrator->>database_agent: /ask (store & fetch embeddings) database_agent-->>Orchestrator: vector IDs Orchestrator-->>CEO: Draft answer CEO-->>User: Final brief``

_Only the CEO talks to the user; all back-channel chatter is A2A._

yaml

 ``--- ### WORKFLOWS.md ```markdown # Key Workflows (Refactor v2) ## 1. Full Research Pipeline 1. **CEO** receives user goal → passes to **Orchestrator**. 2. **Orchestrator** parallel-fires: * `document_agent.process()` → returns `ProcessingSummary`. * `browser_agent.search()` → returns `ResearchHits`. 3. Stores embeddings via `database_agent.upsert()`. 4. (Phase-2) calls `legal_manager_agent.draft_memo()` for structured PDF/Markdown output. 5. CEO returns answer & attaches artefact links. ## 2. Incremental Chat Clarification * Worker raises `NeedUserInputError` → Orchestrator surfaces to CEO → CEO asks user → result routed back down to the waiting worker → graph resumes. ## 3. Hot-swap plugin * Drop `analytics_agent/agent.py` into `specialized_manager_agent/`. * Declare `CAPABILITY="analytics.stats"` at module level. * Registry auto-imports and the Orchestrator can now route `analytics` tasks without redeploying CEO.``

* * *

### MEMORY\_MODEL.md

``# Memory & State Model (Refactor v2) | Layer            | Tech                         | Owner                | TTL       |
|------------------|------------------------------|----------------------|-----------|
| Conversation     | AG-UI SDK buff + Postgres    | AG-UI backend        | hours     |
| TaskGraph state  | Pydantic-Graph + Neo4j       | Orchestrator         | days      |
| Artefact store   | Rust FS via MCP             | All agents           | durable   |
| Vectors          | pgvector (Postgres)          | document/database    | durable   |
| SQL              | Postgres                    | database_agent       | durable   |
| Scratch          | `self.messages` in Pydantic  | each worker          | per task  |
| Audit            | OpenTelemetry + SQL log      | utils.logging        | forever   | **Hand-offs** * Orchestrator embeds summary of chat context into every A2A `/ask`.
* Workers write large outputs to FS → return MCP path instead of blob.
* CEO discards raw vectors; only keeps citation list + artefact links.``

* * *

### DEV\_KICKOFF.md

``# Dev-Kickoff Plan (Refactor v2) ## Phase 0 – Setup * Python 3.11, Poetry, Docker. * Initialise new tree (`FILE_TREE.md`). ## Phase 1 – Core models + agent cards * `MessageEnvelope`, `CAPABILITY` enum. * JSON cards for CEO, Orchestrator, document/browser/database agents. ## Phase 2 – Worker MVP 1. `document_agent` (Unstructured + Tesseract). 2. `browser_agent` (Playwright headless + BeautifulSoup). 3. `database_agent` (psycopg + pgvector). ## Phase 3 – Orchestrator * Build TaskGraph; add retry & timeout guards. * FastA2A wrapper with `/healthz` probe. ## Phase 4 – CEO * Tiny prompt: “You are the managing partner…”. * Link to UI via AG-UI backend. ## Phase 5 – End-to-end test * docker-compose up → ingest sample WCAT bundle → produce precedent memo. ## Phase 6 – Phase-2 agents * `legal_manager_agent` (draft & verify). * red_team & analytics plugins.

CI: `pytest -q && ruff . && ai-bandit`
CD: GH Actions → Docker Hub → fly.io (or k8s).

Happy coding!``

* * *

### ⏹️ Done

These updated documents slot straight into your repo; each reflects the **single-manager, one-level worker** layout while marking MVP boundaries and future growth paths. Copy-paste the blocks over your existing files and you’re ready for the next sprint.

![Export to Google Doc](chrome-extension://iapioliapockkkikccgbiaalfhoieano/assets/create.svg)![Copy with formatting](chrome-extension://iapioliapockkkikccgbiaalfhoieano/assets/copy.svg)![Select for Multi-select](chrome-extension://iapioliapockkkikccgbiaalfhoieano/assets/multi-select.svg)
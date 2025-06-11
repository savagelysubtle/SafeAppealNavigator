# Project File Tree (2025-06-refactor)

```text
airesearchagent/
├── agent_cards/              # A2A capability descriptors
├── docs/                     # architecture, memory, workflows
├── src/
│   └── ai_research_assistant/
│       ├── agents/
│       │   ├── ceo_agent/
│       │   ├── orchestrator_agent/
│       │   └── specialized_manager_agent/
│       │       ├── browser_agent/
│       │       ├── document_agent/
│       │       ├── database_agent/
│       │       └── legal_manager_agent/
│       ├── a2a_services/
│       ├── mcp_integration/
│       ├── ag_ui_backend/
│       └── utils/
└── tests/
```

_Only one “manager” folder (`specialized_manager_agent`) sits between the orchestrator and worker agents—keeping FastA2A imports short while grouping domain workers logically._
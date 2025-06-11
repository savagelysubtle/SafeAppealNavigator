# Memory & State Model (Refactor v2)

| Layer            | Tech                         | Owner                | TTL       |
|------------------|------------------------------|----------------------|-----------|
| Conversation     | AG-UI SDK buff + Postgres    | AG-UI backend        | hours     |
| TaskGraph state  | Pydantic-Graph + Neo4j       | Orchestrator         | days      |
| Artefact store   | Rust FS via MCP             | All agents           | durable   |
| Vectors          | pgvector (Postgres)          | document/database    | durable   |
| SQL              | Postgres                    | database_agent       | durable   |
| Scratch          | `self.messages` in Pydantic  | each worker          | per task  |
| Audit            | OpenTelemetry + SQL log      | utils.logging        | forever   |

**Hand-offs**

*   Orchestrator embeds summary of chat context into every A2A `/ask`.
*   Workers write large outputs to FS → return MCP path instead of blob.
*   CEO discards raw vectors; only keeps citation list + artefact links.

# config/global_settings.py

import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load .env file
load_dotenv()

class GlobalSettings(BaseSettings):
    # LLM API Keys
    OPENAI_API_KEY: str = "sk-..." # Default or load from env
    ANTHROPIC_API_KEY: str | None = None
    GOOGLE_API_KEY: str | None = None
    # Add other LLM keys as needed

    # Service URLs & Ports
    MCP_SERVER_HOST: str = "0.0.0.0"
    MCP_SERVER_PORT: int = 10000
    MCP_SERVER_URL: str = f"http://{MCP_SERVER_HOST}:{MCP_SERVER_PORT}" # Constructed

    RUST_FILESYSTEM_MCP_COMMAND: str = "path/to/your/rust-mcp-filesystem-server"
    RUST_FILESYSTEM_MCP_ARGS: str = "F:/WCBCLAIM F:/AgentWCB" # Example, adjust as needed
    # Note: It's generally better to configure the Rust MCP server's URL if it runs as a separate service
    RUST_FILESYSTEM_MCP_URL: str | None = "http://localhost:10001" # Assuming it runs as a service

    CHIEF_LEGAL_ORCHESTRATOR_A2A_HOST: str = "0.0.0.0"
    CHIEF_LEGAL_ORCHESTRATOR_A2A_PORT: int = 10100
    CHIEF_LEGAL_ORCHESTRATOR_A2A_URL: str = f"http://{CHIEF_LEGAL_ORCHESTRATOR_A2A_HOST}:{CHIEF_LEGAL_ORCHESTRATOR_A2A_PORT}"

    DOCUMENT_PROCESSING_COORDINATOR_A2A_HOST: str = "0.0.0.0"
    DOCUMENT_PROCESSING_COORDINATOR_A2A_PORT: int = 10101
    DOCUMENT_PROCESSING_COORDINATOR_A2A_URL: str = f"http://{DOCUMENT_PROCESSING_COORDINATOR_A2A_HOST}:{DOCUMENT_PROCESSING_COORDINATOR_A2A_PORT}"

    LEGAL_RESEARCH_COORDINATOR_A2A_HOST: str = "0.0.0.0"
    LEGAL_RESEARCH_COORDINATOR_A2A_PORT: int = 10102
    LEGAL_RESEARCH_COORDINATOR_A2A_URL: str = f"http://{LEGAL_RESEARCH_COORDINATOR_A2A_HOST}:{LEGAL_RESEARCH_COORDINATOR_A2A_PORT}"

    DATA_QUERY_COORDINATOR_A2A_HOST: str = "0.0.0.0"
    DATA_QUERY_COORDINATOR_A2A_PORT: int = 10103
    DATA_QUERY_COORDINATOR_A2A_URL: str = f"http://{DATA_QUERY_COORDINATOR_A2A_HOST}:{DATA_QUERY_COORDINATOR_A2A_PORT}"

    AG_UI_BACKEND_HOST: str = "0.0.0.0"
    AG_UI_BACKEND_PORT: int = 10200
    AG_UI_BACKEND_URL: str = f"http://{AG_UI_BACKEND_HOST}:{AG_UI_BACKEND_PORT}"

    GRADIO_SERVER_PORT: int = 7860

    # Database Paths/URIs
    DATABASE_URL_SQLITE: str = "sqlite:///./data/sqlite/cases.db"
    CHROMA_DB_PATH: str = "./data/chroma_db"
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"

    LOG_LEVEL: str = "INFO"

    # Pydantic Settings configuration
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8', extra='ignore')

settings = GlobalSettings()

# src/ai_research_assistant/mcp_intergration/mcp_server.py
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Literal

import click
import numpy as np
import pandas as pd
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from mcp.server.fastmcp import FastMCP
from pydantic import SecretStr

from ai_research_assistant.core.env_manager import env_manager

# --- Server Setup ---
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# --- Configuration ---
try:
    PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.resolve()
except NameError:
    PROJECT_ROOT = Path(".").resolve()

AGENT_CARDS_DIR: Path = PROJECT_ROOT / "agent_cards"
EMBEDDING_PROVIDER: str = "google"
EMBEDDING_MODEL: str = "models/embedding-001"
EMBEDDING_DIMENSION: int = 768  # For embedding-001


# --- Embedding Generation ---
def get_embedding_client() -> GoogleGenerativeAIEmbeddings:
    """
    Initializes and returns the LangChain Google Embeddings client.

    This function uses the central `env_manager` to securely fetch the
    required API key.

    Returns:
        An instance of GoogleGenerativeAIEmbeddings ready for use.

    Raises:
        ValueError: If the required API key is not found in the environment.
    """
    api_key_str = env_manager.get_api_key(EMBEDDING_PROVIDER)

    if not api_key_str:
        error_msg = env_manager.create_error_message(EMBEDDING_PROVIDER)
        raise ValueError(error_msg)

    # Correctly wrap the API key in Pydantic's SecretStr
    api_key = SecretStr(api_key_str)

    return GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL, google_api_key=api_key)


def build_agent_card_embeddings(
    embedding_client: GoogleGenerativeAIEmbeddings,
) -> pd.DataFrame:
    """
    Loads agent cards from JSON files, generates embeddings using LangChain,
    and returns a structured Pandas DataFrame.

    Args:
        embedding_client: The initialized LangChain embeddings client.

    Returns:
        A DataFrame with agent card data and their corresponding embeddings.
        Returns an empty DataFrame if the agent cards directory is not found
        or no cards are loaded.
    """
    agent_cards_data: List[Dict[str, Any]] = []
    if not AGENT_CARDS_DIR.is_dir():
        logger.error(f"Agent cards directory not found: {AGENT_CARDS_DIR}")
        return pd.DataFrame()

    logger.info(f"Loading agent cards from: {AGENT_CARDS_DIR}")
    descriptions_to_embed: List[str] = []
    for file_path in AGENT_CARDS_DIR.glob("*.json"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                skills = ", ".join([s.get("name", "") for s in data.get("skills", [])])
                description = (
                    f"Agent Name: {data.get('agent_name', '')}. "
                    f"Description: {data.get('description', '')}. "
                    f"Capabilities: {data.get('capability', '')}. "
                    f"Skills: {skills}"
                )
                agent_cards_data.append(
                    {
                        "card_uri": f"resource://agent_cards/{file_path.stem}",
                        "agent_card": data,
                    }
                )
                descriptions_to_embed.append(description)
        except Exception as e:
            logger.error(f"Error processing agent card {file_path.name}: {e}")

    if not agent_cards_data:
        logger.warning("No agent cards were loaded.")
        return pd.DataFrame()

    df = pd.DataFrame(agent_cards_data)
    logger.info(f"Generating embeddings for {len(df)} agent cards using LangChain...")

    embeddings = embedding_client.embed_documents(descriptions_to_embed)
    df["card_embeddings"] = embeddings

    logger.info("Embeddings generated successfully.")
    return df


# --- Main Server Logic ---
def serve(
    host: str,
    port: int,
    transport: Literal["stdio", "sse", "streamable-http"],
) -> None:
    """
    Initializes and runs the Agent Finder MCP server.

    This server exposes a `find_agent` tool that enables semantic search
    for agent capabilities.

    Args:
        host: The hostname to bind the server to.
        port: The port number to bind the server to.
        transport: The MCP transport protocol to use.
    """
    try:
        embedding_client = get_embedding_client()
    except ValueError as e:
        logger.error(f"Fatal: Could not initialize embedding client: {e}")
        return

    logger.info("Starting Agent Finder MCP Server...")
    mcp = FastMCP("agent-finder", host=host, port=port)
    df = build_agent_card_embeddings(embedding_client)

    if df.empty:
        logger.error(
            "No agent card embeddings created. The 'find_agent' tool will be disabled."
        )

    @mcp.tool(
        name="find_agent",
        description="Finds the most relevant agent to perform a task based on a natural language query.",
    )
    def find_agent(query: str) -> Dict[str, Any]:
        """
        Finds the most relevant agent card based on semantic similarity.

        Args:
            query: The natural language query describing the task.

        Returns:
            A dictionary representing the best-matching agent card, or an
            error dictionary if no agents are available.
        """
        if df.empty:
            return {"error": "Agent embedding data is not available."}

        query_embedding = embedding_client.embed_query(query)

        # Correctly convert Series of lists to a list of lists for np.stack
        card_embeddings = np.stack(df["card_embeddings"].tolist())

        dot_products = np.dot(card_embeddings, query_embedding)
        best_match_index = np.argmax(dot_products)

        agent_name = df.iloc[best_match_index]["agent_card"]["agent_name"]
        logger.info(f"Query '{query[:50]}...' best matched with agent: {agent_name}")
        return df.iloc[best_match_index]["agent_card"]

    @mcp.resource("resource://agent_cards/list", mime_type="application/json")
    def get_agent_cards_list() -> Dict[str, List[Any]]:
        """Retrieves a list of all loaded agent card dictionaries."""
        if df.empty:
            return {"agent_cards": []}
        return {"agent_cards": df["agent_card"].to_list()}

    logger.info(
        f"Agent Finder MCP Server running at {host}:{port} with transport {transport}"
    )
    mcp.run(transport=transport)


@click.command()
@click.option("--host", default="127.0.0.1", help="Host for the MCP server.")
@click.option("--port", default=10100, help="Port for the MCP server.")
@click.option(
    "--transport",
    default="stdio",
    type=click.Choice(["stdio", "sse", "streamable-http"]),
    help="Transport protocol.",
)
def main(
    host: str,
    port: int,
    transport: Literal["stdio", "sse", "streamable-http"],
) -> None:
    """CLI entry point to run the Agent Finder MCP server."""
    serve(host, port, transport)


if __name__ == "__main__":
    main()

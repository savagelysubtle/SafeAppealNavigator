# File: src/ai_research_assistant/a2a_services/startup.py
import argparse
import json
import logging
import os
from typing import Any, Dict

import uvicorn
from dotenv import load_dotenv

# --- FIX: Direct imports to break circular dependency ---
from ai_research_assistant.agents.orchestrator_agent.agent import OrchestratorAgent
from ai_research_assistant.agents.orchestrator_agent.config import (
    OrchestratorAgentConfig,
)
from ai_research_assistant.agents.specialized_manager_agent.browser_agent.agent import (
    BrowserAgent,
    BrowserAgentConfig,
)
from ai_research_assistant.agents.specialized_manager_agent.database_agent.agent import (
    DatabaseAgent,
    DatabaseAgentConfig,
)
from ai_research_assistant.agents.specialized_manager_agent.document_agent.agent import (
    DocumentAgent,
    DocumentAgentConfig,
)
from ai_research_assistant.mcp.client import create_mcp_toolsets_from_config

from .fasta2a_wrapper import wrap_agent_with_fasta2a

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# --- FIX: Agent registry is now defined directly in the startup script ---
AGENT_REGISTRY: Dict[str, Dict[str, Any]] = {
    "OrchestratorAgent": {
        "agent_class": OrchestratorAgent,
        "config_class": OrchestratorAgentConfig,
    },
    "DocumentAgent": {
        "agent_class": DocumentAgent,
        "config_class": DocumentAgentConfig,
    },
    "BrowserAgent": {"agent_class": BrowserAgent, "config_class": BrowserAgentConfig},
    "DatabaseAgent": {
        "agent_class": DatabaseAgent,
        "config_class": DatabaseAgentConfig,
    },
}


def main():
    load_dotenv()
    parser = argparse.ArgumentParser(
        description="Startup script for AI Research Agent A2A services."
    )
    parser.add_argument(
        "--card-path",
        type=str,
        required=True,
        help="Path to the agent's JSON card file.",
    )
    parser.add_argument(
        "--host",
        type=str,
        default=os.getenv("A2A_DEFAULT_HOST", "0.0.0.0"),
        help="Host for the A2A service.",
    )
    parser.add_argument(
        "--port", type=int, required=True, help="Port for the A2A service."
    )
    args = parser.parse_args()

    try:
        with open(args.card_path, "r") as f:
            card_data = json.load(f)
            agent_name = card_data.get("agent_name")
            if not agent_name:
                raise ValueError("'agent_name' not found in agent card.")
    except Exception as e:
        logger.error(f"Error reading agent card at {args.card_path}: {e}")
        return

    if agent_name not in AGENT_REGISTRY:
        logger.error(
            f"Configuration error: Unknown agent name: {agent_name}. Available: {list(AGENT_REGISTRY.keys())}"
        )
        return

    logger.info(
        f"Starting A2A service for agent: '{agent_name}' on {args.host}:{args.port}"
    )

    try:
        agent_info = AGENT_REGISTRY[agent_name]
        AgentClass = agent_info["agent_class"]
        ConfigClass = agent_info["config_class"]

        logger.info(f"Loading MCP toolsets for agent '{agent_name}'...")
        mcp_toolsets = create_mcp_toolsets_from_config()

        agent_config = ConfigClass()
        agent_instance = AgentClass(config=agent_config, toolsets=mcp_toolsets)

        app = wrap_agent_with_fasta2a(
            agent_instance=agent_instance,
            url=f"http://{args.host}:{args.port}",
            version="1.0.0",
        )

        uvicorn.run(app, host=args.host, port=args.port, log_level="info")
    except Exception as e:
        logger.error(
            f"Failed to start A2A service for agent '{agent_name}': {e}", exc_info=True
        )


if __name__ == "__main__":
    main()

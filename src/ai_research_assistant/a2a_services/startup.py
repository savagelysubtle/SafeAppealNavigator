#!/usr/bin/env python3
"""
Startup script for A2A agents.
Usage: python startup.py --card-path <path> --port <port>
"""

import argparse
import importlib
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict

# Add the project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import uvicorn

from ai_research_assistant.a2a_services.enhanced_a2a_wrapper import (
    create_enhanced_a2a_agent,
)
from ai_research_assistant.mcp.client import create_mcp_toolsets_from_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)-8s - %(name)-20s - %(message)s",
)
logger = logging.getLogger(__name__)

# Agent registry mapping card names to agent module and class names
AGENT_REGISTRY = {
    "ceoagent": ("ai_research_assistant.agents.ceo_agent.agent", "CEOAgent"),
    "orchestratoragent": (
        "ai_research_assistant.agents.orchestrator_agent.agent",
        "OrchestratorAgent",
    ),
    "databaseagent": (
        "ai_research_assistant.agents.specialized_manager_agent.database_agent.agent",
        "DatabaseAgent",
    ),
    "documentagent": (
        "ai_research_assistant.agents.specialized_manager_agent.document_agent.agent",
        "DocumentAgent",
    ),
    "browseragent": (
        "ai_research_assistant.agents.specialized_manager_agent.browser_agent.agent",
        "BrowserAgent",
    ),
}


def load_agent_card(card_path: str) -> Dict[str, Any]:
    """Load agent card from JSON file."""
    with open(card_path, "r") as f:
        return json.load(f)


def main():
    """Main function to start an A2A agent based on the provided agent card."""
    parser = argparse.ArgumentParser(description="Start an A2A agent")
    parser.add_argument(
        "--card-path", required=True, help="Path to the agent card JSON file"
    )
    parser.add_argument(
        "--port", required=True, type=int, help="Port to run the agent on"
    )
    args = parser.parse_args()

    # Load agent card
    try:
        card = load_agent_card(args.card_path)
        logger.info(f"Loaded agent card: {card.get('agent_name', 'Unknown')}")
    except Exception as e:
        logger.error(f"Failed to load agent card from {args.card_path}: {e}")
        sys.exit(1)

    # Get agent name and look up in registry
    agent_name = card.get("agent_name", "").lower().replace(" ", "_")
    if agent_name not in AGENT_REGISTRY:
        logger.error(f"Unknown agent type: {agent_name}")
        logger.error(f"Available agents: {list(AGENT_REGISTRY.keys())}")
        sys.exit(1)

    # Dynamically import the agent class
    module_path, class_name = AGENT_REGISTRY[agent_name]
    try:
        module = importlib.import_module(module_path)
        AgentClass = getattr(module, class_name)
        logger.info(f"Successfully loaded {class_name} from {module_path}")
    except (ImportError, AttributeError) as e:
        logger.error(f"Failed to import {class_name} from {module_path}: {e}")
        sys.exit(1)

    # Create MCP toolsets
    try:
        toolsets = create_mcp_toolsets_from_config()
        logger.info(f"Created {len(toolsets)} MCP toolsets")
    except Exception as e:
        logger.error(f"Failed to create MCP toolsets: {e}")
        toolsets = []

    # Create agent instance
    try:
        agent_instance = AgentClass()
        logger.info(f"Created {class_name} instance")
    except Exception as e:
        logger.error(f"Failed to create {class_name} instance: {e}")
        sys.exit(1)

    # Create A2A agent wrapper
    try:
        app = create_enhanced_a2a_agent(
            agent=agent_instance.pydantic_agent,
            toolsets=toolsets,
            name=card.get("agent_name", "Unknown Agent"),
            url=f"http://localhost:{args.port}",
            version=card.get("version", "1.0.0"),
            description=card.get("description", "AI Research Agent"),
        )
        logger.info(f"Created A2A wrapper for {card.get('agent_name')}")
    except Exception as e:
        logger.error(f"Failed to create A2A wrapper: {e}")
        sys.exit(1)

    # Start the server
    logger.info(f"Starting {card.get('agent_name')} on port {args.port}")
    uvicorn.run(app, host="0.0.0.0", port=args.port, log_level="info")


if __name__ == "__main__":
    main()

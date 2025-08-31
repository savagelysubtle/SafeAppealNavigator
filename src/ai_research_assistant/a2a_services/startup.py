#!/usr/bin/env python3
"""
Startup script for A2A agents using unified LLM factory.
Usage: python startup.py --card-path <path> --port <port> [--model <model>]
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

from ai_research_assistant.core.unified_llm_factory import get_llm_factory
from ai_research_assistant.mcp.client import create_mcp_toolsets_from_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)-8s - %(name)-20s - %(message)s",
)
logger = logging.getLogger(__name__)

# Agent registry mapping card names to agent module and class names
# Names must match the agent_name field in the corresponding agent card JSON files
AGENT_REGISTRY = {
    "CEOAgent": ("ai_research_assistant.agents.ceo_agent.agent", "CEOAgent"),
    "OrchestratorAgent": (
        "ai_research_assistant.agents.orchestrator_agent.agent",
        "OrchestratorAgent",
    ),
    "DatabaseAgent": (
        "ai_research_assistant.agents.specialized_manager_agent.database_agent.agent",
        "DatabaseAgent",
    ),
    "DocumentAgent": (
        "ai_research_assistant.agents.specialized_manager_agent.document_agent.agent",
        "DocumentAgent",
    ),
    "BrowserAgent": (
        "ai_research_assistant.agents.specialized_manager_agent.browser_agent.agent",
        "BrowserAgent",
    ),
}


def load_agent_card(card_path: str) -> Dict[str, Any]:
    """Load agent card from JSON file."""
    with open(card_path, "r") as f:
        return json.load(f)


def main():
    """Main function to start an A2A agent using the unified LLM factory."""
    parser = argparse.ArgumentParser(
        description="Start an A2A agent with factory-managed models"
    )
    parser.add_argument(
        "--card-path", required=True, help="Path to the agent card JSON file"
    )
    parser.add_argument(
        "--port", required=True, type=int, help="Port to run the agent on"
    )
    parser.add_argument(
        "--model",
        default="gemini-2.5-pro",
        help="Model to use (default: gemini-2.5-pro)",
    )
    parser.add_argument(
        "--provider", default="google", help="LLM provider (default: google)"
    )
    args = parser.parse_args()

    # Load agent card
    try:
        card = load_agent_card(args.card_path)
        logger.info(f"Loaded agent card: {card.get('agent_name', 'Unknown')}")
    except Exception as e:
        logger.error(f"Failed to load agent card from {args.card_path}: {e}")
        sys.exit(1)

    # Get agent name and look up in registry (must match exactly)
    agent_name = card.get("agent_name", "")
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

    # Create MCP toolsets using your existing MCP client
    try:
        toolsets = create_mcp_toolsets_from_config()
        logger.info(f"Created {len(toolsets)} MCP toolsets for agent")
    except Exception as e:
        logger.error(f"Failed to create MCP toolsets: {e}")
        toolsets = []

    # --- USE UNIFIED LLM FACTORY FOR MODEL CREATION ---
    try:
        logger.info(
            f"Creating model instance using unified factory: {args.provider}:{args.model}"
        )

        # Create model instance using your factory with proper API key management
        llm_factory = get_llm_factory()
        model_instance = llm_factory.create_llm_from_config(
            {
                "provider": args.provider,
                "model_name": args.model,
            }
        )

        logger.info("✅ Factory created model instance successfully")
    except Exception as e:
        logger.error(f"Failed to create model instance via factory: {e}")
        sys.exit(1)

    # Create agent instance with factory-created model
    try:
        # Use the factory pattern: pass model instance + toolsets
        agent_instance = AgentClass(
            llm_instance=model_instance,  # Factory-created model with API keys
            toolsets=toolsets,  # MCP toolsets
        )
        logger.info(
            f"✅ Created {class_name} instance with factory model and {len(toolsets)} toolsets"
        )
    except Exception as e:
        logger.error(f"Failed to create {class_name} instance: {e}", exc_info=True)
        sys.exit(1)

    # Use PydanticAI's native A2A support - NO custom wrappers needed
    try:
        logger.info("Creating A2A app using PydanticAI native to_a2a() method")

        # Get the underlying PydanticAI agent for A2A conversion
        if hasattr(agent_instance, "pydantic_agent"):
            pydantic_agent = agent_instance.pydantic_agent
        else:
            # Fallback for agents that ARE the PydanticAI agent
            pydantic_agent = agent_instance

        # Create A2A app with metadata from agent card
        app = pydantic_agent.to_a2a(
            name=card.get("agent_name", "Unknown Agent"),
            url=f"http://localhost:{args.port}",
            version=card.get("version", "1.0.0"),
            description=card.get("description", "AI Research Agent"),
        )
        logger.info(
            f"✅ Native PydanticAI A2A app created for {card.get('agent_name')}"
        )
    except Exception as e:
        logger.error(f"Failed to create A2A app: {e}", exc_info=True)
        sys.exit(1)

    # Start the A2A server
    logger.info(f"🚀 Starting {card.get('agent_name')} A2A server on port {args.port}")
    logger.info(f"📝 Model: {args.provider}:{args.model} (via factory)")
    logger.info(f"🔧 MCP Toolsets: {len(toolsets)}")
    uvicorn.run(app, host="0.0.0.0", port=args.port, log_level="info")


if __name__ == "__main__":
    main()

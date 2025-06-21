# File: src/ai_research_assistant/a2a_services/fasta2a_wrapper.py

import logging
from typing import Any, Dict, List, Optional

from fasta2a import Skill

from ai_research_assistant.agents.base_pydantic_agent import BasePydanticAgent
from ai_research_assistant.agents.base_pydantic_agent_config import (
    BasePydanticAgentConfig,
)
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

logger = logging.getLogger(__name__)

AGENT_REGISTRY: Dict[str, Dict[str, Any]] = {
    "ChiefLegalOrchestrator": {
        "agent_class": OrchestratorAgent,
        "config_class": OrchestratorAgentConfig,
    },
    "DocumentProcessingCoordinator": {
        "agent_class": DocumentAgent,
        "config_class": DocumentAgentConfig,
    },
    "LegalResearchCoordinator": {
        "agent_class": BrowserAgent,
        "config_class": BrowserAgentConfig,
    },
    "DataQueryCoordinator": {
        "agent_class": DatabaseAgent,
        "config_class": DatabaseAgentConfig,
    },
}


def create_agent_instance(
    agent_name: str, agent_specific_config_dict: Optional[Dict[str, Any]] = None
) -> BasePydanticAgent:
    """Create an instance of the specified agent."""
    if agent_name not in AGENT_REGISTRY:
        raise ValueError(
            f"Unknown agent name: {agent_name}. Available: {list(AGENT_REGISTRY.keys())}"
        )

    agent_info = AGENT_REGISTRY[agent_name]
    AgentClass = agent_info["agent_class"]
    ConfigClass = agent_info["config_class"]

    base_config_values = {
        "agent_id": f"{agent_name.lower().replace(' ', '_')}_instance_001",
        "agent_name": agent_name,
        **(agent_specific_config_dict or {}),
    }

    try:
        agent_config = ConfigClass(**base_config_values)
    except Exception as e:
        logger.error(
            f"Error creating config for {agent_name} with values {base_config_values}: {e}"
        )
        if ConfigClass is not BasePydanticAgentConfig:
            logger.warning(f"Falling back to BasePydanticAgentConfig for {agent_name}")
            agent_config = BasePydanticAgentConfig(**base_config_values)
        else:
            raise

    agent_instance = AgentClass(config=agent_config)
    logger.info(
        f"Successfully instantiated agent: {agent_name} with ID {agent_instance.agent_id}"
    )
    return agent_instance


def create_skills_from_agent(agent_instance: BasePydanticAgent) -> List[Skill]:
    """Extract skills from agent methods and convert them to FastA2A Skill format."""
    skills = []

    # Get all methods that could be skills
    for attr_name in dir(agent_instance):
        if not attr_name.startswith("_"):
            attr_value = getattr(agent_instance, attr_name)
            if callable(attr_value) and hasattr(attr_value, "__call__"):
                # Skip common methods that aren't skills
                if attr_name not in [
                    "__init__",
                    "run_skill",
                    "health_check",
                    "get_status",
                    "_initialize_llm",
                    "_get_initial_tools",
                    "run",
                    "to_a2a",
                ]:
                    # Create a skill definition
                    skill_description = (
                        getattr(attr_value, "__doc__", None)
                        or f"Executes the {attr_name} skill"
                    )

                    skills.append(
                        Skill(
                            id=attr_name,
                            name=attr_name.replace("_", " ").title(),
                            description=skill_description.split("\n")[0],
                            tags=[agent_instance.agent_name],
                            input_modes=["application/json"],
                            output_modes=["application/json"],
                        )
                    )

    logger.info(
        f"Created {len(skills)} skills for agent {agent_instance.agent_name}: {[s['id'] for s in skills]}"
    )
    return skills


def wrap_agent_with_fasta2a(
    agent_name: str,
    agent_specific_config: Optional[Dict[str, Any]] = None,
    url: str = "http://localhost:8000",
    version: str = "1.0.0",
):
    """
    Wrap a PydanticAI agent as a FastA2A server using the built-in to_a2a() method.

    Args:
        agent_name: Name of the agent to wrap
        agent_specific_config: Optional configuration for the agent
        url: URL where the A2A server will be hosted
        version: Version of the agent

    Returns:
        FastA2A application ready to be served
    """
    logger.info(f"Wrapping agent '{agent_name}' with FastA2A...")

    # Create the agent instance
    agent_instance = create_agent_instance(agent_name, agent_specific_config)

    # Extract skills from the agent
    skills = create_skills_from_agent(agent_instance)

    # Create a PydanticAI agent that represents our custom agent
    from pydantic_ai import Agent

    # Use the agent's description if available
    description = getattr(
        agent_instance, "description", f"A2A service for {agent_instance.agent_name}"
    )

    # Create a simple PydanticAI agent
    pydantic_agent = Agent(
        model="openai:gpt-4",  # Default model, can be overridden
        system_prompt=f"You are {agent_instance.agent_name}. {description}",
    )

    # Note: In a production implementation, you would properly wrap the agent's methods
    # as PydanticAI tools. For now, we're creating a simple facade that exposes
    # the agent through the A2A protocol.

    # Create the A2A app using PydanticAI's to_a2a method
    app = pydantic_agent.to_a2a(
        name=agent_instance.agent_name,
        url=url,
        version=version,
        description=description,
        skills=skills,
    )

    logger.info(f"Agent '{agent_name}' wrapped successfully with {len(skills)} skills.")
    return app

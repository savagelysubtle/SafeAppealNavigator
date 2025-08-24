# File: src/ai_research_assistant/a2a_services/fasta2a_wrapper.py
import logging
from typing import List

from fasta2a import Skill

from ai_research_assistant.agents.base_pydantic_agent import BasePydanticAgent

logger = logging.getLogger(__name__)


def create_skills_from_agent(agent_instance: BasePydanticAgent) -> List[Skill]:
    """Extract @agent_skill decorated methods from agent."""
    skills = []
    for attr_name in dir(agent_instance):
        if not attr_name.startswith("_"):
            attr_value = getattr(agent_instance, attr_name)
            if (
                callable(attr_value)
                and hasattr(attr_value, "_is_agent_skill")
                and attr_value._is_agent_skill
            ):
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

    # --- FIX: Use dictionary-style access for robustness ---
    # This works for both Pydantic models and dicts, resolving the AttributeError.
    skill_ids = [s["id"] for s in skills]
    logger.info(
        f"Created {len(skills)} skills for agent {agent_instance.agent_name}: {skill_ids}"
    )
    return skills


def wrap_agent_with_fasta2a(
    agent_instance: BasePydanticAgent,
    url: str = "http://localhost:8000",
    version: str = "1.0.0",
):
    """
    Wrap a PydanticAI agent as a FastA2A server.
    """
    logger.info(f"Wrapping agent '{agent_instance.agent_name}' with FastA2A...")

    skills = create_skills_from_agent(agent_instance)

    # Use the actual pydantic_agent from our BasePydanticAgent to host the A2A interface
    host_agent = agent_instance.pydantic_agent

    app = host_agent.to_a2a(
        name=agent_instance.agent_name,
        url=url,
        version=version,
        description=getattr(agent_instance.config, "pydantic_ai_system_prompt", ""),
        skills=skills,
    )

    logger.info(
        f"Agent '{agent_instance.agent_name}' wrapped successfully with {len(skills)} skills."
    )
    return app

# File: src/savagelysubtle_airesearchagent/a2a_services/fasta2a_wrapper.py

import logging
from typing import Type, Callable, Awaitable, Dict, Any, List, Optional
from pydantic import BaseModel, create_model

from fasta2a import FastA2A, A2AExecuteTaskParams, A2ATaskResult, MessageEnvelope
from fasta2a.storage.memory import InMemoryTaskStorage
from fasta2a.broker.memory import InMemoryBroker
from fasta2a.worker import Worker

from savagelysubtle_airesearchagent.agents.base_pydantic_agent import BasePydanticAgent
from savagelysubtle_airesearchagent.agents.base_pydantic_agent_config import BasePydanticAgentConfig
# Import specific agent classes and their configs as needed for instantiation
from savagelysubtle_airesearchagent.agents.chief_legal_orchestrator.agent import ChiefLegalOrchestrator
from savagelysubtle_airesearchagent.agents.chief_legal_orchestrator.config import ChiefLegalOrchestratorConfig
# Add other coordinators and their configs here
# from savagelysubtle_airesearchagent.agents.document_processing_coordinator.agent import DocumentProcessingCoordinator
# from savagelysubtle_airesearchagent.agents.document_processing_coordinator.config import DocumentProcessingCoordinatorConfig
# ... and so on for LegalResearchCoordinator and DataQueryCoordinator

logger = logging.getLogger(__name__)

# Mapping agent names to their classes and config classes
# This would ideally be more dynamic or use a plugin system for true scalability
AGENT_REGISTRY: Dict[str, Dict[str, Type]] = {
    "ChiefLegalOrchestrator": {
        "agent_class": ChiefLegalOrchestrator,
        "config_class": ChiefLegalOrchestratorConfig,
    },
    # "DocumentProcessingCoordinator": {
    #     "agent_class": DocumentProcessingCoordinator,
    #     "config_class": DocumentProcessingCoordinatorConfig,
    # },
    # Add other agents here
}
# Placeholder for uninitialized coordinators
class PlaceholderAgent(BasePydanticAgent):
    def __init__(self, config, **kwargs):
        logger.warning(f"Initializing PlaceholderAgent for {config.agent_name}")
        super().__init__(config, **kwargs)
    async def placeholder_skill(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Placeholder skill called on {self.agent_name} with {input_data}")
        return {"message": f"Placeholder skill on {self.agent_name} executed", "input": input_data}

class PlaceholderAgentConfig(BasePydanticAgentConfig):
    pass

if "DocumentProcessingCoordinator" not in AGENT_REGISTRY:
    AGENT_REGISTRY["DocumentProcessingCoordinator"] = {"agent_class": PlaceholderAgent, "config_class": PlaceholderAgentConfig}
if "LegalResearchCoordinator" not in AGENT_REGISTRY:
    AGENT_REGISTRY["LegalResearchCoordinator"] = {"agent_class": PlaceholderAgent, "config_class": PlaceholderAgentConfig}
if "DataQueryCoordinator" not in AGENT_REGISTRY:
    AGENT_REGISTRY["DataQueryCoordinator"] = {"agent_class": PlaceholderAgent, "config_class": PlaceholderAgentConfig}


def create_agent_instance(agent_name: str, agent_specific_config_dict: Optional[Dict[str, Any]] = None) -> BasePydanticAgent:
    """
    Instantiates an agent based on its name.
    Loads agent-specific configuration (e.g., from a file or environment).
    """
    if agent_name not in AGENT_REGISTRY:
        raise ValueError(f"Unknown agent name: {agent_name}. Available: {list(AGENT_REGISTRY.keys())}")

    agent_info = AGENT_REGISTRY[agent_name]
    AgentClass = agent_info["agent_class"]
    ConfigClass = agent_info["config_class"]

    # For simplicity, agent_id and agent_name are derived or fixed.
    # In a real system, this config would be loaded from a more robust source.
    # The agent_specific_config_dict would override defaults in ConfigClass.

    # Base configuration that should be common
    base_config_values = {
        "agent_id": f"{agent_name.lower().replace(' ', '_')}_instance_001",
        "agent_name": agent_name,
    }
    if agent_specific_config_dict:
        base_config_values.update(agent_specific_config_dict)

    try:
        agent_config = ConfigClass(**base_config_values)
    except Exception as e:
        logger.error(f"Error creating config for {agent_name} with values {base_config_values}: {e}")
        # Fallback to basic config if specific one fails, useful for placeholders
        if ConfigClass != BasePydanticAgentConfig and ConfigClass != PlaceholderAgentConfig:
             logger.warning(f"Falling back to BasePydanticAgentConfig for {agent_name}")
             agent_config = BasePydanticAgentConfig(**base_config_values)
        else:
            raise

    # Instantiate the agent
    # MCPClient and AgentStateManager could be injected here if needed globally by the agent
    # For now, BasePydanticAgent initializes its own basic MCPClient.
    agent_instance = AgentClass(config=agent_config)

    logger.info(f"Successfully instantiated agent: {agent_name} with ID {agent_instance.agent_id}")
    return agent_instance


class PydanticAIAgentWorker(Worker):
    """
    FastA2A Worker that routes tasks to a Pydantic AI agent's skills.
    """
    def __init__(self, agent_instance: BasePydanticAgent):
        self.agent = agent_instance
        # Dynamically discover skills (public methods not starting with '_')
        self.skills: Dict[str, Callable[..., Awaitable[Any]]] = {}
        for attr_name in dir(self.agent):
            if not attr_name.startswith("_"):
                attr_value = getattr(self.agent, attr_name)
                if asyncio.iscoroutinefunction(attr_value):
                    # Further check if it's intended as a skill (e.g., via a decorator or naming convention)
                    # For now, assume all public async methods are skills
                    self.skills[attr_name] = attr_value
        logger.info(f"Discovered skills for agent {self.agent.agent_name}: {list(self.skills.keys())}")
        if not self.skills:
             logger.warning(f"No awaitable skills found for agent {self.agent.agent_name}. Adding a placeholder skill if agent is PlaceholderAgent.")
             if isinstance(self.agent, PlaceholderAgent):
                 self.skills["placeholder_skill"] = self.agent.placeholder_skill


    async def execute_task(self, task_id: str, params: A2AExecuteTaskParams) -> A2ATaskResult:
        skill_name = params.skill_name
        skill_args = params.parameters or {}

        logger.info(f"Worker received task {task_id} for skill '{skill_name}' with args: {skill_args}")

        if skill_name not in self.skills:
            logger.error(f"Skill '{skill_name}' not found in agent '{self.agent.agent_name}'. Available: {list(self.skills.keys())}")
            return A2ATaskResult(
                task_id=task_id,
                status="error",
                error_message=f"Skill '{skill_name}' not found.",
                result=None
            )

        try:
            skill_method = self.skills[skill_name]
            # Pydantic models for skill I/O should be handled by FastA2A if schemas are defined
            # Here, we assume skill_args directly match the method's parameters
            result_data = await skill_method(**skill_args)

            # The result_data should be a Pydantic model or JSON-serializable
            return A2ATaskResult(
                task_id=task_id,
                status="completed",
                result=result_data # This will be wrapped in MessageEnvelope part by FastA2A
            )
        except Exception as e:
            logger.error(f"Error executing skill '{skill_name}' on agent '{self.agent.agent_name}': {e}", exc_info=True)
            return A2ATaskResult(
                task_id=task_id,
                status="error",
                error_message=str(e),
                result=None
            )

def wrap_agent_with_fasta2a(agent_name: str, agent_specific_config: Optional[Dict[str, Any]] = None) -> FastA2A:
    """
    Wraps a Pydantic AI agent with FastA2A to expose it as an A2A service.
    """
    logger.info(f"Wrapping agent '{agent_name}' with FastA2A...")

    # 1. Instantiate the agent
    try:
        agent_instance = create_agent_instance(agent_name, agent_specific_config)
    except Exception as e:
        logger.error(f"Failed to create instance for agent '{agent_name}': {e}", exc_info=True)
        raise

    # 2. Create FastA2A components
    storage = InMemoryTaskStorage()
    broker = InMemoryBroker(storage=storage)
    worker = PydanticAIAgentWorker(agent_instance=agent_instance)

    # 3. Initialize FastA2A
    # The agent_id for FastA2A should ideally match the one in the Agent Card
    fasta2a_app = FastA2A(
        agent_id=agent_instance.agent_id, # Use the agent's own ID
        agent_name=agent_instance.agent_name,
        description=f"A2A service for {agent_instance.agent_name}",
        storage=storage,
        broker=broker,
        worker=worker,
        # Define skills based on the agent's capabilities
        # This can be dynamic by inspecting the agent instance
        # For now, let's assume the worker handles skill dispatch
    )

    # Dynamically add skills to FastA2A from the worker's discovered skills
    # FastA2A's skill definition might require input/output Pydantic models
    # For simplicity, we're not defining explicit schemas here for FastA2A itself,
    # relying on the worker to handle parameters.
    # In a more robust setup, you'd iterate through agent_instance.skills (if it's a defined attribute)
    # or use introspection to find methods decorated as skills and their Pydantic models.

    # Example of how you might declare skills if you had their Pydantic models
    # for skill_name_key in worker.skills.keys():
    #     # These schemas would ideally come from the agent's skill definitions
    #     # Placeholder schemas for now
    #     InputModel = create_model(f"{skill_name_key.capitalize()}Input", **{'data': (Dict[str, Any], ...)})
    #     OutputModel = create_model(f"{skill_name_key.capitalize()}Output", **{'result': (Dict[str, Any], ...)})

    #     fasta2a_app.skill(
    #         name=skill_name_key,
    #         description=f"Execute {skill_name_key} on {agent_instance.agent_name}",
    #         input_type=InputModel,
    #         output_type=OutputModel
    #     )
    # logger.info(f"Added {len(worker.skills)} skills to FastA2A for agent {agent_instance.agent_name}.")


    logger.info(f"Agent '{agent_name}' wrapped. A2A Agent ID: {fasta2a_app.agent_id}")
    return fasta2a_app
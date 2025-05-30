# File: src/savagelysubtle_airesearchagent/a2a_services/fasta2a_wrapper.py

import logging
import asyncio # Added missing import
import inspect
from typing import Type, Callable, Awaitable, Dict, Any, List, Optional, Tuple

from pydantic import BaseModel, create_model

from fasta2a import FastA2A, A2AExecuteTaskParams, A2ATaskResult
from fasta2a.storage.memory import InMemoryTaskStorage
from fasta2a.broker.memory import InMemoryBroker
from fasta2a.worker import Worker
from fasta2a.models import SkillDefinition, SkillParameter

from savagelysubtle_airesearchagent.agents.base_pydantic_agent import BasePydanticAgent
from savagelysubtle_airesearchagent.agents.base_pydantic_agent_config import BasePydanticAgentConfig
from savagelysubtle_airesearchagent.agents.chief_legal_orchestrator.agent import ChiefLegalOrchestrator
from savagelysubtle_airesearchagent.agents.chief_legal_orchestrator.config import ChiefLegalOrchestratorConfig
# Import other coordinator agents and their configs once they are created
# from savagelysubtle_airesearchagent.agents.document_processing_coordinator.agent import DocumentProcessingCoordinator
# from savagelysubtle_airesearchagent.agents.document_processing_coordinator.config import DocumentProcessingCoordinatorConfig
# from savagelysubtle_airesearchagent.agents.legal_research_coordinator.agent import LegalResearchCoordinator
# from savagelysubtle_airesearchagent.agents.legal_research_coordinator.config import LegalResearchCoordinatorConfig
# from savagelysubtle_airesearchagent.agents.data_query_coordinator.agent import DataQueryCoordinator
# from savagelysubtle_airesearchagent.agents.data_query_coordinator.config import DataQueryCoordinatorConfig


logger = logging.getLogger(__name__)

AGENT_REGISTRY: Dict[str, Dict[str, Type]] = {
    "ChiefLegalOrchestrator": {
        "agent_class": ChiefLegalOrchestrator,
        "config_class": ChiefLegalOrchestratorConfig,
    },
    # Uncomment and add other agents as they are implemented
    # "DocumentProcessingCoordinator": {
    #     "agent_class": DocumentProcessingCoordinator,
    #     "config_class": DocumentProcessingCoordinatorConfig,
    # },
    # "LegalResearchCoordinator": {
    #     "agent_class": LegalResearchCoordinator,
    #     "config_class": LegalResearchCoordinatorConfig,
    # },
    # "DataQueryCoordinator": {
    #     "agent_class": DataQueryCoordinator,
    #     "config_class": DataQueryCoordinatorConfig,
    # },
}

# Placeholder for uninitialized coordinators
class PlaceholderAgent(BasePydanticAgent):
    def __init__(self, config: BasePydanticAgentConfig, **kwargs: Any):
        logger.warning(f"Initializing PlaceholderAgent for {config.agent_name}")
        super().__init__(config, **kwargs)

    async def placeholder_skill(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Placeholder skill called on {self.agent_name} with {input_data}")
        return {"message": f"Placeholder skill on {self.agent_name} executed", "input": input_data}

class PlaceholderAgentConfig(BasePydanticAgentConfig):
    pass

# Ensure all planned agents have at least a placeholder
for agent_key in ["DocumentProcessingCoordinator", "LegalResearchCoordinator", "DataQueryCoordinator"]:
    if agent_key not in AGENT_REGISTRY:
        AGENT_REGISTRY[agent_key] = {"agent_class": PlaceholderAgent, "config_class": PlaceholderAgentConfig}


def create_agent_instance(agent_name: str, agent_specific_config_dict: Optional[Dict[str, Any]] = None) -> BasePydanticAgent:
    if agent_name not in AGENT_REGISTRY:
        raise ValueError(f"Unknown agent name: {agent_name}. Available: {list(AGENT_REGISTRY.keys())}")

    agent_info = AGENT_REGISTRY[agent_name]
    AgentClass = agent_info["agent_class"]
    ConfigClass = agent_info["config_class"]

    base_config_values = {
        "agent_id": f"{agent_name.lower().replace(' ', '_')}_instance_001", # Consistent ID generation
        "agent_name": agent_name,
        **(agent_specific_config_dict or {})
    }

    try:
        agent_config = ConfigClass(**base_config_values)
    except Exception as e:
        logger.error(f"Error creating config for {agent_name} with values {base_config_values}: {e}")
        if ConfigClass not in [BasePydanticAgentConfig, PlaceholderAgentConfig]:
            logger.warning(f"Falling back to BasePydanticAgentConfig for {agent_name}")
            agent_config = BasePydanticAgentConfig(**base_config_values)
        else:
            raise

    agent_instance = AgentClass(config=agent_config)
    logger.info(f"Successfully instantiated agent: {agent_name} with ID {agent_instance.agent_id}")
    return agent_instance


class PydanticAIAgentWorker(Worker):
    def __init__(self, agent_instance: BasePydanticAgent):
        self.agent = agent_instance
        self.skills: Dict[str, Callable[..., Awaitable[Any]]] = {}
        for attr_name in dir(self.agent):
            if not attr_name.startswith("_"):
                attr_value = getattr(self.agent, attr_name)
                if inspect.iscoroutinefunction(attr_value) and hasattr(attr_value, "__call__"):
                    # Basic check for "skill-like" methods. More specific decorators or naming conventions
                    # on the agent methods would make this more robust.
                    if attr_name not in ["__init__", "run_skill", "health_check", "get_status", "_initialize_llm", "_get_initial_tools"]: # Exclude base/internal methods
                        self.skills[attr_name] = attr_value

        logger.info(f"Discovered skills for agent {self.agent.agent_name}: {list(self.skills.keys())}")
        if not self.skills and isinstance(self.agent, PlaceholderAgent):
            self.skills["placeholder_skill"] = self.agent.placeholder_skill
            logger.info(f"Added placeholder_skill for PlaceholderAgent {self.agent.agent_name}")


    async def execute_task(self, task_id: str, params: A2AExecuteTaskParams) -> A2ATaskResult:
        skill_name = params.skill_name
        skill_args = params.parameters or {}

        logger.info(f"Worker received task {task_id} for skill '{skill_name}' on agent '{self.agent.agent_name}' with args: {skill_args}")

        if skill_name not in self.skills:
            logger.error(f"Skill '{skill_name}' not found in agent '{self.agent.agent_name}'. Available: {list(self.skills.keys())}")
            return A2ATaskResult(task_id=task_id, status="error", error_message=f"Skill '{skill_name}' not found.")

        try:
            skill_method = self.skills[skill_name]
            result_data = await skill_method(**skill_args)
            return A2ATaskResult(task_id=task_id, status="completed", result=result_data)
        except Exception as e:
            logger.error(f"Error executing skill '{skill_name}' on agent '{self.agent.agent_name}': {e}", exc_info=True)
            return A2ATaskResult(task_id=task_id, status="error", error_message=str(e))


def _generate_skill_schema_from_method(method: Callable[..., Any]) -> Tuple[Type[BaseModel], Type[BaseModel]]:
    """
    Generates placeholder Pydantic input/output models for a skill method.
    Ideally, skill methods should use Pydantic models in their type hints.
    """
    method_name = method.__name__
    sig = inspect.signature(method)

    input_fields: Dict[str, Tuple[Any, Any]] = {}
    for name, param in sig.parameters.items():
        if name == 'self':
            continue
        # Default to Any if no type hint or if it's not a Pydantic model
        param_type = param.annotation if param.annotation is not inspect.Parameter.empty else Any
        param_default = ... if param.default is inspect.Parameter.empty else param.default
        input_fields[name] = (param_type, param_default)

    InputModel = create_model(f"{method_name.capitalize()}Input", **input_fields)

    # Infer output type from return annotation
    output_type_hint = sig.return_annotation
    if output_type_hint is inspect.Signature.empty or not isinstance(output_type_hint, type) or not issubclass(output_type_hint, BaseModel):
        # If not a Pydantic model, wrap in a generic result model
        OutputModel = create_model(f"{method_name.capitalize()}Output", result=(output_type_hint if output_type_hint is not inspect.Signature.empty else Any, ...))
    else:
        OutputModel = output_type_hint

    return InputModel, OutputModel


def wrap_agent_with_fasta2a(agent_name: str, agent_specific_config: Optional[Dict[str, Any]] = None) -> FastA2A:
    logger.info(f"Wrapping agent '{agent_name}' with FastA2A...")

    agent_instance = create_agent_instance(agent_name, agent_specific_config)

    storage = InMemoryTaskStorage()
    broker = InMemoryBroker(storage=storage)
    worker = PydanticAIAgentWorker(agent_instance=agent_instance)

    fasta2a_app = FastA2A(
        agent_id=agent_instance.agent_id,
        agent_name=agent_instance.agent_name,
        description=f"A2A service for {agent_instance.agent_name}",
        storage=storage,
        broker=broker,
        worker=worker,
    )

    # Explicitly register skills with FastA2A for better schema definition and validation
    for skill_name, skill_method in worker.skills.items():
        docstring = inspect.getdoc(skill_method) or f"Executes the {skill_name} skill on {agent_instance.agent_name}."

        # Attempt to generate I/O models from method signature
        # This is a simplified approach. Robust schema generation would involve
        # checking if type hints are already Pydantic models.
        try:
            InputModel, OutputModel = _generate_skill_schema_from_method(skill_method)
        except Exception as e: # Broad exception for schema generation issues
            logger.warning(f"Could not generate Pydantic schema for skill '{skill_name}': {e}. Using generic Dict schema.")
            InputModel = create_model(f"{skill_name.capitalize()}Input", **{'data': (Dict[str, Any], {})})
            OutputModel = create_model(f"{skill_name.capitalize()}Output", **{'result': (Dict[str, Any], {})})

        fasta2a_app.skill(
            name=skill_name,
            description=docstring.split('\n')[0], # First line of docstring
            input_type=InputModel,
            output_type=OutputModel,
            # The worker's execute_task method will handle the actual call
        )
    logger.info(f"Registered {len(worker.skills)} skills with FastA2A for agent {agent_instance.agent_name}.")

    logger.info(f"Agent '{agent_name}' wrapped. A2A Agent ID: {fasta2a_app.agent_id}")
    return fasta2a_app
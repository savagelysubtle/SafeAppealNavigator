# File: src/savagelysubtle_airesearchagent/a2a_services/fasta2a_wrapper.py

import inspect
import logging
from typing import Any, Awaitable, Callable, Dict, Optional, Tuple, Type

from fasta2a import Broker, FastA2A, Skill, Storage, Worker
from fasta2a.memory import InMemoryBroker, InMemoryStorage
from fasta2a.schema import (
    Artifact,
    DataPart,
    Message,
    TaskIdParams,
    TaskSendParams,
    TextPart,
)
from pydantic import BaseModel, create_model

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


# Placeholder for uninitialized coordinators
class PlaceholderAgent(BasePydanticAgent):
    def __init__(self, config: BasePydanticAgentConfig, **kwargs: Any):
        logger.warning(f"Initializing PlaceholderAgent for {config.agent_name}")
        super().__init__(config, **kwargs)

    async def placeholder_skill(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Placeholder skill called on {self.agent_name} with {input_data}")
        return {
            "message": f"Placeholder skill on {self.agent_name} executed",
            "input": input_data,
        }


class PlaceholderAgentConfig(BasePydanticAgentConfig):
    pass


# Ensure all planned agents have at least a placeholder
for agent_key in [
    "DocumentProcessingCoordinator",
    "LegalResearchCoordinator",
    "DataQueryCoordinator",
]:
    if agent_key not in AGENT_REGISTRY:
        AGENT_REGISTRY[agent_key] = {
            "agent_class": PlaceholderAgent,
            "config_class": PlaceholderAgentConfig,
        }


def create_agent_instance(
    agent_name: str, agent_specific_config_dict: Optional[Dict[str, Any]] = None
) -> BasePydanticAgent:
    if agent_name not in AGENT_REGISTRY:
        raise ValueError(
            f"Unknown agent name: {agent_name}. Available: {list(AGENT_REGISTRY.keys())}"
        )

    agent_info = AGENT_REGISTRY[agent_name]
    AgentClass = agent_info["agent_class"]
    ConfigClass = agent_info["config_class"]

    base_config_values = {
        "agent_id": f"{agent_name.lower().replace(' ', '_')}_instance_001",  # Consistent ID generation
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


class PydanticAIAgentWorker(Worker):
    def __init__(
        self,
        agent_instance: BasePydanticAgent,
        broker: Broker,
        storage: Storage,
    ):
        super().__init__(broker=broker, storage=storage)
        self.agent = agent_instance
        self.skills: Dict[str, Callable[..., Awaitable[Any]]] = {}
        for attr_name in dir(self.agent):
            if not attr_name.startswith("_"):
                attr_value = getattr(self.agent, attr_name)
                if inspect.iscoroutinefunction(attr_value) and hasattr(
                    attr_value, "__call__"
                ):
                    if attr_name not in [
                        "__init__",
                        "run_skill",
                        "health_check",
                        "get_status",
                        "_initialize_llm",
                        "_get_initial_tools",
                    ]:
                        self.skills[attr_name] = attr_value

        logger.info(
            f"Discovered skills for agent {self.agent.agent_name}: {list(self.skills.keys())}"
        )
        if not self.skills and isinstance(self.agent, PlaceholderAgent):
            self.skills["placeholder_skill"] = self.agent.placeholder_skill
            logger.info(
                f"Added placeholder_skill for PlaceholderAgent {self.agent.agent_name}"
            )

    async def run_task(self, params: TaskSendParams) -> None:
        task_id = params["id"]
        # The skill and parameters should be within the message
        message_parts = params["message"]["parts"]
        skill_name = "unknown_skill"
        skill_args = {}

        # A2A protocol is more generic, we need to find the skill and params
        # Let's assume the first 'data' part holds the skill info
        for part in message_parts:
            if isinstance(part, DataPart) and "skill_name" in part["data"]:
                skill_name = part["data"]["skill_name"]
                skill_args = part["data"].get("parameters", {})
                break
            # Fallback for simpler text-based invocation
            if isinstance(part, TextPart):
                # This is a simplification. A real implementation might parse the text.
                skill_name = part["text"].split(" ")[0]

        logger.info(
            f"Worker received task {task_id} for skill '{skill_name}' on agent '{self.agent.agent_name}' with args: {skill_args}"
        )

        if skill_name not in self.skills:
            logger.error(
                f"Skill '{skill_name}' not found in agent '{self.agent.agent_name}'. Available: {list(self.skills.keys())}"
            )
            await self.storage.update_task(
                task_id,
                state="failed",
                message=Message(
                    role="agent",
                    parts=[
                        TextPart(
                            type="text",
                            text=f"Skill '{skill_name}' not found.",
                        )
                    ],
                ),
            )
            return

        try:
            await self.storage.update_task(task_id, state="working")
            skill_method = self.skills[skill_name]
            result_data = await skill_method(**skill_args)

            # Package result into an artifact
            artifacts = self.build_artifacts(result_data)

            await self.storage.update_task(
                task_id, state="completed", artifacts=artifacts
            )
        except Exception as e:
            logger.error(
                f"Error executing skill '{skill_name}' on agent '{self.agent.agent_name}': {e}",
                exc_info=True,
            )
            await self.storage.update_task(
                task_id,
                state="failed",
                message=Message(
                    role="agent",
                    parts=[TextPart(type="text", text=str(e))],
                ),
            )

    async def cancel_task(self, params: TaskIdParams) -> None:
        logger.info(f"Task {params['id']} cancellation requested.")
        await self.storage.update_task(params["id"], state="canceled")

    def build_message_history(self, task_history: list[Message]) -> list[Any]:
        # This is a placeholder. A real implementation would convert
        # the A2A message history to a format the agent's LLM can understand.
        return [msg["parts"][0]["text"] for msg in task_history if msg["parts"]]

    def build_artifacts(self, result: Any) -> list[Artifact]:
        # This is a placeholder. A real implementation would create
        # proper artifacts based on the result type.
        return [
            Artifact(
                index=0,
                parts=[DataPart(type="data", data={"result": result})],
            )
        ]


def _generate_skill_schema_from_method(
    method: Callable[..., Any],
) -> Tuple[Type[BaseModel], Type[BaseModel]]:
    """
    Generates placeholder Pydantic input/output models for a skill method.
    Ideally, skill methods should use Pydantic models in their type hints.
    """
    method_name = method.__name__
    sig = inspect.signature(method)

    input_fields: Dict[str, Any] = {}
    for name, param in sig.parameters.items():
        if name == "self":
            continue
        param_type = (
            param.annotation if param.annotation is not inspect.Parameter.empty else Any
        )
        param_default = (
            ... if param.default is inspect.Parameter.empty else param.default
        )
        input_fields[name] = (param_type, param_default)

    InputModel = create_model(f"{method_name.capitalize()}Input", **input_fields)

    output_type_hint = sig.return_annotation
    is_pydantic_model = False
    if inspect.isclass(output_type_hint) and issubclass(output_type_hint, BaseModel):
        is_pydantic_model = True

    if is_pydantic_model:
        OutputModel = output_type_hint
    else:
        final_output_type = (
            output_type_hint if output_type_hint is not inspect.Signature.empty else Any
        )
        OutputModel = create_model(
            f"{method_name.capitalize()}Output", result=(final_output_type, ...)
        )

    return InputModel, OutputModel


def wrap_agent_with_fasta2a(
    agent_name: str, agent_specific_config: Optional[Dict[str, Any]] = None
) -> FastA2A:
    logger.info(f"Wrapping agent '{agent_name}' with FastA2A...")

    agent_instance = create_agent_instance(agent_name, agent_specific_config)

    storage = InMemoryStorage()
    broker = InMemoryBroker(storage=storage)
    worker = PydanticAIAgentWorker(
        agent_instance=agent_instance, broker=broker, storage=storage
    )

    registered_skills: list[Skill] = []
    for skill_name, skill_method in worker.skills.items():
        docstring = (
            inspect.getdoc(skill_method)
            or f"Executes the {skill_name} skill on {agent_instance.agent_name}."
        )

        # We are not using the generated I/O models for now as the protocol
        # is more generic. The skill definition is for the agent card.
        registered_skills.append(
            Skill(
                id=skill_name,
                name=skill_name,
                description=docstring.split("\n")[0],
                input_modes=["application/json"],
                output_modes=["application/json"],
                tags=[agent_instance.agent_name],
            )
        )

    fasta2a_app = FastA2A(
        name=agent_instance.agent_name,
        description=f"A2A service for {agent_instance.agent_name}",
        storage=storage,
        broker=broker,
        skills=registered_skills,
        # The worker is started via the lifespan protocol, not passed directly.
    )

    logger.info(
        f"Registered {len(worker.skills)} skills with FastA2A for agent {agent_instance.agent_name}."
    )

    # In a real app, you would manage the worker's lifecycle with the ASGI server,
    # for example, using a lifespan context manager.
    # For simplicity here, we are not starting the worker.
    # To run it:
    # @asynccontextmanager
    # async def lifespan(app: FastA2A):
    #     async with worker.run():
    #         yield
    # fasta2a_app.router.lifespan = lifespan

    logger.info(f"Agent '{agent_name}' wrapped. A2A Agent Name: {fasta2a_app.name}")
    return fasta2a_app

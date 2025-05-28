"""
Agent Coordinator for Legal Research Orchestrator

Handles agent communication, task delegation, and coordination between multiple specialized agents.
Manages concurrent task execution, agent lifecycle, and inter-agent communication.
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

import httpx  # Kept for now if any direct HTTP calls remain, but MCP calls will use MCPClient

# Removed: from mcp import MCPError, ServerNotConnectedError
# Removed: from mcp.client import Client
# New import for MCP client from langchain_mcp_adapters
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools
# from mcp import (  # Assuming these are still relevant from mcp 1.9.1
#     MCPError,
#     ServerNotConnectedError,
# )

# Import specific agent classes that might be created
from ..core.base_agent import AgentConfig, BaseAgent
from ..intake.enhanced_legal_intake import EnhancedLegalIntakeAgent

# from ..legal_research.legal_research_agent import LegalResearchAgent
# ... import other agent classes as needed

logger = logging.getLogger(__name__)


class AgentType(Enum):
    ORCHESTRATOR = "orchestrator"
    INTAKE = "intake"
    LEGAL_RESEARCH = "legal_research"
    SEARCH = "search"
    CROSS_REFERENCE = "cross_reference"
    DATABASE_MAINTENANCE = "database_maintenance"
    DEEP_RESEARCH = "deep_research"
    BROWSER = "browser"
    COLLECTOR = "collector"
    # Add other specific agent types here
    PLACEHOLDER = "placeholder"  # Generic placeholder


@dataclass
class AgentTask:
    """Task for agent execution"""

    task_id: str
    agent_type: AgentType
    task_type: str
    parameters: Dict[str, Any]
    priority: int = 0
    timeout_seconds: int = 300
    retry_count: int = 0
    max_retries: int = 3
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class AgentInstance:
    """Represents an active agent instance"""

    agent_id: str
    agent_type: AgentType
    agent_instance: Any  # Should be BaseAgent or a compatible type
    is_busy: bool = False
    last_used: Optional[datetime] = None
    task_count: int = 0

    def __post_init__(self):
        if self.last_used is None:
            self.last_used = datetime.now()


class AgentPlaceholder:
    """Placeholder agent for testing and development"""

    def __init__(
        self,
        agent_type: AgentType,
        global_settings_manager=None,
        agent_coordinator=None,
    ):  # Added agent_coordinator
        self.agent_type = agent_type
        self.global_settings_manager = global_settings_manager
        self.agent_coordinator = agent_coordinator  # Store agent_coordinator

    async def run(
        self, task_description: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        logger.info(
            f"Placeholder agent {self.agent_type.value} received task: {task_description} with params: {parameters}"
        )
        await asyncio.sleep(1)  # Simulate work
        return {
            "status": "completed by placeholder",
            "agent_type": self.agent_type.value,
        }


class AgentCoordinator:
    """
    Manages agent instances, task execution, and communication with MCP tool servers.
    """

    def __init__(
        self,
        max_concurrent: int = 5,
        timeout_seconds: int = 300,
        global_settings_manager=None,
        mcp_config_path: str = "src/ai_research_assistant/config/mcp/mcp_servers.json",
    ):
        self.max_concurrent_agents = max_concurrent
        self.agent_timeout_seconds = timeout_seconds
        self.global_settings_manager = global_settings_manager

        self.active_agents: Dict[str, BaseAgent] = {}  # Stores actual agent instances
        self.agent_configs: Dict[str, AgentConfig] = {}  # Stores config for agents

        self.raw_mcp_servers_config_data: Dict[
            str, Any
        ] = {}  # Stores the full loaded mcp_servers.json content
        self.mcp_servers_config: Dict[
            str, Any
        ] = {}  # Stores just the "mcp_servers" part
        self._load_mcp_config(mcp_config_path)

        # Initialize MCPClient with the loaded server configurations
        # The MCPClient will handle starting stdio servers and connecting to others.
        try:
            self.mcp_client = MultiServerMCPClient(connections=self.mcp_servers_config)
            logger.info(
                f"MultiServerMCPClient initialized with {len(self.mcp_servers_config)} server configurations."
            )
        except Exception as e:
            logger.error(
                f"Failed to initialize MultiServerMCPClient: {e}", exc_info=True
            )
            self.mcp_client = MultiServerMCPClient(
                connections={}
            )  # Fallback to an empty client

        # Shared HTTP client for any direct HTTP tasks (not MCP related)
        client_timeout = httpx.Timeout(float(timeout_seconds), connect=10.0)
        self.http_client = httpx.AsyncClient(timeout=client_timeout)

        self.task_semaphore = asyncio.Semaphore(max_concurrent)

        logger.info(
            f"AgentCoordinator initialized. Max concurrent agents: {max_concurrent}, MCP Config Path: {mcp_config_path}"
        )
        if not self.mcp_servers_config:
            logger.warning(
                "MCP server configurations section is empty or failed to load. MCP tools may be unavailable via MCPClient."
            )

    def _load_mcp_config(self, config_path: str):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                full_config = json.load(f)
            self.raw_mcp_servers_config_data = full_config  # Store the full structure

            if not isinstance(full_config, dict) or "mcp_servers" not in full_config:
                logger.error(
                    f"MCP config from {config_path} is malformed or missing 'mcp_servers' key. Resetting to empty."
                )
                self.mcp_servers_config = {}
            else:
                # This self.mcp_servers_config is what MCPClient expects
                self.mcp_servers_config = full_config.get("mcp_servers", {})
                logger.info(
                    f"Successfully extracted 'mcp_servers' configurations from {config_path}"
                )
        except FileNotFoundError:
            logger.error(
                f"MCP server configuration file not found: {config_path}. MCP tools will be unavailable."
            )
            self.mcp_servers_config = {}
            self.raw_mcp_servers_config_data = {}
        except json.JSONDecodeError as e:
            logger.error(
                f"Error decoding JSON from MCP server configuration file: {config_path}: {e}. MCP tools will be unavailable."
            )
            self.mcp_servers_config = {}
            self.raw_mcp_servers_config_data = {}
        except Exception as e:
            logger.error(
                f"An unexpected error occurred while loading MCP server configurations from {config_path}: {e}"
            )
            self.mcp_servers_config = {}
            self.raw_mcp_servers_config_data = {}

    async def _create_agent_instance(
        self, agent_id: str, agent_config: AgentConfig
    ) -> Optional[BaseAgent]:
        """
        Creates and initializes a specific agent instance based on AgentConfig.
        """
        agent_type_enum = agent_config.agent_type

        if not isinstance(agent_type_enum, AgentType):
            try:
                agent_type_enum = AgentType(str(agent_type_enum).lower())
            except ValueError:
                logger.error(
                    f"Invalid agent type '{agent_config.agent_type}' provided in AgentConfig for agent_id '{agent_id}'. Cannot create instance."
                )
                return None

        logger.info(
            f"Attempting to create agent instance for ID '{agent_id}' of type '{agent_type_enum.value}'"
        )

        common_kwargs = {
            "agent_id": agent_id,
            "config": agent_config,
            "global_settings_manager": self.global_settings_manager,
            "agent_coordinator": self,
        }

        agent_instance_obj: Optional[BaseAgent] = None
        try:
            if agent_type_enum == AgentType.INTAKE:
                logger.info(
                    f"Creating EnhancedLegalIntakeAgent instance for {agent_type_enum.value}"
                )
                agent_instance_obj = EnhancedLegalIntakeAgent(**common_kwargs)
            elif agent_type_enum == AgentType.PLACEHOLDER or True:
                logger.warning(
                    f"Agent type '{agent_type_enum.value}' not specifically handled or is PLACEHOLDER. Creating generic BaseAgent."
                )
                # Ensure the config passed to BaseAgent is valid for it.
                # If AgentConfig is directly usable by BaseAgent, this is fine.
                agent_instance_obj = BaseAgent(**common_kwargs)
                logger.info(
                    f"Created generic BaseAgent as placeholder for {agent_type_enum.value}"
                )

            if agent_instance_obj:
                logger.info(
                    f"Successfully created agent '{agent_id}' of type '{agent_type_enum.value}'"
                )
            return agent_instance_obj

        except Exception as e:
            logger.error(
                f"Failed to create agent instance for ID '{agent_id}', type '{agent_type_enum.value}': {e}",
                exc_info=True,
            )
            return None

    async def get_agent_instance(
        self, agent_id: str, agent_config: AgentConfig
    ) -> Optional[BaseAgent]:
        if agent_id not in self.active_agents:
            logger.info(f"Agent '{agent_id}' not active. Attempting to create...")
            agent_instance = await self._create_agent_instance(agent_id, agent_config)
            if agent_instance:
                self.active_agents[agent_id] = agent_instance
                self.agent_configs[agent_id] = agent_config
            else:
                logger.error(
                    f"Failed to create and retrieve agent instance for '{agent_id}'"
                )
                return None
        return self.active_agents.get(agent_id)

    async def execute_agent_task(
        self,
        agent_id: str,  # Can be a friendly name or a specific ID
        agent_config: AgentConfig,  # Config to use if agent needs to be created
        task_description: str,  # For agents that take a descriptive task
        parameters: Dict[str, Any],  # Parameters for the agent's task method
        # task_type: str, # This seems to be more for the direct agent.execute_task(AgentTask)
    ) -> Dict[str, Any]:
        async with self.task_semaphore:
            # If agent_id is more of a type/role, ensure agent_config.agent_id is set or use it
            effective_agent_id = agent_config.agent_id or agent_id

            agent = await self.get_agent_instance(effective_agent_id, agent_config)
            if not agent:
                return {
                    "success": False,
                    "error": f"Agent {effective_agent_id} could not be initialized or retrieved.",
                }

            try:
                # The design implies agents have an execute_task method that takes an AgentTask object.
                # Or, a more generic "run" or "process" method.
                # Let's assume a generic method based on agent_config.agent_type for now,
                # or a direct call to a method named in task_description if that's the convention.

                # This part needs clarification on how agent tasks are dispatched.
                # If agents are expected to have methods matching `task_description` or a common `process(params)`:
                if hasattr(agent, task_description) and callable(
                    getattr(agent, task_description)
                ):
                    # Assuming task_description is a method name and parameters are its args
                    result = await getattr(agent, task_description)(**parameters)
                elif hasattr(agent, "process_task"):  # A common method name
                    result = await agent.process_task(task_description, parameters)
                elif hasattr(agent, "run"):  # Fallback
                    result = await agent.run(task_description, parameters)
                else:
                    # If using the AgentTask structure:
                    # task_obj = AgentTask(task_id=str(uuid.uuid4()), agent_type=agent_config.agent_type, task_type=task_description, parameters=parameters)
                    # result = await agent.execute_task(task_obj)
                    logger.error(
                        f"Agent {effective_agent_id} (type {agent_config.agent_type.value}) lacks a suitable method for task '{task_description}' or a generic handler."
                    )
                    return {
                        "success": False,
                        "error": "Agent task execution method not found.",
                    }

                # Assuming result from agent is directly usable or wrapped in a dict by the agent.
                # If the agent returns a complex object, it should be serialized to dict here or by agent.
                if isinstance(result, dict) and "success" in result:
                    return result
                else:
                    return {"success": True, "data": result}

            except asyncio.TimeoutError:
                logger.error(f"Task timed out for agent {effective_agent_id}")
                return {
                    "success": False,
                    "error": f"Task timed out for agent {effective_agent_id}",
                }
            except Exception as e:
                logger.error(
                    f"Error executing task on agent {effective_agent_id}: {e}",
                    exc_info=True,
                )
                return {
                    "success": False,
                    "error": f"Error on agent {effective_agent_id}: {str(e)}",
                }

    async def execute_mcp_tool(
        self,
        mcp_server_name: str,
        task_type: str,  # This is the 'tool_name' for MCPClient
        parameters: Dict[str, Any],
        request_timeout: Optional[float] = None,  # MCPClient has per-call timeout
    ) -> Dict[str, Any]:
        """
        Executes a tool on a specified MCP server using the MultiServerMCPClient.
        Handles session management and error reporting.
        """
        if not self.mcp_client:
            logger.error("MCP client is not initialized. Cannot execute MCP tool.")
            return {"success": False, "error": "MCP client not initialized"}

        logger.info(
            f"Attempting to execute MCP tool '{task_type}' on server '{mcp_server_name}' with params: {parameters}"
        )

        try:
            # MultiServerMCPClient's get_tools() can be used to get a specific tool
            # or all tools. For a single tool execution, we might need to adjust
            # how tools are fetched or invoked if direct invocation like this isn't supported.
            # This assumes a method like `invoke_tool` or similar exists,
            # or that `get_tools` can be filtered and the tool invoked.
            # For now, we adapt to how tools are typically invoked via the client.

            # The MultiServerMCPClient is designed to get *all* tools from a server (or all servers)
            # and then you use them. It doesn't have a direct "invoke_tool_on_server" method.
            # We need to get the tools for the specific server first.

            async with self.mcp_client.session(mcp_server_name) as session:
                # Load tools for the specific session
                tools = await load_mcp_tools(session)

                # Find the specific tool
                target_tool = None
                for tool in tools:
                    # Tool names from MultiServerMCPClient might be prefixed, e.g., "server_name.tool_name"
                    # Or, if loading from a session for a specific server, it might just be "tool_name"
                    # We need to confirm the naming convention.
                    # For now, let's assume task_type is the direct tool name.
                    if tool.name == task_type or tool.name.endswith(f".{task_type}"):
                        target_tool = tool
                        break

                if not target_tool:
                    logger.error(f"Tool '{task_type}' not found on server '{mcp_server_name}'. Available: {[t.name for t in tools]}")
                    return {
                        "success": False,
                        "error": f"Tool '{task_type}' not found on server '{mcp_server_name}'",
                    }

                # Execute the tool
                # The actual invocation depends on how LangChain tools are structured by the adapter
                logger.info(f"Invoking tool '{target_tool.name}' with parameters: {parameters}")
                result = await target_tool.ainvoke(parameters, timeout=request_timeout)

            logger.info(
                f"MCP tool '{task_type}' on server '{mcp_server_name}' executed successfully. Result: {result}"
            )
            # Ensure result is serializable, often tools return Pydantic models or strings
            if hasattr(result, 'dict'):
                return {"success": True, "result": result.dict()}
            elif isinstance(result, (str, dict, list, int, float, bool, type(None))):
                return {"success": True, "result": result}
            else:
                return {"success": True, "result": str(result)}

        except Exception as e:  # Catching a more generic exception
            error_type = type(e).__name__
            error_message = str(e)
            logger.error(
                f"Generic Exception ({error_type}) for server '{mcp_server_name}' tool '{task_type}': {error_message}",
                exc_info=True,
            )
            return {
                "success": False,
                "error": f"MCP tool execution failed: {error_type} - {error_message}",
            }

    async def shutdown_agent(self, agent_id: str):
        if agent_id in self.active_agents:
            agent = self.active_agents.pop(agent_id)
            self.agent_configs.pop(agent_id, None)
            if hasattr(agent, "shutdown") and callable(agent.shutdown):
                try:
                    await agent.shutdown()
                    logger.info(f"Agent {agent_id} shutdown method called.")
                except Exception as e:
                    logger.error(
                        f"Error during agent {agent_id} shutdown: {e}", exc_info=True
                    )
            logger.info(f"Agent {agent_id} instance removed from active pool.")
        else:
            logger.warning(
                f"Attempted to shutdown non-existent or inactive agent: {agent_id}"
            )

    async def close(self):
        """Gracefully close all resources, including MCP client and HTTP client."""
        logger.info("Shutting down AgentCoordinator...")

        # Close the MultiServerMCPClient
        if self.mcp_client:
            try:
                # MultiServerMCPClient uses an async context manager internally for sessions,
                # but direct close method might be available or needed if not used with 'async with'.
                # Checking langchain_mcp_adapters for specific close/cleanup method.
                # Typically, an 'aclose' or similar method is provided for async clients.
                # If it manages server processes, it should shut them down.
                if hasattr(self.mcp_client, "aclose"):
                    await self.mcp_client.aclose()
                elif hasattr(
                    self.mcp_client, "close"
                ):  # Fallback for sync close, though unlikely for this client
                    self.mcp_client.close()
                logger.info("MultiServerMCPClient closed.")
            except Exception as e:
                logger.error(f"Error closing MultiServerMCPClient: {e}", exc_info=True)
            self.mcp_client = None

        # Close the shared HTTP client
        if self.http_client:
            await self.http_client.aclose()
            logger.info("AgentCoordinator's HTTP client closed.")

        logger.info("AgentCoordinator closed.")


# Example AgentConfig (ensure this matches your actual definition in core.base_agent)
# from pydantic import BaseModel, Field
# import uuid # Required if using default_factory for agent_id
# class AgentConfig(BaseModel):
#     agent_id: str = Field(default_factory=lambda: f"agent_{uuid.uuid4().hex[:8]}")
#     agent_type: AgentType # This should refer to your AgentType Enum
#     system_prompt: Optional[str] = None
#     # other config fields like model_name, temperature, etc., if they are per-agent

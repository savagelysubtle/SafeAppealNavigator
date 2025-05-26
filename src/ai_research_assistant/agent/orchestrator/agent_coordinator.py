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

import httpx  # Added for MCP tool communication

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
    agent_instance: Any
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

        self.mcp_servers_config: Dict[str, Any] = {}
        self._load_mcp_config(mcp_config_path)

        # Shared HTTP client for MCP communication and potentially other HTTP tasks
        # Configure with appropriate timeouts
        client_timeout = httpx.Timeout(
            timeout_seconds, connect=10.0
        )  # Overall timeout, connect timeout
        self.http_client = httpx.AsyncClient(timeout=client_timeout)

        # Placeholder for managing concurrent agent tasks, if needed beyond simple dict
        self.task_semaphore = asyncio.Semaphore(max_concurrent)

        logger.info(
            f"AgentCoordinator initialized. Max concurrent agents: {max_concurrent}, Timeout: {timeout_seconds}s"
        )
        if not self.mcp_servers_config:
            logger.warning(
                "MCP server configurations are empty or failed to load. MCP tools may be unavailable."
            )

    def _load_mcp_config(self, config_path: str):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                self.mcp_servers_config = json.load(f)
            if not isinstance(self.mcp_servers_config, dict):
                logger.error(
                    f"MCP config from {config_path} is not a dictionary. Resetting to empty."
                )
                self.mcp_servers_config = {}
            else:
                logger.info(
                    f"Successfully loaded MCP server configurations from {config_path}"
                )
        except FileNotFoundError:
            logger.error(
                f"MCP server configuration file not found: {config_path}. MCP tools will be unavailable."
            )
            self.mcp_servers_config = {}
        except json.JSONDecodeError as e:
            logger.error(
                f"Error decoding JSON from MCP server configuration file: {config_path}: {e}. MCP tools will be unavailable."
            )
            self.mcp_servers_config = {}
        except Exception as e:
            logger.error(
                f"An unexpected error occurred while loading MCP server configurations from {config_path}: {e}"
            )
            self.mcp_servers_config = {}

    async def _create_agent_instance(
        self, agent_id: str, agent_config: AgentConfig
    ) -> Optional[BaseAgent]:
        """
        Creates and initializes a specific agent instance based on AgentConfig.
        """
        agent_type_enum = (
            agent_config.agent_type
        )  # This should be an AgentType enum member

        if not isinstance(agent_type_enum, AgentType):
            try:  # Attempt to convert from string if necessary, though agent_config.agent_type should already be enum
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
            "agent_coordinator": self,  # Pass self to agents
        }

        agent_instance_obj: Optional[BaseAgent] = None
        try:
            if agent_type_enum == AgentType.INTAKE:
                logger.info(
                    f"Creating EnhancedLegalIntakeAgent instance for {agent_type_enum.value}"
                )
                # EnhancedLegalIntakeAgent might have specific args not in common_kwargs, handle as needed
                # For now, assuming common_kwargs are sufficient or handled by its **kwargs
                agent_instance_obj = EnhancedLegalIntakeAgent(**common_kwargs)
            # elif agent_type_enum == AgentType.LEGAL_RESEARCH:
            #     logger.info(f"Creating LegalResearchAgent instance for {agent_type_enum.value}")
            #     agent_instance_obj = LegalResearchAgent(**common_kwargs)
            # Add other specific agent types here
            elif (
                agent_type_enum == AgentType.PLACEHOLDER or True
            ):  # Fallback for undefined types
                logger.warning(
                    f"Agent type '{agent_type_enum.value}' not specifically handled or is PLACEHOLDER. Creating AgentPlaceholder."
                )
                # Note: AgentPlaceholder is not a BaseAgent subclass in this example, adjust if it should be
                # For this example, we'll skip creating a BaseAgent type for it to avoid type errors if it's not.
                # If AgentPlaceholder is to be managed like other agents, it should inherit BaseAgent.
                # This part might need adjustment based on AgentPlaceholder's actual class definition.
                # For now, let's assume we don't add it to self.active_agents if it's not a BaseAgent.
                # Or, create a simple BaseAgent wrapper if needed.
                # To keep it simple, if we want a placeholder in active_agents, it needs to be a BaseAgent:
                placeholder_config = AgentConfig(
                    agent_id=agent_id,
                    agent_type=agent_type_enum,
                    system_prompt="Placeholder",
                )
                agent_instance_obj = BaseAgent(
                    **common_kwargs, config=placeholder_config
                )  # Generic BaseAgent as placeholder
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
        agent_id: str,
        agent_config: AgentConfig,
        task_description: str,
        parameters: Dict[str, Any],
    ) -> Dict[str, Any]:
        async with self.task_semaphore:
            agent = await self.get_agent_instance(agent_id, agent_config)
            if not agent:
                return {
                    "success": False,
                    "error": f"Agent {agent_id} could not be initialized or retrieved.",
                }

            try:
                # Assuming BaseAgent and its subclasses have an async run method
                # result = await agent.run(task_description=task_description, parameters=parameters)
                # For now, let's assume a generic 'process' method or similar
                if hasattr(agent, "process_task"):  # Example method name
                    result = await agent.process_task(task_description, parameters)
                elif hasattr(agent, "run"):
                    result = await agent.run(
                        task_description, parameters
                    )  # Fallback to run
                else:
                    logger.error(
                        f"Agent {agent_id} of type {agent_config.agent_type.value} does not have a 'process_task' or 'run' method."
                    )
                    return {
                        "success": False,
                        "error": "Agent task execution method not found.",
                    }
                return {"success": True, "data": result}
            except asyncio.TimeoutError:
                logger.error(f"Task timed out for agent {agent_id}")
                return {
                    "success": False,
                    "error": f"Task timed out for agent {agent_id}",
                }
            except Exception as e:
                logger.error(
                    f"Error executing task on agent {agent_id}: {e}", exc_info=True
                )
                return {"success": False, "error": f"Error on agent {agent_id}: {e}"}

    async def execute_mcp_tool(
        self,
        mcp_server_name: str,  # This is a STRING, e.g., "filesystem_server"
        task_type: str,  # This is the specific tool/endpoint on the MCP server, e.g., "write_file"
        parameters: Dict[str, Any],
        request_timeout: Optional[float] = None,  # Specific timeout for this request
    ) -> Dict[str, Any]:
        """
        Executes a tool on a specified MCP server.
        This method communicates directly with MCP tool servers and DOES NOT use AgentType for mcp_server_name.
        """
        if not self.mcp_servers_config:
            logger.error(
                "MCP server configurations not loaded or empty. Cannot execute MCP tool."
            )
            return {"success": False, "error": "MCP configurations not loaded."}

        server_details = self.mcp_servers_config.get(mcp_server_name)
        if not server_details:
            logger.error(
                f"MCP server '{mcp_server_name}' not found in configuration. Available: {list(self.mcp_servers_config.keys())}"
            )
            return {
                "success": False,
                "error": f"MCP server '{mcp_server_name}' not configured.",
            }

        if not isinstance(server_details, dict) or "url" not in server_details:
            logger.error(
                f"Configuration for MCP server '{mcp_server_name}' is malformed (must be a dict with a 'url' key)."
            )
            return {
                "success": False,
                "error": f"Malformed configuration for MCP server '{mcp_server_name}'.",
            }

        base_url = server_details["url"]
        # Convention: MCP tools might be at /tools/{task_type} or just /{task_type}
        # The example mcp_servers.json implies the server itself is the endpoint for different tools.
        # Let's assume the task_type is part of the payload or the server routes based on a 'tool' field in params.
        # For a generic MCP client, often the endpoint is fixed and the payload specifies the tool.
        # If the URL itself needs to change per task_type, this needs adjustment.
        # For now, let's assume the base_url is the endpoint and the payload specifies the tool.
        # Or, a common pattern: POST to base_url, payload: {"tool": task_type, "params": parameters}

        # Let's use a convention like base_url/task_type if tools are distinct endpoints
        # Or if server has one endpoint, then task_type goes into payload.
        # Assuming distinct endpoints for now, like http://mcp_server_url/write_file
        tool_url = f"{base_url.rstrip('/')}/{task_type}"

        payload = parameters  # Direct parameters, or wrap if MCP server expects {"tool": task_type, "params": parameters}

        try:
            logger.info(
                f"Executing MCP tool: Server='{mcp_server_name}', URL='{tool_url}', Task='{task_type}'"
            )
            logger.debug(f"MCP Payload: {json.dumps(payload, indent=2)}")

            current_timeout = self.http_client.timeout  # Default client timeout
            if request_timeout is not None:
                # httpx.Timeout can take a single float for all timeouts or a Timeout object
                effective_timeout = httpx.Timeout(request_timeout)
            else:
                effective_timeout = current_timeout

            response = await self.http_client.post(
                tool_url, json=payload, timeout=effective_timeout
            )
            response.raise_for_status()  # Raise an exception for HTTP error codes (4xx or 5xx)

            response_data = response.json()
            logger.info(
                f"Successfully executed MCP tool '{task_type}' on server '{mcp_server_name}'. Status: {response.status_code}"
            )

            if not isinstance(response_data, dict):
                logger.warning(
                    f"MCP tool response from {tool_url} was not a dict: {type(response_data)}. Body: {response.text[:200]}"
                )
                # Attempt to wrap if it's a simple success (e.g. plain string "OK")
                return {
                    "success": False,
                    "error": "Invalid response format from MCP tool (not a dict).",
                    "raw_response_text": response.text,
                }

            # If response_data doesn't inherently have a "success" field, we might infer it or expect it.
            # For now, assume the returned dict is the result.
            return response_data

        except httpx.TimeoutException as e:
            logger.error(
                f"Timeout while calling MCP tool '{task_type}' on '{mcp_server_name}' at '{tool_url}': {e}"
            )
            return {"success": False, "error": f"Timeout calling MCP tool: {str(e)}"}
        except httpx.ConnectError as e:
            logger.error(
                f"Connection error while calling MCP tool '{task_type}' on '{mcp_server_name}' at '{tool_url}': {e}"
            )
            return {
                "success": False,
                "error": f"Connection error calling MCP tool: {str(e)}",
            }
        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error {e.response.status_code} while calling MCP tool '{task_type}' on '{mcp_server_name}' at '{tool_url}': {e.response.text[:500]}"
            )
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code} from MCP tool: {e.response.text[:100]}",
                "details": e.response.text,
            }
        except httpx.RequestError as e:  # Catch-all for other httpx request issues
            logger.error(
                f"Request error while calling MCP tool '{task_type}' on '{mcp_server_name}' at '{tool_url}': {e}"
            )
            return {
                "success": False,
                "error": f"Request error calling MCP tool: {str(e)}",
            }
        except json.JSONDecodeError as e:
            logger.error(
                f"Failed to decode JSON response from MCP tool '{task_type}' on '{mcp_server_name}' at '{tool_url}': {e}. Response text: {response.text[:500]}"
            )
            return {
                "success": False,
                "error": f"JSON decode error from MCP tool: {str(e)}",
                "raw_response_text": response.text if "response" in locals() else "N/A",
            }
        except Exception as e:
            logger.error(
                f"Unexpected error executing MCP tool '{task_type}' on '{mcp_server_name}' at '{tool_url}': {e}",
                exc_info=True,
            )
            return {"success": False, "error": f"Unexpected error: {str(e)}"}

    async def shutdown_agent(self, agent_id: str):
        if agent_id in self.active_agents:
            agent = self.active_agents.pop(agent_id)
            self.agent_configs.pop(agent_id, None)
            if hasattr(
                agent, "shutdown"
            ):  # Assuming agents might have a shutdown method
                await agent.shutdown()
            logger.info(f"Agent {agent_id} has been shutdown and removed.")
        else:
            logger.warning(
                f"Attempted to shutdown non-existent or inactive agent: {agent_id}"
            )

    async def close(self):
        """Clean up resources, like the HTTP client and active agents."""
        logger.info("AgentCoordinator attempting to close...")
        # Shutdown all active agents
        active_agent_ids = list(self.active_agents.keys())
        for agent_id in active_agent_ids:
            logger.info(f"Shutting down agent {agent_id} during coordinator close...")
            await self.shutdown_agent(agent_id)

        if self.http_client:
            await self.http_client.aclose()
            logger.info("AgentCoordinator's HTTP client closed.")
        logger.info("AgentCoordinator closed.")


# Example AgentConfig (ensure this matches your actual definition)
# from pydantic import BaseModel, Field
# class AgentConfig(BaseModel):
#     agent_id: str = Field(default_factory=lambda: f"agent_{uuid.uuid4().hex[:8]}")
#     agent_type: AgentType
#     system_prompt: Optional[str] = None
#     # other config fields

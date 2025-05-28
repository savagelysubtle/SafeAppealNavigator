import inspect
import json
import logging
import os
from typing import Any, Awaitable, Callable, Dict, List, Optional, Type, TypeVar, Union

from browser_use.agent.views import ActionModel, ActionResult
from browser_use.browser.context import BrowserContext
from browser_use.controller.registry.service import RegisteredAction
from browser_use.controller.service import Controller
from browser_use.utils import time_execution_sync
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools
from pydantic import BaseModel, create_model

from src.ai_research_assistant.config import mcp_config

logger = logging.getLogger(__name__)

Context = TypeVar("Context")


class CustomController(Controller):
    def __init__(
        self,
        exclude_actions: list[str] = [],
        output_model: Optional[Type[BaseModel]] = None,
        ask_assistant_callback: Optional[
            Union[
                Callable[[str, BrowserContext], Dict[str, Any]],
                Callable[[str, BrowserContext], Awaitable[Dict[str, Any]]],
            ]
        ] = None,
        mcp_server_config_data: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(exclude_actions=exclude_actions, output_model=output_model)
        self._register_custom_actions()
        self.ask_assistant_callback = ask_assistant_callback

        self.mcp_client: Optional[MultiServerMCPClient] = None
        self.mcp_server_config: Optional[Dict[str, Any]] = mcp_server_config_data

        if self.mcp_server_config is None:
            logger.info(
                "MCP server config not provided at CustomController init. Will be loaded by setup_mcp_client."
            )

    def _register_custom_actions(self):
        """Register all custom browser actions"""

        @self.registry.action(
            "When executing tasks, prioritize autonomous completion. However, if you encounter a definitive blocker "
            "that prevents you from proceeding independently – such as needing credentials you don't possess, "
            "requiring subjective human judgment, needing a physical action performed, encountering complex CAPTCHAs, "
            "or facing limitations in your capabilities – you must request human assistance."
        )
        async def ask_for_assistant(query: str, browser: BrowserContext):
            if self.ask_assistant_callback:
                if inspect.iscoroutinefunction(self.ask_assistant_callback):
                    user_response = await self.ask_assistant_callback(query, browser)
                else:
                    user_response = self.ask_assistant_callback(query, browser)
                msg = f"AI ask: {query}. User response: {user_response.get('response', 'No response') if isinstance(user_response, dict) else str(user_response)}"
                logger.info(msg)
                return ActionResult(extracted_content=msg, include_in_memory=True)
            else:
                return ActionResult(
                    extracted_content="Human cannot help you. Please try another way.",
                    include_in_memory=True,
                )

        @self.registry.action(
            "Upload file to interactive element with file path ",
        )
        async def upload_file(
            index: int,
            path: str,
            browser: BrowserContext,
            available_file_paths: list[str],
        ):
            if path not in available_file_paths:
                return ActionResult(error=f"File path {path} is not available")

            if not os.path.exists(path):
                return ActionResult(error=f"File {path} does not exist")

            dom_el = await browser.get_dom_element_by_index(index)

            file_upload_dom_el = dom_el.get_file_upload_element()

            if file_upload_dom_el is None:
                msg = f"No file upload element found at index {index}"
                logger.info(msg)
                return ActionResult(error=msg)

            file_upload_el = await browser.get_locate_element(file_upload_dom_el)

            if file_upload_el is None:
                msg = f"No file upload element found at index {index}"
                logger.info(msg)
                return ActionResult(error=msg)

            try:
                await file_upload_el.set_input_files(path)
                msg = f"Successfully uploaded file to index {index}"
                logger.info(msg)
                return ActionResult(extracted_content=msg, include_in_memory=True)
            except Exception as e:
                msg = f"Failed to upload file to index {index}: {str(e)}"
                logger.info(msg)
                return ActionResult(error=msg)

    @time_execution_sync("--act")
    async def act(
        self,
        action: ActionModel,
        browser_context: Optional[BrowserContext] = None,
        page_extraction_llm: Optional[BaseChatModel] = None,
        sensitive_data: Optional[Dict[str, str]] = None,
        available_file_paths: Optional[list[str]] = None,
        context: Context | None = None,
    ) -> ActionResult:
        """Execute an action, handling both standard and MCP tools."""
        try:
            # action.model_dump() is preferred for Pydantic v2
            # Use exclude_unset=True if you only want explicitly set fields
            action_data = action.model_dump(exclude_unset=True)

            for action_name, params in action_data.items():
                if (
                    params is None
                ):  # Skip if params are None, though model_dump usually excludes them if unset
                    continue

                # Tools from langchain-mcp-adapters are prefixed (e.g., "mcp_serverName_toolName")
                if action_name.startswith("mcp_"):
                    logger.debug(
                        f"Attempting to execute SDK-based MCP tool: {action_name} with params: {params}"
                    )
                    registered_action = self.registry.registry.actions.get(action_name)

                    if registered_action is None:
                        logger.error(
                            f"MCP tool {action_name} not found in CustomController registry."
                        )
                        return ActionResult(
                            error=f"MCP tool {action_name} not found in registry."
                        )

                    # The 'function' attribute now holds the BaseTool instance
                    mcp_tool_instance = registered_action.function
                    if not isinstance(mcp_tool_instance, BaseTool):
                        logger.error(
                            f"Registered item for {action_name} in CustomController is not a BaseTool instance. Type: {type(mcp_tool_instance)}"
                        )
                        return ActionResult(
                            error=f"Invalid MCP tool setup for {action_name}."
                        )

                    try:
                        # `params` should be the dictionary of arguments for the tool
                        # BaseTool.ainvoke expects a dictionary or a single string/object depending on the tool
                        tool_output = await mcp_tool_instance.ainvoke(params)

                        # Adapt tool_output to ActionResult
                        # LangChain tools typically return a string or a structured dict.
                        if isinstance(tool_output, dict):
                            # Attempt to serialize dicts to JSON strings for consistent ActionResult content
                            # unless a more specific handling is needed for certain dict structures.
                            result_content = json.dumps(tool_output)
                        elif isinstance(tool_output, str):
                            result_content = tool_output
                        elif tool_output is None:
                            result_content = (
                                "MCP tool executed successfully with no direct output."
                            )
                        else:
                            result_content = str(
                                tool_output
                            )  # Fallback for other types

                        logger.info(
                            f"MCP tool {action_name} executed. Output type: {type(tool_output)}, Content snippet: {result_content[:100]}"
                        )
                        return ActionResult(
                            extracted_content=result_content, include_in_memory=True
                        )
                    except Exception as e:
                        logger.error(
                            f"Error executing MCP tool {action_name} via CustomController: {e}",
                            exc_info=True,
                        )
                        return ActionResult(
                            error=f"Failed to execute MCP tool {action_name}: {str(e)}"
                        )
                else:
                    # Existing non-MCP tool execution logic
                    # Ensure this part correctly calls super().registry.execute_action or similar
                    # if the original controller class had its own action execution beyond just the registry.
                    # Based on provided code, self.registry.execute_action is the way.
                    logger.debug(
                        f"Executing standard action: {action_name} with params: {params}"
                    )
                    result = await self.registry.execute_action(
                        action_name,
                        params,
                        browser=browser_context,
                        page_extraction_llm=page_extraction_llm,
                        sensitive_data=sensitive_data,
                        available_file_paths=available_file_paths,
                        context=context,
                    )

                    if isinstance(result, str):
                        return ActionResult(extracted_content=result)
                    elif isinstance(result, ActionResult):
                        return result
                    elif result is None:
                        # Ensure consistent handling of None results for standard actions too
                        return ActionResult(
                            extracted_content=f"Action {action_name} completed with no output."
                        )
                    else:
                        # This case should ideally not be hit if actions always return ActionResult or string
                        logger.warning(
                            f"Unexpected action result type for {action_name}: {type(result)}"
                        )
                        return ActionResult(extracted_content=str(result))

            # Fallback if action_data was empty or no action matched
            logger.warning(f"No action was executed from ActionModel: {action_data}")
            return ActionResult(error="No action specified or matched.")

        except Exception as e:
            logger.error(
                f"Error during CustomController act method: {e}", exc_info=True
            )
            # It's generally good to re-raise unexpected errors or return a generic error ActionResult
            # depending on the desired error propagation strategy.
            # For now, returning an ActionResult to keep flow consistent.
            return ActionResult(
                error=f"An unexpected error occurred in controller: {str(e)}"
            )

    async def setup_mcp_client(
        self, mcp_server_config_override: Optional[Dict[str, Any]] = None
    ):
        """
        Initializes the MultiServerMCPClient and registers discovered tools.
        mcp_server_config_override is for dynamic updates, e.g., from UI.
        """
        if mcp_server_config_override is not None:
            self.mcp_server_config = (
                mcp_server_config_override  # Store the raw full structure
            )
            server_connections_dict = self.mcp_server_config.get("mcp_servers", {})
            logger.info(
                "Using overridden MCP server configuration for CustomController."
            )
        elif (
            self.mcp_server_config
        ):  # If already loaded (e.g., by __init__ or previous call)
            server_connections_dict = self.mcp_server_config.get("mcp_servers", {})
            logger.info("Using existing MCP server configuration in CustomController.")
        else:  # Load from default path if not overridden or pre-loaded
            # Use the globally instantiated mcp_config loader
            full_loaded_config = mcp_config.load_mcp_config()
            self.mcp_server_config = full_loaded_config  # Store the raw full structure
            server_connections_dict = full_loaded_config.get("mcp_servers", {})
            logger.info(
                "Loaded MCP server configuration from default path for CustomController."
            )

        if not server_connections_dict:
            logger.warning(
                "No MCP server configurations provided or found in CustomController. MCP tools will be unavailable."
            )
            if (
                self.mcp_client
            ):  # Ensure old client is closed if we are effectively disabling MCP
                await self.close_mcp_client()
            self.mcp_client = None
            # Clear previously registered MCP tools
            self.registry.registry.actions = {
                k: v
                for k, v in self.registry.registry.actions.items()
                if not k.startswith("mcp_")
            }
            return

        try:
            # Ensure any existing client resources are cleaned up before creating a new one.
            if self.mcp_client:
                logger.info("Closing existing MCP client before re-initializing.")
                await self.close_mcp_client()

            self.mcp_client = MultiServerMCPClient(connections=server_connections_dict)
            logger.info(
                f"MultiServerMCPClient initialized in CustomController with {len(server_connections_dict)} server configurations."
            )
            await self.register_mcp_tools()  # Register tools from the new client
        except Exception as e:
            logger.error(
                f"Failed to initialize MultiServerMCPClient in CustomController: {e}",
                exc_info=True,
            )
            if self.mcp_client:  # Attempt cleanup if partial init failed
                await self.close_mcp_client()
            self.mcp_client = None
            # Clear previously registered MCP tools
            self.registry.registry.actions = {
                k: v
                for k, v in self.registry.registry.actions.items()
                if not k.startswith("mcp_")
            }

    async def register_mcp_tools(self):
        """
        Register the MCP tools discovered via MultiServerMCPClient.
        Tools are registered as LangChain BaseTool instances.
        """
        if not self.mcp_client:
            logger.warning(
                "MCP client not initialized in CustomController. Cannot register MCP tools."
            )
            return

        # Clear previously registered MCP tools to avoid duplicates on re-registration
        self.registry.registry.actions = {
            key: value
            for key, value in self.registry.registry.actions.items()
            if not key.startswith(
                "mcp_"
            )  # Assuming SDK tools are prefixed with "mcp_" by langchain-mcp-adapters
        }
        logger.info(
            "Cleared previously registered MCP tools from CustomController action registry."
        )

        all_sdk_tools: List[BaseTool] = []
        # Ensure self.mcp_client.connections is not None before iterating
        if not self.mcp_client.connections:
            logger.warning(
                "MCP client connections are None. Cannot register MCP tools."
            )
            return

        active_server_names = list(self.mcp_client.connections.keys())

        for server_name in active_server_names:
            try:
                # Check if server is disabled in its config (MultiServerMCPClient might still list it from initial config)
                # Access the server's specific config from the raw self.mcp_server_config
                server_conf_dict = (
                    self.mcp_server_config.get("mcp_servers", {}).get(server_name)
                    if self.mcp_server_config
                    else None
                )

                if server_conf_dict and server_conf_dict.get("disabled", False):
                    logger.info(
                        f"Server '{server_name}' is disabled in config, skipping tool discovery for CustomController."
                    )
                    continue

                # It's important that self.mcp_client.session correctly handles enabled/disabled state
                # or that we rely on the config check above.
                async with self.mcp_client.session(server_name) as session:
                    # load_mcp_tools returns a list of LangChain BaseTool objects
                    server_tools: List[BaseTool] = await load_mcp_tools(session)
                    all_sdk_tools.extend(server_tools)
                    logger.info(
                        f"Discovered {len(server_tools)} tools from server '{server_name}' for CustomController: {[t.name for t in server_tools]}"
                    )
            except Exception as e:
                # Log details including server_name for easier debugging
                logger.error(
                    f"Failed to discover tools from server '{server_name}' in CustomController: {e}",
                    exc_info=True,
                )
                # Optionally, could maintain a list of problematic servers for UI feedback

        if not all_sdk_tools:
            logger.info(
                "No MCP tools discovered from any active server by CustomController."
            )
            return

        registered_tool_count = 0
        for tool_instance in all_sdk_tools:
            # tool_instance is already a LangChain BaseTool.
            # Its name will be like 'mcp_ServerName_OriginalToolName' as per langchain-mcp-adapters.
            final_tool_name = tool_instance.name

            # The args_schema should be a Pydantic model type (Type[BaseModel])
            param_model_class: Type[BaseModel]
            if (
                hasattr(tool_instance, "args_schema")
                and isinstance(tool_instance.args_schema, type)
                and issubclass(tool_instance.args_schema, BaseModel)
            ):
                param_model_class = tool_instance.args_schema
            else:
                # If args_schema is None or not a Pydantic model type, create a default one (empty model)
                # Using a more robust way to generate a unique model name.
                model_dynamic_name = f"{''.join(c if c.isalnum() else '_' for c in final_tool_name)}Params"
                param_model_class = create_model(model_dynamic_name)  # type: ignore
                logger.warning(
                    f"Tool {final_tool_name} in CustomController lacked a Pydantic args_schema or it was invalid. Created default: {model_dynamic_name}"
                )

            # The function to be stored in RegisteredAction is the BaseTool instance itself.
            # The `act` method will later call `tool_instance.ainvoke(params)`.
            registered_action = RegisteredAction(
                name=final_tool_name,
                description=tool_instance.description,
                function=tool_instance,  # Store the BaseTool instance
                param_model=param_model_class,
            )
            self.registry.registry.actions[final_tool_name] = registered_action
            logger.info(
                f"Registered SDK tool via CustomController: {final_tool_name} with description: {tool_instance.description[:70]}..."
            )
            registered_tool_count += 1

        logger.info(
            f"CustomController successfully registered {registered_tool_count} MCP tools from SDK."
        )

    # Revised close_mcp_client() method for MultiServerMCPClient v0.1.1
    async def close_mcp_client(self):
        if self.mcp_client:
            logger.info(
                "Attempting to close MCP connections managed by MultiServerMCPClient in CustomController."
            )
            # MultiServerMCPClient v0.1.1 does not offer a public API to iterate and shut down
            # its internally managed mcp.client.Client instances.
            # Sessions are context-managed and close themselves.
            # Underlying stdio servers managed by mcp.client.Client instances
            # are typically shut down when the Client's async_shutdown() is called.
            # However, we don't have direct access to call that on all managed clients
            # through MultiServerMCPClient's public API.

            # We will log this and dereference the client.
            # For stdio servers, their lifecycle might depend on the main process or explicit
            # mcp.client.Client shutdown, which MultiServerMCPClient abstracts away here.
            logger.info(
                "MultiServerMCPClient sessions close when their contexts end. "
                "Explicit shutdown of all underlying persistent connections (e.g., stdio servers) "
                "is not directly exposed by MultiServerMCPClient v0.1.1's public API."
            )

        self.mcp_client = None  # Dereference the main client object
        logger.info(
            "MultiServerMCPClient instance in CustomController has been dereferenced."
        )

import inspect
import logging
import os
from typing import Any, Awaitable, Callable, Dict, Optional, Type, TypeVar, Union

from browser_use.agent.views import ActionModel, ActionResult
from browser_use.browser.context import BrowserContext
from browser_use.controller.registry.service import RegisteredAction
from browser_use.controller.service import Controller
from browser_use.utils import time_execution_sync
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import BaseTool
from pydantic import BaseModel, create_model

# Updated imports for MCP refactor
from src.ai_research_assistant.mcp.manager import (
    MCPManager,
    get_mcp_manager_instance,
)
from src.ai_research_assistant.config.mcp_config import MCPConfigLoader

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
    ):
        super().__init__(exclude_actions=exclude_actions, output_model=output_model)
        self._register_custom_actions()
        self.ask_assistant_callback = ask_assistant_callback
        self.mcp_manager_instance: Optional[MCPManager] = None # Changed from mcp_client
        self.mcp_server_config: Optional[Dict[str, Any]] = None

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
        #
        page_extraction_llm: Optional[BaseChatModel] = None,
        sensitive_data: Optional[Dict[str, str]] = None,
        available_file_paths: Optional[list[str]] = None,
        #
        context: Context | None = None,
    ) -> ActionResult:
        """Execute an action"""

        try:
            for action_name, params in action.model_dump(exclude_unset=True).items():
                if params is not None:
                    if action_name.startswith("mcp"):
                        logger.debug(f"Invoke MCP tool: {action_name}")
                        registered_action = self.registry.registry.actions.get(
                            action_name
                        )
                        if registered_action is None:
                            return ActionResult(
                                error=f"MCP tool {action_name} not found"
                            )

                        mcp_tool_func = registered_action.function
                        if not isinstance(mcp_tool_func, BaseTool):
                            logger.error(
                                f"Registered function for MCP tool {action_name} is not a BaseTool instance."
                            )
                            return ActionResult(
                                error=f"Invalid MCP tool configuration for {action_name}"
                            )

                        result = await mcp_tool_func.ainvoke(params)
                    else:
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
                        return ActionResult()
                    else:
                        raise ValueError(
                            f"Invalid action result type: {type(result)} of {result}"
                        )
            return ActionResult()
        except Exception as e:
            raise e

    async def setup_mcp_client(
        self, mcp_server_config: Optional[Dict[str, Any]] = None
    ):
        self.mcp_server_config = mcp_server_config
        if self.mcp_server_config and self.mcp_server_config.get(
            "enable_mcp_integration", True
        ):
            try:
                self.mcp_manager_instance = await get_mcp_manager_instance() # Changed
                if self.mcp_manager_instance and self.mcp_manager_instance.get_all_loaded_tools(): # Changed
                    self.register_mcp_tools()
                elif self.mcp_manager_instance: # Changed
                    logger.info(
                        "MCP Manager initialized, but no tools were loaded. Check mcp.json configuration and server availability."
                    )
                else:
                    logger.warning(
                        "Failed to initialize MCP Manager from mcp.manager."
                    )
            except FileNotFoundError as e:
                logger.warning(f"MCP setup skipped: {e}")
            except Exception as e:
                logger.error(f"Error during MCP client setup: {e}", exc_info=True)
        else:
            logger.info("MCP client setup skipped as per configuration.")

    def register_mcp_tools(self):
        """
        Registers MCP tools with the controller.
        It fetches all available tools from MCPManager and then filters them
        based on the current agent type using MCPConfigLoader.
        """
        if not self.mcp_manager_instance or not self.mcp_manager_instance.get_all_loaded_tools():
            logger.warning("MCP Manager not initialized or no tools loaded. Cannot register MCP tools.")
            return

        all_mcp_tools = self.mcp_manager_instance.get_all_loaded_tools()
        if not all_mcp_tools:
            logger.info("No MCP tools available from MCP Manager.")
            return

        config_loader = MCPConfigLoader()
        # TODO: Determine agent_type dynamically if CustomController is used by multiple agent types.
        # For now, using a generic placeholder. This should match a key in agent_mcp_mapping.json.
        agent_type = "CustomControllerAgent" 
        specific_tool_names = config_loader.get_agent_tools(agent_type)

        tools_to_register: List[BaseTool]
        if specific_tool_names:
            logger.info(f"Found specific tool mapping for agent type '{agent_type}'. Filtering tools: {specific_tool_names}")
            # Ensure a map for quick lookup if specific_tool_names is long
            specific_tool_names_set = set(specific_tool_names)
            tools_to_register = [t for t in all_mcp_tools if t.name in specific_tool_names_set]
            if not tools_to_register and all_mcp_tools:
                logger.warning(f"Agent type '{agent_type}' requested specific tools, but none of them were found among the loaded MCP tools. Loaded tools: {[t.name for t in all_mcp_tools]}")
        else:
            logger.info(f"No specific tool mapping found for agent type '{agent_type}'. Registering all available MCP tools ({len(all_mcp_tools)} tools).")
            tools_to_register = all_mcp_tools

        if not tools_to_register:
            logger.info(f"No MCP tools to register for agent type '{agent_type}'.")
            return

        registered_tool_count = 0
        for tool_instance in tools_to_register:
            if not isinstance(tool_instance, BaseTool):
                logger.warning(f"Skipping non-BaseTool object: {tool_instance}")
                continue

            final_tool_name = tool_instance.name

            try:
                param_model_class: Type[BaseModel]
                if tool_instance.args_schema is None:
                    logger.warning(
                        f"MCP tool {final_tool_name} has no args_schema. Creating a default one."
                    )
                    # Ensure the generated name is valid for a class
                    model_name = f"{final_tool_name.replace('_', '').replace('.', '').title()}DefaultParams"
                    param_model_class = create_model(model_name)
                else:
                    # We expect tool_instance.args_schema to be Type[BaseModel]
                    # If linter still complains, it might be a false positive or a deeper type issue
                    # with how ArgsSchema is inferred by the linter.
                    param_model_class = tool_instance.args_schema
                
                registered_action = RegisteredAction(
                    name=final_tool_name,
                    description=tool_instance.description,
                    function=tool_instance,  # Store the BaseTool instance itself
                    param_model=param_model_class,
                )
                self.registry.registry.actions[final_tool_name] = registered_action
                logger.info(
                    f"Registered MCP tool: {final_tool_name} with description: {tool_instance.description[:70]}..."
                )
                registered_tool_count += 1
            except Exception as e:
                logger.error(
                    f"Failed to register MCP tool {final_tool_name}: {e}",
                    exc_info=True,
                )
                continue
        logger.info(
            f"Successfully registered {registered_tool_count} MCP tools for agent type '{agent_type}'."
        )

    async def close_mcp_client(self):
        if self.mcp_manager_instance: # Changed
            await self.mcp_manager_instance.close_connections() # Changed to close_connections
            self.mcp_manager_instance = None # Changed
            logger.info("MCP Manager closed and resources released.")

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

from src.ai_research_assistant.utils.tool_registry import (
    ToolRegistry,
    setup_mcp_client_and_tools,
)

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
        self.mcp_client: Optional[ToolRegistry] = None
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
                self.mcp_client = await setup_mcp_client_and_tools()
                if self.mcp_client and self.mcp_client.tools:
                    self.register_mcp_tools()
                elif self.mcp_client:
                    logger.info(
                        "MCP Client initialized, but no tools were loaded. Check mcp.json configuration and server availability."
                    )
                else:
                    logger.warning(
                        "Failed to initialize MCP client from tool_registry."
                    )
            except FileNotFoundError as e:
                logger.warning(f"MCP setup skipped: {e}")
            except Exception as e:
                logger.error(f"Error during MCP client setup: {e}", exc_info=True)
        else:
            logger.info("MCP client setup skipped as per configuration.")

    def register_mcp_tools(self):
        """
        Register the MCP tools obtained from the ToolRegistry.
        """
        if self.mcp_client and self.mcp_client.tools:
            registered_tool_count = 0
            for tool_instance in self.mcp_client.tools:
                if not isinstance(tool_instance, BaseTool):
                    logger.warning(
                        f"Skipping non-BaseTool object in mcp_client.tools: {tool_instance}"
                    )
                    continue

                final_tool_name = tool_instance.name

                try:
                    param_model_class: Type[BaseModel]
                    if tool_instance.args_schema is None:
                        logger.warning(
                            f"MCP tool {final_tool_name} has no args_schema. Creating a default one."
                        )
                        param_model_class = create_model(
                            f"{final_tool_name.replace('_', '').title()}DefaultParams"
                        )
                    else:
                        param_model_class = tool_instance.args_schema

                    registered_action = RegisteredAction(
                        name=final_tool_name,
                        description=tool_instance.description,
                        function=tool_instance,
                        param_model=param_model_class,
                    )
                    self.registry.registry.actions[final_tool_name] = registered_action
                    logger.info(
                        f"Registered MCP tool: {final_tool_name} with description: {tool_instance.description[:50]}..."
                    )
                    registered_tool_count += 1
                except Exception as e:
                    logger.error(
                        f"Failed to register MCP tool {final_tool_name}: {e}",
                        exc_info=True,
                    )
                    continue
            logger.info(
                f"Registered {registered_tool_count} MCP tools from ToolRegistry."
            )
        elif self.mcp_client and not self.mcp_client.tools:
            logger.info(
                "MCP client is initialized, but no tools were found in the registry."
            )
        else:
            logger.warning(
                "MCP client not started or no tools available, cannot register MCP tools."
            )

    async def close_mcp_client(self):
        if self.mcp_client:
            await self.mcp_client.close()
            self.mcp_client = None
            logger.info("MCP client closed and resources released.")

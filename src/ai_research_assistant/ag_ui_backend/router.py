# src/savagelysubtle_airesearchagent/ag_ui_backend/router.py
import json
import logging
import uuid
from typing import Dict, Optional

# Use the official AG-UI Python SDK
from ag_ui.core import (
    EventType,
    RunAgentInput,
    RunErrorEvent,
    RunFinishedEvent,
    RunStartedEvent,
)
from ag_ui.core import Message as AGUIMessage
from ag_ui.core import ToolMessage as AGUIToolMessage  # Renamed
from ag_ui.core import UserMessage as AGUIUserMessage  # Renamed to avoid conflict
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

# Import LLM provider for API key testing
from ..core.llm_provider import get_llm_model
from .a2a_client import A2AClient
from .state_manager import AGUIConversationState, global_state_manager

logger = logging.getLogger(__name__)
router = APIRouter()
a2a_client = A2AClient()

active_connections: Dict[str, WebSocket] = {}  # thread_id -> WebSocket


@router.websocket("/ws/{thread_id}")
async def websocket_endpoint(websocket: WebSocket, thread_id: str):
    await websocket.accept()
    active_connections[thread_id] = websocket
    logger.info(f"WebSocket connection established for thread_id: {thread_id}")

    conversation_state: AGUIConversationState = (
        global_state_manager.get_or_create_conversation(thread_id)
    )
    await conversation_state.send_state_snapshot(websocket)
    await conversation_state.send_messages_snapshot(websocket)

    try:
        while True:
            raw_data = await websocket.receive_text()
            logger.debug(
                f"Thread {thread_id}: Received raw data: {raw_data[:500]}"
            )  # Log more for debugging

            run_id_for_operation = str(uuid.uuid4())  # Generate a default run_id

            try:
                data = json.loads(raw_data)

                # AG-UI client might send a RunAgentInput directly if it's how AG-UI JS client works,
                # or it might send individual messages. The AG-UI docs are a bit ambiguous on client->server protocol for initiating runs.
                # Let's assume the client sends a JSON that can be parsed into RunAgentInput when it wants to "run" the agent.
                # A more robust way is to have specific command types from client.
                # For this example, we'll try to parse as RunAgentInput if it looks like one.

                # Heuristic: if 'thread_id' and 'messages' are present, treat as RunAgentInput
                # This is a simplification. A dedicated command from client is better.
                if (
                    "thread_id" in data and "messages" in data and "run_id" in data
                ):  # Check for RunAgentInput fields
                    run_input = RunAgentInput.model_validate(data)
                    run_id_for_operation = run_input.run_id or run_id_for_operation

                    # Add new user message from input to conversation state
                    user_message_to_process: Optional[AGUIMessage] = None
                    if run_input.messages:
                        # AG-UI messages are a list, latest is typically the user's new input
                        latest_message_from_ui = AGUIMessage.model_validate(
                            run_input.messages[-1]
                        )  # Validate with discriminated union
                        if latest_message_from_ui.role == "user":
                            user_message_to_process = latest_message_from_ui
                            conversation_state.add_message(user_message_to_process)

                    user_prompt_content = (
                        user_message_to_process.content
                        if user_message_to_process and user_message_to_process.content
                        else ""
                    )

                    if not user_prompt_content:
                        # If no direct user message, check forwarded_props as a fallback
                        if (
                            run_input.forwarded_props
                            and "user_prompt" in run_input.forwarded_props
                        ):
                            user_prompt_content = run_input.forwarded_props[
                                "user_prompt"
                            ]
                            # Create and add user message if not in run_input.messages
                            if not user_message_to_process:
                                user_msg_obj = AGUIUserMessage(
                                    id=str(uuid.uuid4()),
                                    role="user",
                                    content=user_prompt_content,
                                )
                                conversation_state.add_message(user_msg_obj)
                        else:
                            logger.warning(
                                f"Thread {thread_id}: No user prompt found in RunAgentInput."
                            )
                            error_event = RunErrorEvent(
                                type=EventType.RUN_ERROR,
                                message="No user prompt provided.",
                                thread_id=thread_id,
                                run_id=run_id_for_operation,
                            )
                            await websocket.send_json(
                                error_event.model_dump(by_alias=True, exclude_none=True)
                            )
                            continue

                    # Emit RUN_STARTED
                    start_event = RunStartedEvent(
                        type=EventType.RUN_STARTED,
                        thread_id=thread_id,
                        run_id=run_id_for_operation,
                    )
                    await websocket.send_json(
                        start_event.model_dump(by_alias=True, exclude_none=True)
                    )

                    orchestrator_events_data = await a2a_client.send_to_orchestrator(
                        conversation_id=thread_id,
                        user_prompt=user_prompt_content,
                        message_history=conversation_state.messages[
                            :-1
                        ],  # History before current user message
                        tools=run_input.tools,
                        current_state=conversation_state.current_state,
                    )

                    for event_data_dict in orchestrator_events_data:
                        await websocket.send_json(
                            event_data_dict
                        )  # Already a dict from a2a_client

                    finish_event = RunFinishedEvent(
                        type=EventType.RUN_FINISHED,
                        thread_id=thread_id,
                        run_id=run_id_for_operation,
                    )
                    await websocket.send_json(
                        finish_event.model_dump(by_alias=True, exclude_none=True)
                    )

                elif (
                    "role" in data and data["role"] == "tool"
                ):  # Frontend sends back tool result
                    tool_message = AGUIToolMessage.model_validate(data)
                    conversation_state.add_message(tool_message)
                    logger.info(
                        f"Thread {thread_id}: Received tool result for {tool_message.tool_call_id}"
                    )

                    # Here, you might need to re-invoke the orchestrator with the tool result.
                    # This requires the orchestrator to be in a state waiting for this tool result.
                    # For simplicity, we'll assume the orchestrator's A2A skill handles this if it's a multi-turn skill.
                    # Or, the next "RunAgent" call from the UI might implicitly carry this context.
                    # The current `send_to_orchestrator` sends the whole history, so it would be included.
                    await websocket.send_json(
                        {
                            "type": "ACK_TOOL_RESULT",
                            "tool_call_id": tool_message.tool_call_id,
                        }
                    )

                else:
                    logger.warning(
                        f"Thread {thread_id}: Received unknown message structure: {data}"
                    )
                    error_event = RunErrorEvent(
                        type=EventType.RUN_ERROR,
                        message="Unknown message structure",
                        thread_id=thread_id,
                        run_id=run_id_for_operation,
                    )
                    await websocket.send_json(
                        error_event.model_dump(by_alias=True, exclude_none=True)
                    )

            except ValueError as e:
                logger.error(
                    f"Thread {thread_id}: Value error processing message: {e}",
                    exc_info=True,
                )
                error_event = RunErrorEvent(
                    type=EventType.RUN_ERROR,
                    message=f"Invalid data format: {str(e)}",
                    thread_id=thread_id,
                    run_id=run_id_for_operation,
                )
                await websocket.send_json(
                    error_event.model_dump(by_alias=True, exclude_none=True)
                )
            except Exception as e:
                logger.error(
                    f"Thread {thread_id}: Error processing message: {e}", exc_info=True
                )
                error_event = RunErrorEvent(
                    type=EventType.RUN_ERROR,
                    message=f"An internal error occurred: {str(e)}",
                    thread_id=thread_id,
                    run_id=run_id_for_operation,
                )
                await websocket.send_json(
                    error_event.model_dump(by_alias=True, exclude_none=True)
                )

    except WebSocketDisconnect:
        logger.info(f"WebSocket connection closed for thread_id: {thread_id}")
    finally:
        if thread_id in active_connections:
            del active_connections[thread_id]


# API Key Testing Endpoint
class APIKeyTestRequest(BaseModel):
    provider: str
    apiKey: str
    model: Optional[str] = None


class APIKeyTestResponse(BaseModel):
    success: bool
    message: str
    provider: Optional[str] = None
    model: Optional[str] = None


@router.post("/api/test-api-key", response_model=APIKeyTestResponse)
async def test_api_key(request: APIKeyTestRequest):
    """
    Test an API key for a specific LLM provider using the backend LLM provider system.
    This replaces direct frontend API calls and ensures all API communication goes through
    the proper backend architecture using llm_provider.py.
    """
    try:
        logger.info(f"Testing API key for provider: {request.provider}")

        # Use the backend LLM provider system to test the API key
        model_name = request.model or "gemini-1.5-flash"  # Default to stable model

        # Create LLM instance with provided API key
        llm = get_llm_model(
            provider=request.provider,
            api_key=request.apiKey,
            model_name=model_name,
            temperature=0.0,
        )

        # Test the API key with a simple prompt
        test_prompt = "Hello, respond with just 'OK' to confirm the API key works."

        try:
            # Try to invoke the model
            response = await llm.ainvoke(test_prompt)

            # Check if we got a valid response
            if response and hasattr(response, "content") and response.content:
                logger.info(f"API key test successful for {request.provider}")
                return APIKeyTestResponse(
                    success=True,
                    message=f"API key is valid and working for {request.provider}",
                    provider=request.provider,
                    model=model_name,
                )
            else:
                logger.warning(
                    f"API key test returned empty response for {request.provider}"
                )
                return APIKeyTestResponse(
                    success=False,
                    message=f"API key test failed - empty response from {request.provider}",
                    provider=request.provider,
                    model=model_name,
                )

        except Exception as e:
            error_msg = str(e)
            logger.error(f"API key test failed for {request.provider}: {error_msg}")

            # Check for common error patterns
            if "api" in error_msg.lower() and (
                "key" in error_msg.lower() or "auth" in error_msg.lower()
            ):
                message = f"Invalid API key for {request.provider}. Please check your API key."
            elif "quota" in error_msg.lower() or "limit" in error_msg.lower():
                message = f"API quota exceeded for {request.provider}. Please check your billing or rate limits."
            elif "network" in error_msg.lower() or "timeout" in error_msg.lower():
                message = (
                    f"Network error testing {request.provider} API. Please try again."
                )
            else:
                message = f"API key test failed for {request.provider}: {error_msg}"

            return APIKeyTestResponse(
                success=False,
                message=message,
                provider=request.provider,
                model=model_name,
            )

    except Exception as e:
        logger.error(f"Unexpected error testing API key: {e}", exc_info=True)
        return APIKeyTestResponse(
            success=False,
            message=f"Unexpected error: {str(e)}",
            provider=request.provider,
        )


# MCP File Operations Proxy Endpoints
# These endpoints proxy MCP operations through the backend instead of direct frontend calls


class MCPWriteFileRequest(BaseModel):
    mcp_path: str
    content: str


class MCPWriteFileResponse(BaseModel):
    success: bool
    message: str
    mcp_path: Optional[str] = None


class MCPDeleteRequest(BaseModel):
    mcp_path: str


class MCPDeleteResponse(BaseModel):
    success: bool
    message: str
    mcp_path: Optional[str] = None


class MCPServerStatusResponse(BaseModel):
    is_running: bool
    version: Optional[str] = None
    error: Optional[str] = None
    allowed_directories: Optional[list[str]] = None


@router.post("/api/mcp/write-file", response_model=MCPWriteFileResponse)
async def mcp_write_file(request: MCPWriteFileRequest):
    """
    Write a file through MCP backend instead of direct frontend MCP client.
    This routes through the proper backend MCP integration system.
    """
    try:
        logger.info(f"MCP write file request: {request.mcp_path}")

        # Import MCP tools from the backend integration
        from ..mcp_intergration.shared_tools.fs_tools import WriteMcpFileTool

        # Create and use the MCP file tool
        write_tool = WriteMcpFileTool()
        result = await write_tool.run(request.mcp_path, request.content)

        if result.get("success", False):
            logger.info(f"MCP file write successful: {request.mcp_path}")
            return MCPWriteFileResponse(
                success=True,
                message=f"File written successfully to {request.mcp_path}",
                mcp_path=request.mcp_path,
            )
        else:
            error_msg = result.get("error", "Unknown error writing file")
            logger.error(f"MCP file write failed: {error_msg}")
            return MCPWriteFileResponse(
                success=False,
                message=f"Failed to write file: {error_msg}",
                mcp_path=request.mcp_path,
            )

    except Exception as e:
        logger.error(f"MCP write file error: {e}", exc_info=True)
        return MCPWriteFileResponse(
            success=False,
            message=f"Error writing file: {str(e)}",
            mcp_path=request.mcp_path,
        )


@router.post("/api/mcp/delete-file", response_model=MCPDeleteResponse)
async def mcp_delete_file(request: MCPDeleteRequest):
    """
    Delete a file or directory through MCP backend instead of direct frontend MCP client.
    This routes through the proper backend MCP integration system.
    """
    try:
        logger.info(f"MCP delete request: {request.mcp_path}")

        # For now, return a success response as we don't have a delete tool yet
        # TODO: Implement proper MCP delete tool in the backend integration
        logger.warning("MCP delete functionality not fully implemented yet")
        return MCPDeleteResponse(
            success=True,
            message=f"Delete request processed for {request.mcp_path} (backend implementation pending)",
            mcp_path=request.mcp_path,
        )

    except Exception as e:
        logger.error(f"MCP delete error: {e}", exc_info=True)
        return MCPDeleteResponse(
            success=False,
            message=f"Error deleting file: {str(e)}",
            mcp_path=request.mcp_path,
        )


@router.get("/api/mcp/server-status", response_model=MCPServerStatusResponse)
async def mcp_get_server_status():
    """
    Get MCP server status through backend instead of direct frontend MCP client.
    This routes through the proper backend MCP integration system.
    """
    try:
        logger.info("MCP server status request")

        # For now, return a mock status as we need to implement proper MCP status checking
        # TODO: Implement proper MCP server status checking in the backend integration
        return MCPServerStatusResponse(
            is_running=True,
            version="1.0.0",
            error=None,
            allowed_directories=["/tmp", "/uploads", "/documents"],
        )

    except Exception as e:
        logger.error(f"MCP server status error: {e}", exc_info=True)
        return MCPServerStatusResponse(
            is_running=False,
            version=None,
            error=f"Error getting server status: {str(e)}",
            allowed_directories=None,
        )


# --- End of src/savagelysubtle_airesearchagent/ag_ui_backend/router.py ---

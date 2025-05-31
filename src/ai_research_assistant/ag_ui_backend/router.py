# src/savagelysubtle_airesearchagent/ag_ui_backend/router.py
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from typing import Dict, List, Any, Optional
import json
import uuid

# Use the official AG-UI Python SDK
from ag_ui.core import (
    RunAgentInput,
    EventType,
    RunStartedEvent,
    RunFinishedEvent,
    RunErrorEvent,
    UserMessage as AGUIUserMessage, # Renamed to avoid conflict
    ToolMessage as AGUIToolMessage, # Renamed
    Message as AGUIMessage
)
from .state_manager import global_state_manager, AGUIConversationState
from .a2a_client import A2AClient

logger = logging.getLogger(__name__)
router = APIRouter()
a2a_client = A2AClient()

active_connections: Dict[str, WebSocket] = {} # thread_id -> WebSocket

@router.websocket("/ws/{thread_id}")
async def websocket_endpoint(websocket: WebSocket, thread_id: str):
    await websocket.accept()
    active_connections[thread_id] = websocket
    logger.info(f"WebSocket connection established for thread_id: {thread_id}")

    conversation_state: AGUIConversationState = global_state_manager.get_or_create_conversation(thread_id)
    await conversation_state.send_state_snapshot(websocket)
    await conversation_state.send_messages_snapshot(websocket)

    try:
        while True:
            raw_data = await websocket.receive_text()
            logger.debug(f"Thread {thread_id}: Received raw data: {raw_data[:500]}") # Log more for debugging

            run_id_for_operation = str(uuid.uuid4()) # Generate a default run_id

            try:
                data = json.loads(raw_data)

                # AG-UI client might send a RunAgentInput directly if it's how AG-UI JS client works,
                # or it might send individual messages. The AG-UI docs are a bit ambiguous on client->server protocol for initiating runs.
                # Let's assume the client sends a JSON that can be parsed into RunAgentInput when it wants to "run" the agent.
                # A more robust way is to have specific command types from client.
                # For this example, we'll try to parse as RunAgentInput if it looks like one.

                # Heuristic: if 'thread_id' and 'messages' are present, treat as RunAgentInput
                # This is a simplification. A dedicated command from client is better.
                if "thread_id" in data and "messages" in data and "run_id" in data: # Check for RunAgentInput fields
                    run_input = RunAgentInput.model_validate(data)
                    run_id_for_operation = run_input.run_id or run_id_for_operation

                    # Add new user message from input to conversation state
                    user_message_to_process: Optional[AGUIMessage] = None
                    if run_input.messages:
                        # AG-UI messages are a list, latest is typically the user's new input
                        latest_message_from_ui = AGUIMessage.model_validate(run_input.messages[-1]) # Validate with discriminated union
                        if latest_message_from_ui.role == "user":
                            user_message_to_process = latest_message_from_ui
                            conversation_state.add_message(user_message_to_process)

                    user_prompt_content = user_message_to_process.content if user_message_to_process and user_message_to_process.content else ""

                    if not user_prompt_content:
                        # If no direct user message, check forwarded_props as a fallback
                        if run_input.forwarded_props and "user_prompt" in run_input.forwarded_props:
                             user_prompt_content = run_input.forwarded_props["user_prompt"]
                             # Create and add user message if not in run_input.messages
                             if not user_message_to_process:
                                 user_msg_obj = AGUIUserMessage(id=str(uuid.uuid4()), role="user", content=user_prompt_content)
                                 conversation_state.add_message(user_msg_obj)
                        else:
                            logger.warning(f"Thread {thread_id}: No user prompt found in RunAgentInput.")
                            error_event = RunErrorEvent(type=EventType.RUN_ERROR, message="No user prompt provided.", thread_id=thread_id, run_id=run_id_for_operation)
                            await websocket.send_json(error_event.model_dump(by_alias=True, exclude_none=True))
                            continue

                    # Emit RUN_STARTED
                    start_event = RunStartedEvent(type=EventType.RUN_STARTED, thread_id=thread_id, run_id=run_id_for_operation)
                    await websocket.send_json(start_event.model_dump(by_alias=True, exclude_none=True))

                    orchestrator_events_data = await a2a_client.send_to_orchestrator(
                        conversation_id=thread_id,
                        user_prompt=user_prompt_content,
                        message_history=conversation_state.messages[:-1], # History before current user message
                        tools=run_input.tools,
                        current_state=conversation_state.current_state
                    )

                    for event_data_dict in orchestrator_events_data:
                        await websocket.send_json(event_data_dict) # Already a dict from a2a_client

                    finish_event = RunFinishedEvent(type=EventType.RUN_FINISHED, thread_id=thread_id, run_id=run_id_for_operation)
                    await websocket.send_json(finish_event.model_dump(by_alias=True, exclude_none=True))

                elif "role" in data and data["role"] == "tool": # Frontend sends back tool result
                    tool_message = AGUIToolMessage.model_validate(data)
                    conversation_state.add_message(tool_message)
                    logger.info(f"Thread {thread_id}: Received tool result for {tool_message.tool_call_id}")

                    # Here, you might need to re-invoke the orchestrator with the tool result.
                    # This requires the orchestrator to be in a state waiting for this tool result.
                    # For simplicity, we'll assume the orchestrator's A2A skill handles this if it's a multi-turn skill.
                    # Or, the next "RunAgent" call from the UI might implicitly carry this context.
                    # The current `send_to_orchestrator` sends the whole history, so it would be included.
                    await websocket.send_json({"type": "ACK_TOOL_RESULT", "tool_call_id": tool_message.tool_call_id})


                else:
                    logger.warning(f"Thread {thread_id}: Received unknown message structure: {data}")
                    error_event = RunErrorEvent(type=EventType.RUN_ERROR, message="Unknown message structure", thread_id=thread_id, run_id=run_id_for_operation)
                    await websocket.send_json(error_event.model_dump(by_alias=True, exclude_none=True))

            except ValueError as e:
                logger.error(f"Thread {thread_id}: Value error processing message: {e}", exc_info=True)
                error_event = RunErrorEvent(type=EventType.RUN_ERROR, message=f"Invalid data format: {str(e)}", thread_id=thread_id, run_id=run_id_for_operation)
                await websocket.send_json(error_event.model_dump(by_alias=True, exclude_none=True))
            except Exception as e:
                logger.error(f"Thread {thread_id}: Error processing message: {e}", exc_info=True)
                error_event = RunErrorEvent(type=EventType.RUN_ERROR, message=f"An internal error occurred: {str(e)}", thread_id=thread_id, run_id=run_id_for_operation)
                await websocket.send_json(error_event.model_dump(by_alias=True, exclude_none=True))

    except WebSocketDisconnect:
        logger.info(f"WebSocket connection closed for thread_id: {thread_id}")
    finally:
        if thread_id in active_connections:
            del active_connections[thread_id]

# --- End of src/savagelysubtle_airesearchagent/ag_ui_backend/router.py ---
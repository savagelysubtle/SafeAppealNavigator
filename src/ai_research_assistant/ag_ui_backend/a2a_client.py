# src/ai_research_assistant/ag_ui_backend/a2a_client.py
import json  # For logging and potentially for tool arg stringification
import logging
import time  # For MessageEnvelope timestamp
import uuid
from typing import Any, Dict, List, Optional

import httpx
from ag_ui.core import (
    EventType,
    TextMessageContentEvent,
    TextMessageEndEvent,
    TextMessageStartEvent,
    ToolCallArgsEvent,
    ToolCallEndEvent,
    ToolCallStartEvent,
)

# Use the official AG-UI Python SDK
from ag_ui.core import Message as AGUIMessage
from ag_ui.core import Tool as AGUITool
from pydantic import BaseModel, Field  # For project's MessageEnvelope

from ..config.global_settings import settings

logger = logging.getLogger(__name__)


# Placeholder for your project's MessageEnvelope structure
# Replace with actual import from your project's core.models
class Part(BaseModel):
    content: Any  # Can be string or dict/list for JSON
    type: str = "text/plain"


class SkillInvocation(BaseModel):
    skill_name: str
    parameters: Dict[str, Any]


class TaskResult(BaseModel):  # Define a basic TaskResult if not already defined
    status: str = "success"
    parts: List[Part] = Field(default_factory=list)
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MessageEnvelope(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: Optional[str] = None
    task_id: Optional[str] = None
    timestamp: int = Field(default_factory=lambda: int(time.time() * 1000))
    source_agent_id: str = "ag_ui_backend"
    target_agent_id: str = "chief_legal_orchestrator"  # Default target
    skill_invocation: Optional[SkillInvocation] = None
    task_result: Optional[TaskResult] = None  # Using the defined TaskResult
    parts: List[Part] = Field(default_factory=list)  # If top-level parts are used
    metadata: Dict[str, Any] = Field(default_factory=dict)


class A2AClient:
    def __init__(
        self, orchestrator_url: str = settings.CHIEF_LEGAL_ORCHESTRATOR_A2A_URL
    ):
        self.orchestrator_url = orchestrator_url
        self.http_client = httpx.AsyncClient(timeout=60.0)

    async def send_to_orchestrator(
        self,
        conversation_id: str,
        user_prompt: str,
        message_history: List[AGUIMessage],
        tools: List[AGUITool],  # These are tool *definitions* from UI
        current_state: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        logger.info(
            f"Sending request to Orchestrator for conversation {conversation_id}. Prompt: {user_prompt[:100]}..."
        )

        a2a_parts = [Part(content=user_prompt, type="text/plain")]
        a2a_metadata = {
            "ag_ui_message_history": [
                msg.model_dump(by_alias=True, exclude_none=True)
                for msg in message_history
            ],
            "ag_ui_available_tools": [
                tool.model_dump(by_alias=True, exclude_none=True) for tool in tools
            ],
            "ag_ui_current_state": current_state,
        }

        skill_invocation = SkillInvocation(
            skill_name="handle_user_request",
            parameters={
                "user_prompt": user_prompt,
                "ag_ui_tools": a2a_metadata["ag_ui_available_tools"],
            },
        )

        # Ensure target_agent_id is just the ID, not URL, if that's how your A2A services are identified.
        # The actual URL is self.orchestrator_url.
        envelope = MessageEnvelope(
            conversation_id=conversation_id,
            skill_invocation=skill_invocation,
            parts=a2a_parts,
            metadata=a2a_metadata,
            target_agent_id="chief_legal_orchestrator",  # Logical ID
        )

        ag_ui_events_data = []
        try:
            logger.debug(
                f"A2A Request Envelope: {envelope.model_dump_json(indent=2, exclude_none=True)}"
            )
            # Assuming FastA2A endpoint for skill execution
            # The URL might be just self.orchestrator_url if it's the base for the A2A service
            # and FastA2A routes based on target_agent_id or skill_name in the envelope.
            # Or it could be a specific endpoint like /execute_skill or /task
            # Based on kickoff docs, it's likely a general A2A endpoint.
            # Let's assume the orchestrator_url is the base and FastA2A handles routing.
            response = await self.http_client.post(
                self.orchestrator_url,  # Send to base URL of the A2A service
                json=envelope.model_dump(exclude_none=True),
                timeout=120.0,
            )
            response.raise_for_status()
            orchestrator_response_data_dict = response.json()
            # Validate with MessageEnvelope if you expect a MessageEnvelope back
            orchestrator_response_envelope = MessageEnvelope(
                **orchestrator_response_data_dict
            )

            logger.info(
                f"Received response from Orchestrator: {orchestrator_response_envelope.message_id}"
            )
            logger.debug(
                f"A2A Response Envelope: {orchestrator_response_envelope.model_dump_json(indent=2, exclude_none=True)}"
            )

            task_result = orchestrator_response_envelope.task_result
            assistant_message_id = str(
                uuid.uuid4()
            )  # For the assistant's response in AG-UI

            if task_result:
                ag_ui_events_data.append(
                    TextMessageStartEvent(
                        type=EventType.TEXT_MESSAGE_START,
                        message_id=assistant_message_id,
                        role="assistant",
                    ).model_dump(by_alias=True, exclude_none=True)
                )

                streamed_any_content = False
                for part_data in task_result.parts:
                    content_type = part_data.type
                    content = part_data.content

                    if content_type == "text/plain" and isinstance(content, str):
                        ag_ui_events_data.append(
                            TextMessageContentEvent(
                                type=EventType.TEXT_MESSAGE_CONTENT,
                                message_id=assistant_message_id,
                                delta=content,
                            ).model_dump(by_alias=True, exclude_none=True)
                        )
                        streamed_any_content = True
                    elif content_type == "application/json" and isinstance(
                        content, dict
                    ):
                        # This is where you'd map structured A2A content to AG-UI tool calls or custom events
                        # Example: If Orchestrator wants UI to call a tool defined by AG-UI
                        if content.get("a2a_tool_call_request") and content.get(
                            "tool_name"
                        ) in [t.name for t in tools]:
                            tool_call_id = str(uuid.uuid4())
                            tool_name = content["tool_name"]
                            # Arguments should be a JSON string for AG-UI ToolCallArgsEvent
                            tool_args_str = json.dumps(content.get("arguments", {}))

                            ag_ui_events_data.append(
                                ToolCallStartEvent(
                                    type=EventType.TOOL_CALL_START,
                                    tool_call_id=tool_call_id,
                                    tool_call_name=tool_name,
                                ).model_dump(by_alias=True, exclude_none=True)
                            )
                            ag_ui_events_data.append(
                                ToolCallArgsEvent(
                                    type=EventType.TOOL_CALL_ARGS,
                                    tool_call_id=tool_call_id,
                                    delta=tool_args_str,
                                ).model_dump(by_alias=True, exclude_none=True)
                            )
                            ag_ui_events_data.append(
                                ToolCallEndEvent(
                                    type=EventType.TOOL_CALL_END,
                                    tool_call_id=tool_call_id,
                                ).model_dump(by_alias=True, exclude_none=True)
                            )
                            streamed_any_content = True  # A tool call is content
                        else:  # Treat other JSON as text for now
                            formatted_json = json.dumps(content, indent=2)
                            ag_ui_events_data.append(
                                TextMessageContentEvent(
                                    type=EventType.TEXT_MESSAGE_CONTENT,
                                    message_id=assistant_message_id,
                                    delta=formatted_json,
                                ).model_dump(by_alias=True, exclude_none=True)
                            )
                            streamed_any_content = True

                if not streamed_any_content:  # If no parts or no recognized content
                    status_message = task_result.status or "Task processed."
                    ag_ui_events_data.append(
                        TextMessageContentEvent(
                            type=EventType.TEXT_MESSAGE_CONTENT,
                            message_id=assistant_message_id,
                            delta=status_message,
                        ).model_dump(by_alias=True, exclude_none=True)
                    )

                ag_ui_events_data.append(
                    TextMessageEndEvent(
                        type=EventType.TEXT_MESSAGE_END, message_id=assistant_message_id
                    ).model_dump(by_alias=True, exclude_none=True)
                )

            elif (
                orchestrator_response_envelope.parts
            ):  # Check top-level parts if no task_result
                ag_ui_events_data.append(
                    TextMessageStartEvent(
                        type=EventType.TEXT_MESSAGE_START,
                        message_id=assistant_message_id,
                        role="assistant",
                    ).model_dump(by_alias=True, exclude_none=True)
                )
                for part_data in orchestrator_response_envelope.parts:
                    if part_data.type == "text/plain" and isinstance(
                        part_data.content, str
                    ):
                        ag_ui_events_data.append(
                            TextMessageContentEvent(
                                type=EventType.TEXT_MESSAGE_CONTENT,
                                message_id=assistant_message_id,
                                delta=part_data.content,
                            ).model_dump(by_alias=True, exclude_none=True)
                        )
                ag_ui_events_data.append(
                    TextMessageEndEvent(
                        type=EventType.TEXT_MESSAGE_END, message_id=assistant_message_id
                    ).model_dump(by_alias=True, exclude_none=True)
                )
            else:
                # Fallback if no task_result and no parts
                ag_ui_events_data.append(
                    TextMessageStartEvent(
                        type=EventType.TEXT_MESSAGE_START,
                        message_id=assistant_message_id,
                        role="assistant",
                    ).model_dump(by_alias=True, exclude_none=True)
                )
                ag_ui_events_data.append(
                    TextMessageContentEvent(
                        type=EventType.TEXT_MESSAGE_CONTENT,
                        message_id=assistant_message_id,
                        delta="Orchestrator processed the request.",
                    ).model_dump(by_alias=True, exclude_none=True)
                )
                ag_ui_events_data.append(
                    TextMessageEndEvent(
                        type=EventType.TEXT_MESSAGE_END, message_id=assistant_message_id
                    ).model_dump(by_alias=True, exclude_none=True)
                )

        except httpx.HTTPStatusError as e:
            error_content = e.response.text
            logger.error(
                f"HTTP error calling Orchestrator: {e.response.status_code} - {error_content}",
                exc_info=True,
            )
            # Create AG-UI error event
            err_msg_id = str(uuid.uuid4())
            ag_ui_events_data.append(
                TextMessageStartEvent(
                    type=EventType.TEXT_MESSAGE_START,
                    message_id=err_msg_id,
                    role="assistant",
                ).model_dump(by_alias=True, exclude_none=True)
            )
            ag_ui_events_data.append(
                TextMessageContentEvent(
                    type=EventType.TEXT_MESSAGE_CONTENT,
                    message_id=err_msg_id,
                    delta=f"Error communicating with orchestrator: {e.response.status_code}",
                ).model_dump(by_alias=True, exclude_none=True)
            )
            ag_ui_events_data.append(
                TextMessageEndEvent(
                    type=EventType.TEXT_MESSAGE_END, message_id=err_msg_id
                ).model_dump(by_alias=True, exclude_none=True)
            )
        except Exception as e:
            logger.error(f"Error in A2A client: {e}", exc_info=True)
            err_msg_id = str(uuid.uuid4())
            ag_ui_events_data.append(
                TextMessageStartEvent(
                    type=EventType.TEXT_MESSAGE_START,
                    message_id=err_msg_id,
                    role="assistant",
                ).model_dump(by_alias=True, exclude_none=True)
            )
            ag_ui_events_data.append(
                TextMessageContentEvent(
                    type=EventType.TEXT_MESSAGE_CONTENT,
                    message_id=err_msg_id,
                    delta=f"An internal error occurred: {str(e)}",
                ).model_dump(by_alias=True, exclude_none=True)
            )
            ag_ui_events_data.append(
                TextMessageEndEvent(
                    type=EventType.TEXT_MESSAGE_END, message_id=err_msg_id
                ).model_dump(by_alias=True, exclude_none=True)
            )

        return ag_ui_events_data


# --- End of src/savagelysubtle_airesearchagent/ag_ui_backend/a2a_client.py ---

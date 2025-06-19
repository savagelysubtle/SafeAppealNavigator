# src/ai_research_assistant/ag_ui_backend/a2a_client.py
import logging
import uuid
from enum import Enum
from typing import Any, Dict, List
from uuid import UUID

import httpx
from ag_ui.core import (
    EventType,
    TextMessageContentEvent,
    TextMessageEndEvent,
    TextMessageStartEvent,
)

# Use the official AG-UI Python SDK
from ag_ui.core import Message as AGUIMessage
from ag_ui.core import Tool as AGUITool
from pydantic import BaseModel  # For project's MessageEnvelope

from ..config.global_settings import settings
from ..core.models import (
    CodeDiffPart,
    ContractSummaryPart,
    FileContentPart,
    IDECommandPart,
    LegalClauseAnalysisPart,
    MessageEnvelope,
    NotificationPart,
    PlanPart,
    SkillInvocation,
    StatusPart,
)

logger = logging.getLogger(__name__)


# --- Custom AG-UI Events for Void IDE Integration ---


class CustomEventType(str, Enum):
    AGENT_PLAN = "agent_plan"
    AGENT_STATUS = "agent_status"
    CODE_DIFF = "code_diff"
    FILE_CONTENT = "file_content"
    NOTIFICATION = "notification"
    IDE_COMMAND = "ide_command"
    LEGAL_ANALYSIS = "legal_analysis"
    CONTRACT_SUMMARY = "contract_summary"
    # Include base types for reference if needed, though we won't redefine them
    TEXT_MESSAGE_START = EventType.TEXT_MESSAGE_START.value
    TEXT_MESSAGE_CONTENT = EventType.TEXT_MESSAGE_CONTENT.value
    TEXT_MESSAGE_END = EventType.TEXT_MESSAGE_END.value


class BaseCustomEvent(BaseModel):
    type: CustomEventType
    message_id: str  # Correlates with the assistant's response message


class PlanEvent(BaseCustomEvent):
    type: CustomEventType = CustomEventType.AGENT_PLAN
    data: PlanPart


class StatusEvent(BaseCustomEvent):
    type: CustomEventType = CustomEventType.AGENT_STATUS
    data: StatusPart


class CodeDiffEvent(BaseCustomEvent):
    type: CustomEventType = CustomEventType.CODE_DIFF
    data: CodeDiffPart


class FileContentEvent(BaseCustomEvent):
    type: CustomEventType = CustomEventType.FILE_CONTENT
    data: FileContentPart


class NotificationEvent(BaseCustomEvent):
    type: CustomEventType = CustomEventType.NOTIFICATION
    data: NotificationPart


class IDECommandEvent(BaseCustomEvent):
    type: CustomEventType = CustomEventType.IDE_COMMAND
    data: IDECommandPart


class LegalAnalysisEvent(BaseCustomEvent):
    type: CustomEventType = CustomEventType.LEGAL_ANALYSIS
    data: LegalClauseAnalysisPart


class ContractSummaryEvent(BaseCustomEvent):
    type: CustomEventType = CustomEventType.CONTRACT_SUMMARY
    data: ContractSummaryPart


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

        history_dicts = [
            msg.model_dump(by_alias=True, exclude_none=True) for msg in message_history
        ]

        skill_invocation = SkillInvocation(
            skill_name="handle_user_request",
            parameters={"user_prompt": user_prompt, "history": history_dicts},
        )

        envelope = MessageEnvelope(
            conversation_id=UUID(conversation_id),
            skill_invocation=skill_invocation,
            source_agent_id="ag_ui_backend",
            target_agent_id="chief_legal_orchestrator",
        )

        ag_ui_events_data = []
        try:
            logger.debug(
                f"A2A Request Envelope: {envelope.model_dump_json(indent=2, exclude_none=True)}"
            )
            response = await self.http_client.post(
                self.orchestrator_url,
                json=envelope.model_dump(exclude_none=True),
                timeout=120.0,
            )
            response.raise_for_status()
            orchestrator_response_data_dict = response.json()

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
            assistant_message_id = str(uuid.uuid4())

            if task_result:
                ag_ui_events_data.append(
                    TextMessageStartEvent(
                        type=EventType.TEXT_MESSAGE_START,
                        message_id=assistant_message_id,
                        role="assistant",
                    ).model_dump(by_alias=True, exclude_none=True)
                )

                text_content_parts = []

                for part in task_result.parts:
                    content_type = part.type
                    content = part.content

                    event_to_add = None
                    try:
                        if content_type == "text/plain" and isinstance(content, str):
                            text_content_parts.append(content)

                        elif content_type == "application/vnd.agent-plan.v1+json":
                            if isinstance(content, dict):
                                validated_data = PlanPart.model_validate(content)
                                event_to_add = PlanEvent(
                                    message_id=assistant_message_id, data=validated_data
                                )
                            else:
                                logger.warning(
                                    f"Mismatched content for {content_type}: expected dict, got {type(content)}"
                                )
                                text_content_parts.append(str(content))

                        elif content_type == "application/vnd.agent-status.v1+json":
                            if isinstance(content, dict):
                                validated_data = StatusPart.model_validate(content)
                                event_to_add = StatusEvent(
                                    message_id=assistant_message_id, data=validated_data
                                )
                            else:
                                logger.warning(
                                    f"Mismatched content for {content_type}: expected dict, got {type(content)}"
                                )
                                text_content_parts.append(str(content))

                        elif content_type == "application/vnd.code-diff.v1+json":
                            if isinstance(content, dict):
                                validated_data = CodeDiffPart.model_validate(content)
                                event_to_add = CodeDiffEvent(
                                    message_id=assistant_message_id, data=validated_data
                                )
                            else:
                                logger.warning(
                                    f"Mismatched content for {content_type}: expected dict, got {type(content)}"
                                )
                                text_content_parts.append(str(content))

                        elif content_type == "application/vnd.file-content.v1+json":
                            if isinstance(content, dict):
                                validated_data = FileContentPart.model_validate(content)
                                event_to_add = FileContentEvent(
                                    message_id=assistant_message_id, data=validated_data
                                )
                            else:
                                logger.warning(
                                    f"Mismatched content for {content_type}: expected dict, got {type(content)}"
                                )
                                text_content_parts.append(str(content))

                        elif content_type == "application/vnd.notification.v1+json":
                            if isinstance(content, dict):
                                validated_data = NotificationPart.model_validate(
                                    content
                                )
                                event_to_add = NotificationEvent(
                                    message_id=assistant_message_id, data=validated_data
                                )
                            else:
                                logger.warning(
                                    f"Mismatched content for {content_type}: expected dict, got {type(content)}"
                                )
                                text_content_parts.append(str(content))

                        elif content_type == "application/vnd.ide-command.v1+json":
                            if isinstance(content, dict):
                                validated_data = IDECommandPart.model_validate(content)
                                event_to_add = IDECommandEvent(
                                    message_id=assistant_message_id, data=validated_data
                                )
                            else:
                                logger.warning(
                                    f"Mismatched content for {content_type}: expected dict, got {type(content)}"
                                )
                                text_content_parts.append(str(content))

                        elif (
                            content_type
                            == "application/vnd.legal-clause-analysis.v1+json"
                        ):
                            if isinstance(content, dict):
                                validated_data = LegalClauseAnalysisPart.model_validate(
                                    content
                                )
                                event_to_add = LegalAnalysisEvent(
                                    message_id=assistant_message_id, data=validated_data
                                )
                            else:
                                logger.warning(
                                    f"Mismatched content for {content_type}: expected dict, got {type(content)}"
                                )
                                text_content_parts.append(str(content))

                        elif content_type == "application/vnd.contract-summary.v1+json":
                            if isinstance(content, dict):
                                validated_data = ContractSummaryPart.model_validate(
                                    content
                                )
                                event_to_add = ContractSummaryEvent(
                                    message_id=assistant_message_id, data=validated_data
                                )
                            else:
                                logger.warning(
                                    f"Mismatched content for {content_type}: expected dict, got {type(content)}"
                                )
                                text_content_parts.append(str(content))

                        else:
                            # Default to treating unknown content as plain text
                            text_content_parts.append(str(content))
                    except Exception as e:
                        logger.error(
                            f"Failed to process part type {content_type}: {e}",
                            exc_info=True,
                        )
                        text_content_parts.append(f"Error processing content: {str(e)}")

                    if event_to_add:
                        ag_ui_events_data.append(
                            event_to_add.model_dump(by_alias=True, exclude_none=True)
                        )

                if text_content_parts:
                    ag_ui_events_data.append(
                        TextMessageContentEvent(
                            type=EventType.TEXT_MESSAGE_CONTENT,
                            message_id=assistant_message_id,
                            delta=" ".join(text_content_parts),
                        ).model_dump(by_alias=True, exclude_none=True)
                    )

                ag_ui_events_data.append(
                    TextMessageEndEvent(
                        type=EventType.TEXT_MESSAGE_END, message_id=assistant_message_id
                    ).model_dump(by_alias=True, exclude_none=True)
                )

            else:
                # Fallback for responses without a TaskResult
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

# src/savagelysubtle_airesearchagent/ag_ui_backend/state_manager.py
import logging
from typing import Any, Dict, List, Optional

import jsonpatch  # pip install jsonpatch
from ag_ui.core import (
    EventType,
    MessagesSnapshotEvent,
    # JsonPatchOperation is not directly in ag_ui.core, assume List[Any] for delta as per SDK
    StateDeltaEvent,
    StateSnapshotEvent,
)

# Use the official AG-UI Python SDK
from ag_ui.core import (
    Message as AGUIMessage,  # Renaming to avoid confusion if project has its own Message
)
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class AGUIConversationState:
    """Manages state for a single AG-UI conversation thread."""

    def __init__(
        self,
        thread_id: str,
        initial_state: Optional[Dict[str, Any]] = None,
        initial_messages: Optional[List[AGUIMessage]] = None,
    ):
        self.thread_id = thread_id
        self.current_state: Dict[str, Any] = initial_state or {}
        self.messages: List[AGUIMessage] = initial_messages or []
        logger.info(f"AGUIConversationState initialized for thread_id: {thread_id}")

    def add_message(self, message: AGUIMessage):
        self.messages.append(message)
        logger.debug(
            f"Thread {self.thread_id}: Message added: {message.id} ({message.role})"
        )

    def update_state(self, new_state_snapshot: Dict[str, Any]):
        self.current_state = new_state_snapshot
        logger.debug(f"Thread {self.thread_id}: State snapshot updated.")

    def patch_state(
        self, patch_ops: List[Dict[str, Any]]
    ) -> bool:  # AG-UI SDK uses List[Any] for delta, assume list of dicts for jsonpatch
        try:
            self.current_state = jsonpatch.apply_patch(self.current_state, patch_ops)
            logger.debug(f"Thread {self.thread_id}: State patched successfully.")
            return True
        except jsonpatch.JsonPatchException as e:
            logger.error(f"Thread {self.thread_id}: Error applying state patch: {e}")
            return False

    async def send_state_snapshot(self, websocket: WebSocket):
        event = StateSnapshotEvent(
            type=EventType.STATE_SNAPSHOT,  # Explicitly set type
            snapshot=self.current_state,
        )
        # SDK models have alias generator for camelCase, FastAPI should handle it.
        await websocket.send_json(event.model_dump(by_alias=True, exclude_none=True))
        logger.debug(f"Thread {self.thread_id}: Sent StateSnapshotEvent.")

    async def send_messages_snapshot(self, websocket: WebSocket):
        event = MessagesSnapshotEvent(
            type=EventType.MESSAGES_SNAPSHOT,  # Explicitly set type
            messages=self.messages,  # Fixed: pass Message objects directly instead of dict conversion
        )
        await websocket.send_json(event.model_dump(by_alias=True, exclude_none=True))
        logger.debug(f"Thread {self.thread_id}: Sent MessagesSnapshotEvent.")

    async def send_state_delta(
        self, websocket: WebSocket, patch_ops: List[Dict[str, Any]]
    ):
        event = StateDeltaEvent(
            type=EventType.STATE_DELTA,  # Explicitly set type
            delta=patch_ops,
        )
        await websocket.send_json(event.model_dump(by_alias=True, exclude_none=True))
        logger.debug(f"Thread {self.thread_id}: Sent StateDeltaEvent.")


class AGUIStateManager:
    def __init__(self):
        self.conversations: Dict[str, AGUIConversationState] = {}  # thread_id -> state

    def get_or_create_conversation(
        self,
        thread_id: str,
        initial_state: Optional[Dict[str, Any]] = None,
        initial_messages: Optional[List[AGUIMessage]] = None,
    ) -> AGUIConversationState:
        if thread_id not in self.conversations:
            self.conversations[thread_id] = AGUIConversationState(
                thread_id, initial_state, initial_messages
            )
        return self.conversations[thread_id]

    def get_conversation(self, thread_id: str) -> Optional[AGUIConversationState]:
        return self.conversations.get(thread_id)

    def remove_conversation(self, thread_id: str):
        if thread_id in self.conversations:
            del self.conversations[thread_id]
            logger.info(f"Removed conversation state for thread_id: {thread_id}")


global_state_manager = AGUIStateManager()

# --- End of src/savagelysubtle_airesearchagent/ag_ui_backend/state_manager.py ---

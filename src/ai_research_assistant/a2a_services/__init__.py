"""
A2A Services Package - Pure PydanticAI Implementation

This package provides A2A (Agent-to-Agent) protocol services using PydanticAI's
native A2A support. All custom wrappers and decorators have been removed in
favor of standard PydanticAI patterns.

Modules:
    startup: Agent startup script with native PydanticAI A2A conversion
    a2a_compatibility: Standard A2A protocol client for agent communication
"""

from .a2a_compatibility import send_a2a_message

__all__ = ["send_a2a_message"]

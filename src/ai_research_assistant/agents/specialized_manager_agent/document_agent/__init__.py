"""
Document Agent Module

This module provides document intake, processing, and classification capabilities
for the AI Research Assistant.
"""

from .agent import DocumentAgent, DocumentAgentConfig

CAPABILITY = "document_processing"

__all__ = [
    "DocumentAgent",
    "DocumentAgentConfig",
    "CAPABILITY",
]

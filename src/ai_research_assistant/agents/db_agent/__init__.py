"""
Intake Agent Module

This module provides document intake, processing, and classification capabilities
for the AI Research Assistant.
"""

from .intake_agent import CaseType, DocumentType, IntakeAgent

__all__ = [
    "IntakeAgent",
    "DocumentType",
    "CaseType",
]

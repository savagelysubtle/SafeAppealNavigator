"""
Legal Manager Agent Module

This module provides legal memo drafting and citation verification.
This is a Phase-2 agent and is currently a placeholder.
"""

from .agent import LegalManagerAgent, LegalManagerAgentConfig

CAPABILITY = "legal_drafting"

__all__ = [
    "LegalManagerAgent",
    "LegalManagerAgentConfig",
    "CAPABILITY",
]

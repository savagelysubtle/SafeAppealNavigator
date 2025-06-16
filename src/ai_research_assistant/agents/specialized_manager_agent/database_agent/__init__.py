"""
Database Agent Module

This module provides data query and synthesis capabilities.
"""

from .agent import DatabaseAgent, DatabaseAgentConfig

CAPABILITY = "database_operations"

__all__ = [
    "DatabaseAgent",
    "DatabaseAgentConfig",
    "CAPABILITY",
]

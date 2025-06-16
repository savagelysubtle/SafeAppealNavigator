"""
Browser Agent Module

This module provides web browsing, searching, and scraping capabilities.
"""

from .agent import BrowserAgent, BrowserAgentConfig

CAPABILITY = "browser_operations"

__all__ = [
    "BrowserAgent",
    "BrowserAgentConfig",
    "CAPABILITY",
]

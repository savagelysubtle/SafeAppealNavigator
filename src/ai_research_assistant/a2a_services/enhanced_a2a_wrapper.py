# src/ai_research_assistant/a2a_services/enhanced_a2a_wrapper.py
"""
Enhanced A2A wrapper that preserves MCP toolset functionality during agent conversion.

This module addresses the issue where MCP tools get lost during agent.to_a2a() conversion
by providing a custom wrapper that maintains the agent's toolset context.
"""

import logging
from typing import Any, List, Optional

from fastapi import FastAPI
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServer

logger = logging.getLogger(__name__)


class EnhancedA2AWrapper:
    """
    Enhanced A2A wrapper that preserves MCP toolset functionality.

    This wrapper addresses the common issue where MCP tools become unavailable
    after converting a Pydantic AI agent to A2A using the standard to_a2a() method.
    """

    def __init__(self, agent: Agent, toolsets: Optional[List[MCPServer]] = None):
        """
        Initialize the enhanced A2A wrapper.

        Args:
            agent: The Pydantic AI agent to wrap
            toolsets: Optional list of MCP toolsets to ensure are preserved
        """
        self.agent = agent
        self.toolsets = toolsets or []

        # Get original toolsets from agent's internal structure
        self.original_toolsets = []
        if hasattr(agent, "_toolsets"):
            self.original_toolsets = getattr(agent, "_toolsets", [])
        elif hasattr(agent, "__dict__") and "toolsets" in agent.__dict__:
            self.original_toolsets = agent.__dict__.get("toolsets", [])

        # Store reference to the original agent for debugging
        self._original_agent = agent

        logger.info(
            f"Initialized EnhancedA2AWrapper with {len(self.toolsets)} toolsets"
        )

    def create_a2a_app(
        self,
        name: str,
        url: str,
        version: str = "1.0.0",
        description: str = "Enhanced A2A Agent with MCP Support",
        **kwargs,
    ) -> Any:
        """
        Create an A2A app while preserving MCP toolset functionality.

        Args:
            name: Agent name for A2A
            url: Agent URL for A2A
            version: Agent version
            description: Agent description
            **kwargs: Additional arguments passed to to_a2a()

        Returns:
            A2A application with preserved MCP functionality
        """
        logger.info(f"Creating enhanced A2A app for agent: {name}")

        # Verify toolsets before conversion
        self._verify_toolsets_before_conversion()

        # Ensure the agent has the toolsets (using safe access)
        if self.toolsets:
            try:
                # Try multiple methods to set toolsets using safe attribute access
                if hasattr(self.agent, "_toolsets"):
                    setattr(self.agent, "_toolsets", self.toolsets)
                    logger.info(
                        f"Set {len(self.toolsets)} toolsets via _toolsets attribute"
                    )
                elif hasattr(self.agent, "__dict__"):
                    self.agent.__dict__["toolsets"] = self.toolsets
                    self.agent.__dict__["_toolsets"] = self.toolsets
                    logger.info(
                        f"Set {len(self.toolsets)} toolsets via __dict__ mechanism"
                    )

                # Also try to set on any internal agent if it exists
                if hasattr(self.agent, "pydantic_agent"):
                    pydantic_agent = getattr(self.agent, "pydantic_agent", None)
                    if pydantic_agent and hasattr(pydantic_agent, "__dict__"):
                        pydantic_agent.__dict__["toolsets"] = self.toolsets
                        pydantic_agent.__dict__["_toolsets"] = self.toolsets
                        logger.info(
                            f"Set {len(self.toolsets)} toolsets on pydantic_agent"
                        )

            except Exception as e:
                logger.warning(f"Could not reassign toolsets: {e}")

        try:
            # Create A2A app with preserved context
            app = self.agent.to_a2a(
                name=name, url=url, version=version, description=description, **kwargs
            )

            # Verify toolsets after conversion
            self._verify_toolsets_after_conversion()

            # Wrap the app to add MCP preservation hooks
            wrapped_app = self._wrap_app_with_mcp_preservation(app)

            logger.info(f"Successfully created enhanced A2A app for {name}")
            return wrapped_app

        except Exception as e:
            logger.error(f"Failed to create enhanced A2A app: {e}", exc_info=True)
            raise

    def _verify_toolsets_before_conversion(self) -> None:
        """Verify that toolsets are available before A2A conversion."""
        if self.toolsets:
            logger.info(f"Pre-conversion: Agent has {len(self.toolsets)} MCP toolsets")
            for i, toolset in enumerate(self.toolsets):
                logger.debug(f"  Toolset {i}: {type(toolset).__name__}")
        else:
            logger.warning("Pre-conversion: No MCP toolsets found")

        # Check if the agent itself has toolsets using safe access
        agent_toolsets = None
        if hasattr(self.agent, "_toolsets"):
            agent_toolsets = getattr(self.agent, "_toolsets", None)
        elif hasattr(self.agent, "__dict__") and "toolsets" in self.agent.__dict__:
            agent_toolsets = self.agent.__dict__.get("toolsets")

        if agent_toolsets:
            logger.info(
                f"Pre-conversion: Agent has {len(agent_toolsets)} internal toolsets"
            )
        else:
            logger.warning("Pre-conversion: Agent internal toolsets not found")

    def _verify_toolsets_after_conversion(self) -> None:
        """Verify that toolsets are still available after A2A conversion."""
        # Check for toolsets using safe access
        agent_toolsets = None
        if hasattr(self.agent, "_toolsets"):
            agent_toolsets = getattr(self.agent, "_toolsets", None)
        elif hasattr(self.agent, "__dict__") and "toolsets" in self.agent.__dict__:
            agent_toolsets = self.agent.__dict__.get("toolsets")

        if agent_toolsets:
            logger.info(
                f"Post-conversion: Agent still has {len(agent_toolsets)} toolsets"
            )
        else:
            logger.warning("Post-conversion: Agent toolsets may have been lost")

            # Attempt to restore toolsets if they were lost
            if self.toolsets:
                try:
                    logger.warning("Attempting to restore lost toolsets...")
                    if hasattr(self.agent, "__dict__"):
                        self.agent.__dict__["toolsets"] = self.toolsets
                        logger.info(f"Restored {len(self.toolsets)} toolsets to agent")
                except Exception as e:
                    logger.error(f"Could not restore toolsets: {e}")

    def _wrap_app_with_mcp_preservation(self, app: Any) -> Any:
        """
        Wrap the A2A app to preserve MCP context and add simple interaction pre-processing.

        Args:
            app: The original A2A app

        Returns:
            Wrapped app with MCP preservation and simple interaction handling
        """
        from starlette.requests import Request

        # Store reference to toolsets in the app for preservation
        if hasattr(app, "__dict__") and self.toolsets:
            app.__dict__["_preserved_mcp_toolsets"] = self.toolsets
            logger.info(f"Preserved {len(self.toolsets)} MCP toolsets in A2A app")

        # Attempt to restore toolsets to the underlying agent if they were lost
        if hasattr(app, "_agent") and self.toolsets:
            underlying_agent = getattr(app, "_agent", None)
            if underlying_agent:
                try:
                    if hasattr(underlying_agent, "__dict__"):
                        underlying_agent.__dict__["toolsets"] = self.toolsets
                        logger.info(
                            f"Restored {len(self.toolsets)} toolsets to underlying agent"
                        )
                except Exception as e:
                    logger.warning(
                        f"Could not restore toolsets to underlying agent: {e}"
                    )

        # Add simple interaction pre-processing middleware
        original_call = app.__call__

        async def wrapped_call(scope, receive, send):
            if scope["type"] == "http" and scope["method"] == "POST":
                request = Request(scope, receive)
                try:
                    body = await request.body()
                    if body:
                        import json

                        data = json.loads(body)

                        # Check for simple greetings in A2A tasks
                        if data.get("method") == "tasks/send":
                            prompt = (
                                data.get("params", {}).get("prompt", "").lower().strip()
                            )

                            # Simple greeting patterns
                            simple_greetings = [
                                "hello",
                                "hi",
                                "hey",
                                "good morning",
                                "good afternoon",
                                "good evening",
                            ]

                            if prompt in simple_greetings:
                                logger.info(
                                    f"Handling simple greeting directly: {prompt}"
                                )
                                response = {
                                    "jsonrpc": "2.0",
                                    "id": data.get("id"),
                                    "result": {
                                        "taskId": "simple-greeting-"
                                        + str(data.get("id", "unknown")),
                                        "status": {
                                            "state": "completed",
                                            "timestamp": "2025-08-28T00:00:00.000000",
                                        },
                                        "artifacts": [
                                            {
                                                "name": "result",
                                                "parts": [
                                                    {
                                                        "type": "text",
                                                        "text": "Hello! I'm the CEO Agent of the AI Research Assistant system. I can help you with a wide range of tasks including:\n\n🗄️ **Database Operations**: Creating databases, storing documents, vector search\n📄 **Document Processing**: Analyzing PDFs, contracts, legal documents\n🔍 **Research Tasks**: Web research, legal research, information gathering\n⚖️ **Legal Analysis**: Contract review, case analysis, compliance research\n🔄 **Complex Workflows**: Multi-step processes requiring agent coordination\n\nWhat would you like me to help you with today?",
                                                    }
                                                ],
                                            }
                                        ],
                                    },
                                }

                                response_body = json.dumps(response).encode()
                                await send(
                                    {
                                        "type": "http.response.start",
                                        "status": 200,
                                        "headers": [
                                            [b"content-type", b"application/json"]
                                        ],
                                    }
                                )
                                await send(
                                    {
                                        "type": "http.response.body",
                                        "body": response_body,
                                    }
                                )
                                return
                except Exception as e:
                    logger.warning(f"Error in simple interaction pre-processing: {e}")
                    # Fall through to original app

            # Call original app for all other requests
            await original_call(scope, receive, send)

        app.__call__ = wrapped_call
        logger.info("App wrapped with MCP preservation and simple interaction handling")
        return app


def create_enhanced_a2a_agent(
    agent: Agent,
    toolsets: Optional[List[MCPServer]] = None,
    name: str = "Enhanced A2A Agent",
    url: str = "http://localhost:8000",
    version: str = "1.0.0",
    description: str = "AI Research Agent with Enhanced MCP Tool Support",
) -> FastAPI:
    """
    Convenience function to create an enhanced A2A agent with MCP preservation.

    Args:
        agent: The Pydantic AI agent
        toolsets: List of MCP toolsets to preserve
        name: Agent name
        url: Agent URL
        version: Agent version
        description: Agent description

    Returns:
        Enhanced A2A application
    """
    wrapper = EnhancedA2AWrapper(agent, toolsets)
    return wrapper.create_a2a_app(
        name=name, url=url, version=version, description=description
    )

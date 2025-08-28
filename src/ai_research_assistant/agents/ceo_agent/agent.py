# FILE: src/ai_research_assistant/agents/ceo_agent/agent.py

import logging
from typing import Any, List, Optional

from pydantic_ai import RunContext
from pydantic_ai.mcp import MCPServer

from ai_research_assistant.agents.base_pydantic_agent import BasePydanticAgent
from ai_research_assistant.agents.ceo_agent.config import CEOAgentConfig
from ai_research_assistant.agents.ceo_agent.prompts import analyze_user_request

logger = logging.getLogger(__name__)


class CEOAgent(BasePydanticAgent):
    """CEO Agent that serves as the primary user interface and task router."""

    def __init__(
        self,
        config: Optional[CEOAgentConfig] = None,
        llm_instance: Optional[Any] = None,
        toolsets: Optional[List[MCPServer]] = None,
    ):
        # Initialize the parent class normally
        super().__init__(
            config=config or CEOAgentConfig(),
            llm_instance=llm_instance,
            toolsets=toolsets,
        )
        self.config: CEOAgentConfig = self.config  # type: ignore

        # Setup enhanced tools after initialization
        self._setup_enhanced_tools()

        logger.info(
            f"CEOAgent '{self.agent_name}' initialized with delegation capabilities."
        )

    def _setup_enhanced_tools(self):
        """Set up enhanced tools with intelligent delegation patterns"""

        @self.pydantic_agent.tool
        async def intelligent_delegate_to_orchestrator(
            ctx: RunContext[Any], user_request: str
        ) -> str:
            """
            Intelligently delegate user requests to the Orchestrator Agent using
            A2A protocol for SafeAppealNavigator legal case management.

            This tool analyzes the user request and delegates to the Orchestrator Agent
            via HTTP/A2A communication for any work that requires:
            - Database operations (ChromaDB, collections, vector search) for legal case management
            - Document processing (medical reports, WCAT decisions, legal documents)
            - Research tasks (WCAT precedents, WorkSafe BC policies)
            - Legal analysis (case analysis, appeal preparation)
            - Multi-step workflows (case setup, appeal workflows)

            Args:
                user_request: The user's request to analyze and delegate

            Returns:
                The orchestrator's response with results
            """
            logger.info(
                f"CEO Agent delegating SafeAppealNavigator request via A2A: {user_request}"
            )

            try:
                # Import the A2A communication function
                from ai_research_assistant.a2a_services.a2a_compatibility import (
                    send_a2a_message,
                )

                # Enhanced analysis with SafeAppealNavigator context
                analysis = analyze_user_request(user_request)

                # Handle greetings and simple interactions directly
                if analysis["pattern_type"] == "simple":
                    logger.info(
                        f"Handling simple interaction: {analysis['interaction_type']}"
                    )
                    return analysis["response_template"]

                # Delegate work requests to Orchestrator via A2A
                logger.info("Delegating work request to Orchestrator Agent via A2A")

                # Enhanced prompt based on analysis
                if analysis["pattern_type"] == "safeappealnavigator_database":
                    # Use specific database setup instructions
                    delegation_prompt = analysis["delegation_instruction"].format(
                        user_request=user_request
                    )
                elif analysis["pattern_type"] == "delegation":
                    # Use pattern-specific prompt template
                    delegation_prompt = analysis["prompt_template"].format(
                        user_request=user_request
                    )
                else:
                    # Default enhanced delegation prompt
                    delegation_prompt = (
                        f"SafeAppealNavigator legal case management request: {user_request}. "
                        f"This system helps injured workers with WorkSafe BC and WCAT appeals. "
                        f"Please coordinate with appropriate specialized agents to fulfill this request."
                    )

                # Send to Orchestrator Agent via A2A protocol
                orchestrator_url = "http://localhost:10101"
                result = await send_a2a_message(
                    url=orchestrator_url,
                    prompt=delegation_prompt,
                    agent_name="Orchestrator Agent",
                    timeout=120.0,
                )

                logger.info("Successfully received response from Orchestrator Agent")
                return result

            except Exception as e:
                logger.error(f"Error in A2A delegation: {e}", exc_info=True)
                return (
                    f"I encountered an error while coordinating your SafeAppealNavigator request: {str(e)}. "
                    f"This might be a temporary issue with our legal case management system. "
                    f"Please try again, and if the issue persists, let me know."
                )

    async def respond_to_user(self, user_input: str, **kwargs) -> str:
        """
        Process user input and either handle directly or delegate to Orchestrator.
        """
        logger.info(f"CEO Agent received user input: '{user_input[:100]}...'")

        try:
            # Analyze the request type first to determine if we need delegation
            analysis = analyze_user_request(user_input)
            logger.info(f"Request analysis: {analysis['pattern_type']}")

            # For simple interactions, allow direct handling
            if analysis["pattern_type"] == "simple":
                user_prompt = user_input
                logger.info("Handling as simple interaction")
            else:
                # For work requests, force tool usage with very explicit instructions
                user_prompt = (
                    f"The user requested: '{user_input}'. "
                    f"This is a work request that requires delegation. You MUST use the "
                    f"intelligent_delegate_to_orchestrator tool to handle this. "
                    f"Do NOT provide any response about completing work unless you actually call the tool. "
                    f"Call the intelligent_delegate_to_orchestrator tool now with the user's request."
                )
                logger.info("Forcing delegation for work request")

            result = await self.pydantic_agent.run(user_prompt=user_prompt, **kwargs)

            response = result.data if hasattr(result, "data") else str(result)
            logger.info(f"CEO Agent response generated: {len(response)} characters")

            # Log if we detect the agent is fabricating work completion
            if (
                "successfully" in response.lower()
                and analysis["pattern_type"] != "simple"
            ):
                logger.warning(
                    "Agent may be fabricating work completion - check if tool was actually called"
                )

            return response

        except Exception as e:
            logger.error(f"CEO Agent error: {e}", exc_info=True)
            return (
                f"I encountered an error processing your SafeAppealNavigator request: {str(e)}. "
                f"Please try rephrasing your request or contact support if the issue persists."
            )

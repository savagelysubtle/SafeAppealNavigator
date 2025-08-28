#!/usr/bin/env python3
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))
os.environ["GOOGLE_API_KEY"] = "dummy-key-for-testing"

from ai_research_assistant.agents.ceo_agent.agent import CEOAgent
from ai_research_assistant.core.unified_llm_factory import get_llm_factory

try:
    # Create a dummy LLM
    llm_factory = get_llm_factory()
    llm_instance = llm_factory.create_llm_from_config(
        {"provider": "google", "model_name": "gemini-1.5-flash"}
    )

    # Create CEO Agent
    ceo = CEOAgent(llm_instance=llm_instance)

    # Check how many tools it has
    tools = ceo.pydantic_agent._function_tools
    print(f"Number of tools: {len(tools)}")
    for i, tool in enumerate(tools):
        tool_name = getattr(tool, "name", "Unknown")
        tool_desc = getattr(tool, "description", "No description")[:50]
        print(f"Tool {i}: {tool_name} - {tool_desc}...")

except Exception as e:
    print(f"Error: {e}")
    import traceback

    traceback.print_exc()

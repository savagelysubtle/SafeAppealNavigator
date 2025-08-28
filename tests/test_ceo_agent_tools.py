#!/usr/bin/env python3
"""
Test script to verify CEO Agent tool delegation works correctly
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ai_research_assistant.agents.ceo_agent.agent import CEOAgent
from ai_research_assistant.core.unified_llm_factory import get_llm_factory


async def test_ceo_agent_tools():
    """Test the CEO agent with our new tool-based approach"""

    # Check for Google API key in environment variables
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("⚠️  Warning: GOOGLE_API_KEY not found in environment variables")
        print("   Set it with: $env:GOOGLE_API_KEY='your-api-key-here' (PowerShell)")
        print("   Skipping test that requires Google API...")
        return

    print("🧪 Testing CEO Agent Tool Delegation...")
    print("=" * 50)

    try:
        # Create LLM instance
        llm_factory = get_llm_factory()
        llm_instance = llm_factory.create_llm_from_config(
            {"provider": "google", "model_name": "gemini-1.5-flash"}
        )

        # Create CEO Agent
        ceo_agent = CEOAgent(llm_instance=llm_instance)

        print("✅ CEO Agent created successfully")

        # Check that tools are registered
        tools = ceo_agent.pydantic_agent._function_tools
        print(f"📋 Registered tools: {len(tools)}")
        for tool in tools:
            tool_name = getattr(tool, "name", "Unknown")
            tool_desc = getattr(tool, "description", "No description")[:50]
            print(f"  - {tool_name}: {tool_desc}...")

        print("\n🔧 Testing tool delegation...")

        # Test 1: Simple greeting (should use simple_greeting tool)
        print("\n📤 Test 1: Simple greeting")
        result1 = await ceo_agent.pydantic_agent.run("hello")
        print(f"📥 Response: {result1.output}")

        # Test 2: Complex request (should use delegate_to_orchestrator tool)
        print("\n📤 Test 2: Complex database request")
        result2 = await ceo_agent.pydantic_agent.run(
            "start a database for the application"
        )
        print(f"📥 Response: {result2.output}")

        print("\n✅ CEO Agent tool delegation test completed!")

    except Exception as e:
        print(f"❌ Error testing CEO Agent: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_ceo_agent_tools())

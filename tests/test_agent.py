#!/usr/bin/env python3
"""
Quick test script to verify A2A agent functionality
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ai_research_assistant.a2a_services.a2a_compatibility import send_a2a_message


async def test_agent():
    """Test the CEO agent with our A2A protocol fixes"""

    # Set the Google API key
    os.environ["GOOGLE_API_KEY"] = "AIzaSyCWqhIIWHj8i5qDbo-Y3L1-jszF4-9O97M"

    print("🧪 Testing A2A Protocol Fixes...")
    print("=" * 50)

    # Test the CEO agent
    ceo_url = "http://localhost:10105"
    test_message = "hello test"

    try:
        print(f"📤 Sending message to CEO Agent: '{test_message}'")
        response = await send_a2a_message(
            url=ceo_url, prompt=test_message, agent_name="CEO Agent", timeout=30.0
        )
        print(f"✅ Success! Response: {response}")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Starting A2A Agent Test")
    print("Note: Make sure agents are running first with the CLI!")
    print()

    result = asyncio.run(test_agent())

    if result:
        print("\n🎉 A2A Protocol fixes are working!")
    else:
        print("\n💔 A2A Protocol still has issues")

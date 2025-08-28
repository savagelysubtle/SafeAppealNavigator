#!/usr/bin/env python3
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ai_research_assistant.agents.ceo_agent.prompts import (
    SIMPLE_INTERACTIONS,
    analyze_user_request,
)

# Test the analyze_user_request function
test_inputs = ["hello", "hi", "create a new database", "what can you do"]

for test_input in test_inputs:
    result = analyze_user_request(test_input)
    print(f"Input: '{test_input}'")
    print(f"Result: {result}")
    print("-" * 50)

# Also check what's in SIMPLE_INTERACTIONS
print("\nSIMPLE_INTERACTIONS keys:", list(SIMPLE_INTERACTIONS.keys()))
for key, value in SIMPLE_INTERACTIONS.items():
    print(f"{key}: {value['triggers'][:3]}...")  # Show first 3 triggers

#!/usr/bin/env python3
"""Test script to verify agent creation works correctly."""

from ai_research_assistant.agents.orchestrator_agent.agent import OrchestratorAgent
from ai_research_assistant.agents.orchestrator_agent.config import (
    OrchestratorAgentConfig,
)
from ai_research_assistant.core.unified_llm_factory import get_llm_factory

print("✅ Testing agent creation...")
config = OrchestratorAgentConfig()
llm_factory = get_llm_factory()
llm_instance = llm_factory.create_llm_from_config(
    {
        "provider": config.llm_provider,
        "model_name": config.llm_model_name,
    }
)
print("✅ LLM created successfully")

# Create agent with minimal MCP toolsets (empty for testing)
agent = OrchestratorAgent(llm_instance=llm_instance, config=config, toolsets=[])
print("✅ OrchestratorAgent created successfully")
print(f"Agent name: {agent.agent_name}")
print(f"Has orchestrate method: {hasattr(agent, 'orchestrate')}")
print(f"Orchestrate is decorated: {hasattr(agent.orchestrate, '_is_agent_skill')}")

# Test the FastA2A wrapper
from ai_research_assistant.a2a_services.fasta2a_wrapper import (
    create_skills_from_agent,
    wrap_agent_with_fasta2a,
)

print("\n✅ Testing FastA2A integration...")
skills = create_skills_from_agent(agent)
print(f"Skills found: {len(skills)}")
for skill in skills:
    print(f"  - Skill ID: {skill['id']}")
    print(f"  - Skill Name: {skill['name']}")

if skills:
    print("✅ Skills discovered successfully")
    app = wrap_agent_with_fasta2a(agent, url="http://localhost:10101")
    print("✅ FastA2A app created successfully")
    print(f"App type: {type(app)}")
else:
    print("❌ No skills found - this would cause A2A endpoint issues")

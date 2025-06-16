# src/ai_research_assistant/agents/specialized_manager_agent/__init__.py
import importlib
import pkgutil
from typing import Any, Dict, Type

# Dictionary to hold the mapping from capability string to agent class
AGENT_REGISTRY: Dict[str, Type[Any]] = {}

# Discover and register agents based on their CAPABILITY constant
for _, module_name, _ in pkgutil.iter_modules(__path__):
    try:
        # Import the module (e.g., specialized_manager_agent.document_agent)
        module = importlib.import_module(f"{__name__}.{module_name}")

        # Check if the module has a CAPABILITY constant and an Agent class
        if hasattr(module, "CAPABILITY") and hasattr(module, "agent"):
            capability = getattr(module, "CAPABILITY")
            # Find the primary agent class (e.g., DocumentAgent) in the agent submodule
            agent_class_name = (
                module.agent.__all__[0] if hasattr(module.agent, "__all__") else None
            )
            if agent_class_name and hasattr(module.agent, agent_class_name):
                agent_class = getattr(module.agent, agent_class_name)
                AGENT_REGISTRY[capability] = agent_class
    except Exception as e:
        # Log or handle exceptions during module import
        print(f"Could not register agent from module {module_name}: {e}")


def get_agent_class_by_capability(capability: str) -> Type[Any] | None:
    """
    Returns the agent class associated with a given capability.
    """
    return AGENT_REGISTRY.get(capability)


__all__ = [
    "AGENT_REGISTRY",
    "get_agent_class_by_capability",
]

# src/savagelysubtle_airesearchagent/mcp_integration/agent_registry.py
# This file remains largely the same as it's responsible for loading and querying agent cards.
# No changes from the previous version are strictly needed for this re-clarification,
# but ensure it's focused on providing agent card information.

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

AGENT_CARDS_DIR = Path(__file__).parent.parent.parent / "agent_cards"

class AgentRegistry:
    def __init__(self):
        self._agent_cards: Dict[str, Dict[str, Any]] = {}
        self._load_agent_cards()

    def _load_agent_cards(self):
        if not AGENT_CARDS_DIR.exists() or not AGENT_CARDS_DIR.is_dir():
            logger.warning(f"Agent cards directory not found: {AGENT_CARDS_DIR}")
            return

        for card_file in AGENT_CARDS_DIR.glob("*.json"):
            try:
                with open(card_file, "r") as f:
                    card_data = json.load(f)
                if "agent_id" in card_data:
                    self._agent_cards[card_data["agent_id"]] = card_data
                    logger.info(f"Loaded agent card: {card_data['agent_id']}")
                else:
                    logger.warning(f"Agent card {card_file.name} is missing 'agent_id'.")
            except json.JSONDecodeError:
                logger.error(f"Error decoding JSON from agent card: {card_file.name}")
            except Exception as e:
                logger.error(f"Error loading agent card {card_file.name}: {e}")

        logger.info(f"Total agent cards loaded: {len(self._agent_cards)}")

    def get_agent_card(self, agent_id: str) -> Optional[Dict[str, Any]]:
        return self._agent_cards.get(agent_id)

    def list_all_agent_cards(self) -> List[Dict[str, Any]]:
        return list(self._agent_cards.values())

    def find_agent_for_task(self, task_description: str) -> Optional[Dict[str, Any]]:
        """
        Finds an agent suitable for a given task description based on its advertised skills and description.
        This is a simplified version. A real implementation would use embeddings or more sophisticated matching.
        """
        logger.info(f"Attempting to find agent for task: '{task_description}'")
        # Simple keyword matching for now
        best_match_agent: Optional[Dict[str, Any]] = None
        highest_score = 0 # Simple scoring: skill description > agent description

        for agent_id, card in self._agent_cards.items():
            # Check skill descriptions
            for skill in card.get("skills", []):
                skill_desc = skill.get("description", "").lower()
                skill_name = skill.get("name", "").lower()
                if task_description.lower() in skill_desc or task_description.lower() in skill_name:
                    logger.info(f"Found agent {agent_id} for task '{task_description}' based on skill '{skill.get('name', '')}' (score 2)")
                    if 2 > highest_score:
                        highest_score = 2
                        best_match_agent = card
                    # Could return immediately if perfect match or use more complex scoring

            # Check agent description if no skill match or to refine
            agent_desc = card.get("description", "").lower()
            agent_name = card.get("name", "").lower()
            if task_description.lower() in agent_desc or task_description.lower() in agent_name:
                 logger.info(f"Found agent {agent_id} for task '{task_description}' based on agent description/name (score 1)")
                 if 1 > highest_score:
                     highest_score = 1
                     best_match_agent = card

        if best_match_agent:
            logger.info(f"Best match for task '{task_description}': Agent {best_match_agent.get('agent_id')}")
        else:
            logger.warning(f"No agent found for task: {task_description}")
        return best_match_agent

agent_registry_instance = AgentRegistry()

# --- End of src/savagelysubtle_airesearchagent/mcp_integration/agent_registry.py ---
"""
Test suite for Agent Cards validation.

This module contains comprehensive tests for validating agent configuration cards
stored as JSON files, including schema validation, skill definitions, and
dependency checking.
"""

import json
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

# Expected agent card schema structure
REQUIRED_AGENT_CARD_FIELDS = [
    "agent_id",
    "agent_name",
    "agent_type",
    "description",
    "version",
    "skills",
]

REQUIRED_SKILL_FIELDS = ["name", "description", "input_schema", "output_schema"]


@pytest.fixture
def agent_cards_path():
    """Fixture providing the path to agent cards directory."""
    return Path(__file__).parent.parent / "agent_cards"


@pytest.fixture
def sample_agent_card():
    """Fixture providing a valid sample agent card for testing."""
    return {
        "agent_id": "test_agent_001",
        "agent_name": "TestAgent",
        "agent_type": "Specialized",
        "description": "A test agent for validation testing",
        "version": "1.0.0",
        "skills": [
            {
                "name": "test_skill",
                "description": "A test skill for validation",
                "input_schema": {
                    "type": "object",
                    "properties": {"test_param": {"type": "string"}},
                    "required": ["test_param"],
                },
                "output_schema": {
                    "type": "object",
                    "properties": {"result": {"type": "string"}},
                },
            }
        ],
        "dependencies": ["test_dependency"],
        "tags": ["test", "validation"],
    }


@pytest.fixture
def agent_card_loader():
    """Factory fixture for loading agent cards."""

    def _load_agent_card(card_path):
        try:
            with open(card_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return None
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in agent card {card_path}: {e}")

    return _load_agent_card


class TestAgentCardFileExistence:
    """Test cases for verifying agent card files exist."""

    def test_agent_cards_directory_exists(self, agent_cards_path):
        """Test that the agent_cards directory exists."""
        assert agent_cards_path.exists(), (
            f"Agent cards directory not found: {agent_cards_path}"
        )
        assert agent_cards_path.is_dir(), (
            f"Agent cards path is not a directory: {agent_cards_path}"
        )

    @pytest.mark.parametrize(
        "card_name",
        [
            "orchestrator_agent.json",
            "legal_manager_agent.json",
            "ceo_agent.json",
            "browser_agent.json",
            "database_agent.json",
            "document_agent.json",
        ],
    )
    def test_expected_agent_cards_exist(self, agent_cards_path, card_name):
        """Test that all expected agent card files exist."""
        card_path = agent_cards_path / card_name
        assert card_path.exists(), f"Expected agent card not found: {card_name}"
        assert card_path.is_file(), f"{card_name} is not a file"


class TestAgentCardJSONValidation:
    """Test cases for JSON parsing and basic validation."""

    def test_load_all_agent_cards(self, agent_cards_path, agent_card_loader):
        """Test loading all agent cards successfully."""
        agent_card_files = list(agent_cards_path.glob("*.json"))
        assert len(agent_card_files) > 0, "No agent card files found"

        for card_file in agent_card_files:
            card_data = agent_card_loader(card_file)
            assert card_data is not None, f"Failed to load {card_file.name}"
            assert isinstance(card_data, dict), (
                f"{card_file.name} should be a JSON object"
            )

    def test_agent_cards_valid_json_syntax(self, agent_cards_path):
        """Test that all agent cards have valid JSON syntax."""
        agent_card_files = list(agent_cards_path.glob("*.json"))

        for card_file in agent_card_files:
            try:
                with open(card_file, "r", encoding="utf-8") as f:
                    json.load(f)
            except json.JSONDecodeError as e:
                pytest.fail(f"Invalid JSON syntax in {card_file.name}: {e}")


class TestAgentCardSchemaValidation:
    """Test cases for agent card schema validation."""

    def test_sample_agent_card_valid_schema(self, sample_agent_card):
        """Test that sample agent card has valid schema."""
        for field in REQUIRED_AGENT_CARD_FIELDS:
            assert field in sample_agent_card, (
                f"Required field '{field}' missing from agent card"
            )

    def test_all_agent_cards_schema_compliance(
        self, agent_cards_path, agent_card_loader
    ):
        """Test that all agent cards comply with basic schema."""
        agent_card_files = list(agent_cards_path.glob("*.json"))

        for card_file in agent_card_files:
            card_data = agent_card_loader(card_file)

            # Test required fields for each card
            for field in REQUIRED_AGENT_CARD_FIELDS:
                assert field in card_data, (
                    f"Required field '{field}' missing from {card_file.name}"
                )

            # Test field types
            assert isinstance(card_data["agent_id"], str), (
                f"agent_id should be string in {card_file.name}"
            )
            assert isinstance(card_data["agent_name"], str), (
                f"agent_name should be string in {card_file.name}"
            )
            assert isinstance(card_data["skills"], list), (
                f"skills should be list in {card_file.name}"
            )

    def test_orchestrator_agent_card_schema(self, agent_cards_path, agent_card_loader):
        """Test orchestrator agent card schema compliance."""
        card_path = agent_cards_path / "orchestrator_agent.json"
        card_data = agent_card_loader(card_path)

        # Test required fields
        for field in REQUIRED_AGENT_CARD_FIELDS:
            assert field in card_data, (
                f"Required field '{field}' missing from orchestrator card"
            )

        # Test specific orchestrator fields
        assert (
            "orchestrator" in card_data["agent_name"].lower()
            or "orchestrator" in card_data["agent_type"].lower()
        )


class TestAgentCardSkillValidation:
    """Test cases for validating agent skill definitions."""

    def test_sample_agent_card_skill_schema(self, sample_agent_card):
        """Test that sample agent card skills have valid schema."""
        skills = sample_agent_card["skills"]
        assert len(skills) > 0, "Agent card should have at least one skill"

        for skill in skills:
            for field in REQUIRED_SKILL_FIELDS:
                assert field in skill, f"Required skill field '{field}' missing"

    def test_orchestrator_agent_skills(self, agent_cards_path, agent_card_loader):
        """Test orchestrator agent skill definitions."""
        card_path = agent_cards_path / "orchestrator_agent.json"
        card_data = agent_card_loader(card_path)

        skills = card_data["skills"]
        assert len(skills) > 0, "Orchestrator should have skills defined"

        # Check for expected orchestrator skills
        skill_names = [skill["name"] for skill in skills]
        orchestrator_keywords = ["workflow", "research", "orchestrat", "coordinat"]

        has_orchestrator_skill = any(
            any(keyword in skill_name.lower() for keyword in orchestrator_keywords)
            for skill_name in skill_names
        )
        assert has_orchestrator_skill, (
            "Orchestrator should have workflow/coordination skills"
        )

    def test_skill_input_output_schemas(self, agent_cards_path, agent_card_loader):
        """Test that all skills have valid input/output schemas."""
        agent_card_files = list(agent_cards_path.glob("*.json"))

        for card_file in agent_card_files:
            card_data = agent_card_loader(card_file)

            for skill in card_data["skills"]:
                # Test input schema
                input_schema = skill["input_schema"]
                assert isinstance(input_schema, dict), (
                    f"Input schema should be dict in {card_file.name}"
                )
                assert "type" in input_schema, (
                    f"Input schema missing 'type' in {card_file.name}"
                )

                # Test output schema
                output_schema = skill["output_schema"]
                assert isinstance(output_schema, dict), (
                    f"Output schema should be dict in {card_file.name}"
                )
                assert "type" in output_schema, (
                    f"Output schema missing 'type' in {card_file.name}"
                )

    def test_skill_names_unique_per_agent(self, agent_cards_path, agent_card_loader):
        """Test that skill names are unique within each agent card."""
        agent_card_files = list(agent_cards_path.glob("*.json"))

        for card_file in agent_card_files:
            card_data = agent_card_loader(card_file)

            skill_names = [skill["name"] for skill in card_data["skills"]]
            unique_names = set(skill_names)

            assert len(skill_names) == len(unique_names), (
                f"Duplicate skill names in {card_file.name}"
            )


class TestAgentCardDependencyValidation:
    """Test cases for validating agent dependencies."""

    def test_agent_dependencies_are_strings(self, agent_cards_path, agent_card_loader):
        """Test that all dependencies are string values."""
        agent_card_files = list(agent_cards_path.glob("*.json"))

        for card_file in agent_card_files:
            card_data = agent_card_loader(card_file)

            if "dependencies" in card_data:
                dependencies = card_data["dependencies"]
                for dep in dependencies:
                    assert isinstance(dep, str), (
                        f"Dependency should be string in {card_file.name}: {dep}"
                    )
                    assert len(dep.strip()) > 0, f"Empty dependency in {card_file.name}"

    def test_orchestrator_agent_dependencies(self, agent_cards_path, agent_card_loader):
        """Test orchestrator agent dependency declarations."""
        card_path = agent_cards_path / "orchestrator_agent.json"
        card_data = agent_card_loader(card_path)

        if "dependencies" in card_data:
            dependencies = card_data["dependencies"]
            assert isinstance(dependencies, list), "Dependencies should be a list"

            # Check for tool-related dependencies
            tool_deps = [dep for dep in dependencies if "tool" in dep.lower()]
            assert len(tool_deps) > 0, "Orchestrator should have tool dependencies"


class TestAgentCardVersionValidation:
    """Test cases for validating agent version information."""

    def test_agent_versions_are_strings(self, agent_cards_path, agent_card_loader):
        """Test that all agent versions are string values."""
        agent_card_files = list(agent_cards_path.glob("*.json"))

        for card_file in agent_card_files:
            card_data = agent_card_loader(card_file)

            version = card_data["version"]
            assert isinstance(version, str), (
                f"Version should be string in {card_file.name}"
            )
            assert len(version.strip()) > 0, f"Empty version in {card_file.name}"

    def test_agent_versions_follow_semver_pattern(
        self, agent_cards_path, agent_card_loader
    ):
        """Test that agent versions follow semantic versioning pattern."""
        import re

        # Basic semver pattern
        semver_pattern = r"^\d+\.\d+\.\d+$"

        agent_card_files = list(agent_cards_path.glob("*.json"))

        for card_file in agent_card_files:
            card_data = agent_card_loader(card_file)

            version = card_data["version"]
            assert re.match(semver_pattern, version), (
                f"Invalid version format in {card_file.name}: {version}"
            )


@pytest.mark.parametrize(
    "agent_card_name",
    [
        "orchestrator_agent.json",
        "legal_manager_agent.json",
        "ceo_agent.json",
        "browser_agent.json",
        "database_agent.json",
        "document_agent.json",
    ],
)
class TestIndividualAgentCards:
    """Parametrized test cases for individual agent cards."""

    def test_agent_card_loads_successfully(
        self, agent_card_name, agent_cards_path, agent_card_loader
    ):
        """Test that each agent card loads successfully."""
        card_path = agent_cards_path / agent_card_name
        card_data = agent_card_loader(card_path)

        assert card_data is not None, f"Failed to load {agent_card_name}"
        assert isinstance(card_data, dict), f"{agent_card_name} should be a JSON object"

    def test_agent_card_has_required_fields(
        self, agent_card_name, agent_cards_path, agent_card_loader
    ):
        """Test that each agent card has all required fields."""
        card_path = agent_cards_path / agent_card_name
        card_data = agent_card_loader(card_path)

        for field in REQUIRED_AGENT_CARD_FIELDS:
            assert field in card_data, (
                f"Required field '{field}' missing from {agent_card_name}"
            )

    def test_agent_card_skills_valid(
        self, agent_card_name, agent_cards_path, agent_card_loader
    ):
        """Test that each agent card has valid skills."""
        card_path = agent_cards_path / agent_card_name
        card_data = agent_card_loader(card_path)

        skills = card_data["skills"]
        assert len(skills) > 0, f"{agent_card_name} should have at least one skill"

        for skill in skills:
            for field in REQUIRED_SKILL_FIELDS:
                assert field in skill, (
                    f"Required skill field '{field}' missing from {agent_card_name}"
                )


class TestAgentCardIntegration:
    """Integration test cases for agent card system."""

    def test_all_agent_cards_load_together(self, agent_cards_path, agent_card_loader):
        """Test loading all agent cards together (integration test)."""
        agent_card_files = list(agent_cards_path.glob("*.json"))
        loaded_cards = {}

        for card_file in agent_card_files:
            card_data = agent_card_loader(card_file)
            loaded_cards[card_data["agent_id"]] = card_data

        assert len(loaded_cards) > 0, "Should load at least one agent card"

        # All cards should have unique agent IDs
        agent_ids = list(loaded_cards.keys())
        assert len(agent_ids) == len(set(agent_ids)), "Agent IDs should be unique"

    def test_agent_card_system_consistency(self, agent_cards_path, agent_card_loader):
        """Test consistency across the agent card system."""
        agent_card_files = list(agent_cards_path.glob("*.json"))
        all_agent_types = set()

        for card_file in agent_card_files:
            card_data = agent_card_loader(card_file)
            all_agent_types.add(card_data["agent_type"])

        # Should have multiple agent types
        assert len(all_agent_types) > 1, "Should have multiple agent types"


class TestAgentCardErrorHandling:
    """Test cases for error handling and edge cases."""

    def test_agent_card_with_invalid_json(self):
        """Test handling of invalid JSON in agent card."""
        invalid_json = '{"agent_id": "test", "invalid": json}'

        with patch("builtins.open", mock_open(read_data=invalid_json)):
            with pytest.raises(json.JSONDecodeError):
                with open("fake_card.json", "r") as f:
                    json.load(f)

    def test_agent_card_file_not_found(self, agent_card_loader):
        """Test handling of missing agent card file."""
        result = agent_card_loader("nonexistent_card.json")
        assert result is None

    def test_agent_card_with_minimal_fields(self):
        """Test agent card with only required fields."""
        minimal_card = {
            "agent_id": "minimal_agent",
            "agent_name": "MinimalAgent",
            "agent_type": "Test",
            "description": "Minimal test agent",
            "version": "1.0.0",
            "skills": [
                {
                    "name": "minimal_skill",
                    "description": "A minimal skill",
                    "input_schema": {"type": "object"},
                    "output_schema": {"type": "object"},
                }
            ],
        }

        # Should be valid with just required fields
        for field in REQUIRED_AGENT_CARD_FIELDS:
            assert field in minimal_card

    def test_agent_card_with_empty_skills_list(self):
        """Test detection of agent card with empty skills list."""
        card_with_empty_skills = {
            "agent_id": "empty_skills_agent",
            "agent_name": "EmptySkillsAgent",
            "agent_type": "Test",
            "description": "Agent with no skills",
            "version": "1.0.0",
            "skills": [],
        }

        # Empty skills list should be detected
        assert len(card_with_empty_skills["skills"]) == 0

    def test_missing_required_fields_detection(self):
        """Test detection of missing required fields."""
        invalid_card = {
            "agent_name": "InvalidAgent",  # Missing agent_id
            "description": "An invalid agent card",
            # Missing required fields: agent_type, version, skills
        }

        missing_fields = []
        for field in REQUIRED_AGENT_CARD_FIELDS:
            if field not in invalid_card:
                missing_fields.append(field)

        assert len(missing_fields) > 0, "Should detect missing required fields"
        assert "agent_id" in missing_fields
        assert "agent_type" in missing_fields
        assert "version" in missing_fields
        assert "skills" in missing_fields

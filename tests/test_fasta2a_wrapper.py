#!/usr/bin/env python3
"""
Comprehensive tests for the fasta2a_wrapper module.

This module tests the FastA2A wrapper functionality including skill extraction
from agents and agent wrapping for A2A communication.
"""

from unittest.mock import Mock, call, patch

import pytest

from ai_research_assistant.a2a_services.fasta2a_wrapper import (
    create_skills_from_agent,
    wrap_agent_with_fasta2a,
)
from ai_research_assistant.agents.base_pydantic_agent import agent_skill


class MockAgent:
    """Mock agent class for testing skill extraction."""

    def __init__(self, agent_name="test_agent"):
        self.agent_name = agent_name
        # Use simple objects instead of Mock to avoid them being treated as callable skills
        self.config = type("Config", (), {"pydantic_ai_system_prompt": "test prompt"})()
        self.pydantic_agent = type(
            "PydanticAgent", (), {"to_a2a": lambda *args, **kwargs: Mock()}
        )()

    @agent_skill
    def test_skill_method(self):
        """Test skill method for agent."""
        return "test result"

    @agent_skill
    def another_skill_method(self):
        """Another test skill method."""
        return "another result"

    def regular_method(self):
        """Regular method without @agent_skill decorator."""
        return "regular result"

    def _private_method(self):
        """Private method that should be ignored."""
        return "private result"


class MockAgentNoSkills:
    """Mock agent class with no agent skills."""

    def __init__(self, agent_name="no_skills_agent"):
        self.agent_name = agent_name
        # Use simple objects instead of Mock to avoid them being treated as callable skills
        self.config = type("Config", (), {"pydantic_ai_system_prompt": "test prompt"})()
        self.pydantic_agent = type(
            "PydanticAgent", (), {"to_a2a": lambda *args, **kwargs: Mock()}
        )()

    def regular_method(self):
        """Regular method without @agent_skill decorator."""
        return "regular result"

    def _private_method(self):
        """Private method that should be ignored."""
        return "private result"


class TestCreateSkillsFromAgent:
    """Test suite for create_skills_from_agent function."""

    def test_extract_skills_from_agent_with_skills(self):
        """Test extracting skills from an agent with @agent_skill decorated methods."""
        # Arrange
        agent = MockAgent()

        # Act
        skills = create_skills_from_agent(agent)

        # Assert
        assert len(skills) == 2

        # Check first skill
        skill_names = [skill["id"] for skill in skills]
        assert "test_skill_method" in skill_names
        assert "another_skill_method" in skill_names

        # Find specific skills for detailed verification
        test_skill = next(s for s in skills if s["id"] == "test_skill_method")
        assert test_skill["name"] == "Test Skill Method"
        assert test_skill["description"] == "Test skill method for agent."
        assert test_skill["tags"] == ["test_agent"]
        assert test_skill["input_modes"] == ["application/json"]
        assert test_skill["output_modes"] == ["application/json"]

        another_skill = next(s for s in skills if s["id"] == "another_skill_method")
        assert another_skill["name"] == "Another Skill Method"
        assert another_skill["description"] == "Another test skill method."
        assert another_skill["tags"] == ["test_agent"]

    def test_extract_skills_from_agent_no_skills(self):
        """Test extracting skills from an agent with no @agent_skill methods."""
        # Arrange
        agent = MockAgentNoSkills()

        # Act
        skills = create_skills_from_agent(agent)

        # Assert
        assert len(skills) == 0

    def test_skill_creation_with_no_docstring(self):
        """Test skill creation when method has no docstring."""

        # Arrange
        class MockAgentNoDocstring:
            def __init__(self):
                self.agent_name = "no_doc_agent"

            @agent_skill
            def undocumented_skill(self):
                return "result"

        agent = MockAgentNoDocstring()

        # Act
        skills = create_skills_from_agent(agent)

        # Assert
        assert len(skills) == 1
        skill = skills[0]
        assert skill["id"] == "undocumented_skill"
        assert skill["description"] == "Executes the undocumented_skill skill"

    def test_skill_creation_with_multiline_docstring(self):
        """Test skill creation when method has multiline docstring (only first line used)."""

        # Arrange
        class MockAgentMultilineDoc:
            def __init__(self):
                self.agent_name = "multiline_agent"

            @agent_skill
            def multiline_skill(self):
                """First line of documentation.
                This is the second line.
                This is the third line.
                """
                return "result"

        agent = MockAgentMultilineDoc()

        # Act
        skills = create_skills_from_agent(agent)

        # Assert
        assert len(skills) == 1
        skill = skills[0]
        assert skill["description"] == "First line of documentation."

    def test_ignores_private_methods(self):
        """Test that private methods (starting with _) are ignored."""

        # Arrange
        class MockAgentPrivate:
            def __init__(self):
                self.agent_name = "private_agent"

            @agent_skill
            def _private_skill(self):
                """This should be ignored."""
                return "result"

            @agent_skill
            def public_skill(self):
                """This should be included."""
                return "result"

        agent = MockAgentPrivate()

        # Act
        skills = create_skills_from_agent(agent)

        # Assert
        assert len(skills) == 1
        assert skills[0]["id"] == "public_skill"

    def test_ignores_non_callable_attributes(self):
        """Test that non-callable attributes are ignored."""

        # Arrange
        class MockAgentWithAttributes:
            def __init__(self):
                self.agent_name = "attr_agent"
                self.some_attribute = "not callable"
                self.another_attr = 42

            @agent_skill
            def valid_skill(self):
                """Valid skill method."""
                return "result"

        agent = MockAgentWithAttributes()

        # Act
        skills = create_skills_from_agent(agent)

        # Assert
        assert len(skills) == 1
        assert skills[0]["id"] == "valid_skill"

    @patch("ai_research_assistant.a2a_services.fasta2a_wrapper.logger")
    def test_logging_skill_creation(self, mock_logger):
        """Test that skill creation is properly logged."""
        # Arrange
        agent = MockAgent()

        # Act
        skills = create_skills_from_agent(agent)

        # Assert
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        assert "Created 2 skills for agent test_agent" in call_args
        assert "test_skill_method" in call_args
        assert "another_skill_method" in call_args


class TestWrapAgentWithFasta2a:
    """Test suite for wrap_agent_with_fasta2a function."""

    @patch(
        "ai_research_assistant.a2a_services.fasta2a_wrapper.create_skills_from_agent"
    )
    @patch("ai_research_assistant.a2a_services.fasta2a_wrapper.logger")
    def test_wrap_agent_basic_functionality(self, mock_logger, mock_create_skills):
        """Test basic agent wrapping functionality."""
        # Arrange
        mock_agent = Mock()
        mock_agent.agent_name = "test_agent"
        mock_agent.config.pydantic_ai_system_prompt = "Test system prompt"
        mock_agent.pydantic_agent = Mock()

        mock_skills = [
            {
                "id": "test_skill",
                "name": "Test Skill",
                "description": "Test description",
                "tags": ["test_agent"],
                "input_modes": ["application/json"],
                "output_modes": ["application/json"],
            }
        ]
        mock_create_skills.return_value = mock_skills

        mock_app = Mock()
        mock_agent.pydantic_agent.to_a2a.return_value = mock_app

        # Act
        result = wrap_agent_with_fasta2a(
            agent_instance=mock_agent, url="http://localhost:8000", version="1.0.0"
        )

        # Assert
        mock_create_skills.assert_called_once_with(mock_agent)
        mock_agent.pydantic_agent.to_a2a.assert_called_once_with(
            name="test_agent",
            url="http://localhost:8000",
            version="1.0.0",
            description="Test system prompt",
            skills=mock_skills,
        )
        assert result == mock_app

        # Check logging
        mock_logger.info.assert_has_calls(
            [
                call("Wrapping agent 'test_agent' with FastA2A..."),
                call("Agent 'test_agent' wrapped successfully with 1 skills."),
            ]
        )

    @patch(
        "ai_research_assistant.a2a_services.fasta2a_wrapper.create_skills_from_agent"
    )
    @patch("ai_research_assistant.a2a_services.fasta2a_wrapper.logger")
    def test_wrap_agent_with_custom_parameters(self, mock_logger, mock_create_skills):
        """Test agent wrapping with custom URL and version."""
        # Arrange
        mock_agent = Mock()
        mock_agent.agent_name = "custom_agent"
        mock_agent.config.pydantic_ai_system_prompt = "Custom prompt"
        mock_agent.pydantic_agent = Mock()

        mock_skills = []
        mock_create_skills.return_value = mock_skills

        mock_app = Mock()
        mock_agent.pydantic_agent.to_a2a.return_value = mock_app

        # Act
        result = wrap_agent_with_fasta2a(
            agent_instance=mock_agent, url="http://custom-host:9000", version="2.1.3"
        )

        # Assert
        mock_agent.pydantic_agent.to_a2a.assert_called_once_with(
            name="custom_agent",
            url="http://custom-host:9000",
            version="2.1.3",
            description="Custom prompt",
            skills=mock_skills,
        )
        assert result == mock_app

    @patch(
        "ai_research_assistant.a2a_services.fasta2a_wrapper.create_skills_from_agent"
    )
    def test_wrap_agent_with_no_system_prompt(self, mock_create_skills):
        """Test agent wrapping when agent has no system prompt."""
        # Arrange
        mock_agent = Mock()
        mock_agent.agent_name = "no_prompt_agent"
        mock_agent.config = Mock()
        # Simulate getattr returning None for missing attribute
        mock_agent.config.pydantic_ai_system_prompt = None
        mock_agent.pydantic_agent = Mock()

        mock_skills = []
        mock_create_skills.return_value = mock_skills

        mock_app = Mock()
        mock_agent.pydantic_agent.to_a2a.return_value = mock_app

        # Act
        result = wrap_agent_with_fasta2a(agent_instance=mock_agent)

        # Assert
        mock_agent.pydantic_agent.to_a2a.assert_called_once()
        call_kwargs = mock_agent.pydantic_agent.to_a2a.call_args[1]
        assert call_kwargs["description"] is None

    @patch(
        "ai_research_assistant.a2a_services.fasta2a_wrapper.create_skills_from_agent"
    )
    def test_wrap_agent_with_default_parameters(self, mock_create_skills):
        """Test agent wrapping with default URL and version parameters."""
        # Arrange
        mock_agent = Mock()
        mock_agent.agent_name = "default_agent"
        mock_agent.config.pydantic_ai_system_prompt = "Default prompt"
        mock_agent.pydantic_agent = Mock()

        mock_skills = []
        mock_create_skills.return_value = mock_skills

        mock_app = Mock()
        mock_agent.pydantic_agent.to_a2a.return_value = mock_app

        # Act
        result = wrap_agent_with_fasta2a(agent_instance=mock_agent)

        # Assert
        mock_agent.pydantic_agent.to_a2a.assert_called_once_with(
            name="default_agent",
            url="http://localhost:8000",
            version="1.0.0",
            description="Default prompt",
            skills=mock_skills,
        )
        assert result == mock_app

    @patch(
        "ai_research_assistant.a2a_services.fasta2a_wrapper.create_skills_from_agent"
    )
    def test_wrap_agent_exception_handling(self, mock_create_skills):
        """Test that exceptions during agent wrapping are properly propagated."""
        # Arrange
        mock_agent = Mock()
        mock_agent.agent_name = "error_agent"
        mock_agent.config.pydantic_ai_system_prompt = "Error prompt"
        mock_agent.pydantic_agent = Mock()

        mock_skills = []
        mock_create_skills.return_value = mock_skills

        # Simulate an exception during to_a2a call
        mock_agent.pydantic_agent.to_a2a.side_effect = Exception(
            "A2A conversion failed"
        )

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            wrap_agent_with_fasta2a(agent_instance=mock_agent)

        assert str(exc_info.value) == "A2A conversion failed"


class TestAgentSkillDecorator:
    """Test suite for the @agent_skill decorator."""

    def test_agent_skill_decorator_marks_function(self):
        """Test that @agent_skill decorator properly marks functions."""

        # Arrange & Act
        @agent_skill
        def test_function():
            """Test function."""
            return "test"

        # Assert
        assert hasattr(test_function, "_is_agent_skill")
        assert test_function._is_agent_skill is True
        assert hasattr(test_function, "_skill_name")
        assert test_function._skill_name == "test_function"

    def test_agent_skill_decorator_preserves_function(self):
        """Test that @agent_skill decorator preserves original function behavior."""

        # Arrange & Act
        @agent_skill
        def test_function(x, y):
            """Test function that adds two numbers."""
            return x + y

        # Assert
        assert test_function(2, 3) == 5
        assert test_function.__doc__ == "Test function that adds two numbers."
        assert test_function.__name__ == "test_function"

    def test_agent_skill_decorator_on_method(self):
        """Test that @agent_skill decorator works on class methods."""

        # Arrange
        class TestClass:
            @agent_skill
            def test_method(self, value):
                """Test method."""
                return f"processed: {value}"

        # Act
        instance = TestClass()
        result = instance.test_method("test")

        # Assert
        assert result == "processed: test"
        assert hasattr(instance.test_method, "_is_agent_skill")
        assert instance.test_method._is_agent_skill is True


@pytest.fixture
def sample_agent():
    """Fixture providing a sample agent for testing."""
    return MockAgent("sample_agent")


@pytest.fixture
def empty_agent():
    """Fixture providing an agent with no skills for testing."""
    return MockAgentNoSkills("empty_agent")


class TestIntegration:
    """Integration tests for the fasta2a_wrapper module."""

    def test_end_to_end_skill_extraction_and_wrapping(self, sample_agent):
        """Test complete workflow from skill extraction to agent wrapping."""
        # Arrange
        sample_agent.config.pydantic_ai_system_prompt = "Integration test prompt"
        # Use a non-callable mock for pydantic_agent to avoid it being detected as a skill
        mock_pydantic_agent = type("PydanticAgent", (), {})()
        mock_pydantic_agent.to_a2a = Mock()
        sample_agent.pydantic_agent = mock_pydantic_agent
        mock_app = Mock()
        mock_pydantic_agent.to_a2a.return_value = mock_app

        # Act
        skills = create_skills_from_agent(sample_agent)
        wrapped_app = wrap_agent_with_fasta2a(sample_agent)

        # Assert
        assert len(skills) == 2
        assert wrapped_app == mock_app

        # Verify the agent was called with extracted skills
        mock_pydantic_agent.to_a2a.assert_called_once()
        call_kwargs = mock_pydantic_agent.to_a2a.call_args[1]
        assert call_kwargs["skills"] == skills
        assert call_kwargs["name"] == "sample_agent"
        assert call_kwargs["description"] == "Integration test prompt"

    def test_empty_agent_handling(self, empty_agent):
        """Test handling of agent with no skills."""
        # Arrange
        empty_agent.config.pydantic_ai_system_prompt = "Empty agent prompt"
        # Use a non-callable mock for pydantic_agent to avoid it being detected as a skill
        mock_pydantic_agent = type("PydanticAgent", (), {})()
        mock_pydantic_agent.to_a2a = Mock()
        empty_agent.pydantic_agent = mock_pydantic_agent
        mock_app = Mock()
        mock_pydantic_agent.to_a2a.return_value = mock_app

        # Act
        skills = create_skills_from_agent(empty_agent)
        wrapped_app = wrap_agent_with_fasta2a(empty_agent)

        # Assert
        assert len(skills) == 0
        assert wrapped_app == mock_app

        # Verify the agent was called with empty skills list
        mock_pydantic_agent.to_a2a.assert_called_once()
        call_kwargs = mock_pydantic_agent.to_a2a.call_args[1]
        assert call_kwargs["skills"] == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

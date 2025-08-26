#!/usr/bin/env python3
"""
Comprehensive tests for the a2a_services startup module.

This module tests the A2A service startup functionality including argument parsing,
agent initialization, LLM creation, and server startup.
"""

import json
import os
from unittest.mock import Mock, call, mock_open, patch

import pytest

from ai_research_assistant.a2a_services.startup import AGENT_REGISTRY, main


class TestAgentRegistry:
    """Test suite for the AGENT_REGISTRY constant."""

    def test_agent_registry_contains_expected_agents(self):
        """Test that AGENT_REGISTRY contains all expected agent types."""
        expected_agents = [
            "OrchestratorAgent",
            "DocumentAgent",
            "BrowserAgent",
            "DatabaseAgent",
        ]

        for agent_name in expected_agents:
            assert agent_name in AGENT_REGISTRY
            assert "agent_class" in AGENT_REGISTRY[agent_name]
            assert "config_class" in AGENT_REGISTRY[agent_name]

    def test_agent_registry_structure(self):
        """Test the structure of AGENT_REGISTRY entries."""
        for agent_name, agent_info in AGENT_REGISTRY.items():
            assert isinstance(agent_info, dict)
            assert len(agent_info) == 2
            assert "agent_class" in agent_info
            assert "config_class" in agent_info
            assert agent_info["agent_class"] is not None
            assert agent_info["config_class"] is not None


class TestMainFunction:
    """Test suite for the main function."""

    @patch("ai_research_assistant.a2a_services.startup.uvicorn.run")
    @patch("ai_research_assistant.a2a_services.startup.wrap_agent_with_fasta2a")
    @patch("ai_research_assistant.a2a_services.startup.get_llm_factory")
    @patch("ai_research_assistant.a2a_services.startup.create_mcp_toolsets_from_config")
    @patch("ai_research_assistant.a2a_services.startup.load_dotenv")
    @patch("builtins.open", new_callable=mock_open)
    @patch("ai_research_assistant.a2a_services.startup.argparse.ArgumentParser")
    def test_successful_orchestrator_startup(
        self,
        mock_argparse,
        mock_file_open,
        mock_load_dotenv,
        mock_create_mcp,
        mock_get_llm_factory,
        mock_wrap_agent,
        mock_uvicorn_run,
    ):
        """Test successful startup of OrchestratorAgent."""
        # Arrange
        mock_parser = Mock()
        mock_argparse.return_value = mock_parser

        mock_args = Mock()
        mock_args.card_path = "/path/to/orchestrator_agent.json"
        mock_args.host = "localhost"
        mock_args.port = 8001
        mock_parser.parse_args.return_value = mock_args

        card_data = {
            "agent_name": "OrchestratorAgent",
            "description": "Test orchestrator",
        }
        mock_file_open.return_value.read.return_value = json.dumps(card_data)

        # Mock dependencies
        mock_toolsets = [Mock(), Mock()]
        mock_create_mcp.return_value = mock_toolsets

        mock_llm_factory = Mock()
        mock_llm_instance = Mock()
        mock_get_llm_factory.return_value = mock_llm_factory
        mock_llm_factory.create_llm_from_config.return_value = mock_llm_instance

        mock_config = Mock()
        mock_config.llm_provider = "openai"
        mock_config.llm_model_name = "gpt-4"

        mock_agent_instance = Mock()
        mock_agent_class = Mock()
        mock_config_class = Mock()
        mock_config_class.return_value = mock_config
        mock_agent_class.return_value = mock_agent_instance

        mock_app = Mock()
        mock_wrap_agent.return_value = mock_app

        # Patch the registry
        with patch.dict(
            AGENT_REGISTRY,
            {
                "OrchestratorAgent": {
                    "agent_class": mock_agent_class,
                    "config_class": mock_config_class,
                }
            },
        ):
            # Act
            main()

        # Assert key function calls
        mock_load_dotenv.assert_called_once()
        mock_create_mcp.assert_called_once()
        mock_llm_factory.create_llm_from_config.assert_called_once_with(
            {"provider": "openai", "model_name": "gpt-4"}
        )
        mock_agent_class.assert_called_once_with(
            config=mock_config, llm_instance=mock_llm_instance, toolsets=mock_toolsets
        )
        mock_wrap_agent.assert_called_once_with(
            agent_instance=mock_agent_instance,
            url="http://localhost:8001",
            version="1.0.0",
        )
        mock_uvicorn_run.assert_called_once_with(
            mock_app, host="localhost", port=8001, log_level="info"
        )

    @patch("ai_research_assistant.a2a_services.startup.logger")
    @patch("builtins.open", new_callable=mock_open)
    @patch("ai_research_assistant.a2a_services.startup.argparse.ArgumentParser")
    def test_missing_agent_name_in_card(
        self, mock_argparse, mock_file_open, mock_logger
    ):
        """Test handling of agent card missing agent_name field."""
        mock_parser = Mock()
        mock_argparse.return_value = mock_parser

        mock_args = Mock()
        mock_args.card_path = "/path/to/invalid_card.json"
        mock_parser.parse_args.return_value = mock_args

        card_data = {"description": "Test agent without name"}
        mock_file_open.return_value.read.return_value = json.dumps(card_data)

        main()

        mock_logger.error.assert_called()
        error_call = mock_logger.error.call_args[0][0]
        assert "Error reading agent card" in error_call

    @patch("ai_research_assistant.a2a_services.startup.logger")
    @patch("ai_research_assistant.a2a_services.startup.load_dotenv")
    @patch("builtins.open", side_effect=FileNotFoundError("File not found"))
    @patch("ai_research_assistant.a2a_services.startup.argparse.ArgumentParser")
    def test_card_file_not_found(
        self, mock_argparse, mock_file_open, mock_load_dotenv, mock_logger
    ):
        """Test handling of missing agent card file."""
        mock_parser = Mock()
        mock_argparse.return_value = mock_parser

        mock_args = Mock()
        mock_args.card_path = "/path/to/nonexistent.json"
        mock_parser.parse_args.return_value = mock_args

        main()

        mock_logger.error.assert_called()
        error_call = mock_logger.error.call_args[0][0]
        assert "Error reading agent card" in error_call

    @patch("ai_research_assistant.a2a_services.startup.logger")
    @patch("builtins.open", new_callable=mock_open)
    @patch("ai_research_assistant.a2a_services.startup.argparse.ArgumentParser")
    def test_unknown_agent_name(self, mock_argparse, mock_file_open, mock_logger):
        """Test handling of unknown agent name in registry."""
        mock_parser = Mock()
        mock_argparse.return_value = mock_parser

        mock_args = Mock()
        mock_args.card_path = "/path/to/unknown_agent.json"
        mock_parser.parse_args.return_value = mock_args

        card_data = {"agent_name": "UnknownAgent"}
        mock_file_open.return_value.read.return_value = json.dumps(card_data)

        main()

        mock_logger.error.assert_called()
        error_call = mock_logger.error.call_args[0][0]
        assert "Configuration error: Unknown agent name: UnknownAgent" in error_call

    @patch("ai_research_assistant.a2a_services.startup.logger")
    @patch("ai_research_assistant.a2a_services.startup.create_mcp_toolsets_from_config")
    @patch("builtins.open", new_callable=mock_open)
    @patch("ai_research_assistant.a2a_services.startup.argparse.ArgumentParser")
    def test_mcp_toolsets_creation_failure(
        self, mock_argparse, mock_file_open, mock_create_mcp, mock_logger
    ):
        """Test handling of MCP toolsets creation failure."""
        mock_parser = Mock()
        mock_argparse.return_value = mock_parser

        mock_args = Mock()
        mock_args.card_path = "/path/to/agent.json"
        mock_parser.parse_args.return_value = mock_args

        card_data = {"agent_name": "OrchestratorAgent"}
        mock_file_open.return_value.read.return_value = json.dumps(card_data)

        mock_create_mcp.side_effect = Exception("MCP initialization failed")

        main()

        mock_logger.error.assert_called()
        error_call = mock_logger.error.call_args[0][0]
        assert "Failed to start A2A service for agent 'OrchestratorAgent'" in error_call

    @patch.dict(os.environ, {"A2A_DEFAULT_HOST": "custom-host"})
    @patch("ai_research_assistant.a2a_services.startup.uvicorn.run")
    @patch("ai_research_assistant.a2a_services.startup.wrap_agent_with_fasta2a")
    @patch("ai_research_assistant.a2a_services.startup.get_llm_factory")
    @patch("ai_research_assistant.a2a_services.startup.create_mcp_toolsets_from_config")
    @patch("ai_research_assistant.a2a_services.startup.load_dotenv")
    @patch("builtins.open", new_callable=mock_open)
    @patch("ai_research_assistant.a2a_services.startup.argparse.ArgumentParser")
    def test_custom_host_from_env(
        self,
        mock_argparse,
        mock_file_open,
        mock_load_dotenv,
        mock_create_mcp,
        mock_get_llm_factory,
        mock_wrap_agent,
        mock_uvicorn_run,
    ):
        """Test using custom host from environment variable."""
        mock_parser = Mock()
        mock_argparse.return_value = mock_parser

        mock_args = Mock()
        mock_args.card_path = "/path/to/agent.json"
        mock_args.host = "custom-host"
        mock_args.port = 8001
        mock_parser.parse_args.return_value = mock_args

        card_data = {"agent_name": "OrchestratorAgent"}
        mock_file_open.return_value.read.return_value = json.dumps(card_data)

        # Mock successful setup
        mock_create_mcp.return_value = []
        mock_llm_factory = Mock()
        mock_llm_instance = Mock()
        mock_get_llm_factory.return_value = mock_llm_factory
        mock_llm_factory.create_llm_from_config.return_value = mock_llm_instance

        mock_config = Mock()
        mock_config.llm_provider = "openai"
        mock_config.llm_model_name = "gpt-4"

        mock_config_class = Mock()
        mock_config_class.return_value = mock_config

        mock_agent_instance = Mock()
        mock_agent_class = Mock()
        mock_agent_class.return_value = mock_agent_instance

        mock_app = Mock()
        mock_wrap_agent.return_value = mock_app

        with patch.dict(
            AGENT_REGISTRY,
            {
                "OrchestratorAgent": {
                    "agent_class": mock_agent_class,
                    "config_class": mock_config_class,
                }
            },
        ):
            main()

        mock_uvicorn_run.assert_called_once_with(
            mock_app, host="custom-host", port=8001, log_level="info"
        )


class TestArgumentParsing:
    """Test suite for argument parsing functionality."""

    @patch("ai_research_assistant.a2a_services.startup.argparse.ArgumentParser")
    def test_argument_parser_setup(self, mock_argparse):
        """Test that argument parser is configured correctly."""
        mock_parser = Mock()
        mock_argparse.return_value = mock_parser
        mock_parser.parse_args.side_effect = SystemExit(0)

        try:
            main()
        except SystemExit:
            pass

        mock_argparse.assert_called_once_with(
            description="Startup script for AI Research Agent A2A services."
        )

        expected_calls = [
            call(
                "--card-path",
                type=str,
                required=True,
                help="Path to the agent's JSON card file.",
            ),
            call(
                "--host",
                type=str,
                default=os.getenv("A2A_DEFAULT_HOST", "0.0.0.0"),
                help="Host for the A2A service.",
            ),
            call("--port", type=int, required=True, help="Port for the A2A service."),
        ]

        mock_parser.add_argument.assert_has_calls(expected_calls, any_order=False)


class TestErrorHandling:
    """Test suite for error handling scenarios."""

    @patch("ai_research_assistant.a2a_services.startup.logger")
    @patch("builtins.open", new_callable=mock_open)
    @patch("ai_research_assistant.a2a_services.startup.argparse.ArgumentParser")
    def test_invalid_json_in_card(self, mock_argparse, mock_file_open, mock_logger):
        """Test handling of invalid JSON in agent card."""
        mock_parser = Mock()
        mock_argparse.return_value = mock_parser

        mock_args = Mock()
        mock_args.card_path = "/path/to/invalid.json"
        mock_parser.parse_args.return_value = mock_args

        mock_file_open.return_value.read.return_value = "{ invalid json content"

        main()

        mock_logger.error.assert_called()
        error_call = mock_logger.error.call_args[0][0]
        assert "Error reading agent card" in error_call

    @patch("ai_research_assistant.a2a_services.startup.logger")
    @patch("ai_research_assistant.a2a_services.startup.get_llm_factory")
    @patch("ai_research_assistant.a2a_services.startup.create_mcp_toolsets_from_config")
    @patch("builtins.open", new_callable=mock_open)
    @patch("ai_research_assistant.a2a_services.startup.argparse.ArgumentParser")
    def test_llm_creation_failure(
        self,
        mock_argparse,
        mock_file_open,
        mock_create_mcp,
        mock_get_llm_factory,
        mock_logger,
    ):
        """Test handling of LLM instance creation failure."""
        mock_parser = Mock()
        mock_argparse.return_value = mock_parser

        mock_args = Mock()
        mock_args.card_path = "/path/to/agent.json"
        mock_parser.parse_args.return_value = mock_args

        card_data = {"agent_name": "DocumentAgent"}
        mock_file_open.return_value.read.return_value = json.dumps(card_data)

        mock_create_mcp.return_value = []

        mock_llm_factory = Mock()
        mock_get_llm_factory.return_value = mock_llm_factory
        mock_llm_factory.create_llm_from_config.side_effect = Exception(
            "LLM creation failed"
        )

        mock_config = Mock()
        mock_config.llm_provider = "invalid_provider"
        mock_config.llm_model_name = "invalid_model"

        mock_config_class = Mock()
        mock_config_class.return_value = mock_config

        with patch.dict(
            AGENT_REGISTRY,
            {
                "DocumentAgent": {
                    "agent_class": Mock(),
                    "config_class": mock_config_class,
                }
            },
        ):
            main()

        mock_logger.error.assert_called()
        error_call = mock_logger.error.call_args[0][0]
        assert "Failed to start A2A service for agent 'DocumentAgent'" in error_call


@pytest.fixture
def sample_args():
    """Fixture providing sample command line arguments."""
    args = Mock()
    args.card_path = "/path/to/test_agent.json"
    args.host = "localhost"
    args.port = 8000
    return args


@pytest.fixture
def sample_card_data():
    """Fixture providing sample agent card data."""
    return {
        "agent_name": "TestAgent",
        "description": "Test agent for unit testing",
        "version": "1.0.0",
    }


class TestIntegration:
    """Integration tests for the startup module."""

    @patch("ai_research_assistant.a2a_services.startup.logger")
    def test_logging_during_startup(self, mock_logger, sample_args, sample_card_data):
        """Test that appropriate log messages are generated during startup."""
        with patch(
            "ai_research_assistant.a2a_services.startup.argparse.ArgumentParser"
        ) as mock_argparse:
            mock_parser = Mock()
            mock_argparse.return_value = mock_parser
            mock_parser.parse_args.return_value = sample_args

            with patch(
                "builtins.open", mock_open(read_data=json.dumps(sample_card_data))
            ):
                with patch.dict(
                    AGENT_REGISTRY,
                    {"TestAgent": {"agent_class": Mock(), "config_class": Mock()}},
                ):
                    try:
                        main()
                    except:
                        pass  # Ignore other exceptions for this test

            # Check that info logs were called
            assert mock_logger.info.called


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

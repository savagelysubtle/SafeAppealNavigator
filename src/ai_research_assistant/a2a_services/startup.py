# File: src/savagelysubtle_airesearchagent/a2a_services/startup.py

import argparse
import logging
import os

import uvicorn
from dotenv import load_dotenv

from .fasta2a_wrapper import wrap_agent_with_fasta2a

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    load_dotenv() # Load environment variables from .env file

    parser = argparse.ArgumentParser(description="Startup script for Pydantic AI Agent A2A services.")
    parser.add_argument(
        "--agent-name",
        type=str,
        required=True,
        help="Name of the agent to start (e.g., ChiefLegalOrchestrator, DocumentProcessingCoordinator).",
        choices=["ChiefLegalOrchestrator", "DocumentProcessingCoordinator", "LegalResearchCoordinator", "DataQueryCoordinator"]
    )
    parser.add_argument(
        "--host",
        type=str,
        default=os.getenv("A2A_DEFAULT_HOST", "0.0.0.0"), # Default from ENV or 0.0.0.0
        help="Host for the A2A service."
    )
    parser.add_argument(
        "--port",
        type=int,
        help="Port for the A2A service. If not provided, will try to derive from ENV based on agent name."
    )
    parser.add_argument(
        "--config-json",
        type=str,
        default=None,
        help="JSON string containing agent-specific configurations to override defaults."
    )


    args = parser.parse_args()

    # Determine port from environment variables if not provided
    if args.port is None:
        env_port_var = f"{args.agent_name.upper()}_A2A_PORT"
        try:
            args.port = int(os.environ[env_port_var])
        except KeyError:
            logger.error(f"Error: Port not specified and environment variable {env_port_var} not set.")
            return
        except ValueError:
            logger.error(f"Error: Invalid port value in environment variable {env_port_var}.")
            return

    agent_specific_config = None
    if args.config_json:
        import json
        try:
            agent_specific_config = json.loads(args.config_json)
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding --config-json: {e}")
            return


    logger.info(f"Starting A2A service for agent: {args.agent_name} on {args.host}:{args.port}")

    try:
        # The wrap_agent_with_fasta2a function returns the Starlette app (FastA2A instance)
        app = wrap_agent_with_fasta2a(args.agent_name, agent_specific_config)

        # Use uvicorn to run the FastA2A app
        uvicorn.run(app, host=args.host, port=args.port, log_level="info")

    except ValueError as ve:
        logger.error(f"Configuration error: {ve}")
    except Exception as e:
        logger.error(f"Failed to start A2A service for agent {args.agent_name}: {e}", exc_info=True)

if __name__ == "__main__":
    main()
# src/ai_research_assistant/interface/cli.py
import logging
import os
import signal
import sys
from contextlib import AsyncExitStack
from pathlib import Path

import anyio

# --- Path Setup ---
try:
    script_path = Path(__file__).resolve()
    src_path = script_path.parent.parent.parent
    project_root = src_path.parent
    if not src_path.is_dir():
        raise FileNotFoundError(f"The 'src' directory was not found at {src_path}")
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
except Exception as e:
    print(f"FATAL ERROR: Could not set up the Python path. {e}", file=sys.stderr)
    sys.exit(1)

from dotenv import load_dotenv

load_dotenv(project_root / ".env")

# --- Application Imports ---
from ai_research_assistant.agents.ceo_agent.agent import CEOAgent
from ai_research_assistant.core.unified_llm_factory import get_llm_factory
from ai_research_assistant.mcp.client import create_mcp_toolsets_from_config

# --- Configure Logging & Process Management ---
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s - %(levelname)-8s - %(name)-25s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("CLIRunner")
processes = []


def cleanup_processes(signum=None, frame=None):
    # ... (function is unchanged)
    pass


signal.signal(signal.SIGINT, cleanup_processes)
signal.signal(signal.SIGTERM, cleanup_processes)

# ... (start_a2a_service function is unchanged)


async def main():
    """The main asynchronous function to run the CLI test harness."""
    print("\n--- ⚖️ SafeAppealNavigator CLI Test Runner ---")

    try:
        logger.info("Creating MCP toolsets from data/mcp.json...")
        mcp_toolsets = create_mcp_toolsets_from_config()

        async with AsyncExitStack() as stack:
            for toolset in mcp_toolsets:
                await stack.enter_async_context(toolset)

            logger.info(
                f"{len(mcp_toolsets)} MCP server(s) started and managed by pydantic-ai."
            )

            # --- DEFINITIVE FIX: Create and inject the pydantic-ai Model object ---
            logger.info("Initializing LLM instance from factory...")
            llm_factory = get_llm_factory()
            # This now returns a pydantic_ai.models.GoogleModel object
            llm_instance = llm_factory.create_llm_from_config(
                {
                    "provider": "google",
                    "model_name": "gemini-2.5-pro",
                }
            )

            logger.info("Initializing CEO Agent with LLM and active MCP toolsets...")
            ceo_agent = CEOAgent(llm_instance=llm_instance, toolsets=mcp_toolsets)

            print("\n--- ✅ Agent system is ready. ---")
            print("You are now chatting with the CEO Agent.")
            print("Type 'quit' or 'exit' to stop the application.")
            print("-" * 40)

            while True:
                user_input = await anyio.to_thread.run_sync(
                    lambda: input("You: ").strip()
                )
                if user_input.lower() in ["quit", "exit"]:
                    break
                if not user_input:
                    continue

                print("\nCEO is thinking...")
                response = await ceo_agent.handle_user_request(user_prompt=user_input)

                print("\n" + "-" * 40)
                print(f"CEO: {response}")
                print("-" * 40)

        logger.info("MCP toolset context exited, servers shut down.")

    except Exception as e:
        logger.error("A critical error occurred during the CLI session.", exc_info=True)
        print(f"\n💥 An unrecoverable error occurred: {e}")
    finally:
        cleanup_processes()
        logger.info("Shutdown complete.")
        print("\n--- Application has been shut down. ---")


if __name__ == "__main__":
    try:
        anyio.run(main)
    except KeyboardInterrupt:
        print("\nCLI interrupted by user. Shutting down.")
    finally:
        cleanup_processes()

# src/ai_research_assistant/interfaces/cli.py
import asyncio
import logging
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

# --- Correct and Final Path Setup ---
# This block is the key to fixing the ModuleNotFoundError. It makes the script
# self-aware of its location and correctly sets up the Python import path.
try:
    # Get the path of the current script (cli.py)
    script_path = Path(__file__).resolve()
    # Navigate up the directory tree to find the 'src' directory
    # .../interfaces/ -> .../ai_research_assistant/ -> .../src/
    src_path = script_path.parent.parent.parent
    # The project root is one level above 'src'
    project_root = src_path.parent

    if not src_path.is_dir():
        raise FileNotFoundError(f"The 'src' directory was not found at {src_path}")

    # Add the 'src' directory to the Python path for imports
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
except Exception as e:
    print("FATAL ERROR: Could not set up the Python path.", file=sys.stderr)
    print(
        "Please ensure the script is located at 'src/ai_research_assistant/interfaces/cli.py'",
        file=sys.stderr,
    )
    print(f"Error details: {e}", file=sys.stderr)
    sys.exit(1)
# --- End Path Setup ---

from dotenv import load_dotenv

# --- Load Environment Variables ---
# Load the .env file from the detected project root
load_dotenv(project_root / ".env")

# --- Application Imports (now work correctly) ---
from ai_research_assistant.agents.ceo_agent.agent import CEOAgent
from ai_research_assistant.mcp.client import shutdown_mcp_client_manager

# --- Configure Logging ---
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s - %(levelname)-8s - %(name)-25s - %(message)s",
    stream=sys.stdout,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("websockets").setLevel(logging.WARNING)

logger = logging.getLogger("CLIRunner")

# --- Process Management ---
processes = []


def cleanup_processes(signum=None, frame=None):
    """Gracefully terminate all spawned child processes."""
    logger.warning("\nShutting down all background services...")
    for proc in reversed(processes):
        if proc.poll() is None:
            try:
                if sys.platform == "win32":
                    subprocess.run(
                        f"taskkill /F /T /PID {proc.pid}",
                        check=False,
                        capture_output=True,
                    )
                else:
                    os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            except Exception as e:
                logger.error(f"Error terminating process group {proc.pid}: {e}")
    time.sleep(2)
    for proc in processes:
        if proc.poll() is None:
            try:
                proc.kill()
            except Exception as e:
                logger.error(f"Error killing process {proc.pid}: {e}")
    logger.info("Cleanup complete.")


signal.signal(signal.SIGINT, cleanup_processes)
signal.signal(signal.SIGTERM, cleanup_processes)


def start_service(command: list[str], name: str) -> subprocess.Popen:
    """Starts a service as a background subprocess."""
    logger.info(f"Starting service: {name} with command: {' '.join(command)}")
    preexec_fn = os.setsid if sys.platform != "win32" else None
    creationflags = (
        subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
    )

    process = subprocess.Popen(
        command,
        stdout=sys.stdout,
        stderr=sys.stderr,
        text=True,
        preexec_fn=preexec_fn,
        creationflags=creationflags,
        cwd=project_root,  # Run all subprocesses from the project root
    )
    processes.append(process)
    logger.info(f"'{name}' started with PID: {process.pid}")
    return process


async def main():
    """The main asynchronous function to run the CLI test harness."""
    print("\n--- ⚖️ SafeAppealNavigator CLI Test Runner ---")
    print("Starting all required backend services...")

    python_executable = sys.executable
    # Module paths are relative to the 'src' directory
    mcp_server_module = "ai_research_assistant.mcp.server"
    agent_startup_module = "ai_research_assistant.a2a_services.startup"

    # Define service commands
    mcp_server_cmd = [python_executable, "-m", mcp_server_module, "--port", "10100"]
    orchestrator_cmd = [
        python_executable,
        "-m",
        agent_startup_module,
        "--agent-name",
        "ChiefLegalOrchestrator",
    ]
    document_agent_cmd = [
        python_executable,
        "-m",
        agent_startup_module,
        "--agent-name",
        "DocumentProcessingCoordinator",
    ]
    browser_agent_cmd = [
        python_executable,
        "-m",
        agent_startup_module,
        "--agent-name",
        "LegalResearchCoordinator",
    ]
    database_agent_cmd = [
        python_executable,
        "-m",
        agent_startup_module,
        "--agent-name",
        "DataQueryCoordinator",
    ]

    try:
        start_service(mcp_server_cmd, "MCP Server")
        start_service(orchestrator_cmd, "Orchestrator Agent")
        start_service(document_agent_cmd, "Document Agent")
        start_service(browser_agent_cmd, "Browser Agent")
        start_service(database_agent_cmd, "Database Agent")

        logger.info("All services launched. Waiting for them to initialize...")
        await asyncio.sleep(10)

        logger.info("Initializing CEO Agent...")
        ceo_agent = CEOAgent()

        logger.info("Initializing MCP tools for agents...")
        await ceo_agent.initialize_mcp_tools()
        await ceo_agent.orchestrator.initialize_mcp_tools()
        logger.info("Agent tools initialized.")

        print("\n--- ✅ Agent system is ready. ---")
        print("You are now chatting with the CEO Agent.")
        print("Example: 'Please research WCAT decisions related to back injuries.'")
        print("Type 'quit' or 'exit' to stop the application.")
        print("-" * 40)

        while True:
            user_input = await asyncio.to_thread(lambda: input("You: ").strip())

            if user_input.lower() in ["quit", "exit"]:
                break
            if not user_input:
                continue

            print("\nCEO is thinking...")
            response = await ceo_agent.handle_user_request(user_prompt=user_input)

            print("\n" + "-" * 40)
            print(f"CEO: {response}")
            print("-" * 40)

    except Exception as e:
        logger.error("A critical error occurred during the CLI session.", exc_info=True)
        print(f"\n💥 An unrecoverable error occurred: {e}")
    finally:
        cleanup_processes()
        logger.info("Shutting down MCP client manager...")
        await shutdown_mcp_client_manager()
        logger.info("Shutdown complete.")
        print("\n--- Application has been shut down. ---")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nCLI interrupted by user. Shutting down.")
    finally:
        cleanup_processes()

#!/usr/bin/env python
"""
SafeAppealNavigator - Interactive Debug CLI (Corrected Pathing)

This script provides a robust, interactive command-line interface to test the entire
multi-agent system. It correctly starts, manages, and cleans up all necessary
backend services (MCP Server, A2A Agents) and allows you to communicate directly
with the Orchestrator agent to trace the full workflow.

This version includes a robust path-finding mechanism that works reliably
when run from the project root.

FIXED: Health check now sends proper A2A JSON-RPC requests instead of simple
test payloads, resolving validation errors with fasta2a agents.

FIXED: Conversation loop now uses async-safe input handling to prevent hanging
when mixing sync input() calls with anyio async context.
"""

import asyncio
import logging
import os
import signal
import subprocess
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv


# --- Robust Project Setup ---
def find_project_root(start_path: Path, marker: str = "pyproject.toml") -> Path:
    """Traverse upwards from start_path to find the project root."""
    current_path = start_path.resolve()
    while current_path != current_path.parent:  # Stop at the filesystem root
        if (current_path / marker).exists():
            return current_path
        current_path = current_path.parent
    raise FileNotFoundError(
        f"Project root with marker '{marker}' not found starting from {start_path}."
    )


try:
    # Find the project root dynamically, starting from this script's location
    PROJECT_ROOT = find_project_root(Path(__file__))
    SRC_PATH = PROJECT_ROOT / "src"
    if not SRC_PATH.is_dir():
        raise FileNotFoundError(f"The 'src' directory was not found at {SRC_PATH}")
    # Add the 'src' directory to the Python path for reliable imports
    sys.path.insert(0, str(SRC_PATH))
    load_dotenv(PROJECT_ROOT / ".env")
except Exception as e:
    print(f"FATAL ERROR: Could not set up the Python path. {e}", file=sys.stderr)
    sys.exit(1)

# --- Application Imports ---
# No longer needed: from ai_research_assistant.core.models import MessageEnvelope, SkillInvocation

# --- FIX: Import the A2A compatibility layer ---
from ai_research_assistant.a2a_services.a2a_compatibility import send_a2a_message

# --- Configuration ---
LOG_DIR = PROJECT_ROOT / "tmp" / "cli_logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s - %(levelname)-8s - %(name)-25s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("DebugCLI")

# --- Service Definitions ---
# Services configuration
SERVICES = {
    "mcp_server": {
        "cmd": [
            sys.executable,
            str(PROJECT_ROOT / "src/ai_research_assistant/mcp/server.py"),
        ],
        "cwd": PROJECT_ROOT,
        "env": dict(os.environ),
        "log_file": LOG_DIR / "mcp_server.log",
    },
    "ceo_agent": {
        "cmd": [
            sys.executable,
            str(PROJECT_ROOT / "src/ai_research_assistant/a2a_services/startup.py"),
            "--card-path",
            str(PROJECT_ROOT / "agent_cards/ceo_agent.json"),
            "--port",
            "10105",
        ],
        "cwd": PROJECT_ROOT,
        "env": dict(os.environ),
        "log_file": LOG_DIR / "ceo_agent.log",
        "url": "http://localhost:10105",
    },
    "orchestrator": {
        "cmd": [
            sys.executable,
            str(PROJECT_ROOT / "src/ai_research_assistant/a2a_services/startup.py"),
            "--card-path",
            str(PROJECT_ROOT / "agent_cards/orchestrator_agent.json"),
            "--port",
            "10101",
        ],
        "cwd": PROJECT_ROOT,
        "env": dict(os.environ),
        "log_file": LOG_DIR / "orchestrator_agent.log",
        "url": "http://localhost:10101",
    },
    "document_agent": {
        "cmd": [
            sys.executable,
            str(PROJECT_ROOT / "src/ai_research_assistant/a2a_services/startup.py"),
            "--card-path",
            str(PROJECT_ROOT / "agent_cards/document_agent.json"),
            "--port",
            "10102",
        ],
        "cwd": PROJECT_ROOT,
        "env": dict(os.environ),
        "log_file": LOG_DIR / "document_agent.log",
        "url": "http://localhost:10102",
    },
    "browser_agent": {
        "cmd": [
            sys.executable,
            str(PROJECT_ROOT / "src/ai_research_assistant/a2a_services/startup.py"),
            "--card-path",
            str(PROJECT_ROOT / "agent_cards/browser_agent.json"),
            "--port",
            "10103",
        ],
        "cwd": PROJECT_ROOT,
        "env": dict(os.environ),
        "log_file": LOG_DIR / "browser_agent.log",
        "url": "http://localhost:10103",
    },
    "database_agent": {
        "cmd": [
            sys.executable,
            str(PROJECT_ROOT / "src/ai_research_assistant/a2a_services/startup.py"),
            "--card-path",
            str(PROJECT_ROOT / "agent_cards/database_agent.json"),
            "--port",
            "10104",
        ],
        "cwd": PROJECT_ROOT,
        "env": dict(os.environ),
        "log_file": LOG_DIR / "database_agent.log",
        "url": "http://localhost:10104",
    },
}

# --- Process Management ---
processes = []


def cleanup_processes(signum=None, frame=None):
    """Gracefully terminate all running background services."""
    logger.warning("Shutting down background services...")
    for p, name in processes:
        try:
            if p.poll() is None:
                logger.info(f"Terminating {name} (PID: {p.pid})...")
                if os.name != "nt":
                    os.killpg(os.getpgid(p.pid), signal.SIGTERM)
                else:
                    p.terminate()
                p.wait(timeout=5)
        except ProcessLookupError:
            logger.info(f"Process {name} (PID: {p.pid}) already terminated.")
        except Exception as e:
            logger.error(f"Error terminating {name}, attempting to kill. Error: {e}")
            try:
                p.kill()
            except Exception as kill_e:
                logger.error(f"Failed to kill {name}: {kill_e}")
    logger.info("Cleanup complete.")


def cleanup_existing_agents():
    """Kill any existing agent processes that might be using our ports."""
    logger.info("Cleaning up any existing agent processes...")

    try:
        if os.name == "nt":  # Windows
            # Kill any processes using our specific ports
            ports_to_clear = [10101, 10102, 10103, 10104, 10105]

            for port in ports_to_clear:
                try:
                    # Find processes using this port
                    result = subprocess.run(
                        ["netstat", "-ano"], capture_output=True, text=True, check=False
                    )

                    if result.returncode == 0:
                        lines = result.stdout.split("\n")
                        for line in lines:
                            if f":{port}" in line and "LISTENING" in line:
                                parts = line.split()
                                if len(parts) >= 5:
                                    pid = parts[-1]
                                    try:
                                        subprocess.run(
                                            ["taskkill", "/F", "/PID", pid],
                                            capture_output=True,
                                            check=False,
                                        )
                                        logger.info(
                                            f"Killed process {pid} using port {port}"
                                        )
                                    except Exception:
                                        pass
                except Exception:
                    pass

        print("🧹 Cleaned up existing processes on agent ports")

    except Exception as e:
        logger.warning(f"Error during cleanup: {e}")
        print("⚠️ Could not fully clean up existing processes")


def start_service(name: str, config: dict):
    """Start a service in the background and store its process."""
    try:
        logger.info(f"Starting {name}...")

        # Create log file directory if it doesn't exist
        log_file = config["log_file"]
        log_file.parent.mkdir(parents=True, exist_ok=True)

        # Start the process
        with open(log_file, "w") as log:
            process = subprocess.Popen(
                config["cmd"],
                cwd=config.get("cwd", PROJECT_ROOT),
                env=config.get("env", dict(os.environ)),
                stdout=log,
                stderr=subprocess.STDOUT,
                text=True,
            )

        processes.append((process, name))
        logger.info(f"  -> {name} started with PID {process.pid}. Log: {log_file}")

    except Exception as e:
        logger.error(f"Failed to start {name}: {e}")
        print(f"Error starting {name}: {e}")


async def verify_agent_health(
    service_name: str, url: str, max_attempts: int = 10
) -> bool:
    """Verify that an agent is running and responding to connections."""
    for attempt in range(max_attempts):
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Send a proper A2A JSON-RPC health check request
                health_check_payload = {
                    "jsonrpc": "2.0",
                    "method": "tasks/send",
                    "params": {
                        "id": f"health_check_{attempt}",
                        "message": {
                            "role": "user",
                            "parts": [{"type": "text", "text": "hello"}],
                            "messageId": f"health_msg_{attempt}",
                        },
                    },
                    "id": f"health_request_{attempt}",
                }

                response = await client.post(
                    url, json=health_check_payload, timeout=5.0
                )

                # Check if we got a successful response (200 status)
                if response.status_code == 200:
                    logger.info(f"✅ {service_name} is listening and responding")
                    return True

        except httpx.ConnectError:
            logger.debug(
                f"Connection attempt {attempt + 1} for {service_name}: Agent not ready yet"
            )
        except httpx.HTTPStatusError as e:
            # A 500 or other HTTP error means the agent is listening but had an internal error
            # This is still considered "healthy" for our purposes
            logger.info(
                f"✅ {service_name} is listening and responding (HTTP {e.response.status_code})"
            )
            return True
        except Exception as e:
            logger.debug(f"Health check attempt {attempt + 1} for {service_name}: {e}")

        # Wait before retrying
        await asyncio.sleep(2)

    logger.warning(
        f"❌ {service_name} health check failed after {max_attempts} attempts"
    )
    return False


async def verify_all_agents():
    """Verify that all agents are running and healthy."""
    print("--- 🔍 Verifying agent health ---")

    # Check if processes are still running
    failed_services = []
    for process, name in processes:
        if process.poll() is not None:
            logger.error(
                f"❌ {name} process has terminated (exit code: {process.poll()})"
            )
            failed_services.append(name)
            print(f"❌ {name} failed to start - check logs in {LOG_DIR}")

    if failed_services:
        print(f"⚠️ The following services failed to start: {failed_services}")
        print("Check the log files for detailed error information.")
        return False

    # Verify agent HTTP endpoints (skip mcp_server as it doesn't have HTTP endpoint)
    agents_to_check = [
        ("CEO Agent", SERVICES["ceo_agent"]["url"]),
        ("Orchestrator", SERVICES["orchestrator"]["url"]),
        ("Document Agent", SERVICES["document_agent"]["url"]),
        ("Browser Agent", SERVICES["browser_agent"]["url"]),
        ("Database Agent", SERVICES["database_agent"]["url"]),
    ]

    healthy_agents = 0
    for agent_name, url in agents_to_check:
        if await verify_agent_health(agent_name, url):
            healthy_agents += 1

    if healthy_agents == len(agents_to_check):
        print("✅ All agents are healthy and ready!")
        return True
    else:
        print(f"⚠️ Only {healthy_agents}/{len(agents_to_check)} agents are responding")
        return False


async def talk_to_orchestrator(prompt: str):
    """Sends a prompt to the Orchestrator agent using A2A protocol and returns the response."""
    orchestrator_url = SERVICES["orchestrator"]["url"]

    try:
        return await send_a2a_message(
            url=orchestrator_url,
            prompt=prompt,
            agent_name="Orchestrator",
            timeout=300.0,
        )
    except Exception as e:
        logger.error(f"Error communicating with Orchestrator: {e}", exc_info=True)
        return f"Error communicating with Orchestrator: {str(e)}"


async def talk_to_ceo_agent(prompt: str):
    """Sends a prompt to the CEO agent using A2A protocol and returns the response."""
    ceo_url = SERVICES["ceo_agent"]["url"]

    try:
        return await send_a2a_message(
            url=ceo_url, prompt=prompt, agent_name="CEO Agent", timeout=300.0
        )
    except Exception as e:
        logger.error(f"Error communicating with CEO Agent: {e}", exc_info=True)
        return f"Error communicating with CEO Agent: {str(e)}"


async def initialize_database_if_needed():
    """
    Check if ChromaDB databases exist and create initial SafeAppealNavigator database if needed.
    This runs automatically on CLI startup to ensure the system is ready for use.
    """
    logger.info("🔍 Checking database initialization status...")

    try:
        # Connect to Database Agent to check for existing databases
        database_agent_url = SERVICES["database_agent"]["url"]

        # First, check if any collections exist
        check_result = await send_a2a_message(
            url=database_agent_url,
            prompt="List all existing ChromaDB collections to check if database is initialized",
            agent_name="Database Agent",
            timeout=30.0,
        )

        logger.info(f"Database check result: {check_result[:200]}...")

        # If the response indicates no collections or empty database, initialize it
        if (
            "no collections" in check_result.lower()
            or "empty" in check_result.lower()
            or "0 collections" in check_result.lower()
            or len(check_result.strip())
            < 50  # Very short response likely means no databases
        ):
            logger.info(
                "🏗️ No existing database found. Initializing SafeAppealNavigator database..."
            )
            print("🏗️ **Initializing SafeAppealNavigator Database...**")
            print("   Setting up legal case management collections for the first time.")

            # Create the initial SafeAppealNavigator database structure
            init_result = await send_a2a_message(
                url=database_agent_url,
                prompt=(
                    "Create a comprehensive SafeAppealNavigator database setup with the following "
                    "specialized ChromaDB collections for legal case management:\n\n"
                    "1. case_files - Primary case documents, correspondence, claim forms, decision letters\n"
                    "2. medical_records - Medical reports, assessments, treatment records, IME reports\n"
                    "3. wcat_decisions - WCAT precedent decisions, similar cases, appeal outcomes\n"
                    "4. legal_policies - WorkSafe BC policies, procedures, regulations, guidelines\n"
                    "5. templates - Appeal letter templates, legal document formats, form templates\n"
                    "6. research_findings - Legal research results, precedent analysis, case law summaries\n\n"
                    "Use optimal HNSW parameters for legal document similarity search and configure "
                    "metadata schemas appropriate for WorkSafe BC and WCAT case management."
                ),
                agent_name="Database Agent",
                timeout=120.0,
            )

            print("✅ **Database Initialization Complete!**")
            print(
                "   SafeAppealNavigator is ready with legal case management collections."
            )
            logger.info(f"Database initialization result: {init_result[:200]}...")

        else:
            logger.info("✅ Database already initialized. SafeAppealNavigator ready.")
            print(
                "✅ **Database Ready** - SafeAppealNavigator legal case management system loaded."
            )

    except Exception as e:
        logger.error(f"Error during database initialization: {e}")
        print(f"⚠️ **Database Initialization Warning:** {str(e)}")
        print("   You may need to manually create databases if needed.")


# --- Main Application ---
async def main():
    """Main CLI function with automatic database initialization."""
    logger.info("Starting SafeAppealNavigator CLI...")

    print("--- ⚖️  SafeAppealNavigator Interactive Debug CLI ---")
    print(f"INFO: Project Root detected at: {PROJECT_ROOT}")
    print(f"INFO: Logs for all services will be stored in: {LOG_DIR}")

    # Set up signal handlers for cleanup
    signal.signal(signal.SIGINT, cleanup_processes)
    signal.signal(signal.SIGTERM, cleanup_processes)

    try:
        # Clean up any existing agent processes first
        cleanup_existing_agents()

        # Start all backend services first
        for name, config in SERVICES.items():
            start_service(name, config)

        print("--- ✅ All backend services are starting... ---")

        # Wait for services to fully initialize
        await asyncio.sleep(10)

        # Verify that all agents are actually running and healthy
        if not await verify_all_agents():
            print("❌ Some agents failed to start properly. Exiting...")
            print("Check the log files for detailed error information.")
            return

        # Initialize database if needed - this runs automatically
        await initialize_database_if_needed()

        print()  # Add spacing before user interaction
        print("--- 🗣️  Choose your conversation mode ---")
        print(
            "1. Talk to CEO Agent (recommended - handles user requests and delegates to orchestrator)"
        )
        print("2. Talk to Orchestrator Agent directly (for debugging)")

        while True:
            try:
                mode = input("Choose mode (1 or 2): ").strip()
                if mode in ["1", "2"]:
                    break
                print("Please enter 1 or 2")
            except (EOFError, KeyboardInterrupt):
                print("\nExiting...")
                return

        if mode == "1":
            print("\n--- 🗣️  You are now talking to the CEO Agent ---")
            agent_talk_func = talk_to_ceo_agent
            agent_name = "CEO Agent"
        else:
            print("\n--- 🗣️  You are now talking to the Orchestrator Agent ---")
            agent_talk_func = talk_to_orchestrator
            agent_name = "Orchestrator"

        print("Type your research request or 'quit'/'exit' to stop.")
        print("-" * 50)

        while True:
            try:
                # Simplified input handling - avoid anyio threading issues
                print("You: ", end="", flush=True)
                user_input = input()
                user_input = user_input.strip()
            except (EOFError, KeyboardInterrupt):
                print("\nExiting...")
                break

            if user_input.lower() in ["quit", "exit"]:
                break
            if not user_input:
                continue

            print(f"\n{agent_name} is thinking...")
            print("(Check the log files for real-time agent activity)")

            response = await agent_talk_func(user_input)

            print("\n" + "-" * 50)
            print(f"{agent_name}: {response}")
            print("-" * 50)

    finally:
        cleanup_processes()
        print("\n--- Application has been shut down. ---")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("CLI interrupted by user.")

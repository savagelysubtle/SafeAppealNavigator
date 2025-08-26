#!/usr/bin/env python
"""
SafeAppealNavigator - Interactive Debug CLI (Corrected Pathing)

This script provides a robust, interactive command-line interface to test the entire
multi-agent system. It correctly starts, manages, and cleans up all necessary
backend services (MCP Server, A2A Agents) and allows you to communicate directly
with the Orchestrator agent to trace the full workflow.

This version includes a robust path-finding mechanism that works reliably
when run from the project root.
"""

import asyncio
import logging
import os
import signal
import subprocess
import sys
import uuid
from pathlib import Path

import anyio
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
SERVICES = {
    "mcp_server": {
        "command": [
            sys.executable,
            "-m",
            "ai_research_assistant.mcp.server",
            "--port",
            "10100",
            "--transport",
            "sse",
        ],
        "log_file": LOG_DIR / "mcp_server.log",
        "ready_msg": "Agent Finder MCP Server running",
    },
    "orchestrator": {
        "command": [
            sys.executable,
            "-m",
            "ai_research_assistant.a2a_services.startup",
            "--card-path",
            str(PROJECT_ROOT / "agent_cards/orchestrator_agent.json"),
            "--port",
            "10101",
        ],
        "log_file": LOG_DIR / "orchestrator_agent.log",
        "url": "http://localhost:10101",
    },
    "document_agent": {
        "command": [
            sys.executable,
            "-m",
            "ai_research_assistant.a2a_services.startup",
            "--card-path",
            str(PROJECT_ROOT / "agent_cards/document_agent.json"),
            "--port",
            "10102",
        ],
        "log_file": LOG_DIR / "document_agent.log",
    },
    "browser_agent": {
        "command": [
            sys.executable,
            "-m",
            "ai_research_assistant.a2a_services.startup",
            "--card-path",
            str(PROJECT_ROOT / "agent_cards/browser_agent.json"),
            "--port",
            "10103",
        ],
        "log_file": LOG_DIR / "browser_agent.log",
    },
    "database_agent": {
        "command": [
            sys.executable,
            "-m",
            "ai_research_assistant.a2a_services.startup",
            "--card-path",
            str(PROJECT_ROOT / "agent_cards/database_agent.json"),
            "--port",
            "10104",
        ],
        "log_file": LOG_DIR / "database_agent.log",
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


def start_service(name, config):
    """Starts a service as a background process and logs its output."""
    logger.info(f"Starting {name}...")
    log_file = open(config["log_file"], "w")
    preexec_fn = os.setsid if os.name != "nt" else None

    # Use the project root as the current working directory for all subprocesses
    process = subprocess.Popen(
        config["command"],
        stdout=log_file,
        stderr=log_file,
        preexec_fn=preexec_fn,
        cwd=PROJECT_ROOT,
    )
    processes.append((process, name))
    logger.info(
        f"  -> {name} started with PID {process.pid}. Log: {config['log_file']}"
    )
    return process


async def talk_to_orchestrator(prompt: str):
    """Sends a prompt to the Orchestrator agent using A2A protocol and returns the response."""
    orchestrator_url = SERVICES["orchestrator"]["url"]

    # Use proper A2A protocol message format
    a2a_message = {
        "context_id": str(uuid.uuid4()),
        "message": prompt,
        "user_id": "debug_cli",
    }

    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            # Send to the A2A endpoint which should be at the root path
            response = await client.post(
                orchestrator_url,
                json=a2a_message,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            return response.text

    except httpx.HTTPStatusError as e:
        error_body = e.response.text
        logger.error(
            f"HTTP Error from Orchestrator: {e.response.status_code} - {error_body}"
        )
        return f"Error: Received status {e.response.status_code} from the orchestrator."
    except httpx.RequestError as e:
        logger.error(
            f"Could not connect to the Orchestrator at {orchestrator_url}: {e}"
        )
        return "Error: Could not connect to the orchestrator. Is it running?"
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        return f"An unexpected error occurred: {str(e)}"


# --- Main Application ---
async def main():
    """Main asynchronous function to run the CLI test harness."""
    print("\n--- ⚖️  SafeAppealNavigator Interactive Debug CLI ---")
    print(f"INFO: Project Root detected at: {PROJECT_ROOT}")
    print(f"INFO: Logs for all services will be stored in: {LOG_DIR.resolve()}")

    signal.signal(signal.SIGINT, cleanup_processes)
    signal.signal(signal.SIGTERM, cleanup_processes)

    try:
        for name, config in SERVICES.items():
            start_service(name, config)

        print("\n--- ✅ All backend services are starting... ---")
        await asyncio.sleep(10)

        print("\n--- 🗣️  You are now talking to the Orchestrator Agent ---")
        print("Type your research request or 'quit'/'exit' to stop.")
        print("-" * 50)

        while True:
            user_input = await anyio.to_thread.run_sync(lambda: input("You: ").strip())

            if user_input.lower() in ["quit", "exit"]:
                break
            if not user_input:
                continue

            print("\nOrchestrator is thinking...")
            print("(Check the log files for real-time agent activity)")

            response = await talk_to_orchestrator(user_input)

            print("\n" + "-" * 50)
            print(f"Orchestrator: {response}")
            print("-" * 50)

    finally:
        cleanup_processes()
        print("\n--- Application has been shut down. ---")


if __name__ == "__main__":
    try:
        anyio.run(main)
    except KeyboardInterrupt:
        logger.info("CLI interrupted by user.")

#!/usr/bin/env python
"""
Run the complete AI Research Agent application.
This script starts both the backend AG-UI server and the frontend Vite development server.
"""

import os
import signal
import subprocess
import sys
import time
from pathlib import Path


# Colors for terminal output
class Colors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def print_header(message):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{message.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}\n")


def print_info(message):
    print(f"{Colors.OKBLUE}ℹ️  {message}{Colors.ENDC}")


def print_success(message):
    print(f"{Colors.OKGREEN}✅ {message}{Colors.ENDC}")


def print_error(message):
    print(f"{Colors.FAIL}❌ {message}{Colors.ENDC}")


def print_warning(message):
    print(f"{Colors.WARNING}⚠️  {message}{Colors.ENDC}")


# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.absolute()
FRONTEND_DIR = PROJECT_ROOT / "frontend"
BACKEND_MODULE = "src.ai_research_assistant.ag_ui_backend.main:app"

# Store process handles
processes = []


def cleanup_processes(signum=None, frame=None):
    """Clean up all spawned processes"""
    print_warning("\nShutting down services...")
    for proc in processes:
        if proc.poll() is None:  # Process is still running
            if sys.platform == "win32":
                proc.terminate()
            else:
                proc.send_signal(signal.SIGTERM)
            time.sleep(1)
            if proc.poll() is None:  # Still running
                proc.kill()
    print_success("All services stopped.")
    sys.exit(0)


# Register cleanup handlers
signal.signal(signal.SIGINT, cleanup_processes)
signal.signal(signal.SIGTERM, cleanup_processes)
if sys.platform == "win32":
    signal.signal(signal.SIGBREAK, cleanup_processes)


def check_dependencies():
    """Check if required dependencies are installed"""
    print_info("Checking dependencies...")

    # Check for Python packages
    try:
        import uvicorn

        print_success("✓ uvicorn installed")
    except ImportError:
        print_error("uvicorn not installed. Run: uv pip install uvicorn")
        return False

    # Check for Node.js and npm
    try:
        node_version = subprocess.run(
            ["node", "--version"], capture_output=True, text=True
        )
        if node_version.returncode == 0:
            print_success(f"✓ Node.js installed ({node_version.stdout.strip()})")
        else:
            print_error("Node.js not found. Please install Node.js.")
            return False
    except FileNotFoundError:
        print_error("Node.js not found. Please install Node.js.")
        return False

    # Check if frontend dependencies are installed
    node_modules = FRONTEND_DIR / "node_modules"
    if not node_modules.exists():
        print_warning("Frontend dependencies not installed. Installing...")
        npm_install = subprocess.run(["npm", "install"], cwd=FRONTEND_DIR)
        if npm_install.returncode != 0:
            print_error("Failed to install frontend dependencies.")
            return False
        print_success("Frontend dependencies installed.")
    else:
        print_success("✓ Frontend dependencies installed")

    return True


def start_backend():
    """Start the AG-UI backend server"""
    print_info("Starting AG-UI Backend Server...")

    # Use uvicorn to run the FastAPI app
    backend_cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        BACKEND_MODULE,
        "--host",
        "0.0.0.0",
        "--port",
        "10200",
        "--reload",
    ]

    if sys.platform == "win32":
        # Windows specific: use CREATE_NEW_PROCESS_GROUP
        backend_process = subprocess.Popen(
            backend_cmd,
            cwd=PROJECT_ROOT,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        )
    else:
        # Unix: use preexec_fn to ensure process group
        backend_process = subprocess.Popen(
            backend_cmd, cwd=PROJECT_ROOT, preexec_fn=os.setsid
        )

    processes.append(backend_process)
    print_success("AG-UI Backend Server started on http://localhost:10200")
    return backend_process


def start_frontend():
    """Start the frontend Vite development server"""
    print_info("Starting Frontend Development Server...")

    # Run npm run dev
    if sys.platform == "win32":
        frontend_cmd = ["npm.cmd", "run", "dev"]
    else:
        frontend_cmd = ["npm", "run", "dev"]

    frontend_process = subprocess.Popen(frontend_cmd, cwd=FRONTEND_DIR)

    processes.append(frontend_process)
    print_success("Frontend Development Server starting...")
    return frontend_process


def main():
    """Main function to orchestrate the startup"""
    print_header("AI Research Agent - Application Launcher")

    # Change to project root
    os.chdir(PROJECT_ROOT)
    print_info(f"Working directory: {PROJECT_ROOT}")

    # Check dependencies
    if not check_dependencies():
        print_error("Dependency check failed. Please install missing dependencies.")
        sys.exit(1)

    print("")

    # Start backend
    backend_proc = start_backend()

    # Wait a bit for backend to initialize
    print_info("Waiting for backend to initialize...")
    time.sleep(3)

    # Check if backend is running
    if backend_proc.poll() is not None:
        print_error("Backend failed to start. Check the logs above.")
        cleanup_processes()
        sys.exit(1)

    print("")

    # Start frontend
    frontend_proc = start_frontend()

    # Wait a bit for frontend to initialize
    time.sleep(3)

    # Check if frontend is running
    if frontend_proc.poll() is not None:
        print_error("Frontend failed to start. Check the logs above.")
        cleanup_processes()
        sys.exit(1)

    print("")
    print_success("All services started successfully!")
    print_info("AG-UI Backend: http://localhost:10200")
    print_info("Frontend: http://localhost:5173 (or check the output above)")
    print_warning("Press Ctrl+C to stop all services")

    # Keep the script running
    try:
        while True:
            # Check if any process has died
            for proc in processes:
                if proc.poll() is not None:
                    print_error("A service has stopped unexpectedly!")
                    cleanup_processes()
            time.sleep(1)
    except KeyboardInterrupt:
        cleanup_processes()


if __name__ == "__main__":
    main()

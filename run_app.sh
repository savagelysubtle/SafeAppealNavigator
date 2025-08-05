#!/bin/bash
# AI Research Agent - Unix/Linux Application Launcher
# This script starts both the backend and frontend servers

echo "============================================================"
echo "          AI Research Agent - Application Launcher"
echo "============================================================"
echo ""

# Check if Python is available
if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
    echo "ERROR: Python is not installed or not in PATH."
    echo "Please install Python and try again."
    exit 1
fi

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo "ERROR: Node.js is not installed or not in PATH."
    echo "Please install Node.js and try again."
    exit 1
fi

# Find the correct Python command
if command -v python &> /dev/null; then
    PYTHON_CMD="python"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
fi

# Run the Python launcher script
echo "Starting AI Research Agent..."
$PYTHON_CMD run_app.py

# Script will handle its own cleanup on exit
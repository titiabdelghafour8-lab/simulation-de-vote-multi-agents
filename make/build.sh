#!/bin/bash
set -e

echo "Starting build process..."

# Create a virtual environment if it doesn't exist
if [ ! -d "linux_venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv linux_venv
fi

# Activate virtual environment
source linux_venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip

if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    pip install streamlit pandas python-dotenv pydantic langchain-groq langchain-core
fi

echo "Build complete!"
echo ""
echo "Available commands:"
echo "  make simulate    # Run the voting simulation"
echo "  make dashboard   # Start the Streamlit dashboard"

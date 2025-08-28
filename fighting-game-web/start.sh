#!/bin/bash
set -e  # Exit on error

# Log environment
env | sort

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Check Python version
echo "Python version:"
python --version

# Start the server
echo "Starting server..."
exec python server.py

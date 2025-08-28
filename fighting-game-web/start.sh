#!/bin/bash
# Install dependencies
pip install -r requirements.txt

# Start the server
exec python server.py

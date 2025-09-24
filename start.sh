#!/bin/bash

# Twitch MCP Server Start Script
# For Railway and Docker deployments

set -e

echo "🎮 Starting Twitch MCP Server..."

# Default values (Railway sets PORT automatically)
TRANSPORT=${TRANSPORT:-http}
HOST=${HOST:-0.0.0.0}
PORT=${PORT:-8080}
AUTOMATION_MODE=${AUTOMATION_MODE:-false}

# Build command
CMD="uv run python mcp_twitch_server.py --transport $TRANSPORT --host $HOST"

# Add port if set
if [ ! -z "$PORT" ]; then
    CMD="$CMD --port $PORT"
fi

# Add automation mode if enabled
if [ "$AUTOMATION_MODE" = "true" ]; then
    CMD="$CMD --automation-mode"
    echo "🎬 Automation mode enabled"
fi

echo "🚀 Command: $CMD"

# Execute command
exec $CMD

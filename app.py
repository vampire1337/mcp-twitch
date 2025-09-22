#!/usr/bin/env python3
"""
🚀 Railway Entry Point for MCP Twitch Server

This file serves as the main entry point for Railway deployment,
providing a clean interface and production-ready configuration.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add current directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

from mcp_twitch_server import TwitchMCPServer


async def main():
    """Main entry point for Railway deployment"""
    
    # Get configuration from environment variables (Railway will provide these)
    client_id = os.getenv('TWITCH_CLIENT_ID')
    access_token = os.getenv('TWITCH_ACCESS_TOKEN')
    port = int(os.getenv('PORT', 8080))
    host = os.getenv('HOST', '0.0.0.0')
    transport = os.getenv('TRANSPORT', 'http')
    
    # Validate required configuration
    if not client_id:
        print("❌ Error: TWITCH_CLIENT_ID environment variable is required")
        print("🔑 Get your Client ID from: https://dev.twitch.tv/console/apps")
        sys.exit(1)
    
    print(f"🎮 Starting MCP Twitch Server")
    print(f"   Transport: {transport}")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   Client ID: {client_id[:8]}...")
    if access_token:
        print(f"   Access Token: {access_token[:8]}...")
    
    try:
        # Create and configure server
        server = TwitchMCPServer(client_id=client_id, access_token=access_token)
        
        # Create MCP server instance
        mcp = await server.create_server()
        
        # Get tools count for logging
        tools = await mcp.get_tools()
        print(f"✅ Server ready with {len(tools)} tools")
        
        # Run the server based on transport type
        if transport.lower() == 'http':
            print(f"🌐 Starting HTTP server on {host}:{port}")
            # Use FastMCP's built-in HTTP transport with async method
            await mcp.run_async(transport='http', host=host, port=port)
            
        else:
            print("📡 Starting STDIO transport")
            # Run stdio transport (for local MCP clients) with async method
            await mcp.run_async()
            
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Set production-friendly defaults
    if 'FASTMCP_LOG_LEVEL' not in os.environ:
        os.environ['FASTMCP_LOG_LEVEL'] = 'INFO'
    
    # Run the server
    asyncio.run(main())

#!/usr/bin/env python3
"""
MCP Server example for the Patent Downloader SDK.

This example demonstrates how to start and use the MCP server
for patent downloading functionality.
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to the path so we can import the package
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from patent_downloader.mcp_server import PatentDownloaderMCPServer
except ImportError as e:
    print(f"Error: {e}")
    print("Make sure you have installed the MCP dependencies:")
    print("  pip install 'patent-downloader[mcp]'")
    sys.exit(1)


async def main():
    """Main MCP server example."""
    print("Patent Downloader SDK - MCP Server Example")
    print("=" * 50)

    # Create and start the MCP server
    server = PatentDownloaderMCPServer()

    print("Starting MCP server on localhost:8000")
    print("The server provides the following tools:")
    print("  - download_patent: Download a single patent PDF")
    print("  - download_patents: Download multiple patent PDFs")
    print("  - get_patent_info: Get detailed patent information")
    print()
    print("You can connect to this server using an MCP client.")
    print("Press Ctrl+C to stop the server.")

    try:
        await server.run(host="localhost", port=8000)
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Error running server: {e}")


if __name__ == "__main__":
    asyncio.run(main())

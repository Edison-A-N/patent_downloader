#!/usr/bin/env python3
"""
MCP Server example for the Patent Downloader SDK using mcp.FastMCP.

This example demonstrates how to start and use the MCP server
for patent downloading functionality using stdio transport.
"""

import os
import sys
from pathlib import Path

# Add the src directory to the path so we can import the package
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from patent_downloader.mcp_server import create_mcp_server
except ImportError as e:
    print(f"Error: {e}")
    print("Make sure you have installed the MCP dependencies:")
    print("  pip install 'patent-downloader[mcp]'")
    sys.exit(1)


def main():
    """Main MCP server example."""
    print("Patent Downloader SDK - MCP Server Example (mcp.FastMCP)")
    print("=" * 50)

    # Set default output directory if not already set
    if "OUTPUT_DIR" not in os.environ:
        os.environ["OUTPUT_DIR"] = "./downloads"
        print(f"Setting default OUTPUT_DIR to: {os.environ['OUTPUT_DIR']}")

    # Create the MCP server
    server = create_mcp_server()

    print("Starting MCP server using stdio transport")
    print("The server provides the following tools:")
    print("  - download_patent: Download a single patent PDF")
    print("  - download_patents: Download multiple patent PDFs")
    print("  - get_patent_info: Get detailed patent information")
    print()
    print("Configuration:")
    print(f"  Output directory: {os.environ.get('OUTPUT_DIR', './downloads')}")
    print()
    print("You can connect to this server using an MCP client that supports stdio transport.")
    print("Press Ctrl+C to stop the server.")

    try:
        server.run()
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Error running server: {e}")


if __name__ == "__main__":
    main()

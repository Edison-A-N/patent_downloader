"""MCP (Model Context Protocol) server for patent downloader."""

import asyncio
import logging
from typing import Any, Dict
from pathlib import Path

try:
    from mcp import Server
    from mcp.types import (
        CallToolRequest,
        CallToolResult,
        ListToolsRequest,
        ListToolsResult,
        Tool,
    )
except ImportError:
    raise ImportError("MCP support requires the 'mcp' package. Install with: pip install 'patent-downloader[mcp]'")

from .downloader import PatentDownloader
from .exceptions import PatentDownloadError

logger = logging.getLogger(__name__)


class PatentDownloaderMCPServer:
    """MCP server for patent downloading functionality."""

    def __init__(self):
        """Initialize the MCP server."""
        self.server = Server("patent-downloader")
        self.downloader = PatentDownloader()
        self._setup_handlers()

    def _setup_handlers(self) -> None:
        """Setup MCP handlers."""
        self.server.list_tools(self._handle_list_tools)
        self.server.call_tool(self._handle_call_tool)

    async def _handle_list_tools(self, request: ListToolsRequest) -> ListToolsResult:
        """Handle list tools request."""
        tools = [
            Tool(
                name="download_patent",
                description="Download a single patent PDF from Google Patents",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "patent_number": {
                            "type": "string",
                            "description": "The patent number to download (e.g., 'WO2013078254A1')",
                        },
                        "output_dir": {
                            "type": "string",
                            "description": "Directory to save the PDF file (default: current directory)",
                        },
                    },
                    "required": ["patent_number"],
                },
            ),
            Tool(
                name="download_patents",
                description="Download multiple patent PDFs from Google Patents",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "patent_numbers": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of patent numbers to download",
                        },
                        "output_dir": {
                            "type": "string",
                            "description": "Directory to save the PDF files (default: current directory)",
                        },
                    },
                    "required": ["patent_numbers"],
                },
            ),
            Tool(
                name="get_patent_info",
                description="Get detailed information about a patent",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "patent_number": {"type": "string", "description": "The patent number to get information for"}
                    },
                    "required": ["patent_number"],
                },
            ),
        ]
        return ListToolsResult(tools=tools)

    async def _handle_call_tool(self, request: CallToolRequest) -> CallToolResult:
        """Handle tool call requests."""
        try:
            if request.name == "download_patent":
                return await self._handle_download_patent(request.arguments)
            elif request.name == "download_patents":
                return await self._handle_download_patents(request.arguments)
            elif request.name == "get_patent_info":
                return await self._handle_get_patent_info(request.arguments)
            else:
                return CallToolResult(content=[{"type": "text", "text": f"Unknown tool: {request.name}"}], isError=True)
        except Exception as e:
            logger.error(f"Error handling tool call {request.name}: {e}")
            return CallToolResult(content=[{"type": "text", "text": f"Error: {str(e)}"}], isError=True)

    async def _handle_download_patent(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle download_patent tool call."""
        try:
            patent_number = arguments.get("patent_number")
            output_dir = arguments.get("output_dir", ".")

            if not patent_number:
                return CallToolResult(
                    content=[{"type": "text", "text": "Error: patent_number is required"}], isError=True
                )

            # Run download in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(None, self.downloader.download_patent, patent_number, output_dir)

            if success:
                output_path = Path(output_dir) / f"{patent_number}.pdf"
                return CallToolResult(
                    content=[
                        {"type": "text", "text": f"Successfully downloaded patent {patent_number} to {output_path}"}
                    ]
                )
            else:
                return CallToolResult(
                    content=[{"type": "text", "text": f"Failed to download patent {patent_number}"}], isError=True
                )

        except PatentDownloadError as e:
            return CallToolResult(content=[{"type": "text", "text": f"Download error: {str(e)}"}], isError=True)

    async def _handle_download_patents(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle download_patents tool call."""
        try:
            patent_numbers = arguments.get("patent_numbers", [])
            output_dir = arguments.get("output_dir", ".")

            if not patent_numbers:
                return CallToolResult(
                    content=[{"type": "text", "text": "Error: patent_numbers is required"}], isError=True
                )

            # Run download in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(None, self.downloader.download_patents, patent_numbers, output_dir)

            successful = [pn for pn, success in results.items() if success]
            failed = [pn for pn, success in results.items() if not success]

            result_text = "Download completed:\n"
            result_text += f"  Successful: {len(successful)} patents\n"
            result_text += f"  Failed: {len(failed)} patents\n"

            if successful:
                result_text += f"  Successfully downloaded: {', '.join(successful)}\n"
            if failed:
                result_text += f"  Failed to download: {', '.join(failed)}"

            return CallToolResult(content=[{"type": "text", "text": result_text}], isError=len(failed) > 0)

        except PatentDownloadError as e:
            return CallToolResult(content=[{"type": "text", "text": f"Download error: {str(e)}"}], isError=True)

    async def _handle_get_patent_info(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle get_patent_info tool call."""
        try:
            patent_number = arguments.get("patent_number")

            if not patent_number:
                return CallToolResult(
                    content=[{"type": "text", "text": "Error: patent_number is required"}], isError=True
                )

            # Run info retrieval in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            patent_info = await loop.run_in_executor(None, self.downloader.get_patent_info, patent_number)

            info_text = f"Patent Information for {patent_number}:\n"
            info_text += f"  Title: {patent_info.title}\n"
            info_text += f"  Inventors: {', '.join(patent_info.inventors)}\n"
            info_text += f"  Assignee: {patent_info.assignee}\n"
            info_text += f"  Publication Date: {patent_info.publication_date}\n"
            info_text += f"  URL: {patent_info.url}\n"
            info_text += f"  Abstract: {patent_info.abstract[:200]}..."

            return CallToolResult(content=[{"type": "text", "text": info_text}])

        except PatentDownloadError as e:
            return CallToolResult(
                content=[{"type": "text", "text": f"Error retrieving patent info: {str(e)}"}], isError=True
            )

    async def run(self, host: str = "localhost", port: int = 8000) -> None:
        """Run the MCP server."""
        logger.info(f"Starting MCP server on {host}:{port}")
        await self.server.run(host=host, port=port)


def start_mcp_server(host: str = "localhost", port: int = 8000) -> None:
    """Start the MCP server."""
    server = PatentDownloaderMCPServer()

    try:
        asyncio.run(server.run(host=host, port=port))
    except KeyboardInterrupt:
        logger.info("MCP server stopped by user")
    except Exception as e:
        logger.error(f"Error running MCP server: {e}")
        raise

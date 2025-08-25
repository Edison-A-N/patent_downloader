"""MCP (Model Context Protocol) server for patent downloader using mcp.FastMCP."""

import logging
import os
from pathlib import Path
from typing import List

try:
    from mcp.server import FastMCP
except ImportError:
    raise ImportError("MCP support requires the 'mcp' package. Install with: pip install 'patent-downloader[mcp]'")

from .downloader import PatentDownloader
from .exceptions import PatentDownloadError

logger = logging.getLogger(__name__)


def create_mcp_server(output_dir: str = "./downloads") -> FastMCP:
    """Create and configure the MCP server."""
    server = FastMCP("patent-downloader")
    downloader = PatentDownloader()
    output_dir = Path(output_dir)

    @server.tool()
    def download_patent(patent_number: str, output_dir: str = output_dir) -> str:
        """Download a single patent PDF from Google Patents.

        Args:
            patent_number: The patent number to download (e.g., 'WO2013078254A1')
            output_dir: Directory to save the PDF file

        Returns:
            Success or error message
        """
        try:
            # Ensure output directory exists
            Path(output_dir).mkdir(parents=True, exist_ok=True)

            success = downloader.download_patent(patent_number, output_dir)

            if success:
                output_path = Path(output_dir) / f"{patent_number}.pdf"
                return f"Successfully downloaded patent {patent_number} to {output_path}"
            else:
                return f"Failed to download patent {patent_number}"

        except PatentDownloadError as e:
            return f"Download error: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error downloading patent {patent_number}: {e}")
            return f"Unexpected error: {str(e)}"

    @server.tool()
    def download_patents(patent_numbers: List[str], output_dir: str = output_dir) -> str:
        """Download multiple patent PDFs from Google Patents.

        Args:
            patent_numbers: List of patent numbers to download
            output_dir: Directory to save the PDF files

        Returns:
            Summary of download results
        """
        try:
            # Ensure output directory exists
            Path(output_dir).mkdir(parents=True, exist_ok=True)

            results = downloader.download_patents(patent_numbers, output_dir)

            successful = [pn for pn, success in results.items() if success]
            failed = [pn for pn, success in results.items() if not success]

            result_text = "Download completed:\n"
            result_text += f"  Successful: {len(successful)} patents\n"
            result_text += f"  Failed: {len(failed)} patents\n"

            if successful:
                result_text += f"  Successfully downloaded: {', '.join(successful)}\n"
            if failed:
                result_text += f"  Failed to download: {', '.join(failed)}"

            return result_text

        except PatentDownloadError as e:
            return f"Download error: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error downloading patents: {e}")
            return f"Unexpected error: {str(e)}"

    @server.tool()
    def get_patent_info(patent_number: str) -> str:
        """Get detailed information about a patent.

        Args:
            patent_number: The patent number to get information for

        Returns:
            Formatted patent information
        """
        try:
            patent_info = downloader.get_patent_info(patent_number)

            info_text = f"Patent Information for {patent_number}:\n"
            info_text += f"  Title: {patent_info.title}\n"
            info_text += f"  Inventors: {', '.join(patent_info.inventors)}\n"
            info_text += f"  Assignee: {patent_info.assignee}\n"
            info_text += f"  Publication Date: {patent_info.publication_date}\n"
            info_text += f"  URL: {patent_info.url}\n"
            info_text += f"  Abstract: {patent_info.abstract[:200]}..."

            return info_text

        except PatentDownloadError as e:
            return f"Error retrieving patent info: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error getting patent info for {patent_number}: {e}")
            return f"Unexpected error: {str(e)}"

    return server


def start_mcp_server() -> None:
    """Start the MCP server using stdio transport."""
    output_dir = os.getenv("OUTPUT_DIR", "./downloads")
    server = create_mcp_server(output_dir=output_dir)

    try:
        logger.info("Starting MCP server using stdio transport")
        server.run()
    except KeyboardInterrupt:
        logger.info("MCP server stopped by user")
    except Exception as e:
        logger.error(f"Error running MCP server: {e}")
        raise


if __name__ == "__main__":
    start_mcp_server()

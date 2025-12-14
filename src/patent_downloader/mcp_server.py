"""MCP (Model Context Protocol) server for patent downloader using mcp.FastMCP."""

import json
import logging
import os
from pathlib import Path
from typing import List, Optional

from mcp.server import FastMCP
from pydantic import BaseModel, Field

from .downloader import PatentDownloader
from .exceptions import PatentDownloadError

logger = logging.getLogger(__name__)

# Configuration file path
CONFIG_DIR = Path.home() / ".patent_downloader"
CONFIG_FILE = CONFIG_DIR / "config.json"


# Pydantic models for MCP output schemas


class DownloadPatentResponse(BaseModel):
    """Response for downloading a single patent."""

    patent_number: str = Field(..., description="The patent number")
    file_path: Optional[str] = Field(None, description="Path to the downloaded PDF file")


class DownloadPatentsResponse(BaseModel):
    """Response for downloading multiple patents."""

    total: int = Field(..., description="Total number of patents processed")
    successful: int = Field(..., description="Number of successfully downloaded patents")
    failed: int = Field(..., description="Number of failed downloads")
    successful_patents: List[str] = Field(
        default_factory=list, description="List of successfully downloaded patent numbers"
    )
    failed_patents: List[str] = Field(default_factory=list, description="List of failed patent numbers")
    output_directory: str = Field(..., description="Directory where patents were saved")


class PatentInfoResponse(BaseModel):
    """Response for getting patent information."""

    patent_number: str = Field(..., description="The patent number")
    title: str = Field(..., description="Patent title")
    inventors: List[str] = Field(default_factory=list, description="List of inventors")
    assignee: str = Field(..., description="Patent assignee/owner")
    publication_date: str = Field(..., description="Publication date")
    abstract: str = Field(..., description="Patent abstract")
    url: str = Field(..., description="URL to the patent page")


def _get_config_path() -> Path:
    """Get the configuration file path."""
    return CONFIG_FILE


def _load_config() -> dict:
    """Load configuration from file."""
    config_path = _get_config_path()
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load config file: {e}. Using defaults.")
    return {}


def _save_config(config: dict) -> None:
    """Save configuration to file."""
    config_path = _get_config_path()
    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except IOError as e:
        logger.error(f"Failed to save config file: {e}")


def _get_default_output_dir() -> str:
    """Get the default output directory from config or environment."""
    config = _load_config()
    if "output_dir" in config:
        return config["output_dir"]
    # Fallback to environment variable or default
    return os.getenv("OUTPUT_DIR", "./downloads")


def _set_default_output_dir(output_dir: str) -> None:
    """Set the default output directory in config."""
    config = _load_config()
    # Expand ~ to home directory and normalize path
    expanded_dir = os.path.expanduser(output_dir)
    normalized_dir = str(Path(expanded_dir).resolve())
    config["output_dir"] = normalized_dir
    _save_config(config)


def create_mcp_server(output_dir: Optional[str] = None) -> FastMCP:
    """Create and configure the MCP server.

    Args:
        output_dir: Optional initial output directory. If not provided, uses config or default.
    """
    server = FastMCP("patent-downloader")
    downloader = PatentDownloader()

    # Save to config if provided via parameter
    if output_dir is not None:
        _set_default_output_dir(output_dir)

    @server.tool(structured_output=True)
    def download_patent(patent_number: str, output_dir: Optional[str] = None) -> DownloadPatentResponse:
        """Download a single patent PDF from Google Patents.

        Args:
            patent_number: The patent number to download (e.g., 'WO2013078254A1')
            output_dir: Optional directory to save the PDF file.
                       If not provided, uses the configured default directory.

        Returns:
            Response with download status, file path, and message
        """
        try:
            # Use provided output_dir or fall back to configured default
            if output_dir is None:
                output_dir = _get_default_output_dir()

            # Expand ~ to home directory and ensure output directory exists
            output_dir = os.path.expanduser(str(output_dir))
            Path(output_dir).mkdir(parents=True, exist_ok=True)

            success = downloader.download_patent(patent_number, output_dir)

            if success:
                output_path = str(Path(output_dir) / f"{patent_number}.pdf")
                return DownloadPatentResponse(
                    success=True,
                    patent_number=patent_number,
                    file_path=output_path,
                    message=f"Successfully downloaded patent {patent_number} to {output_path}",
                )
            else:
                return DownloadPatentResponse(
                    success=False,
                    patent_number=patent_number,
                    file_path=None,
                    message=f"Failed to download patent {patent_number}",
                )

        except PatentDownloadError as e:
            return DownloadPatentResponse(
                success=False, patent_number=patent_number, file_path=None, message=f"Download error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error downloading patent {patent_number}: {e}")
            return DownloadPatentResponse(
                success=False, patent_number=patent_number, file_path=None, message=f"Unexpected error: {str(e)}"
            )

    @server.tool(structured_output=True)
    def download_patents(patent_numbers: List[str], output_dir: Optional[str] = None) -> DownloadPatentsResponse:
        """Download multiple patent PDFs from Google Patents.

        Args:
            patent_numbers: List of patent numbers to download
            output_dir: Optional directory to save the PDF files.
                       If not provided, uses the configured default directory.

        Returns:
            Response with download statistics and results
        """
        try:
            # Use provided output_dir or fall back to configured default
            if output_dir is None:
                output_dir = _get_default_output_dir()

            # Expand ~ to home directory and ensure output directory exists
            output_dir = os.path.expanduser(str(output_dir))
            Path(output_dir).mkdir(parents=True, exist_ok=True)

            results = downloader.download_patents(patent_numbers, output_dir)

            successful = [pn for pn, success in results.items() if success]
            failed = [pn for pn, success in results.items() if not success]

            return DownloadPatentsResponse(
                total=len(results),
                successful=len(successful),
                failed=len(failed),
                successful_patents=successful,
                failed_patents=failed,
                output_directory=output_dir,
            )

        except PatentDownloadError as e:
            logger.error(f"Download error: {e}")
            return DownloadPatentsResponse(
                total=0,
                successful=0,
                failed=0,
                successful_patents=[],
                failed_patents=[],
                output_directory=output_dir if output_dir else "",
            )
        except Exception as e:
            logger.error(f"Unexpected error downloading patents: {e}")
            return DownloadPatentsResponse(
                total=0,
                successful=0,
                failed=0,
                successful_patents=[],
                failed_patents=[],
                output_directory=output_dir if output_dir else "",
            )

    @server.tool(structured_output=True)
    def download_patents_from_file(
        file_path: str, has_header: bool = False, output_dir: Optional[str] = None
    ) -> DownloadPatentsResponse:
        """Download multiple patent PDFs from a file (txt or csv).

        Args:
            file_path: Path to the file containing patent numbers
            has_header: Whether the file has a header row
            output_dir: Optional directory to save the PDF files.
                       If not provided, uses the configured default directory.

        Returns:
            Response with download statistics and results
        """
        try:
            # Use provided output_dir or fall back to configured default
            if output_dir is None:
                output_dir = _get_default_output_dir()

            # Expand ~ to home directory
            output_dir = os.path.expanduser(str(output_dir))
            # Use the downloader's file download method
            results = downloader.download_patents_from_file(file_path, has_header, output_dir)

            successful = [pn for pn, success in results.items() if success]
            failed = [pn for pn, success in results.items() if not success]

            return DownloadPatentsResponse(
                total=len(results),
                successful=len(successful),
                failed=len(failed),
                successful_patents=successful,
                failed_patents=failed,
                output_directory=output_dir,
            )

        except FileNotFoundError as e:
            logger.error(f"File not found: {e}")
            return DownloadPatentsResponse(
                total=0,
                successful=0,
                failed=0,
                successful_patents=[],
                failed_patents=[],
                output_directory=output_dir if output_dir else "",
            )
        except ValueError as e:
            logger.error(f"Invalid file format or content: {e}")
            return DownloadPatentsResponse(
                total=0,
                successful=0,
                failed=0,
                successful_patents=[],
                failed_patents=[],
                output_directory=output_dir if output_dir else "",
            )
        except PatentDownloadError as e:
            logger.error(f"Download error: {e}")
            return DownloadPatentsResponse(
                total=0,
                successful=0,
                failed=0,
                successful_patents=[],
                failed_patents=[],
                output_directory=output_dir if output_dir else "",
            )
        except Exception as e:
            logger.error(f"Unexpected error downloading patents from file: {e}")
            return DownloadPatentsResponse(
                total=0,
                successful=0,
                failed=0,
                successful_patents=[],
                failed_patents=[],
                output_directory=output_dir if output_dir else "",
            )

    @server.tool(structured_output=True)
    def get_patent_info(patent_number: str) -> PatentInfoResponse:
        """Get detailed information about a patent.

        Args:
            patent_number: The patent number to get information for

        Returns:
            Response with detailed patent information
        """
        try:
            patent_info = downloader.get_patent_info(patent_number)

            return PatentInfoResponse(
                patent_number=patent_info.patent_number,
                title=patent_info.title,
                inventors=patent_info.inventors,
                assignee=patent_info.assignee,
                publication_date=patent_info.publication_date,
                abstract=patent_info.abstract,
                url=patent_info.url or "",
                success=True,
                message=None,
            )

        except PatentDownloadError as e:
            logger.error(f"Error retrieving patent info: {e}")
            return PatentInfoResponse(
                patent_number=patent_number,
                title="",
                inventors=[],
                assignee="",
                publication_date="",
                abstract="",
                url="",
                success=False,
                message=f"Error retrieving patent info: {str(e)}",
            )
        except Exception as e:
            logger.error(f"Unexpected error getting patent info for {patent_number}: {e}")
            return PatentInfoResponse(
                patent_number=patent_number,
                title="",
                inventors=[],
                assignee="",
                publication_date="",
                abstract="",
                url="",
                success=False,
                message=f"Unexpected error: {str(e)}",
            )

    return server


def start_mcp_server() -> None:
    """Start the MCP server using stdio transport.

    The server will use the configured default output directory from:
    1. Environment variable OUTPUT_DIR (if set)
    2. Configuration file (~/.patent_downloader/config.json)
    3. Default: ./downloads
    """
    # Check if OUTPUT_DIR is set in environment, use it as initial config
    output_dir = os.getenv("OUTPUT_DIR")
    server = create_mcp_server(output_dir=output_dir)

    try:
        logger.info("Starting MCP server using stdio transport")
        default_dir = _get_default_output_dir()
        logger.info(f"Default download directory: {default_dir}")
        server.run()
    except KeyboardInterrupt:
        logger.info("MCP server stopped by user")
    except Exception as e:
        logger.error(f"Error running MCP server: {e}")
        raise


if __name__ == "__main__":
    start_mcp_server()

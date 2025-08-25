"""Command-line interface for the patent downloader."""

import argparse
import sys
import logging

from .downloader import PatentDownloader
from .exceptions import PatentDownloadError


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


def download_command(args: argparse.Namespace) -> int:
    """Handle the download command."""
    try:
        downloader = PatentDownloader()

        if len(args.patent_numbers) == 1:
            # Single patent download
            success = downloader.download_patent(args.patent_numbers[0], args.output_dir)
            if success:
                print(f"Successfully downloaded patent {args.patent_numbers[0]}")
                return 0
            else:
                print(f"Failed to download patent {args.patent_numbers[0]}")
                return 1
        else:
            # Multiple patents download
            results = downloader.download_patents(args.patent_numbers, args.output_dir)

            successful = [pn for pn, success in results.items() if success]
            failed = [pn for pn, success in results.items() if not success]

            print("Download completed:")
            print(f"  Successful: {len(successful)} patents")
            print(f"  Failed: {len(failed)} patents")

            if successful:
                print(f"  Successfully downloaded: {', '.join(successful)}")
            if failed:
                print(f"  Failed to download: {', '.join(failed)}")

            return 0 if not failed else 1

    except PatentDownloadError as e:
        print(f"Error: {e}")
        return 1
    except KeyboardInterrupt:
        print("\nDownload interrupted by user")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1


def info_command(args: argparse.Namespace) -> int:
    """Handle the info command."""
    try:
        downloader = PatentDownloader()
        patent_info = downloader.get_patent_info(args.patent_number)

        print(f"Patent Information for {args.patent_number}:")
        print(f"  Title: {patent_info.title}")
        print(f"  Inventors: {', '.join(patent_info.inventors)}")
        print(f"  Assignee: {patent_info.assignee}")
        print(f"  Publication Date: {patent_info.publication_date}")
        print(f"  URL: {patent_info.url}")
        print(f"  Abstract: {patent_info.abstract[:200]}...")

        return 0

    except PatentDownloadError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1


def mcp_server_command(_: argparse.Namespace) -> int:
    """Handle the MCP server command."""
    try:
        from .mcp_server import start_mcp_server

        start_mcp_server()
        return 0
    except ImportError:
        print("MCP support not available. Install with: pip install 'patent-downloader[mcp]'")
        return 1
    except Exception as e:
        print(f"Error starting MCP server: {e}")
        return 1


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Download patents from Google Patents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  patent-downloader download WO2013078254A1
  patent-downloader download WO2013078254A1 US20130123448A1 --output-dir ./patents
  patent-downloader info WO2013078254A1
  patent-downloader mcp-server --port 8000
        """,
    )

    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Download command
    download_parser = subparsers.add_parser("download", help="Download patent(s)")
    download_parser.add_argument("patent_numbers", nargs="+", help="Patent number(s) to download")
    download_parser.add_argument(
        "-o", "--output-dir", default=".", help="Output directory for downloaded files (default: current directory)"
    )
    download_parser.set_defaults(func=download_command)

    # Info command
    info_parser = subparsers.add_parser("info", help="Get patent information")
    info_parser.add_argument("patent_number", help="Patent number to get information for")
    info_parser.set_defaults(func=info_command)

    # MCP server command
    mcp_parser = subparsers.add_parser("mcp-server", help="Start MCP server")
    mcp_parser.add_argument("--host", default="localhost", help="Host to bind to (default: localhost)")
    mcp_parser.add_argument("--port", type=int, default=8000, help="Port to bind to (default: 8000)")
    mcp_parser.set_defaults(func=mcp_server_command)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    setup_logging(args.verbose)

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

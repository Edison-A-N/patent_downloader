"""Command-line interface for the patent downloader."""

import argparse
import sys

from .downloader import PatentDownloader
from .exceptions import PatentDownloadError
from .progress_logger import setup_progress_logging, get_progress_logger
from .file_utils import read_patent_numbers_from_file


def print_progress_bar(completed: int, total: int, patent_number: str, success: bool):
    """Print a progress bar using modern UI with proper log coordination."""
    progress_logger = get_progress_logger()
    progress_logger.update_progress(completed, total, patent_number, success)


def download_command(args: argparse.Namespace) -> int:
    """Handle the download command."""
    progress_logger = get_progress_logger()

    try:
        downloader = PatentDownloader(max_retries=args.max_retries, progress_logger=progress_logger)

        # Get patent numbers from file or command line arguments
        if args.file:
            # Start progress tracking
            patent_numbers = read_patent_numbers_from_file(args.file, args.has_header)
            total = len(patent_numbers)
            if total > 0:
                progress_logger.start_progress(total)

            results = downloader.download_patents_from_file(
                args.file, args.has_header, args.output_dir, progress_callback=print_progress_bar
            )

            # Finish progress tracking
            progress_logger.finish_progress()

            successful = [pn for pn, success in results.items() if success]
            failed = [pn for pn, success in results.items() if not success]

            progress_logger.log_message(f"Download completed: {len(successful)} successful, {len(failed)} failed")
            if successful:
                progress_logger.log_message(f"Successfully downloaded: {', '.join(successful)}", "success")
            if failed:
                progress_logger.log_message(f"Failed to download: {', '.join(failed)}", "warning")

            return 0 if not failed else 1
        else:
            patent_numbers = args.patent_numbers

            if len(patent_numbers) == 1:
                # Single patent download
                progress_logger.log_message(f"Downloading patent {patent_numbers[0]}...")
                success = downloader.download_patent(patent_numbers[0], args.output_dir)
                if success:
                    progress_logger.log_message(f"Successfully downloaded patent {patent_numbers[0]}", "success")
                    return 0
                else:
                    progress_logger.log_message(f"Failed to download patent {patent_numbers[0]}", "error")
                    return 1
            else:
                # Multiple patents download with progress
                total = len(patent_numbers)
                progress_logger.log_message(f"Starting download of {total} patents...")
                progress_logger.start_progress(total)

                results = downloader.download_patents(
                    patent_numbers, args.output_dir, progress_callback=print_progress_bar
                )

                # Finish progress tracking
                progress_logger.finish_progress()

                successful = [pn for pn, success in results.items() if success]
                failed = [pn for pn, success in results.items() if not success]

                progress_logger.log_message(f"Download completed: {len(successful)} successful, {len(failed)} failed")
                if successful:
                    progress_logger.log_message(f"Successfully downloaded: {', '.join(successful)}", "success")
                if failed:
                    # Final download failure result is ERROR level
                    progress_logger.log_message(f"Failed to download: {', '.join(failed)}", "error")

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
    progress_logger = get_progress_logger()

    try:
        downloader = PatentDownloader(max_retries=args.max_retries, progress_logger=progress_logger)
        progress_logger.log_message(f"Fetching information for patent {args.patent_number}...")
        patent_info = downloader.get_patent_info(args.patent_number)

        # Force show user results (important information)
        progress_logger.log_message(f"Patent Information for {args.patent_number}:", force_show=True)
        progress_logger.log_message(f"  Title: {patent_info.title}", force_show=True)
        progress_logger.log_message(f"  Inventors: {', '.join(patent_info.inventors)}", force_show=True)
        progress_logger.log_message(f"  Assignee: {patent_info.assignee}", force_show=True)
        progress_logger.log_message(f"  Publication Date: {patent_info.publication_date}", force_show=True)
        progress_logger.log_message(f"  URL: {patent_info.url}", force_show=True)
        if patent_info.abstract:
            progress_logger.log_message(f"  Abstract: {patent_info.abstract[:200]}...", force_show=True)

        return 0

    except PatentDownloadError as e:
        progress_logger.log_message(f"Error: {e}", "error")
        return 1
    except Exception as e:
        progress_logger.log_message(f"Unexpected error: {e}", "error")
        return 1


def mcp_server_command(_: argparse.Namespace) -> int:
    """Handle the MCP server command."""
    progress_logger = get_progress_logger()

    try:
        from .mcp_server import start_mcp_server

        progress_logger.log_message("Starting MCP server...")
        start_mcp_server()
        return 0
    except ImportError:
        progress_logger.log_message(
            "MCP support not available. Install with: pip install 'patent-downloader[mcp]'", "error"
        )
        return 1
    except Exception as e:
        progress_logger.log_message(f"Error starting MCP server: {e}", "error")
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
  patent-downloader download --file patents.txt --has-header
  patent-downloader download --file patents.csv
  patent-downloader info WO2013078254A1
  patent-downloader mcp-server --port 8000
        """,
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity level (use -v for INFO, -vv for DEBUG, -vvv for TRACE)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Download command
    download_parser = subparsers.add_parser("download", help="Download patent(s)")
    download_parser.add_argument("patent_numbers", nargs="*", help="Patent number(s) to download")
    download_parser.add_argument(
        "-o", "--output-dir", default=".", help="Output directory for downloaded files (default: current directory)"
    )
    download_parser.add_argument(
        "-f", "--file", help="File containing patent numbers (txt or csv). Cannot be used with patent_numbers argument"
    )
    download_parser.add_argument(
        "--has-header", action="store_true", help="File has a header row (works for both TXT and CSV files)"
    )
    download_parser.add_argument(
        "--max-retries", type=int, default=3, help="Maximum number of retry attempts for failed downloads (default: 3)"
    )
    download_parser.set_defaults(func=download_command)

    # Info command
    info_parser = subparsers.add_parser("info", help="Get patent information")
    info_parser.add_argument("patent_number", help="Patent number to get information for")
    info_parser.add_argument(
        "--max-retries", type=int, default=3, help="Maximum number of retry attempts for failed requests (default: 3)"
    )
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

    # Validate download command arguments
    if args.command == "download":
        if args.file and args.patent_numbers:
            progress_logger = get_progress_logger()
            progress_logger.log_message("Error: Cannot use both --file and patent_numbers arguments together", "error")
            return 1
        if not args.file and not args.patent_numbers:
            progress_logger = get_progress_logger()
            progress_logger.log_message("Error: Must provide either patent_numbers or --file argument", "error")
            return 1

    # Setup logging with progress bar support
    setup_progress_logging(args.verbose)

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

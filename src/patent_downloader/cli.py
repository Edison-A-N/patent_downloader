"""Command-line interface for the patent downloader."""

import argparse
import sys
import logging
import threading

from .downloader import PatentDownloader
from .exceptions import PatentDownloadError

# Create a lock for thread-safe progress bar updates
progress_lock = threading.Lock()


def print_progress_bar(completed: int, total: int, patent_number: str, success: bool):
    """Print a progress bar using =========== symbols."""
    with progress_lock:
        progress = int((completed / total) * 80)
        bar = "=" * progress + " " * (80 - progress)

        print(f"\r[{bar}] {completed}/{total}", end="", flush=True)

        if completed == total:
            print()  # New line at the end


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


def download_command(args: argparse.Namespace) -> int:
    """Handle the download command."""
    try:
        downloader = PatentDownloader()

        # Get patent numbers from file or command line arguments
        if args.file:
            results = downloader.download_patents_from_file(
                args.file, args.has_header, args.output_dir, progress_callback=print_progress_bar
            )

            successful = [pn for pn, success in results.items() if success]
            failed = [pn for pn, success in results.items() if not success]

            print("\nDownload completed:")
            print(f"  Successful: {len(successful)} patents")
            print(f"  Failed: {len(failed)} patents")

            if successful:
                print(f"  Successfully downloaded: {', '.join(successful)}")
            if failed:
                print(f"  Failed to download: {', '.join(failed)}")

            return 0 if not failed else 1
        else:
            patent_numbers = args.patent_numbers

            if len(patent_numbers) == 1:
                # Single patent download
                success = downloader.download_patent(patent_numbers[0], args.output_dir)
                if success:
                    print(f"Successfully downloaded patent {patent_numbers[0]}")
                    return 0
                else:
                    print(f"Failed to download patent {patent_numbers[0]}")
                    return 1
            else:
                # Multiple patents download with progress
                total = len(patent_numbers)
                print(f"Starting download of {total} patents...")

                results = downloader.download_patents(
                    patent_numbers, args.output_dir, progress_callback=print_progress_bar
                )

                successful = [pn for pn, success in results.items() if success]
                failed = [pn for pn, success in results.items() if not success]

                print("\nDownload completed:")
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
  patent-downloader download --file patents.txt --has-header
  patent-downloader download --file patents.csv
  patent-downloader info WO2013078254A1
  patent-downloader mcp-server --port 8000
        """,
    )

    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")

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

    # Validate download command arguments
    if args.command == "download":
        if args.file and args.patent_numbers:
            print("Error: Cannot use both --file and patent_numbers arguments together")
            return 1
        if not args.file and not args.patent_numbers:
            print("Error: Must provide either patent_numbers or --file argument")
            return 1

    setup_logging(args.verbose)

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

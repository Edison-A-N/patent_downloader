#!/usr/bin/env python3
"""
Basic usage example for the Patent Downloader SDK.

This example demonstrates how to use the SDK to download patents
and retrieve patent information.
"""

import sys
from pathlib import Path

# Add the src directory to the path so we can import the package
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from patent_downloader import PatentDownloader
from patent_downloader.exceptions import PatentDownloadError


def main():
    """Main example function."""
    print("Patent Downloader SDK - Basic Usage Example")
    print("=" * 50)

    # Create a downloader instance
    downloader = PatentDownloader()

    # Example patent numbers
    patent_numbers = ["WO2013078254A1", "US20130123448A1", "EP1234567A1"]

    # Create output directory
    output_dir = Path("downloaded_patents")
    output_dir.mkdir(exist_ok=True)

    print(f"Output directory: {output_dir.absolute()}")
    print()

    # Example 1: Download a single patent
    print("Example 1: Download a single patent")
    print("-" * 30)

    try:
        success = downloader.download_patent(patent_numbers[0], str(output_dir))
        if success:
            print(f"✓ Successfully downloaded {patent_numbers[0]}")
        else:
            print(f"✗ Failed to download {patent_numbers[0]}")
    except PatentDownloadError as e:
        print(f"✗ Error downloading {patent_numbers[0]}: {e}")

    print()

    # Example 2: Get patent information
    print("Example 2: Get patent information")
    print("-" * 30)

    try:
        patent_info = downloader.get_patent_info(patent_numbers[0])
        print(f"Patent: {patent_info.patent_number}")
        print(f"Title: {patent_info.title}")
        print(f"Inventors: {', '.join(patent_info.inventors)}")
        print(f"Assignee: {patent_info.assignee}")
        print(f"Publication Date: {patent_info.publication_date}")
        print(f"Abstract: {patent_info.abstract[:100]}...")
        print(f"URL: {patent_info.url}")
    except PatentDownloadError as e:
        print(f"✗ Error getting patent info: {e}")

    print()

    # Example 3: Download multiple patents
    print("Example 3: Download multiple patents")
    print("-" * 30)

    try:
        results = downloader.download_patents(patent_numbers, str(output_dir))

        successful = [pn for pn, success in results.items() if success]
        failed = [pn for pn, success in results.items() if not success]

        print("Download completed:")
        print(f"  Successful: {len(successful)} patents")
        print(f"  Failed: {len(failed)} patents")

        if successful:
            print(f"  Successfully downloaded: {', '.join(successful)}")
        if failed:
            print(f"  Failed to download: {', '.join(failed)}")

    except PatentDownloadError as e:
        print(f"✗ Error downloading patents: {e}")

    print()

    # Example 4: Using context manager
    print("Example 4: Using context manager")
    print("-" * 30)

    try:
        with PatentDownloader() as ctx_downloader:
            success = ctx_downloader.download_patent("WO2013078254A1", str(output_dir))
            if success:
                print("✓ Successfully downloaded using context manager")
            else:
                print("✗ Failed to download using context manager")
    except PatentDownloadError as e:
        print(f"✗ Error with context manager: {e}")

    print()
    print("Example completed!")
    print(f"Check the '{output_dir}' directory for downloaded files.")


if __name__ == "__main__":
    main()

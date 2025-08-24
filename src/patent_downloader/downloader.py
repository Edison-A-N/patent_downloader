"""Main patent downloader implementation."""

import requests
from pathlib import Path
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
import logging

from .exceptions import (
    PatentDownloadError,
    PatentNotFoundError,
    DownloadFailedError,
    NetworkError,
    InvalidPatentNumberError,
)
from .models import PatentInfo

logger = logging.getLogger(__name__)


class PatentDownloader:
    """Main class for downloading patents from Google Patents."""

    def __init__(self, timeout: int = 30, user_agent: Optional[str] = None):
        """
        Initialize the patent downloader.

        Args:
            timeout: Request timeout in seconds
            user_agent: Custom user agent string
        """
        self.timeout = timeout
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Safari/537.36"
        )
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": self.user_agent,
                "Accept": "application/pdf,application/octet-stream,*/*",
                "Accept-Language": "en-US,en;q=0.9",
            }
        )

    def download_patent_data(self, patent_number: str) -> bytes:
        """
        Download a patent PDF from Google Patents and return the data as bytes.
        """
        try:
            self._validate_patent_number(patent_number)
            patent_url = f"https://patents.google.com/patent/{patent_number}/en"
            pdf_link = self._retrieve_pdf_link(patent_number, patent_url)
            return self._download_pdf_data(pdf_link, patent_number, patent_url)
        except Exception as e:
            logger.error(f"Error downloading patent {patent_number}: {e}")
            raise DownloadFailedError(f"Error downloading patent {patent_number}: {e}") from e

    def download_patent(self, patent_number: str, output_dir: str = ".") -> bool:
        """
        Download a patent PDF from Google Patents.

        Args:
            patent_number: The patent number to download (e.g., "WO2013078254A1")
            output_dir: Directory to save the PDF file (default: current directory)

        Returns:
            bool: True if download successful, False otherwise

        Raises:
            InvalidPatentNumberError: If patent number is invalid
            PatentNotFoundError: If patent is not found
            DownloadFailedError: If download fails
            NetworkError: If there's a network error
        """
        try:
            self._validate_patent_number(patent_number)

            patent_url = f"https://patents.google.com/patent/{patent_number}/en"

            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            pdf_link = self._retrieve_pdf_link(patent_number, patent_url)

            if not pdf_link:
                raise PatentNotFoundError(f"Could not find PDF download link for patent {patent_number}")

            # Download the PDF
            return self._download_pdf(pdf_link, patent_number, output_path, patent_url)

        except requests.RequestException as e:
            logger.error(f"Network error downloading patent {patent_number}: {e}")
            raise NetworkError(f"Network error: {e}") from e
        except PatentDownloadError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error for patent {patent_number}: {e}")
            raise DownloadFailedError(f"Unexpected error: {e}") from e

    def download_patents(self, patent_numbers: List[str], output_dir: str = ".") -> Dict[str, bool]:
        """
        Download multiple patents.

        Args:
            patent_numbers: List of patent numbers to download
            output_dir: Directory to save the PDF files

        Returns:
            Dict mapping patent numbers to success status
        """
        results = {}

        for patent_number in patent_numbers:
            try:
                success = self.download_patent(patent_number, output_dir)
                results[patent_number] = success
            except Exception as e:
                logger.error(f"Failed to download patent {patent_number}: {e}")
                results[patent_number] = False

        return results

    def get_patent_info(self, patent_number: str) -> PatentInfo:
        """
        Get information about a patent.

        Args:
            patent_number: The patent number

        Returns:
            PatentInfo object with patent details

        Raises:
            PatentNotFoundError: If patent is not found
        """
        try:
            self._validate_patent_number(patent_number)

            patent_url = f"https://patents.google.com/patent/{patent_number}/en"
            response = self.session.get(patent_url, timeout=self.timeout)
            response.raise_for_status()

            return self._parse_patent_info(response.content, patent_number, patent_url)

        except requests.RequestException as e:
            raise NetworkError(f"Network error: {e}") from e
        except Exception as e:
            raise PatentNotFoundError(f"Could not retrieve patent info: {e}") from e

    def _validate_patent_number(self, patent_number: str) -> None:
        """Validate patent number format."""
        if not patent_number or not isinstance(patent_number, str):
            raise InvalidPatentNumberError("Patent number must be a non-empty string")

        # Basic validation - can be enhanced with more specific patterns
        if len(patent_number.strip()) < 3:
            raise InvalidPatentNumberError("Patent number too short")

    def _retrieve_pdf_link(self, patent_number: str, patent_url: str) -> str:
        """
        Download a patent PDF from Google Patents and return the data as bytes.

        Args:
            patent_number: The patent number to download (e.g., "WO2013078254A1")

        Returns:
            bytes: The PDF data as bytes

        Raises:
            InvalidPatentNumberError: If patent number is invalid
            PatentNotFoundError: If patent is not found
            DownloadFailedError: If download fails
            NetworkError: If there's a network error
        """
        try:
            response = self.session.get(patent_url, timeout=self.timeout)
            response.raise_for_status()

            pdf_link = self._find_pdf_link(response.content, patent_number)

            if not pdf_link:
                raise PatentNotFoundError(f"Could not find PDF download link for patent {patent_url}")

            return pdf_link

        except requests.RequestException as e:
            logger.error(f"Network error downloading patent {patent_url}: {e}")
            raise NetworkError(f"Network error: {e}") from e
        except PatentDownloadError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error for patent {patent_url}: {e}")
            raise DownloadFailedError(f"Unexpected error: {e}") from e

    def _find_pdf_link(self, content: bytes, patent_number: str) -> Optional[str]:
        """Find PDF download link in the patent page."""
        soup = BeautifulSoup(content, "html.parser")

        # Try multiple strategies to find the PDF link
        pdf_link = None

        # Strategy 1: Look for download links with PDF in href
        for link in soup.find_all("a", href=True):
            href = link.get("href", "").lower()
            text = link.get_text().lower()
            if ("download" in href or "download" in text) and "pdf" in href:
                pdf_link = link["href"]
                break

        # Strategy 2: Look for "Download PDF" text
        if not pdf_link:
            for link in soup.find_all("a", href=True):
                text = link.get_text().strip()
                if text.lower() == "download pdf" or "download" in text.lower():
                    pdf_link = link["href"]
                    break

        # Strategy 3: Look for download patterns in href
        if not pdf_link:
            for link in soup.find_all("a", href=True):
                href = link.get("href", "")
                if "/download" in href or "download=true" in href:
                    pdf_link = href
                    break

        # Strategy 4: Try common download URLs
        if not pdf_link:
            pdf_link = f"https://patents.google.com/patent/{patent_number}/en/download"

        if not pdf_link:
            pdf_link = f"https://patents.google.com/xhr/query?url=patent={patent_number}&download=true"

        # Normalize the URL
        if pdf_link:
            if pdf_link.startswith("/"):
                pdf_link = f"https://patents.google.com{pdf_link}"
            elif not pdf_link.startswith("http"):
                pdf_link = f"https://patents.google.com/{pdf_link}"

        return pdf_link

    def _download_pdf_data(self, pdf_link: str, patent_number: str, referer: str) -> bytes:
        """Download the PDF data and return as bytes."""
        try:
            headers = {"Referer": referer}

            logger.info(f"Downloading PDF data for patent {patent_number} from {pdf_link}")

            pdf_response = self.session.get(pdf_link, headers=headers, timeout=self.timeout)
            pdf_response.raise_for_status()

            # Verify it's actually a PDF
            content_type = pdf_response.headers.get("content-type", "").lower()
            if "pdf" not in content_type and not pdf_response.content.startswith(b"%PDF"):
                logger.warning(f"Response doesn't appear to be a PDF (Content-Type: {content_type})")

            logger.info(
                f"Successfully downloaded PDF data for patent {patent_number} ({len(pdf_response.content)} bytes)"
            )
            return pdf_response.content

        except Exception as e:
            logger.error(f"Error downloading PDF data for patent {patent_number}: {e}")
            raise DownloadFailedError(f"Failed to download PDF data: {e}") from e

    def _download_pdf(self, pdf_link: str, patent_number: str, output_path: Path, referer: str) -> bool:
        """Download the PDF file."""
        try:
            pdf_data = self._download_pdf_data(pdf_link, patent_number, referer)

            output_file = output_path / f"{patent_number}.pdf"
            with open(output_file, "wb") as f:
                f.write(pdf_data)

            logger.info(f"Successfully downloaded {output_file}")
            return True

        except Exception as e:
            logger.error(f"Error downloading PDF for patent {patent_number}: {e}")
            return False

    def _parse_patent_info(self, content: bytes, patent_number: str, patent_url: str) -> PatentInfo:
        """Parse patent information from the HTML content."""
        soup = BeautifulSoup(content, "html.parser")

        # Extract basic information
        title = self._extract_title(soup)
        inventors = self._extract_inventors(soup)
        assignee = self._extract_assignee(soup)
        publication_date = self._extract_publication_date(soup)
        abstract = self._extract_abstract(soup)

        return PatentInfo(
            patent_number=patent_number,
            title=title,
            inventors=inventors,
            assignee=assignee,
            publication_date=publication_date,
            abstract=abstract,
            url=patent_url,
        )

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract patent title."""
        title_elem = soup.find("span", itemprop="title")
        if title_elem:
            return title_elem.get_text().strip()

        # Fallback to h1
        h1_elem = soup.find("h1")
        if h1_elem:
            return h1_elem.get_text().strip()

        return "Unknown Title"

    def _extract_inventors(self, soup: BeautifulSoup) -> List[str]:
        """Extract inventor names."""
        inventors = []
        inventor_elems = soup.find_all("span", itemprop="inventor")

        for elem in inventor_elems:
            name = elem.get_text().strip()
            if name:
                inventors.append(name)

        return inventors

    def _extract_assignee(self, soup: BeautifulSoup) -> str:
        """Extract assignee information."""
        assignee_elem = soup.find("span", itemprop="assignee")
        if assignee_elem:
            return assignee_elem.get_text().strip()

        return "Unknown Assignee"

    def _extract_publication_date(self, soup: BeautifulSoup) -> str:
        """Extract publication date."""
        date_elem = soup.find("time", itemprop="publicationDate")
        if date_elem:
            return date_elem.get_text().strip()

        return "Unknown Date"

    def _extract_abstract(self, soup: BeautifulSoup) -> str:
        """Extract patent abstract."""
        abstract_elem = soup.find("div", itemprop="abstract")
        if abstract_elem:
            return abstract_elem.get_text().strip()

        return "No abstract available"

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.session.close()

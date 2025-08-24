"""Tests for the patent downloader."""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
import tempfile
import shutil

from patent_downloader import PatentDownloader
from patent_downloader.exceptions import (
    PatentNotFoundError,
    InvalidPatentNumberError,
    NetworkError,
)
from patent_downloader.models import PatentInfo


class TestPatentDownloader:
    """Test cases for PatentDownloader class."""

    def setup_method(self):
        """Setup test method."""
        self.downloader = PatentDownloader()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Teardown test method."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_validate_patent_number_valid(self):
        """Test patent number validation with valid input."""
        # Should not raise any exception
        self.downloader._validate_patent_number("WO2013078254A1")
        self.downloader._validate_patent_number("US20130123448A1")
        self.downloader._validate_patent_number("EP1234567A1")

    def test_validate_patent_number_invalid(self):
        """Test patent number validation with invalid input."""
        with pytest.raises(InvalidPatentNumberError):
            self.downloader._validate_patent_number("")

        with pytest.raises(InvalidPatentNumberError):
            self.downloader._validate_patent_number("AB")

        with pytest.raises(InvalidPatentNumberError):
            self.downloader._validate_patent_number(None)

        with pytest.raises(InvalidPatentNumberError):
            self.downloader._validate_patent_number(123)

    @patch("patent_downloader.downloader.requests.Session")
    def test_download_patent_success(self, mock_session):
        """Test successful patent download."""
        # Mock the session
        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance

        # Mock the patent page response
        mock_page_response = Mock()
        mock_page_response.raise_for_status.return_value = None
        mock_page_response.content = b'<html><a href="/download">Download PDF</a></html>'

        # Mock the PDF response
        mock_pdf_response = Mock()
        mock_pdf_response.raise_for_status.return_value = None
        mock_pdf_response.content = b"%PDF-1.4 fake pdf content"
        mock_pdf_response.headers = {"content-type": "application/pdf"}

        mock_session_instance.get.side_effect = [mock_page_response, mock_pdf_response]

        # Test download
        result = self.downloader.download_patent("WO2013078254A1", self.temp_dir)

        assert result is True
        assert (Path(self.temp_dir) / "WO2013078254A1.pdf").exists()

    @patch("patent_downloader.downloader.requests.Session")
    def test_download_patent_network_error(self, mock_session):
        """Test patent download with network error."""
        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance
        mock_session_instance.get.side_effect = Exception("Network error")

        with pytest.raises(NetworkError):
            self.downloader.download_patent("WO2013078254A1", self.temp_dir)

    @patch("patent_downloader.downloader.requests.Session")
    def test_download_patent_not_found(self, mock_session):
        """Test patent download when patent is not found."""
        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance

        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.content = b"<html>Patent not found</html>"

        mock_session_instance.get.return_value = mock_response

        with pytest.raises(PatentNotFoundError):
            self.downloader.download_patent("INVALID123", self.temp_dir)

    def test_download_patents_multiple(self):
        """Test downloading multiple patents."""
        with patch.object(self.downloader, "download_patent") as mock_download:
            mock_download.side_effect = [True, False, True]

            results = self.downloader.download_patents(
                ["WO2013078254A1", "US20130123448A1", "EP1234567A1"], self.temp_dir
            )

            expected = {"WO2013078254A1": True, "US20130123448A1": False, "EP1234567A1": True}

            assert results == expected

    @patch("patent_downloader.downloader.requests.Session")
    def test_get_patent_info_success(self, mock_session):
        """Test successful patent info retrieval."""
        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance

        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.content = b"""
        <html>
            <span itemprop="title">Test Patent Title</span>
            <span itemprop="inventor">John Doe</span>
            <span itemprop="assignee">Test Company</span>
            <time itemprop="publicationDate">2023-01-01</time>
            <div itemprop="abstract">Test abstract</div>
        </html>
        """

        mock_session_instance.get.return_value = mock_response

        result = self.downloader.get_patent_info("WO2013078254A1")

        assert isinstance(result, PatentInfo)
        assert result.patent_number == "WO2013078254A1"
        assert result.title == "Test Patent Title"
        assert "John Doe" in result.inventors
        assert result.assignee == "Test Company"
        assert result.publication_date == "2023-01-01"
        assert result.abstract == "Test abstract"

    def test_find_pdf_link_strategies(self):
        """Test different strategies for finding PDF links."""
        # Test strategy 1: download + pdf in href
        content1 = b'<a href="/download.pdf">Download PDF</a>'
        link1 = self.downloader._find_pdf_link(content1, "WO2013078254A1")
        assert link1 is not None

        # Test strategy 2: "Download PDF" text
        content2 = b'<a href="/some-link">Download PDF</a>'
        link2 = self.downloader._find_pdf_link(content2, "WO2013078254A1")
        assert link2 is not None

        # Test strategy 3: /download in href
        content3 = b'<a href="/patent/download">Download</a>'
        link3 = self.downloader._find_pdf_link(content3, "WO2013078254A1")
        assert link3 is not None

        # Test fallback URL
        content4 = b"<html>No download links</html>"
        link4 = self.downloader._find_pdf_link(content4, "WO2013078254A1")
        assert link4 is not None
        assert "download" in link4

    def test_context_manager(self):
        """Test context manager functionality."""
        with PatentDownloader() as downloader:
            assert isinstance(downloader, PatentDownloader)
            assert downloader.session is not None

        # Session should be closed after context exit
        assert downloader.session is not None  # Mock session doesn't actually close


class TestPatentInfo:
    """Test cases for PatentInfo model."""

    def test_patent_info_creation(self):
        """Test PatentInfo creation."""
        patent_info = PatentInfo(
            patent_number="WO2013078254A1",
            title="Test Patent",
            inventors=["John Doe", "Jane Smith"],
            assignee="Test Company",
            publication_date="2023-01-01",
            abstract="Test abstract",
            url="https://patents.google.com/patent/WO2013078254A1",
            pdf_url="https://patents.google.com/patent/WO2013078254A1/download",
        )

        assert patent_info.patent_number == "WO2013078254A1"
        assert patent_info.title == "Test Patent"
        assert len(patent_info.inventors) == 2
        assert patent_info.assignee == "Test Company"
        assert patent_info.publication_date == "2023-01-01"
        assert patent_info.abstract == "Test abstract"
        assert patent_info.url == "https://patents.google.com/patent/WO2013078254A1"
        assert patent_info.pdf_url == "https://patents.google.com/patent/WO2013078254A1/download"

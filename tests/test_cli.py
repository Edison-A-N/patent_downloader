"""Tests for the command-line interface."""

from unittest.mock import patch, Mock
import tempfile
import shutil

from patent_downloader.cli import download_command, info_command, setup_logging


class TestCLI:
    """Test cases for CLI functionality."""

    def setup_method(self):
        """Setup test method."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Teardown test method."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_setup_logging(self):
        """Test logging setup."""
        # Should not raise any exception
        setup_logging(verbose=False)
        setup_logging(verbose=True)

    @patch("patent_downloader.cli.PatentDownloader")
    def test_download_command_single_success(self, mock_downloader_class):
        """Test single patent download success."""
        mock_downloader = Mock()
        mock_downloader_class.return_value = mock_downloader
        mock_downloader.download_patent.return_value = True

        args = Mock()
        args.patent_numbers = ["WO2013078254A1"]
        args.output_dir = self.temp_dir

        result = download_command(args)

        assert result == 0
        mock_downloader.download_patent.assert_called_once_with("WO2013078254A1", self.temp_dir)

    @patch("patent_downloader.cli.PatentDownloader")
    def test_download_command_single_failure(self, mock_downloader_class):
        """Test single patent download failure."""
        mock_downloader = Mock()
        mock_downloader_class.return_value = mock_downloader
        mock_downloader.download_patent.return_value = False

        args = Mock()
        args.patent_numbers = ["WO2013078254A1"]
        args.output_dir = self.temp_dir

        result = download_command(args)

        assert result == 1

    @patch("patent_downloader.cli.PatentDownloader")
    def test_download_command_multiple(self, mock_downloader_class):
        """Test multiple patent download."""
        mock_downloader = Mock()
        mock_downloader_class.return_value = mock_downloader
        mock_downloader.download_patents.return_value = {
            "WO2013078254A1": True,
            "US20130123448A1": False,
            "EP1234567A1": True,
        }

        args = Mock()
        args.patent_numbers = ["WO2013078254A1", "US20130123448A1", "EP1234567A1"]
        args.output_dir = self.temp_dir

        result = download_command(args)

        assert result == 1  # Some failed
        mock_downloader.download_patents.assert_called_once_with(
            ["WO2013078254A1", "US20130123448A1", "EP1234567A1"], self.temp_dir
        )

    @patch("patent_downloader.cli.PatentDownloader")
    def test_download_command_exception(self, mock_downloader_class):
        """Test download command with exception."""
        mock_downloader = Mock()
        mock_downloader_class.return_value = mock_downloader
        mock_downloader.download_patent.side_effect = Exception("Test error")

        args = Mock()
        args.patent_numbers = ["WO2013078254A1"]
        args.output_dir = self.temp_dir

        result = download_command(args)

        assert result == 1

    @patch("patent_downloader.cli.PatentDownloader")
    def test_info_command_success(self, mock_downloader_class):
        """Test patent info command success."""
        from patent_downloader.models import PatentInfo

        mock_downloader = Mock()
        mock_downloader_class.return_value = mock_downloader

        patent_info = PatentInfo(
            patent_number="WO2013078254A1",
            title="Test Patent",
            inventors=["John Doe"],
            assignee="Test Company",
            publication_date="2023-01-01",
            abstract="Test abstract",
            url="https://patents.google.com/patent/WO2013078254A1",
        )
        mock_downloader.get_patent_info.return_value = patent_info

        args = Mock()
        args.patent_number = "WO2013078254A1"

        result = info_command(args)

        assert result == 0
        mock_downloader.get_patent_info.assert_called_once_with("WO2013078254A1")

    @patch("patent_downloader.cli.PatentDownloader")
    def test_info_command_exception(self, mock_downloader_class):
        """Test patent info command with exception."""
        mock_downloader = Mock()
        mock_downloader_class.return_value = mock_downloader
        mock_downloader.get_patent_info.side_effect = Exception("Test error")

        args = Mock()
        args.patent_number = "WO2013078254A1"

        result = info_command(args)

        assert result == 1

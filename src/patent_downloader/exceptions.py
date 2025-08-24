"""Custom exceptions for the patent downloader."""


class PatentDownloadError(Exception):
    """Base exception for patent download errors."""

    pass


class PatentNotFoundError(PatentDownloadError):
    """Raised when a patent is not found."""

    pass


class DownloadFailedError(PatentDownloadError):
    """Raised when downloading a patent fails."""

    pass


class InvalidPatentNumberError(PatentDownloadError):
    """Raised when an invalid patent number is provided."""

    pass


class NetworkError(PatentDownloadError):
    """Raised when there's a network-related error."""

    pass

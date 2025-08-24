"""Data models for the patent downloader."""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class PatentInfo:
    """Information about a patent."""

    patent_number: str
    title: str
    inventors: List[str]
    assignee: str
    publication_date: str
    abstract: str
    url: Optional[str] = None
    pdf_url: Optional[str] = None


@dataclass
class DownloadResult:
    """Result of a patent download operation."""

    patent_number: str
    success: bool
    file_path: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class SearchResult:
    """Result of a patent search."""

    patents: List[PatentInfo]
    total_count: int
    query: str

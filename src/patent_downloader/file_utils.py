"""File utility functions for reading patent numbers from files."""

import os
import csv
from pathlib import Path
from typing import List


def read_patent_numbers_from_file(file_path: str, has_header: bool = False) -> List[str]:
    """
    Read patent numbers from a file (txt or csv).

    Args:
        file_path: Path to the file to read
        has_header: Whether the file has a header row (for both TXT and CSV files)

    Returns:
        List of patent numbers

    Raises:
        ValueError: If file format is not supported or data format is invalid
    """
    # Expand ~ to home directory
    path = Path(os.path.expanduser(file_path))

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if path.suffix.lower() == ".txt":
        return _read_txt_file(path, has_header)
    elif path.suffix.lower() == ".csv":
        return _read_csv_file(path, has_header)
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}. Only .txt and .csv are supported.")


def _read_txt_file(path: Path, has_header: bool) -> List[str]:
    """Read patent numbers from a text file."""
    patent_numbers = []

    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

        if has_header and lines:
            lines = lines[1:]  # Skip header row

        for line in lines:
            line = line.strip()
            if line:  # Skip empty lines
                patent_numbers.append(line)

    if not patent_numbers:
        raise ValueError("Text file contains no patent numbers")

    return patent_numbers


def _read_csv_file(path: Path, has_header: bool) -> List[str]:
    """Read patent numbers from a CSV file."""
    patent_numbers = []

    with open(path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)

        if has_header:
            next(reader, None)  # Skip header row

        for row in reader:
            if not row:
                continue  # Skip empty rows

            if len(row) > 1:
                raise ValueError("CSV file must contain only one column of patent numbers")

            patent_number = row[0].strip()
            if patent_number:  # Skip empty cells
                patent_numbers.append(patent_number)

    if not patent_numbers:
        raise ValueError("CSV file contains no patent numbers")

    return patent_numbers

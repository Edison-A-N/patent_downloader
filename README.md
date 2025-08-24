# Patent Downloader SDK

A Python SDK for downloading patents from Google Patents with Model Context Protocol (MCP) support.

## Features

- Download patent PDFs from Google Patents
- Simple and clean API
- MCP (Model Context Protocol) server support
- Command-line interface
- Type hints and comprehensive error handling

## Installation

### Using uv (recommended)

```bash
# Install with basic dependencies
uv add patent-downloader

# Install with MCP support
uv add "patent-downloader[mcp]"

# Install with development dependencies
uv add "patent-downloader[dev]"
```

### Using pip

```bash
# Install with basic dependencies
pip install patent-downloader

# Install with MCP support
pip install "patent-downloader[mcp]"

# Install with development dependencies
pip install "patent-downloader[dev]"
```

## Quick Start

### Basic Usage

```python
from patent_downloader import PatentDownloader

# Create downloader instance
downloader = PatentDownloader()

# Download a patent
success = downloader.download_patent("WO2013078254A1", output_dir="./patents")

if success:
    print("Patent downloaded successfully!")
else:
    print("Failed to download patent")
```

### Command Line Interface

```bash
# Download a single patent
patent-downloader download WO2013078254A1

# Download to specific directory
patent-downloader download WO2013078254A1 --output-dir ./my_patents

# Download multiple patents
patent-downloader download WO2013078254A1 US20130123448A1 EP1234567A1
```

### MCP Server

Start the MCP server:

```bash
# Start MCP server
patent-downloader mcp-server

# Or with custom port
patent-downloader mcp-server --port 8000
```

The MCP server provides the following functions:

- `download_patent`: Download a single patent
- `download_patents`: Download multiple patents
- `search_patents`: Search for patents (future feature)

## API Reference

### PatentDownloader

Main class for downloading patents.

#### Methods

- `download_patent(patent_number: str, output_dir: str = ".") -> bool`
  - Downloads a single patent PDF
  - Returns `True` if successful, `False` otherwise

- `download_patents(patent_numbers: List[str], output_dir: str = ".") -> Dict[str, bool]`
  - Downloads multiple patents
  - Returns a dictionary mapping patent numbers to success status

- `search_patents(query: str, limit: int = 10) -> List[PatentInfo]` (future)
  - Search for patents by query
  - Returns list of patent information

### PatentInfo

Data class containing patent information.

```python
@dataclass
class PatentInfo:
    patent_number: str
    title: str
    inventors: List[str]
    assignee: str
    publication_date: str
    abstract: str
```

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/patent_downloader.git
cd patent_downloader

# Install with development dependencies
uv sync --group dev

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=patent_downloader

# Run specific test file
pytest tests/test_downloader.py
```

### Code Quality

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Type checking
mypy src/

# Linting
flake8 src/ tests/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

### 0.1.0
- Initial release
- Basic patent downloading functionality
- MCP server support
- Command-line interface 
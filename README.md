# Patent Downloader SDK

A Python SDK for downloading patents from Google Patents with MCP support.

## Features

- Download patent PDFs from Google Patents
- Get patent information (title, inventors, assignee, etc.)
- MCP server support
- Command-line interface
- Simple API with error handling

## Installation

```bash
# Using uv (recommended)
uv add patent-downloader
uv add "patent-downloader[mcp]"

# Using pip
pip install patent-downloader
pip install "patent-downloader[mcp]"
```

## Quick Start

### Python API

```python
from patent_downloader import PatentDownloader

# Download a patent
downloader = PatentDownloader()
success = downloader.download_patent("WO2013078254A1", "./patents")

# Get patent info
info = downloader.get_patent_info("WO2013078254A1")
print(f"Title: {info.title}")

# Download multiple patents
results = downloader.download_patents(["WO2013078254A1", "US20130123448A1"])
```

### Command Line

```bash
# Download patents
patent-downloader download WO2013078254A1
patent-downloader download WO2013078254A1 US20130123448A1 --output-dir ./patents

# Get patent info
patent-downloader info WO2013078254A1

# Start MCP server
patent-downloader mcp-server
```

### MCP Server

The MCP server provides these functions:
- `download_patent`: Download a single patent
- `download_patents`: Download multiple patents  
- `get_patent_info`: Get patent information

```bash
# Start server
patent-downloader mcp-server

# Or with uvx
uvx patent-downloader mcp-server
```

## API

### PatentDownloader

```python
# Download patent
downloader.download_patent(patent_number, output_dir=".")

# Download multiple patents
downloader.download_patents(patent_numbers, output_dir=".")

# Get patent info
downloader.get_patent_info(patent_number)
```

### PatentInfo

```python
@dataclass
class PatentInfo:
    patent_number: str
    title: str
    inventors: List[str]
    assignee: str
    publication_date: str
    abstract: str
    url: Optional[str] = None
```

## License

MIT License

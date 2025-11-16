# Patent Downloader SDK

A Python SDK for downloading patents from Google Patents with MCP support.

## Features

- Download patent PDFs from Google Patents
- Get patent information (title, inventors, assignee, etc.)
- MCP server support
- Command-line interface
- Simple API with error handling
- **Support for batch downloading from files (TXT/CSV)**

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

# Download patents from file
results = downloader.download_patents_from_file("patents.txt", has_header=False)
```

### Command Line

```bash
# Download patents
patent-downloader download WO2013078254A1
patent-downloader download WO2013078254A1 US20130123448A1 --output-dir ./patents

# Download patents from file
patent-downloader download --file patents.txt
patent-downloader download --file patents.csv --has-header

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

You can configure the default download directory using the `OUTPUT_DIR` environment variable in your MCP configuration. This allows you to set a fixed download path for all patent downloads.

#### Quick Install for Cursor

**Using uvx** (no installation required)

Basic installation (default download directory: `~/downloads`):
```
cursor://anysphere.cursor-deeplink/mcp/install?name=patent-downloader&config=eyJjb21tYW5kIjogInV2eCIsICJhcmdzIjogWyItLXdpdGgiLCAibWNwIiwgInBhdGVudC1kb3dubG9hZGVyIiwgIm1jcC1zZXJ2ZXIiXX0
```

**Note**: If you need to customize the download directory, you'll need to manually edit your `mcp.json` file after installation and add the `env` section:

```json
{
  "mcpServers": {
    "patent-downloader": {
      "command": "uvx",
      "args": ["--with", "mcp", "patent-downloader", "mcp-server"],
      "env": {
        "OUTPUT_DIR": "~/Downloads/patents"
      }
    }
  }
}
```

#### Manual Setup

```bash
# Start server
patent-downloader mcp-server

# Using uvx to run without installation (specify MCP dependencies):
uvx --with mcp patent-downloader mcp-server
```

## API

### PatentDownloader

```python
# Download patent
downloader.download_patent(patent_number, output_dir=".")

# Download multiple patents
downloader.download_patents(patent_numbers, output_dir=".")

# Download patents from file
downloader.download_patents_from_file(file_path, has_header=False, output_dir=".")

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

## File Format Support

The SDK supports reading patent numbers from both TXT and CSV files:

### TXT Files
- One patent number per line
- Optional header row (use `--has-header` flag)
- Example:
  ```
  WO2013078254A1
  US20130123448A1
  EP1234567A1
  ```

### CSV Files
- Single column of patent numbers
- Optional header row (use `--has-header` flag)
- Example:
  ```csv
  patent_number
  WO2013078254A1
  US20130123448A1
  EP1234567A1
  ```

## License

MIT License

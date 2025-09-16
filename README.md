# Smartsheet to JSON Sync Tool

A Python template for synchronizing Smartsheet workspace data to JSON files. This tool fetches all sheets from a Smartsheet workspace and stores them as structured JSON files for use in your applications.

## Features

- **Full workspace sync**: Download all sheets from a Smartsheet workspace
- **Selective sync**: Sync only specific sheets by ID
- **JSON file storage**: Clean, structured JSON files for each sheet
- **Metadata tracking**: Workspace and sync operation history
- **Error handling**: Robust error handling with detailed logging
- **CLI interface**: Easy-to-use command line interface
- **Configurable**: Environment-based configuration

## Project Structure

```
smartsheet-to-json/
├── config/
│   ├── settings.py          # Configuration management
│   └── .env.example         # Environment variables template
├── src/
│   ├── smartsheet_client.py # Smartsheet API wrapper
│   ├── json_storage.py      # JSON file operations
│   └── sync_manager.py      # Main sync orchestration
├── utils/
│   └── logger.py            # Logging configuration
├── data/                    # JSON data storage (created automatically)
│   ├── workspace_meta.json  # Workspace information
│   ├── sheets/              # Individual sheet data files
│   └── sync_history.json    # Sync operation logs
├── main.py                  # CLI entry point
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Setup

### 1. Setup Virtual Environment and Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Note**: Always activate the virtual environment before running the script:
```bash
source venv/bin/activate
```

### 2. Configure Environment

Copy the example environment file and add your credentials:

```bash
cp config/.env.example .env
```

Edit `.env` with your Smartsheet credentials:

```bash
# Required
SMARTSHEET_API_TOKEN=your_smartsheet_api_token_here
WORKSPACE_ID=your_workspace_id_here

# Optional
LOG_LEVEL=INFO
REQUEST_TIMEOUT=30
MAX_RETRIES=3
```

### 3. Get Your Smartsheet Credentials

**API Token:**
1. Log in to Smartsheet
2. Go to Account → Personal Settings → API Access
3. Generate a new access token

**Workspace ID:**
1. Navigate to your workspace in Smartsheet
2. The workspace ID is in the URL: `https://app.smartsheet.com/workspaces/{WORKSPACE_ID}`

## Usage

### Basic Commands

```bash
# Test connection
python main.py validate

# Full sync of all sheets
python main.py sync

# Sync specific sheets by ID
python main.py sync --sheets 1234567890 9876543210

# Check current status
python main.py status

# Clean up old files (keep latest 5)
python main.py cleanup --keep 5
```

### Output Formats

```bash
# JSON output for programmatic use
python main.py sync --output json
python main.py status --format json

# Human-readable table format (default)
python main.py status --format table
```

## Data Structure

### Sheet Data Format

Each sheet is stored as a JSON file with this structure:

```json
{
  "metadata": {
    "id": 1234567890,
    "name": "Project Tasks",
    "total_row_count": 150,
    "created_at": "2024-01-01T10:00:00Z",
    "modified_at": "2024-01-15T14:30:00Z",
    "last_sync": "2024-01-15 14:35:22"
  },
  "columns": [
    {
      "id": 123,
      "title": "Task Name",
      "type": "TEXT_NUMBER",
      "primary": true,
      "index": 0
    }
  ],
  "rows": [
    {
      "id": 456,
      "row_number": 1,
      "cells": {
        "123": {
          "value": "Design wireframes",
          "display_value": "Design wireframes"
        }
      }
    }
  ]
}
```

### Using the Data in Your App

```python
import json
from pathlib import Path

# Load workspace metadata
with open('data/workspace_meta.json', 'r') as f:
    workspace = json.load(f)

# Load specific sheet
with open('data/sheets/sheet_1234567890.json', 'r') as f:
    sheet_data = json.load(f)

# Access sheet metadata
print(f"Sheet: {sheet_data['metadata']['name']}")
print(f"Rows: {sheet_data['metadata']['total_row_count']}")

# Access rows and cells
for row in sheet_data['rows']:
    for column_id, cell in row['cells'].items():
        print(f"Cell value: {cell['value']}")
```

## Integration Examples

### As a Module

```python
from src.sync_manager import SyncManager

# Initialize
sync_manager = SyncManager()

# Sync all data
result = sync_manager.full_sync()

# Sync specific sheets
result = sync_manager.sync_specific_sheets([1234567890])

# Get current status
status = sync_manager.get_status()
```

### Scheduled Sync

Add to your crontab for periodic syncing:

```bash
# Sync every hour
0 * * * * cd /path/to/smartsheet-to-json && python main.py sync

# Daily cleanup, keep latest 30
0 2 * * * cd /path/to/smartsheet-to-json && python main.py cleanup --keep 30
```

## Configuration Options

All configuration is in `config/settings.py` and can be overridden with environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `SMARTSHEET_API_TOKEN` | Your Smartsheet API token | Required |
| `WORKSPACE_ID` | Target workspace ID | Required |
| `LOG_LEVEL` | Logging level | `INFO` |
| `REQUEST_TIMEOUT` | API request timeout (seconds) | `30` |
| `MAX_RETRIES` | Maximum retry attempts | `3` |

## Troubleshooting

### Common Issues

**"Invalid token" error:**
- Verify your API token is correct
- Check that the token has access to the workspace

**"Workspace not found":**
- Verify the workspace ID is correct
- Ensure your API token has access to the workspace

**"Permission denied" errors:**
- Check file permissions in the data directory
- Ensure the script can create/write files

### Logs

Check the log file for detailed error information:
```bash
tail -f smartsheet_sync.log
```

## Migration to Database

When you're ready to move from JSON files to a database:

1. **PostgreSQL with JSONB**: Store the JSON data in JSONB columns
2. **SQLite**: Lightweight option for single-user apps
3. **MongoDB**: Document database that natively handles JSON

The JSON structure is designed to be database-friendly and can be easily imported into most database systems.

## Contributing

This is a template project. Feel free to modify and extend it for your specific needs:

- Add data transformation logic
- Implement incremental syncing
- Add web API endpoints
- Create a web dashboard
- Add data validation

## License

This template is provided as-is for educational and development purposes.
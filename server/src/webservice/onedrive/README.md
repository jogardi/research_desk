# OneDrive Module

A self-contained Python module for accessing Microsoft OneDrive via the Graph API.

## Features

- Download files and folders from OneDrive
- Walk folder trees recursively
- Support for both personal and business OneDrive accounts
- Two authentication methods:
  - **Device Code Flow** (interactive, with token caching)
  - **Client Secret** (app-only, for automation)

## Dependencies

Add these to your `pyproject.toml`:

```toml
[tool.poetry.dependencies]
azure-identity = "^1.15.0"
azure-core = "^1.30.0"
requests = "^2.31.0"
tenacity = "^8.2.0"
msal = "^1.26.0"
```

Or install with pip:

```bash
pip install azure-identity azure-core requests tenacity msal
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `AZURE_CLIENT_ID` | Yes | Azure app registration client ID |
| `AZURE_CLIENT_SECRET` | For client_secret auth | Azure app client secret |
| `AZURE_TENANT_ID` | For client_secret auth | Azure tenant ID |
| `TARGET_USER` | For client_secret auth | User email or ID to access their OneDrive |

## Usage

```python
from onedrive.client import OneDriveClient

# Initialize client (triggers authentication)
client = OneDriveClient()

# Get a file by path
file_info = client.get_file_by_path("Documents/report.pdf")

# Download a file
client.download_file(file_info["id"], "./local_report.pdf")

# Walk a folder tree
files = client.walk_folder_tree(folder_id)
for f in files:
    print(f["path"], f["name"])
```

## Configuration

Edit `config.py` to change:
- `AUTH_METHOD` - authentication method (`CACHED_DEVICE_CODE` or `CLIENT_SECRET`)
- Retry settings for API requests

## Files

| File | Description |
|------|-------------|
| `client.py` | High-level OneDrive client |
| `graph_api.py` | Low-level Graph API client |
| `auth_context.py` | Authentication context (credentials, paths) |
| `config.py` | Configuration settings |
| `logger.py` | Simple file/console logger |
| `auth/` | Authentication implementations |


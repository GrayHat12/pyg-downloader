# Basic File Downloader

Uses multiple parallel connections to download a file.

## Usage
```py
from src.manager import Manager

URL = "https://download.samplelib.com/mp4/sample-15s.mp4"

manager = Manager(URL)

manager.start_download()

```

## Options
Manager supports the following options:
* URL (required) : The URL of the file to download.
* max_connections (optional) : The maximum number of parallel connections to use. Default is 4. Maximum allowed is 8.
* show_progress (optional) : Whether to show a progress bar. Default is True.
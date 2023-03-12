# pyg-downloader

Uses multiple parallel connections to download a file.

## Testing
```bash
pytest
```

## Install
```bash
pip install pyg-downloader
```
**OR** if you want to show progress
```bash
pip install pyg-downloader[atpbar]
```

## Usage

### CLI
```bash
pyg-downloader https://download.samplelib.com/mp4/sample-15s.mp4 -o test.mp4 --max-connections 8 --progress
```

### To Download to disk
```py
from pyg_download_manager import DownloadManager

manager = DownloadManager(max_connections=8, show_progress=True)

# Download to disk and returns the path to the file
# destination_path is the path to the folder for download
# filename is the name of the file to save to. Default is the filename from url.
path = manager.download("https://download.samplelib.com/mp4/sample-15s.mp4", destination_path='./', filename=None)
```

### To Download to memory
```py
from pyg_download_manager import DownloadManager

manager = DownloadManager(max_connections=8, show_progress=True)

# Download data to an BytesIO object and returns the object
# task_name is used to log progress. Default is the filename from url.
data = manager.get("https://download.samplelib.com/mp4/sample-15s.mp4", task_name='Test Task')
```
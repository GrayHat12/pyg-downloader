import sys

sys.path.append('./src')

from download_manager import DownloadManager

manager = DownloadManager(max_connections=8, show_progress=True)

# Download to current working directory and returns the path to the file
# destination_path is the path to the folder for download
# filename is the name of the file to save to. Default is the filename from url.
path = manager.download("https://download.samplelib.com/mp4/sample-15s.mp4", destination_path='./', filename=None)
import os
from io import BytesIO

from download_manager import DownloadManager


def test_manager():
    URL = "https://download.samplelib.com/mp4/sample-15s.mp4"

    manager = DownloadManager(max_connections=8, show_progress=True)

    path = manager.download(URL, destination_path='./', filename=None)

    assert isinstance(path, str)
    assert os.path.exists(path)

    data = manager.get(url=URL)

    assert isinstance(data, BytesIO)
    assert len(data.getvalue()) > 0

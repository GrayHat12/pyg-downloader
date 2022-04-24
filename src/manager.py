from math import ceil
from typing import Union
import requests
import threading
from atpbar import atpbar, flush, disable

from src.downloader import Downloader


class Manager:
    def __init__(self, url: str, max_connections: int = 4, show_progress=True, destination_path: str = './', filename: Union[str, None] = None):
        self.download_url = url
        self.number_of_connections = min(max_connections, 8)
        self.uuids = []
        self.filename = filename
        self.filesize = None
        self.filetype = None
        self.destination_path = destination_path or './'
        if not self.destination_path.endswith('/'):
            self.destination_path += '/'
        if not show_progress:
            disable()

    def get_complete_path(self):
        return f"{self.destination_path}{self.filename}"

    def get_meta(self):
        response = requests.head(self.download_url)
        if not self.filename:
            self.filename = self.download_url.split('/')[-1]
        self.filesize = int(response.headers['Content-Length'])
        self.filetype = response.headers.get('Content-Type', None)
        with open(self.get_complete_path(), 'wb+') as f:
            f.write(b'0'*self.filesize)

    def start_download(self):
        self.get_meta()

        if not self.filename or not self.filesize:
            raise Exception('Failed to fetch meta data')

        start_range = 0
        part_size = ceil(self.filesize / self.number_of_connections)
        parts = []

        for i in range(1, self.number_of_connections+1):
            end_range = start_range + part_size
            if i == self.number_of_connections:
                end_range = ""
            name = f"Part {i} of {self.filename}"
            parts.append(
                threading.Thread(target=self.single_download, args=(
                    start_range, end_range, name), name=name)
            )
            if isinstance(end_range, int):
                start_range = end_range + 1

        # start all threads
        for part in parts:
            part.start()

        # join all threads
        for part in parts:
            part.join()
        
        flush()

    def single_download(self, range_from: int, range_to: Union[str, int], name: str):
        download_range = f"bytes={range_from}-{range_to}"
        current_pos = range_from
        with Downloader(self.download_url, download_range) as downloader:
            with open(self.get_complete_path(), 'r+b') as f:
                f.seek(current_pos)
                for chunk, progress in atpbar(downloader, name=name):
                    f.write(chunk)

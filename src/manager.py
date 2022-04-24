from math import ceil
from typing import Union
from uuid import uuid4
import requests
import threading
from atpbar import atpbar, flush, disable
import os

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

    def get_meta(self):
        response = requests.head(self.download_url)
        if not self.filename:
            self.filename = self.download_url.split('/')[-1]
        self.filesize = int(response.headers['Content-Length'])
        self.filetype = response.headers.get('Content-Type', None)

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
            uid = uuid4().hex
            self.uuids.append(uid)
            name = f"Part {i} of {self.filename}"
            parts.append(
                threading.Thread(target=self.single_download, args=(
                    uid, start_range, end_range, name), name=name)
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

        filepath = f"{self.destination_path}{self.filename}"

        with open(filepath, 'wb+') as f:
            f.write(b'')

        for uid in self.uuids:
            filename = f"{uid}-{self.filename}.part"
            src_path = f"{self.destination_path}{filename}"
            with open(src_path, 'rb') as src_file:
                with open(filepath, 'ab') as dest_file:
                    dest_file.write(src_file.read())
            os.remove(src_path)

    def log_progress(self, uid: str, progress: int):
        print(f"{uid} - {progress}%")

    def single_download(self, uid: str, range_from: int, range_to: Union[str, int], name: str):
        filename = f"{uid}-{self.filename}.part"
        filepath = f"{self.destination_path}{filename}"
        download_range = f"bytes={range_from}-{range_to}"
        with Downloader(self.download_url, filename, download_range) as downloader:
            with open(filepath, 'ab+') as f:
                for chunk, progress in atpbar(downloader, name=name):
                    f.write(chunk)

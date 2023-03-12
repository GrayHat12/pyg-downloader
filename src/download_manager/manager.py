import os
import threading
from io import BytesIO
from math import ceil
from typing import Iterable, List, Optional, Union

import requests

try:
    from atpbar import atpbar, disable, flush
except ImportError as e:
    import warnings

    def empty_function(*args, **kwargs):
        warnings.warn(
            "You need to install atpbar to use 'show_progress' feature.")

    def atpbar(iterable: Iterable, *args, **kwargs):
        for i in iterable:
            yield i, 0
    disable = empty_function
    flush = empty_function

from downloader import Downloader


class DownloadManager:

    def __init__(self, max_connections: int = 4, show_progress: bool = False):
        if not isinstance(max_connections, int):
            raise TypeError("max_connections must be an integer")
        if not isinstance(show_progress, bool):
            raise TypeError("show_progress must be a boolean")
        self.__number_of_connections = min(max(max_connections, 1), 8)

        if not show_progress:
            disable()

    def __get_meta(self, url: str):
        response = requests.head(url)
        filesize = int(response.headers['Content-Length'])
        filetype = response.headers.get('Content-Type', None)
        return filesize, filetype

    def download(self, url: str, destination_path: str = './', filename: Optional[str] = None):
        """
        Download data to disk. Return full filepath
        """

        if not isinstance(url, str):
            raise TypeError("url must be a string")

        destination_path = destination_path or './'
        if not destination_path.endswith('/'):
            destination_path += '/'

        if not filename:
            filename = url.split('/')[-1]

        filesize, filetype = self.__get_meta(url)

        if not filename or not filesize:
            raise Exception('Failed to fetch meta data')

        with open(f"{destination_path}{filename}", 'wb+') as f:
            f.write(b'0'*filesize)

        start_range = 0
        part_size = ceil(filesize / self.__number_of_connections)
        parts: List[threading.Thread] = []

        for i in range(1, self.__number_of_connections+1):
            end_range = start_range + part_size
            if i == self.__number_of_connections:
                end_range = ""
            name = f"Part {i} of {filename}"
            thread = threading.Thread(target=self.__disk_download, args=(
                url, f"{destination_path}{filename}", start_range, end_range, name), name=name)
            thread.start()
            parts.append(thread)
            if isinstance(end_range, int):
                start_range = end_range + 1

        # join all threads
        for part in parts:
            part.join()

        flush()
        return os.path.abspath(f"{destination_path}{filename}")

    def get(self, url: str, task_name: Optional[str] = None):
        """
        Download data in memory and return it as a BytesIO object
        """

        if not isinstance(url, str):
            raise TypeError("url must be a string")

        if not task_name or not isinstance(task_name, str):
            task_name = url.split('/')[-1]

        filesize, filetype = self.__get_meta(url)

        if not filesize:
            raise Exception('Failed to fetch meta data')
        data = BytesIO(b'0' * filesize)

        start_range = 0
        part_size = ceil(filesize / self.__number_of_connections)
        parts: List[threading.Thread] = []

        for i in range(1, self.__number_of_connections+1):
            end_range = start_range + part_size
            if i == self.__number_of_connections:
                end_range = ""
            name = f"Part {i} of {task_name}"
            thread = threading.Thread(target=self.__object_download, args=(
                url, data, start_range, end_range, name), name=name)
            thread.start()
            parts.append(thread)
            if isinstance(end_range, int):
                start_range = end_range + 1

        # join all threads
        for part in parts:
            part.join()

        flush()
        return data

    def __disk_download(self, download_url: str, filepath: str, range_from: int, range_to: Union[str, int], name: str):
        download_range = f"bytes={range_from}-{range_to}"
        current_pos = range_from
        with Downloader(download_url, download_range) as downloader:
            with open(filepath, 'r+b') as f:
                f.seek(current_pos)
                for chunk, progress in atpbar(downloader, name=name):
                    f.write(chunk)

    def __object_download(self, download_url: str, object: BytesIO, range_from: int, range_to: Union[str, int], name: str):
        download_range = f"bytes={range_from}-{range_to}"
        current_pos = range_from
        with Downloader(download_url, download_range) as downloader:
            object.seek(current_pos)
            for chunk, progress in atpbar(downloader, name=name):
                object.write(chunk)

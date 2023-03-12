from math import ceil
from typing import Generator, Tuple
import requests


class Downloader(object):
    def __init__(self, url: str, download_range: str):
        """
        Range: bytes=0-100
        """
        self.download_url = url
        self.range = download_range
        self.chunk_size = 1024
        self.total_size, self.length, self.response = self.__create_connection()
        self._gen = self._generator()

    def __create_connection(self):
        response = requests.get(self.download_url, headers={
                                'Range': self.range}, stream=True)
        total_size = int(response.headers.get('Content-Length'))
        length = total_size // self.chunk_size
        return total_size, length, response
    
    def __len__(self):
        return self.length
    
    def _generator(self) -> Generator[Tuple[bytes, int], None, None]:
        completed = 0
        for chunk in self.response.iter_content(chunk_size=self.chunk_size):
            if chunk:
                completed += len(chunk)
                yield chunk, ceil((completed / self.total_size) * 100)
    
    def __iter__(self):
        return self
    
    def __next__(self):
        return next(self._gen)
    
    def close(self):
        self.response.close()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def __enter__(self):
        return self

    def __del__(self):
        self.close()
import asyncio
import os
from dataclasses import dataclass
from typing import Any, Callable, Coroutine, Dict, List, Optional, Tuple
from uuid import uuid4

import aiofiles
from aiohttp import ClientSession
from aiohttp.client import _RequestContextManager

from utils import deduceFileName, determine_ranges


@dataclass
class ChildDownloadTask:
    id: str
    url: str
    destination_directory: str
    filename: str
    parent_id: str
    part_size: int
    downloaded_size: int
    response: _RequestContextManager
    range: Optional[str] = None
    total_size: Optional[int] = None
    completed: bool = False


class DownloadManager:

    def __init__(
            self, 
            max_connections: int = 4, 
            allow_redirects: bool = True, 
            show_progress: bool = False, 
            on_progress: Optional[Callable[[str, List[Tuple[int, int]]], None]] = None, 
            on_completion: Optional[Callable[[str], None]] = None, 
            on_error: Optional[Callable[[str, Exception], None]] = None,
            on_filename: Optional[Callable[[str, str], None]] = None,
            on_total_size: Optional[Callable[[str, Optional[int]], None]] = None,
        ):
        if not isinstance(max_connections, int):
            raise TypeError("max_connections must be an integer")
        if not isinstance(show_progress, bool):
            raise TypeError("show_progress must be a boolean")
        self.__number_of_connections = min(max(max_connections, 1), 8)
        self.__allow_redirects = allow_redirects
        self.__show_progress = show_progress
        self.__download_queue: Dict[str, ChildDownloadTask] = {}
        self.__session = ClientSession()
        self.__on_progress = on_progress
        self.__on_error = on_error
        self.__on_completion = on_completion
        self.__on_filename = on_filename
        self.__on_total_size = on_total_size

    async def await_downloads(self):
        tasks: List[Coroutine[Any, Any, None]] = []
        done_parents: List[str] = []
        for item in self.__download_queue.keys():
            tasks.append(self.await_download(item))
            if item not in done_parents:
                if self.__on_filename:
                    self.__on_filename(self.__download_queue[item].parent_id, self.__download_queue[item].filename)
                if self.__on_total_size:
                    self.__on_total_size(self.__download_queue[item].parent_id, self.__download_queue[item].total_size)
                done_parents.append(item)
        return await asyncio.gather(*tasks)

    async def await_download(self, id: str):
        try:
            item = self.__download_queue.get(id, None)
            if not item:
                return
            if not isinstance(item, ChildDownloadTask):
                return
            filepath = os.path.join(item.destination_directory, item.filename)
            if not os.path.exists(filepath):
                async with aiofiles.open(filepath, mode='wb+') as file:
                    if item.total_size:
                        await file.write(b'\0' * item.total_size)

            async with aiofiles.open(filepath, mode='wb') as file:
                if item.range:
                    start_range = int(item.range[len('bytes='):].split('-')[0])
                    await file.seek(start_range)
                async with item.response as response:
                    async for chunk in response.content.iter_chunked(1024):
                        item = self.__download_queue.get(id, None)
                        if item:
                            item.downloaded_size += len(chunk)
                        self.__download_queue[id] = item
                        await file.write(chunk)
                        self.onProgress(id)
                self.onCompletion(id)
        except Exception as e:
            self.onError(id, e)

    def onError(self, id: str, error: Exception):
        item = self.__download_queue.pop(id, None)
        if not item:
            return
        if isinstance(item, ChildDownloadTask):
            id = item.parent_id
            if item.response and not item.response.close:
                item.response.close()
            other_children = [child for child in self.__download_queue.values(
            ) if isinstance(child, ChildDownloadTask) and child.parent_id == id]
            for child in other_children:
                _item = self.__download_queue.pop(child.id, None)
                if _item.response and not _item.response.close:
                    _item.response.close()
        if self.__on_error:
            self.__on_error(id, error)

    def onProgress(self, id: str):
        item = self.__download_queue.get(id, None)
        if not item:
            return
        all_childs = [child for child in self.__download_queue.values() if isinstance(
            child, ChildDownloadTask) and child.parent_id == item.parent_id]
        parallel_progress = [(child.downloaded_size, child.part_size)
                             for child in all_childs]
        if self.__on_progress:
            self.__on_progress(item.parent_id, parallel_progress)

    def onCompletion(self, id: str):
        item = self.__download_queue.get(id, None)
        if not item:
            return
        self.__download_queue[id].completed = True
        if item.response and not item.response.close:
            item.response.close()
        all_childs = [child for child in self.__download_queue.values() if isinstance(
            child, ChildDownloadTask) and child.parent_id == item.parent_id]
        if all([child.completed for child in all_childs]):
            if self.__on_completion:
                self.__on_completion(item.parent_id)
            # pop all childs
            for child in all_childs:
                self.__download_queue.pop(child.id, None)
        else:
            pass
            # print('Not all childs completed for', item.filename)

    async def add_download_task(self, url: str, destination_directory: str = './', filename: Optional[str] = None):
        task_id = uuid4().hex
        headers = {}
        real_url = url
        try:
            async with self.__session.head(url, allow_redirects=self.__allow_redirects) as response:
                headers = response.headers
                real_url = response.real_url.human_repr()
                response.close()
        except Exception as e:
            # print('Error', e)
            pass
        if not filename:
            filename = deduceFileName(real_url, headers)
        if not filename:
            raise Exception("Could not deduce filename")
        ranges, filesize = determine_ranges(
            real_url, headers, self.__number_of_connections)
        # else:
        #     ranges = []
        #     filesize = None
        child_tasks: List[ChildDownloadTask] = []
        if not ranges:
            child_tasks.append(ChildDownloadTask(
                id=uuid4().hex,
                url=url,
                destination_directory=destination_directory,
                filename=filename,
                parent_id=task_id,
                part_size=0,
                downloaded_size=0,
                response=self.__session.get(
                    url, allow_redirects=self.__allow_redirects),
                range=None,
                total_size=None,
                completed=False
            ))
        else:
            for range in ranges:
                child_tasks.append(ChildDownloadTask(
                    id=uuid4().hex,
                    url=url,
                    destination_directory=destination_directory,
                    filename=filename,
                    parent_id=task_id,
                    part_size=0,
                    downloaded_size=0,
                    response=self.__session.get(
                        url, allow_redirects=self.__allow_redirects, headers={'Range': range}),
                    range=range,
                    completed=False,
                    total_size=filesize
                ))
        for child in child_tasks:
            self.__download_queue[child.id] = child
        return task_id

    def __enter__(self):
        return self

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        await self.__session.close()

    async def __exit__(self, exc_type, exc_val, exc_tb):
        await self.close()

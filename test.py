import sys

sys.path.append('./src')

from src.pyg_manager import DownloadManager
from typing import List, Tuple, Dict, Optional
# from tqdm.asyncio import tqdm_asyncio, tqdm
from tqdm import tqdm
import asyncio
from dataclasses import dataclass

ITEMS_TO_DOWNLOAD = [
    "https://download.samplelib.com/mp4/sample-15s.mp4",
    "https://rb.gy/f7bno",
    # "https://file-examples.com/storage/fe8c2cbedf64dfa9aa00eb2/2017/04/file_example_MP4_1920_18MG.mp4",
    "https://speed.hetzner.de/100MB.bin",
    "http://212.183.159.230/100MB.zip",
    # "http://212.183.159.230/200MB.zip",
    # "http://212.183.159.230/512MB.zip"
]

@dataclass
class Item:
    progress: tqdm
    url: str
    id: str
    filename: Optional[str] = None
    total_size: Optional[int] = None

ITEMS_MAP: Dict[str, Item] = {}

def on_progress(id: str, progress: List[Tuple[int, int]]):
    global ITEMS_MAP
    item = ITEMS_MAP.get(id, None)
    if not item:
        print(f"Progress for {id}: {progress}")
        return
    total_download = sum([x[0] for x in progress])
    # total_size = sum([x[1] for x in progress])
    # item.progress.total = total_size
    item.progress.update(total_download - item.progress.n)
    item.progress.refresh()

def on_error(id: str, error: Exception):
    global ITEMS_MAP
    item = ITEMS_MAP.get(id, None)
    if not item:
        print(f"Error for {id}: {error}")
        return
    item.progress.close()
    item.progress.set_description(f"Error {error} for {item.url}")
    item.progress.refresh()

def on_completion(id: str):
    global ITEMS_MAP
    item = ITEMS_MAP.get(id, None)
    if not item:
        print(f"Completed for {id}")
        return
    item.progress.set_description(f"Completed for {item.url}")
    item.progress.update(item.progress.total - item.progress.n)
    item.progress.refresh()
    item.progress.close()

def on_filename(id: str, filename: str):
    global ITEMS_MAP
    item = ITEMS_MAP.get(id, None)
    if not item:
        print(f"Filename for {id}: {filename}")
        return
    item.progress.set_description(f"Downloading {filename}")
    item.filename = filename

def on_total_size(id: str, total_size: Optional[int]):
    global ITEMS_MAP
    item = ITEMS_MAP.get(id, None)
    if not item:
        print(f"Total size for {id}: {total_size}")
        return
    if total_size:
        # item.progress.total = total_size
        # item.progress.refresh()
        prog = item.progress.n
        item.progress.reset(total=total_size)
        item.progress.update(prog)
        item.progress.refresh()
        # print(total_size)
    item.total_size = total_size

async def runner():
    global ITEMS_MAP
    async with DownloadManager(max_connections=8, allow_redirects=True, show_progress=True, on_progress=on_progress, on_completion=on_completion, on_error=on_error, on_filename=on_filename, on_total_size=on_total_size) as manager:

        # Download to current working directory and returns the path to the file
        # destination_path is the path to the folder for download
        # filename is the name of the file to save to. Default is the filename from url.
        # path = manager.download("https://download.samplelib.com/mp4/sample-15s.mp4", destination_path='./', filename=None)

        for index, url in enumerate(ITEMS_TO_DOWNLOAD):
            progress_bar = tqdm(position=index, bar_format='{l_bar}{bar}{r_bar}', leave=True, unit_scale=True, unit_divisor=1024, unit='iB', desc=f"Downloading {url}", total=None)
            progress_bar.set_description(f"Downloading {url}")
            id = await manager.add_download_task(url, destination_directory='./testing-downs', filename=None)
            ITEMS_MAP[id] = Item(progress_bar, url, id)
        
        out = await manager.await_downloads()
        return out

if __name__ == "__main__":
    print(asyncio.run(runner()))
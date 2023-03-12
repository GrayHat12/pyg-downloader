import argparse
import os
import sys

from pyg_manager import DownloadManager


def cli():
    parser = argparse.ArgumentParser(
        prog='pyg-downloader',
        description='Downloader',
    )
    parser.add_argument('url', help='URL to download')
    parser.add_argument('-o', '--output', help='Output file path')
    parser.add_argument('-c', '--max-connections', type=int, default=4, help='Number of connections')
    parser.add_argument('-p', '--progress', action='store_true', help='Show progress')
    args = parser.parse_args(sys.argv[1:])

    manager = DownloadManager(max_connections=args.max_connections, show_progress=args.progress)

    file = os.path.split(args.output)
    if len(file) == 0 or (file[0] is None and file[1] is None):
        file = ['.', None]
    elif file[0] is None and file[1] is not None:
        file = ['.', file[1]]
    elif file[0] is not None and file[1] is None:
        file = [file[0], None]
    else:
        file = [file[0], file[1]]

    filepath = manager.download(args.url, destination_path=file[0], filename=file[1])

    print(f'Downloaded to {filepath}')
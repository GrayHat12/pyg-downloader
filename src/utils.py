import mimetypes
import os
import re
import math
import unicodedata
from typing import List, Optional

from aiohttp.multipart import CIMultiDictProxy


def slugify(value: str, allow_unicode: bool = False):
    """
    Taken from https://github.com/django/django/blob/master/django/utils/text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    if not isinstance(value, str):
        return None
    if not value:
        return None
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode(
            'ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\.\s-]', '', value.lower())
    return re.sub(r'[-\s]+', '-', value).strip('-_')


def getFileNameFromContentDisposition(content_disposition: Optional[str]):
    if not content_disposition:
        return None
    if not isinstance(content_disposition, str):
        return None
    if 'filename=' not in content_disposition:
        return None
    filename = ""
    filename_regex = r"""filename[^;=\n]*=((['"]).*?\2|[^;\n]*)"""
    matches = re.match(filename_regex, content_disposition)
    if not matches:
        return None
    if matches.group(1):
        filename = matches.group(1)
        return slugify(filename)

def getFileNameFromContentType(content_type: Optional[str], url: str):
    extension = mimetypes.guess_extension(content_type)
    clean_url = removeQueryStringsFromUrl(url)
    filename_without_extension = os.path.splitext(os.path.basename(clean_url))[0]
    print('filename_without_extension', filename_without_extension)
    return f'{slugify(filename_without_extension)}{"." if extension else ""}{extension or ""}'

def removeQueryStringsFromUrl(url: str) -> str:
    return re.split(r"""[?#]""", url)[0]

def deduceFileNameFromUrl(url: str):
    clean_url = removeQueryStringsFromUrl(url)
    # print('clean_url', clean_url)
    # print('os.path.basename(clean_url)', os.path.basename(clean_url))
    return slugify(os.path.basename(clean_url))


def deduceFileName(url: str, headers: CIMultiDictProxy[str]):
    # First option
    file_name_from_content_disposition = getFileNameFromContentDisposition(headers.get('content-disposition', headers.get('Content-Disposition', None)))
    if file_name_from_content_disposition:
        # print('file_name_from_content_disposition', file_name_from_content_disposition)
        return file_name_from_content_disposition

    # Second option
    file_name_from_url = url.split('/')[-1]
    _, ext = os.path.splitext(file_name_from_url)
    if ext:
        file_name_from_url = deduceFileNameFromUrl(url)
        if file_name_from_url:
            # print('file_name_from_url', file_name_from_url)
            return file_name_from_url
    
    # Third option
    file_name_from_content_type = getFileNameFromContentType(headers.get('content-type', headers.get('Content-Type', None)), url)
    if file_name_from_content_type:
        # print('file_name_from_content_type', file_name_from_content_type)
        return file_name_from_content_type
    
    # Fallbak option
    return slugify(url)

def determine_ranges(url: str, headers: CIMultiDictProxy[str], paralled_connections: int):
    ranges: List[str] = []
    filesize = None
    filesize_string = headers.get('content-length', headers.get('Content-Length', None))
    try:
        if filesize_string:
            filesize = int(filesize_string)
            start_range = 0
            part_size = math.ceil(filesize / paralled_connections)
            for i in range(1, paralled_connections + 1):
                end_range = start_range + part_size
                if i == paralled_connections:
                    end_range = ""
                ranges.append(f"bytes={start_range}-{end_range}")
    except:
        return ranges, filesize
    return ranges, filesize
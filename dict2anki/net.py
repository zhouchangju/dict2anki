import mimetypes
import os
import re
import socket
import urllib.parse
import zlib
from http.client import HTTPResponse
from typing import Union, Tuple, Optional, Dict
from urllib.request import Request, urlopen

from .utils import valid_path, get_tag, Log

__all__ = [
    'fake_headers', 'urlopen_with_retry', 'url_get_content', 'url_save', 'url_save_guess_file',
]

TAG = get_tag(__name__)


def fake_headers() -> Dict[str, str]:
    return {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Charset': 'utf-8,*;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'utf-8, *;q=0.5',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/76.0.3809.132 Safari/537.36',
    }


def urlopen_with_retry(url: Union[str, Request],
                       headers: Dict[str, str] = None,
                       retry: int = 5,
                       **kwargs) -> HTTPResponse:
    Log.d(TAG, f"urlopen: url={url}, headers={headers}, retry={retry}, kwargs={kwargs}")
    if isinstance(url, str):
        url = Request(url)
    if headers:
        url.headers = headers
    
    for i in range(1, retry + 1):
        try:
            return urlopen(url, **kwargs)
        except Exception as e:
            Log.w(TAG, f"urlopen attempt {i} error: {e}")
            if i == retry:
                raise e


def url_get_content(url: Union[str, Request, HTTPResponse],
                    headers: Dict[str, str] = None,
                    retry: int = 5,
                    **kwargs) -> Union[bytes, str]:
    Log.d(TAG, f"get content, url={url}, headers={headers}, retry={retry}, kwargs={kwargs}")
    
    if isinstance(url, HTTPResponse):
        response = url
        url_str = response.geturl()
    else:
        response = urlopen_with_retry(url, headers, retry, **kwargs)
        url_str = url if isinstance(url, str) else url.full_url

    data = None
    for i in range(1, retry + 1):
        try:
            data = response.read()
            break
        except Exception as e:
            Log.w(TAG, f"read response attempt {i} error: {e}")
            if i == retry:
                raise e
            response = urlopen_with_retry(url_str, headers, 1, **kwargs)

    content_encoding = response.headers.get('Content-Encoding')
    if content_encoding == 'gzip':
        data = zlib.decompress(data, zlib.MAX_WBITS | 16)
    elif content_encoding == 'deflate':
        try:
            data = zlib.decompress(data)
        except zlib.error:
            Log.w(TAG, 'cannot decompress, treat as deflate data')
            data = zlib.decompress(data, -zlib.MAX_WBITS)
    elif content_encoding:
        raise NotImplementedError(f"unknown encoding: {content_encoding}")

    charset = None
    content_type = response.headers.get('Content-Type', '')
    if content_type:
        match = re.search(r'charset=([\w-]+)', content_type)
        if match:
            charset = match.group(1)
            Log.d(TAG, f"charset={charset}")
    
    return data.decode(charset) if charset else data.decode('utf-8', 'ignore')


def url_save_guess_file(url: Union[str, Request],
                        headers: Dict[str, str] = None,
                        retry: int = 5,
                        **kwargs) -> Tuple[str, Optional[int]]:
    Log.d(TAG, f"guess file, url={url}, headers={headers}, retry={retry}, kwargs={kwargs}")
    name, size = None, None
    with urlopen_with_retry(url, headers, retry, **kwargs) as response:
        if response.headers.get('Content-Disposition'):
            match = re.search(r'filename="(.+)"', response.headers['Content-Disposition'])
            if match:
                name = match.group(1)
        
        if not name:
            path = urllib.parse.urlparse(response.geturl()).path
            name = urllib.parse.unquote(os.path.basename(path))
            if not name:
                name = 'file'
                ext = mimetypes.guess_extension(response.headers.get('Content-Type', '').split(';', 1)[0])
                if ext:
                    name += ext
        
        if response.headers.get('Content-Length'):
            size = int(response.headers['Content-Length'])
            
    Log.d(TAG, f"guess file, name={name}, size={size}")
    return name, size


def url_save(url: Union[str, Request],
             headers: Dict[str, str] = None,
             filename: str = None,
             force: bool = False,
             reporthook=None,
             **kwargs) -> Tuple[str, int]:
    Log.d(TAG, f"url save, url={url}, headers={headers}, filename={filename}, force={force}, reporthook={reporthook}, kwargs={kwargs}")
    
    if isinstance(url, str):
        url = Request(url)
    
    if headers:
        url.headers = headers
    else:
        headers = url.headers

    name, total_size = url_save_guess_file(url, **kwargs)
    total_size = total_size if total_size is not None else float('inf')
    
    if filename is None:
        filename = os.path.join(os.curdir, name)
    filename = valid_path(filename, force)

    mode = 'wb'
    part_file = filename + '.part' if total_size != float('inf') else filename
    part_size = 0
    
    if os.path.exists(part_file):
        part_size = os.path.getsize(part_file)
        if 0 < part_size < total_size:
            Log.i(TAG, f"'.part' file already exists: {part_file}, trying to append")
            mode = 'ab'
        else:
            part_size = 0

    if part_size < total_size:
        if part_size:
            headers['Range'] = f"bytes={part_size}-"
        
        response = urlopen_with_retry(url, **kwargs)
        remaining_size = float('inf')
        
        content_range = response.headers.get('Content-Range')
        content_length = response.headers.get('Content-Length')
        
        if content_range:
            match = re.search(r'(\d+)-(\d+)/(\d+)$', content_range)
            if match:
                remaining_size = int(match.group(3)) - int(match.group(1))
        elif content_length:
            remaining_size = int(content_length)
            
        if part_size + remaining_size != total_size:
            Log.i(TAG, "'.part' file inconsistent with server, retrieving")
            part_size = 0
            mode = 'wb'
            # Reset header for full download? The original didn't explicitly remove 'Range' here but re-opened file.
            # If we re-open file as 'wb', we should probably not send Range header or expect full content.
            # But the loop continues... and `urlopen_with_retry` was already called. 
            # Original code: checks inconsistency, sets part_size=0, mode='wb'.
            # Then enters `with open(...)`. Inside loop `response.read()`.
            # Wait, if `part_size + remaining_size != total_size`, we are already reading from a response that MIGHT be partial (if Range was sent).
            # If server ignored Range, remaining_size would be full size?
            # If we detect inconsistency, we probably should re-request without Range, but original code didn't re-request *immediately*.
            # It just truncates local file ('wb') and writes what it gets from current response?
            # If current response is partial but wrong range, writing it to 'wb' file is wrong.
            # However, I must preserve functionality. I'll stick to the structure.

        with open(part_file, mode) as f:
            bs = 512 * 1024
            while part_size < total_size:
                buffer = None
                try:
                    buffer = response.read(bs)
                except socket.timeout:
                    Log.w(TAG, 'timeout during downloading, retrying')
                
                if buffer:
                    f.write(buffer)
                    part_size += len(buffer)
                    if reporthook:
                        reporthook(part_size, total_size)
                else:
                    if part_size >= total_size or total_size == float('inf'):
                        break
                    # Retry logic
                    headers['Range'] = f"bytes={part_size}-"
                    response = urlopen_with_retry(url, **kwargs)
                    
    assert part_size == os.path.getsize(part_file)
    if part_file != filename:
        if os.access(filename, os.W_OK):
            os.remove(filename)
        os.rename(part_file, filename)
        
    Log.d(TAG, f"url save completed, file={filename}, size={part_size}")
    return filename, part_size

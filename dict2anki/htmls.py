import re
from typing import Optional, Iterator, Tuple, Callable

from .utils import get_tag, Log

__all__ = [
    'find_positions', 'findall', 'find', 'sub', 'removeall',
]

TAG = get_tag(__name__)


def find_positions(html_str: str, tag: str, attrib: str = '', hook: Optional[Callable[[int, int], None]] = None) -> Iterator[Tuple[int, int]]:
    open_tag = re.compile(rf'<{tag}(?:\s*?|\s[\s\S]*?)>')
    close_tag = re.compile(rf'</{tag}\s*?>')
    all_tag = re.compile(rf'</?{tag}\s*?>|<{tag}\s[\s\S]*?>')
    # must match with open_tag first
    start_tag = re.compile(rf'<{tag}[\s\S]*?{attrib}[\s\S]*?>')
    
    count = 0
    start = -1
    
    for m in all_tag.finditer(html_str):
        token = m.group(0)
        if open_tag.fullmatch(token):
            if start != -1:
                count += 1
            elif start_tag.match(token):
                count = 1
                start = m.start()
        elif start != -1 and close_tag.fullmatch(token):
            count -= 1
            if count == 0:
                Log.d(TAG, f"paired tags found, start={start}, end={m.end()}")
                if hook:
                    hook(start, m.end())
                yield start, m.end()
                start = -1


def findall(html_str: str, tag: str, attrib: str = '') -> Iterator[str]:
    for i, j in find_positions(html_str, tag, attrib):
        yield html_str[i:j]


def find(html_str: str, tag: str, attrib: str = '') -> Optional[str]:
    return next(findall(html_str, tag, attrib), None)


def sub(html_str: str, replace: Callable[[str], str], tag: str, attrib: str = '') -> str:
    positions = list(find_positions(html_str, tag, attrib))
    
    for i, j in reversed(positions):
        segment = html_str[i:j]
        Log.d(TAG, f"replacing element: {segment}")
        html_str = html_str[:i] + replace(segment) + html_str[j:]
    return html_str


def removeall(html_str: str, tag: str, attrib: str = '') -> str:
    return sub(html_str, lambda h: '', tag, attrib)

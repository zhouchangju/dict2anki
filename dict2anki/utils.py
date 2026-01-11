import os
import re
import sys
from typing import Callable, Optional

__all__ = [
    'Log',
    'get_tag', 'valid_path',
    'ProgressBar'
]


def get_tag(name: str) -> str:
    return name.rsplit('.', 1)[-1]


TAG = get_tag(__name__)


class Log:
    DEBUG = 1
    INFO = 2
    WARN = 3
    ERROR = 4

    level = INFO

    _TERM = os.getenv('TERM', '')
    _ANSI_TERMINAL = _TERM.startswith('xterm') or _TERM in ('eterm-color', 'linux', 'screen', 'vt100')

    _RESET = '0'
    _RED = '31'
    _GREEN = '32'
    _YELLOW = '33'

    @staticmethod
    def _colorize(msg: str, *colors: str) -> str:
        if Log._ANSI_TERMINAL:
            return f"\033[{';'.join(colors)}m{msg}\033[{Log._RESET}m"
        return msg

    @staticmethod
    def _print(msg: str, *colors: str):
        sys.stderr.write(Log._colorize(f"{msg}\n", *colors))

    @staticmethod
    def d(tag: str, msg: str):
        if Log.level <= Log.DEBUG:
            Log._print(f"D/{tag:<10}: {msg}")

    @staticmethod
    def i(tag: str, msg: str):
        if Log.level <= Log.INFO:
            Log._print(f"I/{tag:<10}: {msg}", Log._GREEN)

    @staticmethod
    def w(tag: str, msg: str):
        if Log.level <= Log.WARN:
            Log._print(f"W/{tag:<10}: {msg}", Log._YELLOW)

    @staticmethod
    def e(tag: str, msg: str):
        if Log.level <= Log.ERROR:
            Log._print(f"E/{tag:<10}: {msg}", Log._RED)


def valid_path(path: str, force: bool = True) -> str:
    Log.d(TAG, f"valid path, path={path}, force={force}")
    dir_name, base_name = os.path.split(path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    
    base_name = re.sub(r'[/:*?"<>|]', '_', base_name)
    path = os.path.join(dir_name, base_name)
    
    if force:
        return path

    while os.path.exists(path):
        name, ext = os.path.splitext(base_name)
        # Handle case where file starts with dot (e.g. .gitignore) which splitext handles as name='.gitignore', ext=''
        # Original logic swapped them if ext was empty, presumably for files like 'README' vs '.config'? 
        # Actually standard splitext on 'README' is ('README', ''). 
        # The original code's intention with `if not ext` swap seems specific to dot-prefixed files or no-extension files.
        # Let's preserve the original behavior's outcome but clean the regex.
        if not ext:
            name, ext = ext, name
            
        match = re.search(r'_\(([1-9]\d*)\)$', name)
        if not match:
            name += '_(1)'
        else:
            new_idx = int(match.group(1)) + 1
            name = name[:match.start()] + f'_({new_idx})'
            
        base_name = name + ext
        path = os.path.join(dir_name, base_name)

    Log.d(TAG, f"valid path, path={path}")
    return path


class ProgressBar:
    def __init__(self, total: int = 100, progress: int = 0, detail: Optional[Callable[[int], str]] = None, extra: str = None):
        self._total = total
        self._progress = progress
        self._detail = detail
        self._extra = extra
        self._show = False
        self._formation = '{:>5}% ├{:─<25}┤ {:>9} / {:<9}{:>23}'

    @property
    def total(self):
        return self._total

    @total.setter
    def total(self, value: int):
        self._total = value
        self.update()

    @property
    def progress(self):
        return self._progress

    @progress.setter
    def progress(self, value: int):
        self._progress = value
        self.update()

    @property
    def extra(self):
        return self._extra

    @extra.setter
    def extra(self, value: str):
        self._extra = value
        self.update()

    def update(self):
        self._show = True
        percentage = round(self._progress * 100 / self._total, 1) if self._total > 0 else 0
        percentage = min(percentage, 100)
        bar_count = int(percentage) // 4
        
        prog_str = self._detail(self._progress) if self._detail else str(self._progress)
        total_str = self._detail(self._total) if self._detail else str(self._total)
        extra_str = self._extra if self._extra is not None else ''
        
        line = self._formation.format(percentage, '█' * bar_count, prog_str, total_str, extra_str)
        sys.stdout.write('\r' + line)
        sys.stdout.flush()

    def increment(self, n: int = 1):
        self._progress += n
        self.update()

    def done(self):
        if self._show:
            print()
            self._show = False

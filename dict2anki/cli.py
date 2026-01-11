import argparse
import os
import socket
from typing import List, Tuple

from .extractors import EXTRACTORS, DEFAULT_EXTRACTOR
from .utils import get_tag, Log

TAG = get_tag(__name__)

DEFAULT_TIME_OUT = 20


def parse_args() -> Tuple[str, str, List[str]]:
    parser = argparse.ArgumentParser(
        prog='dict2anki',
        description='dict2anki is a tool converting words to Anki cards.'
    )
    parser.add_argument(
        '-i', '--input-file', metavar='FILE', type=argparse.FileType('r'), required=True,
        help='read words from FILE split by lines, ignoring lines starting with "#"'
    )
    parser.add_argument(
        '-o', '--output-path', metavar='PATH', help='set output path'
    )
    parser.add_argument(
        '-e', '--extractor', metavar='DICT', default=DEFAULT_EXTRACTOR,
        choices=EXTRACTORS.keys(),
        help=f"available extractors: {', '.join(EXTRACTORS.keys())}, default: {DEFAULT_EXTRACTOR}"
    )
    parser.add_argument(
        '-d', '--debug', action='store_true',
        help='show debug info'
    )
    
    args = parser.parse_args()

    if args.debug:
        Log.level = Log.DEBUG
    
    if args.extractor == DEFAULT_EXTRACTOR:
        Log.i(TAG, f"no extractor specified, using default: {DEFAULT_EXTRACTOR}")

    output_path = os.path.join(args.output_path or os.curdir, args.extractor)

    Log.d(TAG, f"loading words from {args.input_file.name}")
    words = []
    with args.input_file:
        for line in args.input_file:
            line = line.strip()
            if line and not line.startswith('#'):
                words.append(line)
                
    Log.d(TAG, f"{len(words)} words loaded")
    
    return args.extractor, output_path, words


def main():
    extractor_name, output_path, words = parse_args()

    socket.setdefaulttimeout(DEFAULT_TIME_OUT)

    extractor_class = EXTRACTORS[extractor_name]
    extractor = extractor_class(output_path)
    extractor.generate_front_template()
    extractor.generate_back_template()
    extractor.generate_styling()
    extractor.generate_cards(*words)

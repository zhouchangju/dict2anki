import asyncio
import csv
import os
from abc import ABCMeta, abstractmethod
from typing import Tuple, List

from dict2anki.utils import valid_path, Log, get_tag, ProgressBar

__all__ = [
    'WordNotFoundError', 'ExtractError', 'CardExtractor',
]

TAG = get_tag(__name__)

DEFAULT_OUT_PATH = os.path.join(os.curdir, TAG)
DEFAULT_MEDIA_FOLDER = 'collection.media'
DEFAULT_FRONT_TEMPLATE_FILE = 'front-template.txt'
DEFAULT_BACK_TEMPLATE_FILE = 'back-template.txt'
DEFAULT_STYLING_FILE = 'styling.txt'
DEFAULT_CARDS_FILE = 'cards.txt'

DEFAULT_FRONT_TEMPLATE = '''{{正面}}'''

DEFAULT_BACK_TEMPLATE = '''{{FrontSide}}
<hr id=answer>
{{背面}}'''

DEFAULT_STYLING = '''.card {
 font-family: arial;
 font-size: 20px;
 text-align: left;
 color: black;
 background-color: white;
}
'''

DEFAULT_CONCURRENCY = 8


class WordNotFoundError(Exception):
    pass


class ExtractError(Exception):
    pass


class CardExtractor(metaclass=ABCMeta):

    def __init__(self, out_path: str = DEFAULT_OUT_PATH, media_folder: str = DEFAULT_MEDIA_FOLDER,
                 front: str = DEFAULT_FRONT_TEMPLATE_FILE, back: str = DEFAULT_BACK_TEMPLATE_FILE,
                 styling: str = DEFAULT_STYLING_FILE, cards: str = DEFAULT_CARDS_FILE):
        self.out_path = out_path
        self.media_path = os.path.join(out_path, media_folder)
        self.front_template_file = os.path.join(out_path, front)
        self.back_template_file = os.path.join(out_path, back)
        self.styling_file = os.path.join(out_path, styling)
        self.cards_file = os.path.join(out_path, cards)
        self._front_template = DEFAULT_FRONT_TEMPLATE
        self._back_template = DEFAULT_BACK_TEMPLATE
        self._styling = DEFAULT_STYLING

    def _write_template(self, desc: str, path: str, content: str):
        Log.i(TAG, f"generating {desc}")
        file_path = valid_path(path)
        with open(file_path, 'w', encoding='utf8') as fp:
            fp.write(content)
        Log.i(TAG, f"generated {desc} to: {file_path}")

    def generate_front_template(self):
        self._write_template('front template', self.front_template_file, self._front_template)

    def generate_back_template(self):
        self._write_template('back template', self.back_template_file, self._back_template)

    def generate_styling(self):
        self._write_template('styling', self.styling_file, self._styling)

    def generate_cards(self, *words: str):
        Log.i(TAG, f"generating {len(words)} cards")
        file_path = valid_path(self.cards_file)

        visited = set()
        skipped = []
        bar = ProgressBar(len(words))
        
        async def process_word(sem: asyncio.Semaphore, word: str) -> List[str]:
            async with sem:
                try:
                    # Run blocking get_card in thread pool
                    loop = asyncio.get_running_loop()
                    actual, fields = await loop.run_in_executor(None, self.get_card, word)
                except Exception as e:
                    Log.e(TAG, f"can't get card: \"{word}\", {e}")
                    skipped.append(word)
                    Log.e(TAG, f"skipped: \"{word}\"")
                    return None
                
                # Update progress bar
                bar.extra = actual
                bar.increment()

                if actual not in visited:
                    visited.add(word)
                    visited.add(actual)
                    return fields
            return None

        async def run_tasks():
            sem = asyncio.Semaphore(DEFAULT_CONCURRENCY)
            tasks = [process_word(sem, w) for w in words]
            return await asyncio.gather(*tasks)

        bar.update()
        results = asyncio.run(run_tasks())
        cards = [res for res in results if res]
        bar.done()
        
        with open(file_path, 'a', encoding='utf8') as fp:
            writer = csv.writer(fp)
            writer.writerows(cards)
            
        Log.i(TAG, f"generated {len(cards)} cards to: {file_path}")
        if skipped:
            Log.e(TAG, f"skipped {len(skipped)} words:\n" + "\n".join(skipped))

    @abstractmethod
    def get_card(self, word: str) -> Tuple[str, List[str]]:
        pass

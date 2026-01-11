import os
import re
import urllib.parse
from typing import Tuple, List

from dict2anki import htmls
from dict2anki.net import url_get_content, urlopen_with_retry, fake_headers, url_save, url_save_guess_file
from dict2anki.utils import Log, valid_path, get_tag
from .extractor import CardExtractor, WordNotFoundError, ExtractError

__all__ = [
    'CambridgeExtractor',
]

TAG = get_tag(__name__)

DEFAULT_OUT_PATH = os.path.join(os.curdir, TAG)

DEFAULT_FRONT_TEMPLATE = '''<hr>
<div style="text-align:center">{{正面}}</div>'''

URL_ROOT = 'https://dictionary.cambridge.org/'

URL_QUERY = 'https://dictionary.cambridge.org/zhs/%E8%AF%8D%E5%85%B8/%E8%8B%B1%E8%AF%AD-%E6%B1%89%E8%AF%AD-%E7%AE%80%E4%BD%93/{}'

URL_STYLE = 'https://dictionary.cambridge.org/zhs/common.css'

URL_FONT = 'https://dictionary.cambridge.org/zhs/external/fonts/cdoicons.woff'

URL_AMP = 'https://cdn.ampproject.org/v0.js'

URL_AMP_AUDIO = 'https://cdn.ampproject.org/v0/amp-audio-0.1.js'

URL_AMP_ACCORDION = 'https://cdn.ampproject.org/v0/amp-accordion-0.1.js'

THRESHOLD_COLLAPSE = 4096

HTML_COLLAPSE = '<amp-accordion><section>{}</section></amp-accordion>'

HTML_COLLAPSE1 = '<amp-accordion><section>' \
                 '<header class="ca_h daccord_h"><i class="i i-plus ca_hi"></i>{}</header>{}' \
                 '</section></amp-accordion>'

parse_tag = re.compile(r'^(<[\s\S]*?>)([\s\S]*)(</[\s\S]*>)$')


class CambridgeExtractor(CardExtractor):

    def __init__(self, out_path: str = DEFAULT_OUT_PATH, **kwargs):
        super().__init__(out_path, **kwargs)
        self._front_template = DEFAULT_FRONT_TEMPLATE
        self._styling = None

    def generate_styling(self):
        if not self._styling:
            self._styling = self._retrieve_styling()
        super().generate_styling()

    def _retrieve_styling(self) -> str:
        Log.i(TAG, 'retrieving styling')
        style = url_get_content(URL_STYLE, fake_headers())
        
        font_name, _ = url_save_guess_file(URL_FONT, fake_headers())
        # add '_' to tell Anki that the file is used by template
        local_font_path = os.path.join(self.media_path, '_' + font_name)
        saved_font, _ = url_save(
            URL_FONT,
            headers=fake_headers(),
            filename=valid_path(local_font_path),
            force=True
        )
        Log.i(TAG, f"saved font file to: {saved_font}")
        
        font_basename = os.path.basename(saved_font)
        style = re.sub(rf'url\([\S]*?/{font_name}', f'url({font_basename}', style)
        style += '.large-ipa { font-size: 24px; color: #333; margin: 10px 0; display: block; }'
        
        scripts = []
        for js_url in [URL_AMP, URL_AMP_AUDIO, URL_AMP_ACCORDION]:
             content = url_get_content(js_url, fake_headers()).replace('\n', ' ')
             scripts.append(f'<script type="text/javascript">{content}</script>')
        
        style = f"<style>{style}</style>\n" + "\n".join(scripts) + "\n"
        
        Log.i(TAG, 'retrieved styling')
        return style

    def get_card(self, word: str) -> Tuple[str, List[str]]:
        Log.d(TAG, f"querying \"{word}\"")
        quoted_word = urllib.parse.quote(word.replace('/', ' '))
        response = urlopen_with_retry(
            URL_QUERY.format(quoted_word),
            fake_headers()
        )
        
        final_url_path = urllib.parse.urlsplit(response.geturl()).path
        actual = final_url_path.rsplit('/', 1)[-1]
        actual = actual.replace('-', ' ')
        
        if not actual:
            raise WordNotFoundError(f"can't find: \"{word}\"")
            
        # Normalize for redirect check
        normalized_word = ' '.join(word.replace('/', ' ').replace('-', ' ').replace("'", ' ').lower().split())
        if actual != normalized_word:
            Log.i(TAG, f"redirected \"{word}\" to: \"{actual}\"")
            
        content = url_get_content(response, fake_headers())
        fields = self._extract_fields(content)
        Log.d(TAG, f"parsed: \"{actual}\"")
        return actual, fields

    def _extract_fields(self, html_str: str) -> List[str]:
        try:
            back = htmls.find(html_str, 'div', 'class="di-body"')
            front = htmls.find(back, 'div', 'class="di-title"')

            ipa = htmls.find(back, 'span', 'class="ipa"')
            if ipa:
                front += f'<div class="large-ipa">/{ipa}/</div>'

            audio_matches = re.findall(r'src="(/zhs/media[^"]+)"', back)
            if audio_matches:
                selected_audio = next((a for a in audio_matches if 'us_pron' in a), audio_matches[0])
                audio_url = URL_ROOT + selected_audio.lstrip('/')
                front += f'<audio src="{audio_url}" autoplay controls></audio>'

            # remove titles
            back = htmls.removeall(back, 'div', 'class="di-title"')
            
            # support online audios
            back = re.sub(r'src="/zhs/media', f'src="{URL_ROOT}zhs/media', back)
            
            # remove unwanted elements
            to_remove = [
                ('div', 'class="xref'),
                ('div', 'class="cid"'),
                ('div', 'class="dwl hax"'),
                ('div', 'class="hfr lpb-2"'),
                ('div', 'class="daccord"'),
                ('script', ''),
                ('div', 'ad_contentslot'),
                ('div', 'class="bb hax"'),
            ]
            for tag, attr in to_remove:
                back = htmls.removeall(back, tag, attr)

            def remove_tag(h):
                return parse_tag.sub(r'\g<2>', h)

            # remove links/underlines but keep text
            back = htmls.sub(back, remove_tag, 'a', 'class="query"')
            back = htmls.sub(back, remove_tag, 'a', 'href=')
            back = htmls.sub(back, remove_tag, 'span', 'class="x-h dx-h"')

            # collapse long cards
            if len(back) > THRESHOLD_COLLAPSE:
                back = self._collapse(back)
            return [front, back]
        except Exception as e:
            raise ExtractError('can\'t extract fields', e)

    def _collapse(self, html_str: str) -> str:
        def collapse1(h):
            header = htmls.find(htmls.find(h, 'div', 'def-body ddef_b'), 'span', 'trans dtrans dtrans-se')
            return HTML_COLLAPSE1.format(header, h)

        html_str = htmls.sub(html_str, collapse1, 'div', 'def-block ddef_block')
        return html_str

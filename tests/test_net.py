import hashlib
import urllib.parse
from unittest import TestCase

from dict2anki.net import *
from dict2anki.utils import Log, get_tag

TAG = get_tag(__name__)

Log.level = Log.DEBUG

URL_CAMBRIDGE_QUERY = 'https://dictionary.cambridge.org/zhs/%E6%90%9C%E7%B4%A2/direct/?datasetsearch=english-chinese' \
                      '-simplified&q={}'

URL_DEBIAN_CD_PATH = 'https://cdimage.debian.org/debian-cd/current/amd64/iso-cd/{}'


class TestNet(TestCase):
    def test_urlopen_with_retry(self):
        url = URL_CAMBRIDGE_QUERY.format(urllib.parse.quote('cater to'))
        with urlopen_with_retry(url, fake_headers()) as response:
            Log.d(TAG, f"headers={response.headers}")
            Log.d(TAG, f"status={response.status}, url={response.url}")

    def test_url_get_content(self):
        Log.d(TAG, url_get_content(URL_DEBIAN_CD_PATH.format('SHA256SUMS'), fake_headers()))

    def test_url_save_guess_file(self):
        sha256, file = url_get_content(URL_DEBIAN_CD_PATH.format('SHA256SUMS'), fake_headers()).splitlines()[0].split()
        Log.d(TAG, f"sha256={sha256}, file={file}")
        self.assertEqual(file, url_save_guess_file(URL_DEBIAN_CD_PATH.format(file))[0])

    def test_url_save(self):
        sha256, file = url_get_content(
            URL_DEBIAN_CD_PATH.format('SHA256SUMS'),
            fake_headers()
        ).splitlines()[0].split()
        Log.d(TAG, f"sha256={sha256}, file={file}")
        file_actual, size = url_save(
            URL_DEBIAN_CD_PATH.format(file),
            reporthook=lambda a, b: Log.d(TAG, f"{round(a * 100 / b, 1):>5}% downloaded")
        )
        Log.d(TAG, f"file size: {round(size / 1024 / 1024, 1)} MiB")
        sha256_actual = hashlib.sha256()
        with open(file_actual, 'rb') as f:
            buffer = f.read(512 * 1024)
            while buffer:
                sha256_actual.update(buffer)
                buffer = f.read(512 * 1024)
        self.assertEqual(sha256, sha256_actual.hexdigest())

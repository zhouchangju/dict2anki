# dict2anki

## Project Overview

`dict2anki` is a Python-based CLI tool designed to batch generate Anki cards from a list of words. It fetches definitions and media from online dictionaries (currently supporting the Cambridge Dictionary) and produces importable Anki files (`cards.txt`).

**Key Features:**
*   **Dictionary Support:** Cambridge Dictionary (English-Chinese Simplified).
*   **Zero Dependencies:** Relies entirely on the Python standard library (no `requests` or `BeautifulSoup`).
*   **Custom Parsing:** Implements a custom regex-based HTML parser (`htmls.py`) and HTTP client (`net.py`).
*   **Anki Integration:** Generates front/back templates and styling for Anki note types.

## Architecture

*   **`dict2anki/cli.py`**: Handles command-line argument parsing and execution flow.
*   **`dict2anki/net.py`**: A custom HTTP client wrapper around `urllib` handling retries and encoding.
*   **`dict2anki/htmls.py`**: A lightweight, regex-based HTML parser for finding and manipulating tags.
*   **`dict2anki/extractors/`**: Contains logic for specific dictionary sources.
    *   `extractor.py`: Defines the `CardExtractor` base class.
    *   `cambridge.py`: Implementation for Cambridge Dictionary.

## Building and Running

### Prerequisites
*   Python >= 3.7

### Installation

From source:
```bash
git clone https://github.com/qianbinbin/dict2anki.git
cd dict2anki
```

### Usage

1.  **Prepare a word list file** (e.g., `words.txt`) with one word per line. Lines starting with `#` are ignored.
2.  **Run the tool:**

    Using the module directly:
    ```bash
    python3 -m dict2anki -i words.txt
    ```

    Or install and run:
    ```bash
    pip install .
    dict2anki -i words.txt
    ```

    This will generate `cards.txt` and other template files in the current directory (or a subdirectory named after the extractor).

### Running Tests

The project uses the `unittest` framework. Note that some tests (like `test_extractor_cambridge.py`) perform actual network requests.

```bash
python3 -m unittest discover tests
```

## Development Conventions

*   **Standard Library Only:** The project avoids external dependencies to ensure portability and ease of installation. New features should ideally stick to the standard library.
*   **HTML Parsing:** Do not introduce `BeautifulSoup` or `lxml` unless necessary. Use the existing `htmls.py` module for parsing tasks.
*   **Logging:** Use the custom `Log` class from `dict2anki.utils` instead of Python's built-in `logging` module.
*   **Code Style:** Follow PEP 8 guidelines.

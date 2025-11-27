# Markdown Table Extractor

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/badge/uv-package%20manager-blueviolet)](https://docs.astral.sh/uv/)
[![marimo](https://img.shields.io/badge/marimo-literate%20programming-green)](https://marimo.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Robust structured data extraction from markdown text, built with literate programming using marimo notebooks.**

## ✨ Features

- ✅ **Proper separator detection** - Handles `:--:`, `---:`, `:---` alignment syntax
- ✅ **Caption detection** - Finds "Table 3. Results" patterns above tables
- ✅ **Continuation merging** - Automatically merges "Table 3 (Continued)" tables
- ✅ **HTML cleanup** - Removes `<br>` and other artifacts from headers
- ✅ **Sub-header handling** - Merges multi-level headers properly
- ✅ **LLM extraction** - AI-powered fallback for complex edge cases
- ✅ **Type-safe** - Full type hints with `py.typed` marker
- ✅ **Literate programming** - Each module is a marimo notebook

## 📚 Literate Programming with Marimo

Unlike traditional packages, **every module is a marimo notebook**:

```
src/markdown_table_extractor/core/
├── models.py      # 📓 Data classes notebook
├── parser.py      # 📓 Markdown parsing notebook  
├── cleaner.py     # 📓 Data cleaning notebook
├── merger.py      # 📓 Table merging notebook
└── extractor.py   # 📓 Main extraction notebook
```

Each file is simultaneously:
- **A Python module** - Import normally: `from markdown_table_extractor import extract_tables`
- **A notebook** - Edit interactively: `marimo edit src/.../parser.py`
- **Documentation** - Read the code alongside explanations
- **A script** - Run standalone: `python src/.../parser.py`

This follows the [literate programming](https://en.wikipedia.org/wiki/Literate_programming) paradigm pioneered by Donald Knuth, similar to [nbdev](https://nbdev.fast.ai/) but with marimo's pure-Python notebooks.

## Installation

```bash
# Using uv (recommended)
uv add markdown-table-extractor

# With LLM support (OpenAI/Anthropic)
uv add "markdown-table-extractor[llm]"

# Development with marimo
uv add "markdown-table-extractor[notebook]"
```

## Quick Start

### Simple Usage

```python
from markdown_table_extractor import extract_tables

markdown = """
| Name | Age |
| --- | --- |
| Alice | 30 |
| Bob | 25 |
"""

tables = extract_tables(markdown)
print(tables[0])
#    Name  Age
# 0  Alice   30
# 1    Bob   25
```

### Full API with Metadata

```python
from markdown_table_extractor import extract_markdown_tables, TableMergeStrategy

result = extract_markdown_tables(
    markdown_text,
    merge_strategy=TableMergeStrategy.IDENTICAL_HEADERS,
    detect_captions=True,
    skip_sub_headers=True
)

for table in result:
    print(f"Caption: {table.caption}")
    print(f"Shape: {table.dataframe.shape}")
    print(table.dataframe)
```

### Exploring the Notebooks

```bash
# Open any module as an interactive notebook
marimo edit src/markdown_table_extractor/core/parser.py

# Run the interactive demo
marimo edit src/markdown_table_extractor/core/extractor.py
```

## API Reference

### Core Functions

| Function | Description |
|----------|-------------|
| `extract_tables(text)` | Simple API returning `list[DataFrame]` |
| `extract_markdown_tables(text, ...)` | Full API returning `ExtractionResult` |

### Models

| Class | Description |
|-------|-------------|
| `ExtractedTable` | Single table with metadata (caption, line numbers) |
| `ExtractionResult` | Collection of tables with errors and merge count |
| `TableMergeStrategy` | Enum: `NONE`, `IDENTICAL_HEADERS`, `COMPATIBLE_COLUMNS` |

### Utilities (from parser.py notebook)

| Function | Description |
|----------|-------------|
| `is_separator_row(line)` | Check if line is a table separator |
| `is_table_row(line)` | Check if line is any table row |
| `parse_table_row(line)` | Extract cell values from a row |
| `detect_caption(lines, start)` | Find table caption |

### Utilities (from cleaner.py notebook)

| Function | Description |
|----------|-------------|
| `clean_column_name(name)` | Remove HTML artifacts from header |
| `headers_match(h1, h2)` | Check if headers are compatible |
| `normalize_headers(headers)` | Canonical form for comparison |

## Development

```bash
# Clone and setup
git clone https://github.com/username/markdown-table-extractor
cd markdown-table-extractor
uv sync --all-extras

# Run tests
uv run pytest

# Run linter
uv run ruff check src tests

# Type checking
uv run mypy src

# Edit any module interactively
uv run marimo edit src/markdown_table_extractor/core/parser.py
```

## Project Structure

```
markdown-table-extractor/
├── pyproject.toml              # Package configuration
├── README.md
├── src/
│   └── markdown_table_extractor/
│       ├── __init__.py         # Public API
│       ├── py.typed            # Type hints marker
│       └── core/
│           ├── __init__.py     # Re-exports from notebooks
│           ├── models.py       # 📓 Data classes notebook
│           ├── parser.py       # 📓 Parsing utilities notebook
│           ├── cleaner.py      # 📓 Cleaning utilities notebook
│           ├── merger.py       # 📓 Merging logic notebook
│           └── extractor.py    # 📓 Main extraction notebook
└── tests/
    └── test_extractor.py
```

## Why Marimo Notebooks?

| Traditional | Marimo Literate |
|-------------|-----------------|
| Code in .py, docs separate | Code + docs in same file |
| Read code, guess intent | Read explanation alongside code |
| Tests in separate files | Interactive tests in notebook |
| Static documentation | Interactive documentation |
| Jupyter: JSON format | Pure Python, Git-friendly |

## Why Not nbdev?

| nbdev | marimo |
|-------|--------|
| Jupyter notebooks (JSON) | Pure Python files |
| Requires export step | Direct import |
| `#| export` directives | `@app.function` decorator |
| Complex build process | Just Python |

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions welcome! Edit the notebooks, add tests, and submit PRs.

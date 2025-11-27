# CLAUDE.md

> Context file for AI assistants working on this project.

## Project Overview

**markdown-table-extractor** is a Python library for extracting structured data from markdown tables, designed for processing academic manuscripts where tables often:
- Span multiple pages with "(Continued)" markers
- Have complex alignment syntax (`:--:`, `---:`, `:---`)
- Contain HTML artifacts like `<br>` tags
- Include multi-level sub-headers

## Architecture

```
src/markdown_table_extractor/
├── __init__.py          # Public API exports
├── py.typed             # PEP 561 type hints marker
├── cli.py               # Command-line interface (mte command)
├── core/                # Core extraction logic
│   ├── __init__.py      # Re-exports from submodules
│   ├── models.py        # Data classes: ExtractedTable, ExtractionResult, TableMergeStrategy
│   ├── parser.py        # Markdown parsing: is_separator_row, parse_table_row, detect_caption
│   ├── cleaner.py       # Data cleaning: clean_column_name, headers_match, normalize_headers
│   ├── merger.py        # Table merging: merge_tables, should_merge_tables
│   └── extractor.py     # Main orchestration: extract_tables, extract_markdown_tables
└── llm/                 # Optional LLM-powered extraction
    ├── __init__.py
    └── extractor.py     # Uses Simon Willison's `llm` library
```

## Key Design Decisions

### Regular Python Modules (Not Marimo Notebooks)

We initially attempted to use marimo notebooks as modules (literate programming style), but `@app.function` decorators only work when marimo generates the file. **All core modules are now regular Python files.**

If you want interactive documentation, create a **separate** marimo notebook in a `notebooks/` directory that imports from the package.

### Two APIs

1. **Simple API**: `extract_tables(text)` → `list[pd.DataFrame]`
2. **Full API**: `extract_markdown_tables(text, ...)` → `ExtractionResult`

### LLM Integration

Uses Simon Willison's [`llm`](https://llm.datasette.io/) library (not raw OpenAI/Anthropic SDKs) because it provides:
- Unified API across providers
- Built-in SQLite logging (`llm logs`)
- Structured output via Pydantic schemas

## Common Tasks

### Run Tests
```bash
uv run pytest
```

### Run CLI
```bash
uv run mte extract input.md
uv run mte extract input.md -o output.csv
uv run mte extract input.md --llm  # requires [llm] extra
```

### Install for Development
```bash
uv pip install -e ".[dev]"
# or
uv sync --group dev
```

### Type Checking
```bash
uv run mypy src
```

### Linting
```bash
uv run ruff check src tests
uv run ruff format src tests
```

## Code Conventions

- **Type hints**: All functions should have full type annotations
- **Docstrings**: Google style
- **Line length**: 88 characters (ruff default)
- **Imports**: Use `from __future__ import annotations` at top of each module

## Key Functions to Know

### `is_separator_row(line: str) -> bool`
Detects separator rows like `| --- |` or `| :--: |`. Critical for not including separators in data.

### `detect_caption(lines, table_start_line) -> tuple[str | None, bool]`
Looks above a table for captions like "Table 3. Results". Returns (caption, is_continuation).

### `merge_tables(tables, strategy) -> list[ExtractedTable]`
Combines tables marked as continuations into single tables.

### `extract_markdown_tables(text, merge_strategy, detect_captions, skip_sub_headers)`
Main entry point. Orchestrates parser → cleaner → merger pipeline.

## Testing Patterns

Tests are in `tests/test_extractor.py`. Key test classes:
- `TestSeparatorDetection` - parametrized tests for separator formats
- `TestTableMerging` - continuation table merging
- `TestCaptionDetection` - caption pattern matching
- `TestHTMLCleaning` - `<br>` tag removal

## Dependencies

**Required:**
- `pandas>=2.0.0`
- `tabulate>=0.9.0` (for DataFrame.to_markdown())

**Optional [llm]:**
- `llm>=0.19`
- `pydantic>=2.0.0`

**Dev:**
- `pytest`, `ruff`, `mypy`, `marimo`

## Gotchas

1. **`from __future__ import annotations`** must be the FIRST statement after the docstring (no blank lines before it)

2. **Separator detection regex**: `^:?-{1,}:?$` per cell - handles all alignment variants

3. **Sub-header rows**: Rows right after separator with mostly empty cells get merged into column names

4. **CLI requires `uv run`**: Use `uv run mte` not just `mte` unless venv is activated

## File Locations

- **pyproject.toml**: Package config, dependencies, tool settings
- **tests/**: Test suite
- **src/**: All source code (src layout for proper packaging)

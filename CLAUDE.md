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
markdown-table-extractor/
├── CLAUDE.md            # This file - AI assistant context
├── pyproject.toml       # Package config and dependencies
├── README.md            # User documentation
├── tests/
│   └── test_extractor.py
└── src/markdown_table_extractor/
    ├── __init__.py          # Public API exports
    ├── py.typed             # PEP 561 type hints marker
    ├── cli.py               # Regular Python (CLI doesn't benefit from notebook)
    ├── core/                # 📓 All marimo notebooks
    │   ├── __init__.py      # Re-exports from submodules
    │   ├── models.py        # 📓 Data classes: ExtractedTable, ExtractionResult
    │   ├── parser.py        # 📓 Markdown parsing: is_separator_row, parse_table_row
    │   ├── cleaner.py       # 📓 Data cleaning: clean_column_name, headers_match
    │   ├── merger.py        # 📓 Table merging: merge_tables, should_merge_tables
    │   └── extractor.py     # 📓 Main orchestration: extract_tables
    └── llm/                 # 📓 Optional LLM-powered extraction
        ├── __init__.py
        └── extractor.py     # 📓 Uses Simon Willison's `llm` library
```

📓 = marimo notebook (importable module + interactive documentation)

## Key Design Decisions

### Marimo Notebooks as Modules (Literate Programming)

All core modules are **marimo notebooks** that are also importable Python modules. This provides:
- Interactive documentation alongside code
- Live demos and testing within the module
- Pure Python files (git-friendly, not JSON like Jupyter)

**The pattern:**
```python
"""Module docstring."""
from __future__ import annotations

import marimo

# MODULE-LEVEL: imports and functions (importable)
import pandas as pd
import re

def my_function(x: str) -> bool:
    """This function is importable."""
    return bool(x)

# NOTEBOOK: app and cells (for interactive demos)
app = marimo.App(width="medium")

@app.cell
def _():
    import marimo as mo
    return (mo,)

@app.cell
def _(mo):
    mo.md("# Module Demo")
    return

@app.cell
def _():
    # Interactive demo using module functions
    result = my_function("test")
    result
    return

if __name__ == "__main__":
    app.run()
```

**Critical rules:**
1. Functions go at **module level** (before `app = marimo.App()`) — NOT as `@app.function`
2. `@app.function` only works in files created by `marimo edit` — avoid it for importable code
3. `from __future__ import annotations` must be FIRST after docstring
4. Cell returns use tuple syntax: `return (var1, var2)` or `return (var,)` for single

**Three ways to use each module:**
```bash
# 1. Import in Python
from markdown_table_extractor.core.parser import is_separator_row

# 2. Interactive notebook
uv run marimo edit src/markdown_table_extractor/core/parser.py

# 3. Run as script
uv run python src/markdown_table_extractor/core/parser.py
```

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

### Edit Module Notebooks Interactively
```bash
# Edit any module as an interactive notebook
uv run marimo edit src/markdown_table_extractor/core/parser.py
uv run marimo edit src/markdown_table_extractor/core/extractor.py

# Run in app mode (read-only)
uv run marimo run src/markdown_table_extractor/core/parser.py
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

5. **Module-level functions, NOT `@app.function`**: For importable code, define functions at module level BEFORE `app = marimo.App()`. The `@app.function` decorator only works in files created through `marimo edit`.

6. **Marimo cell returns use tuple syntax**: `return (var1, var2)` or `return (var,)` for single variables. Without parentheses/comma, single values won't be available to other cells.

7. **Imports in cells vs module level**: 
   - Module-level imports: Available to importers AND notebook cells
   - Cell imports (like `import marimo as mo`): Only available within notebook, not when imported

## File Locations

- **pyproject.toml**: Package config, dependencies, tool settings
- **tests/**: Test suite
- **src/**: All source code (src layout for proper packaging)

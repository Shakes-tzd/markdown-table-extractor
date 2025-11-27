"""Markdown table parsing utilities.

This module contains functions for detecting and parsing markdown table structures.
All functions handle the various alignment syntaxes used in markdown tables.
"""
from __future__ import annotations

import marimo
import re
from typing import Optional


# ============================================================================
# MODULE-LEVEL CODE (importable)
# ============================================================================

# Pattern to detect separator cells (handles all alignment formats)
SEPARATOR_CELL_PATTERN = re.compile(r'^:?-{1,}:?$')


def is_separator_row(line: str) -> bool:
    """Check if a line is a markdown table separator row.

    Handles various alignment formats:
    - |---|---|           (basic)
    - | :--: | :--: |     (centered)
    - |:---|---:|         (left/right aligned)
    - | --- | --- | --- | (with spaces)

    Args:
        line: A single line of text to check

    Returns:
        True if the line is a table separator row

    Examples:
        >>> is_separator_row("| --- | --- |")
        True
        >>> is_separator_row("| :--: | :--: |")
        True
        >>> is_separator_row("| Data | More |")
        False
    """
    stripped = line.strip()
    if not stripped:
        return False

    # Must contain at least one pipe and dash
    if '|' not in stripped or '-' not in stripped:
        return False

    # Split by pipe and check each cell
    cells = stripped.split('|')

    # Filter out empty strings from leading/trailing pipes
    cells = [c.strip() for c in cells if c.strip()]

    if not cells:
        return False

    # Each cell should match: optional colons around dashes
    return all(SEPARATOR_CELL_PATTERN.match(cell) for cell in cells)


def is_table_row(line: str) -> bool:
    """Check if a line is a table data row.

    A table row starts and ends with a pipe character.

    Args:
        line: A single line of text to check

    Returns:
        True if the line is a table row

    Examples:
        >>> is_table_row("| Cell 1 | Cell 2 |")
        True
        >>> is_table_row("Not a table row")
        False
    """
    stripped = line.strip()
    return stripped.startswith('|') and stripped.endswith('|')


def parse_table_row(line: str) -> list[str]:
    """Parse a table row into cell values.

    Args:
        line: A table row line (must start and end with |)

    Returns:
        List of cell values with whitespace stripped

    Examples:
        >>> parse_table_row("| A | B | C |")
        ['A', 'B', 'C']
    """
    stripped = line.strip()

    # Remove leading and trailing pipes
    if stripped.startswith('|'):
        stripped = stripped[1:]
    if stripped.endswith('|'):
        stripped = stripped[:-1]

    # Split by | and strip whitespace
    cells = [cell.strip() for cell in stripped.split('|')]
    return cells


def is_sub_header_row(line: str) -> bool:
    """Detect if a row is a sub-header row (common in multi-level table headers).

    Sub-header rows typically:
    - Have mostly empty cells
    - Have short text labels in some cells
    - Appear right after the separator row

    Args:
        line: The table row line to check

    Returns:
        True if this appears to be a sub-header row

    Examples:
        >>> is_sub_header_row("| | | Early | Late | Both |")
        True
    """
    if not is_table_row(line):
        return False

    cells = parse_table_row(line)

    if not cells:
        return False

    # Count empty vs non-empty cells
    non_empty = [c for c in cells if c.strip()]
    empty_ratio = 1 - (len(non_empty) / len(cells)) if cells else 0

    # If most cells are empty, check if non-empty ones look like sub-headers
    if empty_ratio > 0.5:
        for cell in non_empty:
            # Sub-headers are typically short labels without numbers/dates
            if len(cell) < 20 and not re.search(r'\d{4}|\d+\.\d+', cell):
                continue
            else:
                return False
        return True

    return False


def detect_caption(
    lines: list[str],
    table_start_line: int,
    max_lines_before: int = 5
) -> tuple[Optional[str], bool, Optional[str], bool]:
    """Detect table caption by looking at lines before the table.

    Searches for patterns like:
    - "Table 1. Title"
    - "Table 1 (Continued)"
    - "**Table 1. Title**"

    Args:
        lines: All lines in the document
        table_start_line: Line index where the table starts
        max_lines_before: Maximum lines to search before table

    Returns:
        Tuple of (caption_text, is_continuation, table_number, is_bare_caption)
        - caption_text: Full caption text or None
        - is_continuation: True if caption contains "continued" marker
        - table_number: Extracted table number (e.g., "3", "3a") or None
        - is_bare_caption: True if caption is just "Table N" without description
    """
    # Caption patterns for manuscripts
    caption_patterns = [
        re.compile(r'^(?:Table|TABLE)\s*(\d+[a-z]?)[.:]?\s*(.*)$', re.IGNORECASE),
        re.compile(r'^(?:Table|TABLE)\s*(\d+[a-z]?)\s*\(([^)]+)\)\s*(.*)$', re.IGNORECASE),
        re.compile(r'^\*\*(?:Table|TABLE)\s*(\d+[a-z]?)[.:]?\s*(.*)\*\*$', re.IGNORECASE),
    ]

    continuation_pattern = re.compile(
        r'\(?\s*(?:continued|cont\.?|cont\'d)\s*\)?',
        re.IGNORECASE
    )

    search_start = max(0, table_start_line - max_lines_before)

    for i in range(table_start_line - 1, search_start - 1, -1):
        if i < 0:
            break
        line = lines[i].strip()

        # Skip empty lines
        if not line:
            continue

        # Skip horizontal rules
        if line.startswith('---') and '|' not in line:
            continue

        # Check caption patterns
        for pattern in caption_patterns:
            match = pattern.match(line)
            if match:
                is_continuation = bool(continuation_pattern.search(line))
                table_number = match.group(1) if match.lastindex >= 1 else None

                # Check if bare caption (just "Table N" with no description)
                # Get the description part (everything after the number)
                if match.lastindex >= 2:
                    description = match.group(2).strip()
                    # Remove continuation markers to check for bare caption
                    desc_clean = continuation_pattern.sub('', description).strip()
                    is_bare_caption = not desc_clean or desc_clean in ['.', ':']
                else:
                    is_bare_caption = True

                return line, is_continuation, table_number, is_bare_caption

        # If we hit a non-caption line, stop looking
        break

    return None, False, None, False


# ============================================================================
# MARIMO NOTEBOOK (interactive documentation)
# ============================================================================

app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    # Import module-level functions for use in cells
    from markdown_table_extractor.core.parser import (
        is_separator_row,
        is_table_row,
        parse_table_row,
        is_sub_header_row,
        detect_caption,
    )
    return (mo, pd, is_separator_row, is_table_row, parse_table_row, is_sub_header_row, detect_caption)


@app.cell
def _(mo):
    mo.md("""
    # Markdown Table Parser

    Functions for detecting and parsing markdown table structures.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ## `is_table_row(line: str) -> bool`

    Check if a line is a table data row. A table row starts and ends with `|`.
    """)
    return


@app.cell
def _(mo, is_table_row):
    # Example 1: Valid table row
    _ex1 = "| Cell 1 | Cell 2 |"
    _result1 = is_table_row(_ex1)

    # Example 2: Not a table row
    _ex2 = "Just plain text"
    _result2 = is_table_row(_ex2)

    mo.vstack([
        mo.md(f"**Example 1:** `{_ex1}` → `{_result1}`"),
        mo.md(f"**Example 2:** `{_ex2}` → `{_result2}`"),
        mo.callout(
            f"is_table_row() correctly identifies table rows by checking for | at start and end",
            kind="success" if _result1 and not _result2 else "warn"
        )
    ])
    return


@app.cell
def _(mo):
    mo.md("""
    ## `is_separator_row(line: str) -> bool`

    Detects separator rows like `| --- |` with various alignment markers.
    """)
    return


@app.cell
def _(mo, is_separator_row):
    # Examples with different alignment patterns
    _sep_examples = [
        ("| --- | --- |", True, "Basic"),
        ("| :--- | ---: |", True, "Left/Right aligned"),
        ("| :---: | :---: |", True, "Center aligned"),
        ("| Data | More |", False, "Data row"),
    ]

    _results = []
    for line, expected, desc in _sep_examples:
        result = is_separator_row(line)
        _results.append(f"{'✅' if result == expected else '❌'} `{line}` → `{result}` ({desc})")

    mo.md("\n\n".join(_results))
    return


@app.cell
def _(mo):
    mo.md("""
    ## `parse_table_row(line: str) -> list[str]`

    Extract cell values from a table row.
    """)
    return


@app.cell
def _(mo, parse_table_row, pd):
    # Example: Parse a table row
    _row = "| Name | Age | City |"
    _cells = parse_table_row(_row)

    # Show as DataFrame
    _cells_df = pd.DataFrame([_cells], columns=_cells)

    mo.vstack([
        mo.md(f"**Input:** `{_row}`"),
        mo.md(f"**Parsed cells:** `{_cells}`"),
        mo.ui.table(_cells_df, selection=None),
    ])
    return


@app.cell
def _(mo):
    mo.md("""
    ## `detect_caption(lines, table_start_line) -> tuple`

    Find table captions like "Table 3. Results" or "Table 1 (Continued)".
    """)
    return


@app.cell
def _(mo, detect_caption):
    # Example document with caption
    _doc = [
        "# Research Results",
        "",
        "Table 3. Patient Demographics",
        "",
        "| Name | Age |",
        "| --- | --- |",
    ]

    _caption, _is_cont, _table_num, _is_bare = detect_caption(_doc, 4)

    mo.vstack([
        mo.md("**Document:**"),
        mo.md(f"```markdown\n{chr(10).join(_doc)}\n```"),
        mo.md("**Detected:**"),
        mo.md(f"- Caption: `{_caption}`"),
        mo.md(f"- Table Number: `{_table_num}`"),
        mo.md(f"- Is Continuation: `{_is_cont}`"),
        mo.md(f"- Is Bare: `{_is_bare}`"),
    ])
    return


@app.cell
def _(mo):
    mo.md("""
    ---

    ## 🔍 Comprehensive Demos

    Below are comprehensive tests showing all functions working together.
    """)
    return


@app.cell
def _(mo, is_separator_row, pd):
    # Test separator detection with visual output
    test_cases = [
        ("| --- | --- |", "Basic separator", True),
        ("| :--- | ---: |", "Left and right aligned", True),
        ("| :---: | :---: |", "Center aligned", True),
        ("| Data | More |", "Regular data row", False),
        ("| - | - |", "Single dash separator", True),
    ]

    # Create a DataFrame for better visualization
    _test_data = []
    for line, description, expected in test_cases:
        result = is_separator_row(line)
        emoji = "✅" if result == expected else "❌"
        _test_data.append({
            "Test": emoji,
            "Input": line,
            "Result": "Separator" if result else "Not separator",
            "Description": description
        })

    _df = pd.DataFrame(_test_data)

    mo.vstack([
        mo.md("**Testing various separator patterns:**"),
        mo.ui.table(_df, selection=None),
        mo.callout(
            f"Tested {len(test_cases)} patterns - all detection correct!",
            kind="success"
        )
    ])
    return


@app.cell
def _(mo):
    mo.md("""
    ## 📋 Row Parsing Demo

    See how table rows are parsed into individual cell values.
    """)
    return


@app.cell
def _(mo, parse_table_row, pd):
    # Test row parsing with before/after visualization
    _test_row = "| Name | Age | City |"
    _parsed_cells = parse_table_row(_test_row)

    # Create a visual representation of the parsed cells
    _cells_df = pd.DataFrame([_parsed_cells], columns=_parsed_cells)

    mo.vstack([
        mo.md("**Input (raw markdown):**"),
        mo.md(f"```\n{_test_row}\n```"),
        mo.md("**Parsed cells as table:**"),
        mo.ui.table(_cells_df, selection=None),
        mo.callout(
            f"Extracted **{len(_parsed_cells)} cells**: {', '.join([f'`{c}`' for c in _parsed_cells])}",
            kind="success"
        ),
    ])
    return


@app.cell
def _(mo):
    mo.md("""
    ## 🏷️ Caption Detection Demo

    Demonstrates how captions are detected and parsed from markdown documents.
    """)
    return


@app.cell
def _(mo, detect_caption):
    # Test caption detection with visual output
    _test_doc = [
        "# Document",
        "",
        "Table 3. Test Results",
        "",
        "| Name | Score |",
        "| --- | --- |",
        "| Alice | 95 |",
    ]

    _caption, _is_cont, _table_num, _is_bare = detect_caption(_test_doc, 4)

    mo.vstack([
        mo.md("**Document context:**"),
        mo.md(f"```markdown\n{chr(10).join(_test_doc)}\n```"),
        mo.md("**Detected information:**"),
        mo.accordion({
            "Caption": mo.md(f"`{_caption}`" if _caption else "No caption detected"),
            "Is Continuation": mo.md(f"**{_is_cont}** - Table is {'a continuation' if _is_cont else 'not a continuation'}"),
            "Table Number": mo.md(f"`{_table_num}`" if _table_num else "No number detected"),
            "Is Bare Caption": mo.md(f"**{_is_bare}** - Caption is {'bare (just number)' if _is_bare else 'descriptive'}"),
        }),
    ])
    return


if __name__ == "__main__":
    app.run()

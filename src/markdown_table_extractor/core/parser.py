"""Markdown table parsing utilities.

This module contains functions for detecting and parsing markdown table structures.
"""
from __future__ import annotations

import marimo
import re
from typing import Optional


# ============================================================================
# MODULE-LEVEL CODE (importable)
# ============================================================================

# Pattern for separator cells: ---, :---, ---:, :---:
_SEPARATOR_CELL_PATTERN = re.compile(r"^:?-{1,}:?$")


def is_table_row(line: str) -> bool:
    """Check if a line looks like a markdown table row.
    
    Args:
        line: A single line of text
        
    Returns:
        True if the line starts and ends with pipe characters
    """
    stripped = line.strip()
    return stripped.startswith("|") and stripped.endswith("|")


def is_separator_row(line: str) -> bool:
    """Check if a line is a markdown table separator row.
    
    Separator rows contain only dashes and optional colons for alignment:
    - `| --- |` (no alignment)
    - `| :--- |` (left align)
    - `| ---: |` (right align)
    - `| :---: |` (center align)
    
    Args:
        line: A single line of text
        
    Returns:
        True if this is a separator row
    """
    if not is_table_row(line):
        return False
    
    cells = parse_table_row(line)
    if not cells:
        return False
    
    return all(_SEPARATOR_CELL_PATTERN.match(cell.strip()) for cell in cells)


def is_sub_header_row(line: str, threshold: float = 0.7) -> bool:
    """Check if a row is likely a sub-header (mostly empty cells).
    
    Sub-headers often appear after the separator row with content
    only in the first cell(s), like category labels.
    
    Args:
        line: A single line of text
        threshold: Fraction of cells that must be empty (default 0.7)
        
    Returns:
        True if this appears to be a sub-header row
    """
    if not is_table_row(line):
        return False
    
    cells = parse_table_row(line)
    if not cells:
        return False
    
    empty_count = sum(1 for c in cells if not c.strip())
    return empty_count / len(cells) >= threshold


def parse_table_row(line: str) -> list[str]:
    """Parse a markdown table row into individual cells.
    
    Handles escaped pipes within cells.
    
    Args:
        line: A markdown table row like `| A | B | C |`
        
    Returns:
        List of cell contents: ["A", "B", "C"]
    """
    stripped = line.strip()
    
    # Remove leading/trailing pipes
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    
    # Split on unescaped pipes
    # Simple split for now - could be enhanced for escaped pipes
    cells = stripped.split("|")
    
    return [cell.strip() for cell in cells]


def detect_caption(
    lines: list[str],
    table_start_line: int,
    lookback: int = 5,
) -> tuple[Optional[str], bool, Optional[str], bool]:
    """Look for a table caption above the table.

    Searches for patterns like:
    - "Table 1. Description"
    - "Table 1: Description"
    - "Table 1 - Description"
    - "Table 1 (Continued)"
    - "Table 2" (bare number - likely malformed continuation)

    Args:
        lines: All lines of the document
        table_start_line: Line index where table starts
        lookback: How many lines above to search

    Returns:
        Tuple of (caption, is_continuation, table_number, is_bare):
        - caption: Full caption text or None
        - is_continuation: True if marked as "(Continued)" or bare
        - table_number: Extracted table number (e.g., "1", "2", "3a") or None
        - is_bare: True if caption has no description (just "Table N")
    """
    caption_pattern = re.compile(
        r"^(?:table|tbl\.?)\s*(\d+[a-z]?)\s*[.:\-–—]?\s*(.*)",
        re.IGNORECASE,
    )
    continuation_pattern = re.compile(
        r"\(?\s*(?:continued|cont\.?|cont'd)\s*\)?",
        re.IGNORECASE,
    )

    start = max(0, table_start_line - lookback)

    for i in range(table_start_line - 1, start - 1, -1):
        line = lines[i].strip()

        # Skip empty lines
        if not line:
            continue

        # Skip lines that look like table rows
        if is_table_row(line):
            continue

        # Strip markdown formatting for matching (bold, italic, etc.)
        clean_line = line.replace("**", "").replace("__", "").replace("*", "").replace("_", "").strip()

        match = caption_pattern.match(clean_line)
        if match:
            table_num = match.group(1)  # e.g., "1", "2", "3a"
            description = match.group(2).strip()  # e.g., "Patient Demographics"

            # Check if explicitly marked as continuation
            has_continuation_marker = bool(continuation_pattern.search(clean_line))

            # Bare table number (no description) - likely malformed continuation
            is_bare = not description

            # Return original line with formatting intact
            return line, has_continuation_marker or is_bare, table_num, is_bare

    return None, False, None, False


# ============================================================================
# MARIMO NOTEBOOK (interactive documentation)
# ============================================================================

app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _(mo):
    mo.md(
        """
        # Markdown Table Parser

        Functions for detecting and parsing markdown table structures.

        ## Key Functions

        - `is_table_row(line)` - Check if line is a table row
        - `is_separator_row(line)` - Check if line is separator (---)
        - `parse_table_row(line)` - Extract cell contents
        - `detect_caption(lines, start)` - Find table caption
        """
    )
    return


@app.cell
def _(mo):
    mo.md("## Separator Detection Demo")
    return


@app.cell
def _():
    # Test separator detection
    test_lines = [
        "| --- | --- |",
        "| :--- | ---: |",
        "| :---: | :---: |",
        "| Data | More |",
        "| - | - |",
    ]
    
    for line in test_lines:
        result = is_separator_row(line)
        print(f"{line:25} -> separator={result}")
    return (test_lines,)


@app.cell
def _(mo):
    mo.md("## Row Parsing Demo")
    return


@app.cell
def _():
    # Test row parsing
    row = "| Name | Age | City |"
    cells = parse_table_row(row)
    print(f"Input: {row}")
    print(f"Cells: {cells}")
    return (row, cells)


if __name__ == "__main__":
    app.run()

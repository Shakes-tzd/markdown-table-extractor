"""Markdown table parsing utilities.

This module contains functions for detecting and parsing markdown table structures.
All functions handle the various alignment syntaxes used in markdown tables.

Import directly:
    from markdown_table_extractor.core.parser import is_separator_row, parse_table_row
"""
from __future__ import annotations

import re
from typing import Optional

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


def is_sub_header_row(cells: list[str], header_cells: list[str]) -> bool:
    """Detect if a row is a sub-header row (common in multi-level table headers).

    Sub-header rows typically:
    - Have mostly empty cells
    - Have short text labels in some cells
    - Appear right after the separator row

    Args:
        cells: The row cells to check
        header_cells: The main header cells for context

    Returns:
        True if this appears to be a sub-header row

    Examples:
        >>> is_sub_header_row(['', '', 'Early', 'Late', 'Both'], ['A', 'B', 'Morbidity', '', ''])
        True
    """
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
) -> tuple[Optional[str], bool]:
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
        Tuple of (caption_text, is_continuation)
    """
    # Caption patterns for manuscripts
    caption_patterns = [
        re.compile(r'^(?:Table|TABLE)\s*(\d+)[.:]?\s*(.*)$', re.IGNORECASE),
        re.compile(r'^(?:Table|TABLE)\s*(\d+)\s*\(([^)]+)\)\s*(.*)$', re.IGNORECASE),
        re.compile(r'^\*\*(?:Table|TABLE)\s*(\d+)[.:]?\s*(.*)\*\*$', re.IGNORECASE),
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
                return line, is_continuation

        # If we hit a non-caption line, stop looking
        break

    return None, False

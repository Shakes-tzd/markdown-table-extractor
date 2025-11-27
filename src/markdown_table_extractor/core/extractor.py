"""Main table extraction functionality.

This module provides the primary API for extracting tables from markdown.
"""
from __future__ import annotations

import marimo
from typing import Optional

import pandas as pd

from markdown_table_extractor.core.models import (
    ExtractedTable,
    ExtractionResult,
    TableMergeStrategy,
)
from markdown_table_extractor.core.parser import (
    detect_caption,
    is_separator_row,
    is_sub_header_row,
    is_table_row,
    parse_table_row,
)
from markdown_table_extractor.core.cleaner import (
    clean_column_name,
    clean_value,
    merge_sub_header,
)
from markdown_table_extractor.core.merger import merge_tables


# ============================================================================
# MODULE-LEVEL CODE (importable)
# ============================================================================


def extract_single_table(
    lines: list[str],
    start_idx: int,
    detect_captions: bool = True,
    skip_sub_headers: bool = True,
) -> tuple[ExtractedTable, int]:
    """Extract a single table starting at the given line.
    
    Args:
        lines: All document lines
        start_idx: Line index where table starts
        detect_captions: Whether to look for captions above
        skip_sub_headers: Whether to merge sub-header rows
        
    Returns:
        Tuple of (ExtractedTable, end_index)
    """
    table_lines: list[str] = []
    raw_lines: list[str] = []
    idx = start_idx
    
    # Collect all table rows
    while idx < len(lines) and is_table_row(lines[idx]):
        table_lines.append(lines[idx])
        raw_lines.append(lines[idx])
        idx += 1
    
    if len(table_lines) < 2:
        # Need at least header + separator
        df = pd.DataFrame()
        return ExtractedTable(df, start_line=start_idx, end_line=idx), idx
    
    # Parse header (first row)
    headers = parse_table_row(table_lines[0])
    headers = [clean_column_name(h) for h in headers]

    # Find separator row
    separator_idx = None
    for i, line in enumerate(table_lines[1:], 1):
        if is_separator_row(line):
            separator_idx = i
            break

    if separator_idx is None:
        # No separator found - treat as data only
        data_rows = [parse_table_row(line) for line in table_lines]
        df = pd.DataFrame(data_rows)
        return ExtractedTable(df, start_line=start_idx, end_line=idx), idx

    # Check for sub-header after separator
    data_start = separator_idx + 1

    # Check if main header is mostly empty (>70% empty cells)
    # If so, the row after separator likely contains the real headers
    header_empty_count = sum(1 for h in headers if not h.strip())
    header_mostly_empty = header_empty_count / len(headers) > 0.7 if headers else False

    if skip_sub_headers and data_start < len(table_lines):
        next_row_cells = parse_table_row(table_lines[data_start])

        # If header is mostly empty and next row has content, use next row as headers
        if header_mostly_empty and any(c.strip() for c in next_row_cells):
            # Merge: use next row values, keep any non-empty header values
            new_headers = []
            for old_h, new_h in zip(headers, next_row_cells):
                new_h_clean = clean_column_name(new_h)
                if new_h_clean.strip():
                    # Next row has content - use it, possibly with prefix from header
                    if old_h.strip():
                        new_headers.append(f"{old_h.strip()} {new_h_clean}")
                    else:
                        new_headers.append(new_h_clean)
                else:
                    # Next row empty - keep old header
                    new_headers.append(old_h.strip())
            headers = new_headers
            data_start += 1
        elif is_sub_header_row(table_lines[data_start]):
            # Traditional sub-header merge (sub-header is mostly empty)
            sub_headers = parse_table_row(table_lines[data_start])
            headers = merge_sub_header(headers, sub_headers)
            data_start += 1
    
    # Parse data rows (skip separator rows)
    data_rows: list[list[str]] = []
    expected_cols = len(headers)

    for line in table_lines[data_start:]:
        if not is_separator_row(line):
            cells = parse_table_row(line)
            cells = [clean_value(c) for c in cells]

            # Normalize row length to match header count
            if len(cells) < expected_cols:
                # Pad with empty strings
                cells.extend([""] * (expected_cols - len(cells)))
            elif len(cells) > expected_cols:
                # Trim to header count
                cells = cells[:expected_cols]

            data_rows.append(cells)

    # Create DataFrame
    df = pd.DataFrame(data_rows, columns=headers)

    # Detect caption
    caption = None
    is_continuation = False
    table_number = None
    is_bare_caption = False
    if detect_captions:
        caption, is_continuation, table_number, is_bare_caption = detect_caption(lines, start_idx)

    table = ExtractedTable(
        dataframe=df,
        caption=caption,
        start_line=start_idx,
        end_line=idx,
        raw_markdown="\n".join(raw_lines),
        is_continuation=is_continuation,
    )

    # Store metadata for bare caption detection (not in model yet, but we'll use it for merging logic)
    table._table_number = table_number
    table._is_bare_caption = is_bare_caption

    return table, idx


def extract_markdown_tables(
    text: str,
    merge_strategy: TableMergeStrategy = TableMergeStrategy.IDENTICAL_HEADERS,
    detect_captions: bool = True,
    skip_sub_headers: bool = True,
) -> ExtractionResult:
    """Extract all tables from markdown text.
    
    This is the full API that returns metadata about each table.
    
    Args:
        text: Markdown document text
        merge_strategy: How to handle continuation tables
        detect_captions: Whether to look for table captions
        skip_sub_headers: Whether to merge sub-header rows into headers
        
    Returns:
        ExtractionResult with all tables and any errors
    """
    lines = text.split("\n")
    tables: list[ExtractedTable] = []
    errors: list[str] = []
    
    idx = 0
    while idx < len(lines):
        if is_table_row(lines[idx]):
            try:
                table, idx = extract_single_table(
                    lines, idx, detect_captions, skip_sub_headers
                )
                if not table.dataframe.empty:
                    tables.append(table)
            except Exception as e:
                errors.append(f"Error at line {idx}: {e}")
                idx += 1
        else:
            idx += 1
    
    # Merge continuation tables
    original_count = len(tables)
    if merge_strategy != TableMergeStrategy.NONE:
        tables = merge_tables(tables, merge_strategy)
    merged_count = original_count - len(tables)
    
    return ExtractionResult(
        tables=tables,
        errors=errors,
        merged_count=merged_count,
    )


def extract_tables(text: str) -> list[pd.DataFrame]:
    """Simple API: Extract tables and return DataFrames only.
    
    This is the easiest way to get tables from markdown:
    
    ```python
    from markdown_table_extractor import extract_tables
    
    tables = extract_tables(markdown_text)
    for df in tables:
        print(df)
    ```
    
    Args:
        text: Markdown document text
        
    Returns:
        List of pandas DataFrames
    """
    result = extract_markdown_tables(text)
    return result.get_dataframes()


# ============================================================================
# MARIMO NOTEBOOK (interactive documentation)
# ============================================================================

app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from markdown_table_extractor.core.extractor import (
        extract_tables,
        extract_markdown_tables,
        extract_single_table,
    )
    return (mo, extract_tables, extract_markdown_tables, extract_single_table)


@app.cell
def _(mo):
    mo.md(
        """
        # Table Extractor

        Main entry point for extracting tables from markdown.

        ## API

        **Simple (returns DataFrames):**
        ```python
        tables = extract_tables(text)
        ```

        **Full (returns ExtractionResult with metadata):**
        ```python
        result = extract_markdown_tables(text)
        for table in result:
            print(table.caption, table.dataframe)
        ```
        """
    )
    return


@app.cell
def _(mo):
    mo.md("## Live Demo")
    return


@app.cell
def _():
    sample_markdown = """
# Sample Document

Table 1. Test Results

| Name | Score | Grade |
|------|-------|-------|
| Alice | 95 | A |
| Bob | 87 | B |
| Carol | 92 | A |

Some text between tables.

Table 2. Summary

| Metric | Value |
|--------|-------|
| Mean | 91.3 |
| Median | 92 |
"""
    return (sample_markdown,)


@app.cell
def _(sample_markdown):
    # Extract tables
    result = extract_markdown_tables(sample_markdown)
    print(f"Found {len(result)} tables")
    print(f"Errors: {result.errors}")
    return (result,)


@app.cell
def _(result):
    # Show first table
    if result.tables:
        _table1 = result.tables[0]
        print(f"Caption: {_table1.caption}")
        _table1.dataframe
    return


@app.cell
def _(result):
    # Show second table
    if len(result.tables) > 1:
        _table2 = result.tables[1]
        print(f"Caption: {_table2.caption}")
        _table2.dataframe
    return


if __name__ == "__main__":
    app.run()

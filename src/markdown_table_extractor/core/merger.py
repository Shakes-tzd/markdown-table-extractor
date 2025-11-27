"""Table merging utilities.

Handles merging adjacent tables that are continuations of each other.
"""
from __future__ import annotations

import marimo
import re
from typing import Optional

import pandas as pd

from markdown_table_extractor.core.models import ExtractedTable, TableMergeStrategy
from markdown_table_extractor.core.cleaner import headers_match


# ============================================================================
# MODULE-LEVEL CODE (importable)
# ============================================================================

CONTINUATION_PATTERN = re.compile(
    r"\(?\s*(?:continued|cont\.?|cont'd)\s*\)?",
    re.IGNORECASE,
)


def is_continuation_table(table: ExtractedTable) -> bool:
    """Check if a table is marked as a continuation.

    Args:
        table: Table to check

    Returns:
        True if caption contains "continued" or similar
    """
    if table.is_continuation:
        return True

    if table.caption and CONTINUATION_PATTERN.search(table.caption):
        return True

    return False


def _check_header_similarity(cols1: list, cols2: list) -> bool:
    """Check if two column lists are similar enough to merge.

    Uses fuzzy matching if rapidfuzz available, otherwise exact match.

    Args:
        cols1: First column list
        cols2: Second column list

    Returns:
        True if headers are similar enough
    """
    if len(cols1) != len(cols2):
        return False

    # Try Level 2 (fuzzy matching) if available
    try:
        from rapidfuzz import fuzz

        # Fuzzy header matching
        similarities = [
            fuzz.token_set_ratio(str(c1), str(c2))
            for c1, c2 in zip(cols1, cols2)
        ]
        avg_sim = sum(similarities) / len(similarities)
        return avg_sim > 80  # 80% threshold

    except ImportError:
        # Level 1: Exact match (case-insensitive)
        return all(
            str(c1).lower().strip() == str(c2).lower().strip()
            for c1, c2 in zip(cols1, cols2)
        )


def should_merge_bare_caption(
    prev_table: ExtractedTable,
    current_table: ExtractedTable,
) -> bool:
    """Check if a bare caption table should be merged with the previous table.

    Handles:
    1. Tables with NO caption (caption=None) - merge if structure matches
    2. Tables with bare captions (just "Table N") - merge if sequential + structure matches

    Level 1 (always available): Column count + exact header matching
    Level 2 (optional): + fuzzy matching if rapidfuzz available

    Args:
        prev_table: Previous table
        current_table: Current table with bare/no caption

    Returns:
        True if tables should be merged
    """
    # Case 1: Table with NO caption at all (caption=None)
    # Merge if column count matches (even if headers don't match)
    # This handles tables without header rows where first data row was used as headers
    if current_table.caption is None or (isinstance(current_table.caption, str) and not current_table.caption.strip()):
        # Level 1: Column count must match
        prev_cols = list(prev_table.dataframe.columns)
        curr_cols = list(current_table.dataframe.columns)

        if len(prev_cols) != len(curr_cols):
            return False

        # First try header similarity check
        if _check_header_similarity(prev_cols, curr_cols):
            return True

        # If headers don't match but column count does,
        # this might be a table without headers where data became headers
        # Merge anyway since it's likely a continuation
        return True

    # Case 2: Table with bare caption (just "Table N")
    # Must have bare caption metadata
    if not hasattr(current_table, '_is_bare_caption') or not current_table._is_bare_caption:
        return False

    # Must have table numbers
    if not hasattr(prev_table, '_table_number') or not hasattr(current_table, '_table_number'):
        return False

    prev_num = prev_table._table_number
    curr_num = current_table._table_number

    if not prev_num or not curr_num:
        return False

    # Convert to comparable format (handle "3a" style numbers)
    try:
        prev_int = int(prev_num.rstrip('abcdefghijklmnopqrstuvwxyz'))
        curr_int = int(curr_num.rstrip('abcdefghijklmnopqrstuvwxyz'))
    except (ValueError, AttributeError):
        return False

    # Check if sequential (curr = prev + 1) or same number
    is_sequential = curr_int in [prev_int, prev_int + 1]
    if not is_sequential:
        return False

    # Level 1: Column count must match
    prev_cols = list(prev_table.dataframe.columns)
    curr_cols = list(current_table.dataframe.columns)

    if len(prev_cols) != len(curr_cols):
        return False

    # Check header similarity
    return _check_header_similarity(prev_cols, curr_cols)


def should_merge_tables(
    table1: ExtractedTable,
    table2: ExtractedTable,
    strategy: TableMergeStrategy = TableMergeStrategy.IDENTICAL_HEADERS,
) -> bool:
    """Determine if two tables should be merged.
    
    Args:
        table1: First table
        table2: Second table (potential continuation)
        strategy: Merge strategy to use
        
    Returns:
        True if tables should be merged
    """
    if strategy == TableMergeStrategy.NONE:
        return False
    
    # Second table must be marked as continuation
    if not is_continuation_table(table2):
        return False
    
    if strategy == TableMergeStrategy.IDENTICAL_HEADERS:
        h1 = list(table1.dataframe.columns)
        h2 = list(table2.dataframe.columns)
        return headers_match(h1, h2)
    
    if strategy == TableMergeStrategy.COMPATIBLE_COLUMNS:
        diff = abs(table1.column_count - table2.column_count)
        return diff <= 2
    
    return False


def merge_two_tables(
    table1: ExtractedTable,
    table2: ExtractedTable,
) -> ExtractedTable:
    """Merge two tables into one.

    Uses the first table's caption and combines rows.
    Handles cases where table2 has different headers (e.g., no header row).

    CRITICAL: When table2 has no caption and different headers, the headers
    are actually data that was misinterpreted. We recover this lost row.

    Args:
        table1: Base table
        table2: Continuation table

    Returns:
        Merged table
    """
    df1 = table1.dataframe.copy()
    df2 = table2.dataframe.copy()

    # If column counts match but headers don't, this might be a headerless table
    # where the first data row was used as headers
    if len(df1.columns) == len(df2.columns) and list(df1.columns) != list(df2.columns):
        # Check if table2 has no caption (headerless table indicator)
        is_headerless = (
            table2.caption is None or
            (isinstance(table2.caption, str) and not table2.caption.strip())
        )

        if is_headerless:
            # RECOVER LOST ROW: The "headers" are actually data!
            # Insert them as the first row
            lost_row = pd.DataFrame([df2.columns], columns=df1.columns)
            df2.columns = df1.columns  # Align column names
            df2 = pd.concat([lost_row, df2], ignore_index=True)
        else:
            # Normal case: just rename columns
            df2.columns = df1.columns

    # Concatenate dataframes
    merged_df = pd.concat([df1, df2], ignore_index=True)

    return ExtractedTable(
        dataframe=merged_df,
        caption=table1.caption,  # Keep original caption
        start_line=table1.start_line,
        end_line=table2.end_line,
        raw_markdown=table1.raw_markdown + "\n\n" + table2.raw_markdown,
        is_continuation=False,
    )


def merge_tables(
    tables: list[ExtractedTable],
    strategy: TableMergeStrategy = TableMergeStrategy.IDENTICAL_HEADERS,
) -> list[ExtractedTable]:
    """Merge adjacent continuation tables.

    Handles both explicit continuations and bare caption tables (malformed continuations).

    Args:
        tables: List of extracted tables
        strategy: How to determine which tables to merge

    Returns:
        List of tables with continuations merged
    """
    if not tables or strategy == TableMergeStrategy.NONE:
        return tables

    result: list[ExtractedTable] = []
    current = tables[0]

    for next_table in tables[1:]:
        # Check for bare caption merging first (higher priority)
        if should_merge_bare_caption(current, next_table):
            current = merge_two_tables(current, next_table)
        # Then check normal merge strategy
        elif should_merge_tables(current, next_table, strategy):
            current = merge_two_tables(current, next_table)
        else:
            result.append(current)
            current = next_table

    result.append(current)
    return result


# ============================================================================
# MARIMO NOTEBOOK (interactive documentation)
# ============================================================================

app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    from markdown_table_extractor.core.merger import (
        CONTINUATION_PATTERN,
        is_continuation_table,
        should_merge_tables,
        merge_tables,
        merge_two_tables,
    )
    from markdown_table_extractor.core.models import ExtractedTable, TableMergeStrategy
    return (mo, pd, CONTINUATION_PATTERN, is_continuation_table, should_merge_tables, merge_tables, merge_two_tables, ExtractedTable, TableMergeStrategy)


@app.cell
def _(mo):
    mo.md(
        """
        # Table Merger

        Handles merging continuation tables (e.g., "Table 3 (Continued)").

        ## Key Functions

        - `is_continuation_table(table)` - Check for continuation marker
        - `should_merge_tables(t1, t2, strategy)` - Check if mergeable
        - `merge_tables(tables, strategy)` - Merge all continuations
        """
    )
    return


@app.cell
def _(mo):
    mo.md("## Continuation Detection Demo")
    return


@app.cell
def _():
    # Test continuation patterns
    test_captions = [
        "Table 3. Results",
        "Table 3 (Continued)",
        "Table 3 (cont.)",
        "Table 3 - cont'd",
    ]
    
    for caption in test_captions:
        is_cont = bool(CONTINUATION_PATTERN.search(caption))
        print(f"{caption:30} -> continuation={is_cont}")
    return (test_captions,)


@app.cell
def _(mo):
    mo.md("## Merge Demo")
    return


@app.cell
def _(pd, ExtractedTable, merge_tables):
    # Create sample tables
    df1 = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
    df2 = pd.DataFrame({"A": [5, 6], "B": [7, 8]})

    t1 = ExtractedTable(df1, caption="Table 1. Data")
    t2 = ExtractedTable(df2, caption="Table 1 (Continued)", is_continuation=True)

    print("Before merge:")
    print(f"  Table 1: {len(t1.dataframe)} rows")
    print(f"  Table 2: {len(t2.dataframe)} rows")

    merged = merge_tables([t1, t2])

    print(f"\nAfter merge:")
    print(f"  Result: {len(merged[0].dataframe)} rows")
    return (df1, df2, t1, t2, merged)


if __name__ == "__main__":
    app.run()

"""Data models for markdown table extraction.

This module defines the core data structures used throughout the library.
"""
from __future__ import annotations

import marimo
from dataclasses import dataclass, field
from enum import Enum
from typing import Iterator, Optional

import pandas as pd


# ============================================================================
# MODULE-LEVEL CODE (importable)
# ============================================================================


class TableMergeStrategy(Enum):
    """Strategy for merging adjacent tables.

    Attributes:
        NONE: Don't merge any tables
        IDENTICAL_HEADERS: Merge tables with identical/similar headers (default)
        COMPATIBLE_COLUMNS: Merge if column counts are within tolerance (±2)
    """

    NONE = "none"
    IDENTICAL_HEADERS = "identical_headers"
    COMPATIBLE_COLUMNS = "compatible_columns"


@dataclass
class ExtractedTable:
    """A single extracted table with metadata.

    Attributes:
        dataframe: The extracted table data
        caption: Detected table caption (e.g., "Table 3. Results")
        start_line: Line number where table starts
        end_line: Line number where table ends
        raw_markdown: Original markdown text
        is_continuation: True if marked as continuation
    """

    dataframe: pd.DataFrame
    caption: Optional[str] = None
    start_line: int = 0
    end_line: int = 0
    raw_markdown: str = ""
    is_continuation: bool = False

    @property
    def column_count(self) -> int:
        return len(self.dataframe.columns)

    @property
    def row_count(self) -> int:
        return len(self.dataframe)

    def __repr__(self) -> str:
        caption_str = (
            f"'{self.caption[:30]}...'"
            if self.caption and len(self.caption) > 30
            else repr(self.caption)
        )
        return (
            f"ExtractedTable(rows={self.row_count}, cols={self.column_count}, "
            f"caption={caption_str})"
        )


@dataclass
class ExtractionResult:
    """Complete result of table extraction.

    Supports iteration: `for table in result: ...`
    Supports indexing: `result[0]`
    """

    tables: list[ExtractedTable] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    merged_count: int = 0

    def __len__(self) -> int:
        return len(self.tables)

    def __iter__(self) -> Iterator[ExtractedTable]:
        return iter(self.tables)

    def __getitem__(self, index: int) -> ExtractedTable:
        return self.tables[index]

    def get_dataframes(self) -> list[pd.DataFrame]:
        """Return just the DataFrames without metadata."""
        return [t.dataframe for t in self.tables]

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def __repr__(self) -> str:
        error_str = f", errors={len(self.errors)}" if self.errors else ""
        merged_str = f", merged={self.merged_count}" if self.merged_count else ""
        return f"ExtractionResult(tables={len(self.tables)}{merged_str}{error_str})"


# ============================================================================
# MARIMO NOTEBOOK (interactive documentation)
# ============================================================================

app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    from markdown_table_extractor.core.models import (
        ExtractedTable,
        ExtractionResult,
        TableMergeStrategy,
    )
    return (mo, pd, ExtractedTable, ExtractionResult, TableMergeStrategy)


@app.cell
def _(mo):
    mo.md(
        """
        # Data Models

        This module defines the core data structures for table extraction.

        ## Classes

        - **TableMergeStrategy**: Enum for merge behavior
        - **ExtractedTable**: Single table with metadata  
        - **ExtractionResult**: Collection of tables with errors
        """
    )
    return


@app.cell
def _(pd, ExtractedTable):
    # Live demo
    df = pd.DataFrame({"Name": ["Alice", "Bob"], "Score": [95, 87]})
    table = ExtractedTable(
        dataframe=df,
        caption="Table 1. Test Scores",
    )
    table
    return (df, table)


@app.cell
def _(table):
    # Show properties
    f"Columns: {table.column_count}, Rows: {table.row_count}"
    return


if __name__ == "__main__":
    app.run()

"""
Markdown Table Extractor

A robust, type-safe library for extracting structured data from markdown text.
Designed for manuscript processing with support for:
- Proper separator row detection
- Table caption detection
- Automatic merging of continuation tables
- LLM-based extraction for edge cases (optional)

Usage:
    from markdown_table_extractor import extract_tables
    
    # Simple usage - returns list of DataFrames
    tables = extract_tables(markdown_text)
    
    # Full API with metadata
    from markdown_table_extractor import extract_markdown_tables, TableMergeStrategy
    
    result = extract_markdown_tables(
        markdown_text,
        merge_strategy=TableMergeStrategy.IDENTICAL_HEADERS
    )
    for table in result.tables:
        print(f"Caption: {table.caption}")
        print(table.dataframe)
"""

from markdown_table_extractor.core.extractor import (
    extract_markdown_tables,
    extract_tables,
)
from markdown_table_extractor.core.models import (
    ExtractedTable,
    ExtractionResult,
    TableMergeStrategy,
)
from markdown_table_extractor.core.parser import (
    is_separator_row,
    is_table_row,
    parse_table_row,
)
from markdown_table_extractor.core.cleaner import (
    clean_column_name,
    normalize_headers,
)

__version__ = "0.1.0"

__all__ = [
    # Main extraction functions
    "extract_tables",
    "extract_markdown_tables",
    # Models/Types
    "ExtractedTable",
    "ExtractionResult",
    "TableMergeStrategy",
    # Utilities
    "is_separator_row",
    "is_table_row",
    "parse_table_row",
    "clean_column_name",
    "normalize_headers",
    # Version
    "__version__",
]

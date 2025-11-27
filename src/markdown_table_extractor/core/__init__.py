"""Core extraction modules."""
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
    headers_match,
    normalize_headers,
)
from markdown_table_extractor.core.merger import (
    merge_tables,
    should_merge_tables,
)
from markdown_table_extractor.core.extractor import (
    extract_markdown_tables,
    extract_tables,
)

__all__ = [
    # Models
    "ExtractedTable",
    "ExtractionResult",
    "TableMergeStrategy",
    # Parser
    "detect_caption",
    "is_separator_row",
    "is_sub_header_row",
    "is_table_row",
    "parse_table_row",
    # Cleaner
    "clean_column_name",
    "clean_value",
    "headers_match",
    "normalize_headers",
    # Merger
    "merge_tables",
    "should_merge_tables",
    # Extractor
    "extract_markdown_tables",
    "extract_tables",
]

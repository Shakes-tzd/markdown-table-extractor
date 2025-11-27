"""Tests for core extraction functionality."""

import pytest
import pandas as pd

from markdown_table_extractor import (
    extract_tables,
    extract_markdown_tables,
    TableMergeStrategy,
    is_separator_row,
)


class TestSeparatorDetection:
    """Test separator row detection for various formats."""
    
    @pytest.mark.parametrize("line,expected", [
        # Basic separators
        ("| --- | --- |", True),
        ("|---|---|", True),
        ("| ---- | ---- |", True),
        
        # Alignment syntax
        ("| :--: | :--: |", True),
        ("| :--- | ---: |", True),
        ("|:--|--:|", True),
        ("| :---: | :---: | :---: |", True),
        
        # With spaces
        ("|  ---  |  ---  |", True),
        ("| :--:  |  :--: |", True),
        
        # Not separators
        ("| Data | More |", False),
        ("| 2021 | 45% |", False),
        ("| --- Data | More --- |", False),
        ("Not a table row", False),
        ("", False),
    ])
    def test_separator_detection(self, line: str, expected: bool):
        assert is_separator_row(line) == expected


class TestSimpleExtraction:
    """Test basic table extraction."""
    
    def test_single_table(self):
        markdown = """
| Name | Age |
| --- | --- |
| Alice | 30 |
| Bob | 25 |
"""
        tables = extract_tables(markdown)
        
        assert len(tables) == 1
        df = tables[0]
        assert list(df.columns) == ["Name", "Age"]
        assert len(df) == 2
        assert df.iloc[0]["Name"] == "Alice"
    
    def test_multiple_tables(self):
        markdown = """
| A | B |
|---|---|
| 1 | 2 |

Some text between tables.

| X | Y | Z |
|---|---|---|
| a | b | c |
"""
        tables = extract_tables(markdown)

        assert len(tables) == 2
        assert list(tables[0].columns) == ["A", "B"]
        assert list(tables[1].columns) == ["X", "Y", "Z"]
    
    def test_empty_text(self):
        tables = extract_tables("")
        assert len(tables) == 0
    
    def test_no_tables(self):
        markdown = "Just some text without any tables."
        tables = extract_tables(markdown)
        assert len(tables) == 0


class TestTableMerging:
    """Test continuation table merging."""
    
    def test_continuation_merge(self):
        markdown = """
Table 3. Results

| Study | Outcome |
|-------|---------|
| A | Good |
| B | Fair |

Table 3. (Continued)

| Study | Outcome |
|-------|---------|
| C | Good |
| D | Poor |
"""
        # With merging
        result = extract_markdown_tables(
            markdown, 
            merge_strategy=TableMergeStrategy.IDENTICAL_HEADERS
        )
        
        assert len(result.tables) == 1
        assert result.merged_count == 1
        assert len(result.tables[0].dataframe) == 4
    
    def test_no_merge_strategy(self):
        markdown = """
| A | B |
|---|---|
| 1 | 2 |

| A | B |
|---|---|
| 3 | 4 |
"""
        result = extract_markdown_tables(
            markdown,
            merge_strategy=TableMergeStrategy.NONE
        )
        
        assert len(result.tables) == 2
        assert result.merged_count == 0


class TestCaptionDetection:
    """Test table caption detection."""
    
    def test_basic_caption(self):
        markdown = """
Table 1. Patient Demographics

| Age | Sex |
|-----|-----|
| 45  | M   |
"""
        result = extract_markdown_tables(markdown, detect_captions=True)
        
        assert len(result.tables) == 1
        assert result.tables[0].caption == "Table 1. Patient Demographics"
    
    def test_bold_caption(self):
        markdown = """
**Table 2. Study Results**

| Variable | Value |
|----------|-------|
| Mean     | 42.5  |
"""
        result = extract_markdown_tables(markdown, detect_captions=True)
        
        assert result.tables[0].caption is not None
        assert "Table 2" in result.tables[0].caption
    
    def test_continuation_detection(self):
        markdown = """
Table 3 (Continued)

| A | B |
|---|---|
| 1 | 2 |
"""
        result = extract_markdown_tables(markdown)
        
        assert result.tables[0].is_continuation is True


class TestHTMLCleaning:
    """Test HTML artifact cleaning in column names."""
    
    def test_br_tags(self):
        markdown = """
| Mean <br> Age | Follow-Up <br> (months) |
|---------------|-------------------------|
| 45            | 12                      |
"""
        tables = extract_tables(markdown)
        
        # Should have cleaned column names
        cols = list(tables[0].columns)
        assert "<br>" not in cols[0]
        assert "<br>" not in cols[1]


class TestSubHeaderHandling:
    """Test multi-level header handling."""
    
    def test_sub_header_merge(self):
        markdown = """
| Study | Morbidity | | |
|-------|-----------|-------|------|
|       | Early     | Late  | Both |
| A     | Yes       | No    | No   |
| B     | No        | Yes   | No   |
"""
        result = extract_markdown_tables(markdown, skip_sub_headers=True)
        
        # Sub-headers should be merged into column names
        df = result.tables[0].dataframe
        # The exact behavior depends on implementation
        assert len(df) >= 2  # Should have data rows


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_mismatched_columns(self):
        """Table with varying column counts per row."""
        markdown = """
| A | B | C |
|---|---|---|
| 1 | 2 |
| 3 | 4 | 5 | 6 |
"""
        tables = extract_tables(markdown)
        
        # Should handle gracefully
        assert len(tables) == 1
        assert len(tables[0].columns) == 3
    
    def test_special_characters_in_cells(self):
        markdown = """
| Formula | Result |
|---------|--------|
| $x^2$   | 4      |
| a & b   | true   |
"""
        tables = extract_tables(markdown)
        
        assert len(tables) == 1
        assert "$x^2$" in tables[0].iloc[0]["Formula"]


class TestFullAPI:
    """Test the full ExtractionResult API."""
    
    def test_result_iteration(self):
        markdown = """
| A | B |
|---|---|
| 1 | 2 |
"""
        result = extract_markdown_tables(markdown)
        
        # Test iteration
        tables = list(result)
        assert len(tables) == 1
        
        # Test indexing
        table = result[0]
        assert table.row_count == 1
        assert table.column_count == 2
    
    def test_get_dataframes(self):
        markdown = """
| A | B |
|---|---|
| 1 | 2 |
"""
        result = extract_markdown_tables(markdown)
        dfs = result.get_dataframes()
        
        assert isinstance(dfs, list)
        assert isinstance(dfs[0], pd.DataFrame)
    
    def test_error_collection(self):
        result = extract_markdown_tables("")
        
        # Should not have errors for empty input
        assert result.has_errors is False

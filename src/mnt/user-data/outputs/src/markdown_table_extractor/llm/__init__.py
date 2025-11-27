"""LLM-based table extraction for handling edge cases.

This module provides AI-powered extraction as a fallback or alternative
to regex-based parsing. Useful for:
- Complex nested tables
- Inconsistent formatting
- Tables with merged cells
- Non-standard markdown variants

Requires: pip install markdown-table-extractor[llm]
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional, Protocol, runtime_checkable

import pandas as pd

from markdown_table_extractor.core.models import ExtractedTable, ExtractionResult


if TYPE_CHECKING:
    pass  # Future type imports


@runtime_checkable
class LLMClient(Protocol):
    """Protocol for LLM clients (OpenAI, Anthropic, etc.)"""
    
    def create_completion(self, prompt: str, **kwargs: Any) -> str:
        """Generate a completion from the LLM."""
        ...


@dataclass
class LLMConfig:
    """Configuration for LLM-based extraction.
    
    Attributes:
        model: Model identifier (e.g., "gpt-4o", "claude-sonnet-4-20250514")
        temperature: Sampling temperature (0.0 for deterministic)
        max_tokens: Maximum tokens in response
        provider: "openai" or "anthropic"
    """
    model: str = "gpt-4o-mini"
    temperature: float = 0.0
    max_tokens: int = 4096
    provider: str = "openai"


# System prompt for table extraction
TABLE_EXTRACTION_PROMPT = """You are a precise data extraction assistant. Extract ALL tables from the provided markdown text.

For each table, output a JSON object with:
- "caption": The table caption/title if present (null if none)
- "headers": Array of column header strings
- "rows": Array of arrays, each inner array is a row of cell values

Output format: A JSON array of table objects.

Rules:
1. Preserve exact cell values - do not interpret or modify them
2. Handle multi-line cells by joining with spaces
3. Include ALL tables, even small ones
4. If a table has no caption, set caption to null
5. Empty cells should be empty strings ""

Example output:
[
  {
    "caption": "Table 1. Patient Demographics",
    "headers": ["Variable", "Group A", "Group B"],
    "rows": [
      ["Age (years)", "45.2 ± 12.1", "44.8 ± 11.9"],
      ["Sex (M/F)", "23/27", "25/25"]
    ]
  }
]

Return ONLY valid JSON, no markdown code blocks or explanations."""


def extract_tables_with_llm(
    text: str,
    config: Optional[LLMConfig] = None,
    api_key: Optional[str] = None,
) -> ExtractionResult:
    """Extract tables using an LLM for parsing.
    
    This function provides more flexible extraction for edge cases
    that regex-based parsing might miss.
    
    Args:
        text: The markdown text to parse
        config: LLM configuration (uses defaults if None)
        api_key: API key for the LLM provider (or set via environment)
        
    Returns:
        ExtractionResult containing extracted tables
        
    Raises:
        ImportError: If required LLM package is not installed
        ValueError: If extraction fails
        
    Examples:
        >>> from markdown_table_extractor.llm import extract_tables_with_llm
        >>> result = extract_tables_with_llm(markdown_text)
        >>> print(result.tables[0].dataframe)
    """
    config = config or LLMConfig()
    result = ExtractionResult()
    
    try:
        if config.provider == "openai":
            tables_json = _extract_with_openai(text, config, api_key)
        elif config.provider == "anthropic":
            tables_json = _extract_with_anthropic(text, config, api_key)
        else:
            raise ValueError(f"Unknown provider: {config.provider}")
        
        # Parse JSON response into tables
        result.tables = _parse_llm_response(tables_json)
        
    except ImportError as e:
        result.errors.append(
            f"LLM provider '{config.provider}' not installed. "
            f"Install with: pip install markdown-table-extractor[llm]. Error: {e}"
        )
    except Exception as e:
        result.errors.append(f"LLM extraction failed: {e}")
    
    return result


def _extract_with_openai(
    text: str, 
    config: LLMConfig, 
    api_key: Optional[str]
) -> str:
    """Extract tables using OpenAI API."""
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError(
            "OpenAI package not installed. "
            "Install with: pip install openai"
        )
    
    client = OpenAI(api_key=api_key) if api_key else OpenAI()
    
    response = client.chat.completions.create(
        model=config.model,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        messages=[
            {"role": "system", "content": TABLE_EXTRACTION_PROMPT},
            {"role": "user", "content": f"Extract all tables from:\n\n{text}"}
        ],
        response_format={"type": "json_object"}
    )
    
    return response.choices[0].message.content or "[]"


def _extract_with_anthropic(
    text: str, 
    config: LLMConfig, 
    api_key: Optional[str]
) -> str:
    """Extract tables using Anthropic API."""
    try:
        from anthropic import Anthropic
    except ImportError:
        raise ImportError(
            "Anthropic package not installed. "
            "Install with: pip install anthropic"
        )
    
    client = Anthropic(api_key=api_key) if api_key else Anthropic()
    
    response = client.messages.create(
        model=config.model,
        max_tokens=config.max_tokens,
        system=TABLE_EXTRACTION_PROMPT,
        messages=[
            {"role": "user", "content": f"Extract all tables from:\n\n{text}"}
        ]
    )
    
    # Extract text from response
    content = response.content[0]
    if hasattr(content, 'text'):
        return content.text
    return "[]"


def _parse_llm_response(json_str: str) -> list[ExtractedTable]:
    """Parse JSON response from LLM into ExtractedTable objects."""
    try:
        # Handle potential JSON wrapper
        data = json.loads(json_str)
        
        # Extract tables array (handle different response formats)
        if isinstance(data, dict):
            tables_data = data.get("tables", data.get("data", [data]))
        elif isinstance(data, list):
            tables_data = data
        else:
            return []
        
        tables = []
        for table_data in tables_data:
            if not isinstance(table_data, dict):
                continue
                
            headers = table_data.get("headers", [])
            rows = table_data.get("rows", [])
            caption = table_data.get("caption")
            
            if headers and rows:
                df = pd.DataFrame(rows, columns=headers)
                tables.append(ExtractedTable(
                    dataframe=df,
                    caption=caption,
                    raw_markdown=""  # Not available from LLM extraction
                ))
        
        return tables
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON from LLM: {e}")


# Convenience function for quick extraction
def llm_extract(
    text: str,
    model: str = "gpt-4o-mini",
    provider: str = "openai"
) -> list[pd.DataFrame]:
    """Quick LLM-based table extraction.
    
    Simplified API that returns just DataFrames.
    
    Args:
        text: Markdown text to parse
        model: Model to use
        provider: "openai" or "anthropic"
        
    Returns:
        List of DataFrames
    """
    config = LLMConfig(model=model, provider=provider)
    result = extract_tables_with_llm(text, config)
    return result.get_dataframes()

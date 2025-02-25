"""
Tests for utility functions.
"""

import pytest
from src.utils import normalize_benchmark_format, find_closest_benchmark, format_benchmark_response

def test_normalize_benchmark_format():
    """Test benchmark format normalization."""
    # Test valid formats
    assert normalize_benchmark_format("MA.K.NSO.1.1") == "MA.K.NSO.1.1"
    assert normalize_benchmark_format("ma.k.nso.1.1") == "MA.K.NSO.1.1"  # Case conversion
    assert normalize_benchmark_format("MA-K-NSO-1-1") == "MA.K.NSO.1.1"  # Dash conversion
    assert normalize_benchmark_format("MA_K_NSO_1_1") == "MA.K.NSO.1.1"  # Underscore conversion
    assert normalize_benchmark_format("MA K NSO 1 1") == "MA.K.NSO.1.1"  # Space conversion
    assert normalize_benchmark_format(" MA.K.NSO.1.1 ") == "MA.K.NSO.1.1"  # Trim spaces
    
    # Test K12 format
    assert normalize_benchmark_format("MA.K12.MTR.1.1") == "MA.K12.MTR.1.1"
    
    # Test invalid formats
    assert normalize_benchmark_format("invalid") is None
    assert normalize_benchmark_format("MA.K.NSO") is None
    assert normalize_benchmark_format("123.456") is None

def test_find_closest_benchmark():
    """Test benchmark matching."""
    benchmark_list = ["MA.K.NSO.1.1", "MA.K.NSO.1.2", "MA.K12.MTR.1.1"]
    
    # Test exact match
    match, message = find_closest_benchmark("MA.K.NSO.1.1", benchmark_list)
    assert match == "MA.K.NSO.1.1"
    assert "Exact match" in message
    
    # Test K12 format
    match, message = find_closest_benchmark("MA.K12.MTR.1.1", benchmark_list)
    assert match == "MA.K12.MTR.1.1"
    assert "Exact match" in message
    
    # Test fuzzy match
    match, message = find_closest_benchmark("MA.K.NSO.1.3", benchmark_list)
    assert match is None or match in benchmark_list
    
    # Test invalid format
    match, message = find_closest_benchmark("invalid", benchmark_list)
    assert match is None
    assert "Invalid benchmark format" in message

def test_format_benchmark_response():
    """Test response formatting."""
    # Test basic response
    response = {
        "benchmark_code": "MA.K.NSO.1.1",
        "definition": "Test definition",
        "in_other_words": "Simple explanation",
        "example": "Example problem"
    }
    formatted = format_benchmark_response(response)
    assert "**Definition:** MA.K.NSO.1.1: Test definition" in formatted
    assert "**In Other Words:**" in formatted
    assert "Simple explanation" in formatted
    assert "**Example:**" in formatted
    assert "Example problem" in formatted
    
    # Test structured example
    response = {
        "benchmark_code": "MA.K.NSO.1.1",
        "definition": "Test definition",
        "in_other_words": "Simple explanation",
        "example": {
            "problem": "What is 2+2?",
            "solution": "4"
        }
    }
    formatted = format_benchmark_response(response)
    assert "**Problem:** What is 2+2?" in formatted
    assert "**Solution:** 4" in formatted

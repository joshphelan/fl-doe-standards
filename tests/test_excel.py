"""
Tests for Excel processor functionality.
"""

import pytest
from pathlib import Path
from src.excel_processor import process_excel_benchmarks, ExcelProcessingError, Benchmark

# Test data path
EXCEL_PATH = "data/raw/BEST Math Extract.xlsx"

def test_excel_file_exists():
    """Test that the Excel file exists in the correct location."""
    assert Path(EXCEL_PATH).exists(), f"Excel file not found at {EXCEL_PATH}"

def test_process_excel_benchmarks():
    """Test processing of Excel file."""
    benchmarks = process_excel_benchmarks(EXCEL_PATH)
    
    # Basic validation
    assert benchmarks, "No benchmarks were processed"
    assert isinstance(benchmarks, dict), "Benchmarks should be returned as dictionary"
    
    # Check a sample benchmark
    sample_id = next(iter(benchmarks))
    sample_benchmark = benchmarks[sample_id]
    assert isinstance(sample_benchmark, Benchmark), "Benchmark should be a Benchmark object"
    assert sample_benchmark.id == sample_id
    assert sample_benchmark.definition, "Benchmark should have a definition"
    assert sample_benchmark.grade_level, "Benchmark should have a grade level"
    assert sample_benchmark.subject == "Mathematics"

def test_invalid_file_path():
    """Test handling of invalid file path."""
    with pytest.raises(FileNotFoundError):
        process_excel_benchmarks("nonexistent.xlsx")

def test_benchmark_attributes():
    """Test that processed benchmarks have required attributes."""
    benchmarks = process_excel_benchmarks(EXCEL_PATH)
    
    # Get first benchmark
    sample_benchmark = next(iter(benchmarks.values()))
    
    # Check attributes
    assert hasattr(sample_benchmark, 'id'), "Benchmark should have id"
    assert hasattr(sample_benchmark, 'definition'), "Benchmark should have definition"
    assert hasattr(sample_benchmark, 'grade_level'), "Benchmark should have grade_level"
    assert hasattr(sample_benchmark, 'subject'), "Benchmark should have subject"

def test_benchmark_format():
    """Test that benchmark IDs follow expected format."""
    benchmarks = process_excel_benchmarks(EXCEL_PATH)
    
    # Check first benchmark ID format (e.g., MA.K.NSO.1.1)
    sample_id = next(iter(benchmarks.keys()))
    assert '.' in sample_id, "Benchmark ID should contain periods"
    parts = sample_id.split('.')
    assert len(parts) >= 4, "Benchmark ID should have at least 4 parts"
    assert parts[0] == "MA", "Math benchmarks should start with MA"

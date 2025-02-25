"""
Tests for Excel processor functionality.
"""

import pytest
import pandas as pd
import logging
from pathlib import Path
from src.excel_processor import (
    process_excel_benchmarks,
    ExcelProcessingError,
    Benchmark,
    get_benchmark,
    save_benchmarks_pickle,
    load_benchmarks_pickle
)

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

def test_get_benchmark():
    """Test retrieving a benchmark by ID."""
    benchmarks = process_excel_benchmarks(EXCEL_PATH)
    sample_id = next(iter(benchmarks.keys()))
    
    # Test valid benchmark retrieval
    result = get_benchmark(sample_id, benchmarks)
    assert result is not None, "Should retrieve existing benchmark"
    assert result.id == sample_id, "Retrieved benchmark should match ID"
    
    # Test nonexistent benchmark
    result = get_benchmark("INVALID.ID", benchmarks)
    assert result is None, "Should return None for nonexistent benchmark"

def test_empty_excel_handling(tmp_path):
    """Test handling of empty Excel file."""
    # Create empty Excel file
    empty_file = tmp_path / "empty.xlsx"
    pd.DataFrame().to_excel(empty_file)
    
    with pytest.raises(ExcelProcessingError, match="Excel file contains no data"):
        process_excel_benchmarks(str(empty_file))

def test_missing_column_handling(tmp_path):
    """Test handling of Excel file with missing required columns."""
    # Create Excel file with missing columns
    invalid_file = tmp_path / "invalid.xlsx"
    df = pd.DataFrame({"Wrong_Column": ["test"]})
    df.to_excel(invalid_file)
    
    with pytest.raises(ExcelProcessingError, match="Excel format error: Missing column"):
        process_excel_benchmarks(str(invalid_file))

def test_logging(caplog):
    """Test that appropriate logging occurs during processing."""
    with caplog.at_level(logging.INFO):
        benchmarks = process_excel_benchmarks(EXCEL_PATH)
        
    # Check for expected log messages
    assert "Reading Excel file" in caplog.text, "Should log file reading"
    assert "Successfully processed" in caplog.text, "Should log successful processing"
    assert str(len(benchmarks)) in caplog.text, "Should log number of benchmarks"

def test_pickle_save_load(tmp_path):
    """Test saving and loading benchmarks via pickle."""
    # Process benchmarks
    benchmarks = process_excel_benchmarks(EXCEL_PATH)
    
    # Save to temporary pickle file
    pickle_path = tmp_path / "test_benchmarks.pkl"
    save_benchmarks_pickle(benchmarks, str(pickle_path))
    
    # Load from pickle file
    loaded_benchmarks = load_benchmarks_pickle(str(pickle_path))
    
    # Verify data integrity
    assert len(loaded_benchmarks) == len(benchmarks), "Should maintain same number of benchmarks"
    assert list(loaded_benchmarks.keys()) == list(benchmarks.keys()), "Should maintain same benchmark IDs"
    
    # Check a sample benchmark
    sample_id = next(iter(benchmarks.keys()))
    assert loaded_benchmarks[sample_id].definition == benchmarks[sample_id].definition, "Should maintain benchmark definitions"
    assert loaded_benchmarks[sample_id].grade_level == benchmarks[sample_id].grade_level, "Should maintain grade levels"

def test_pickle_file_not_found():
    """Test error handling when pickle file doesn't exist."""
    with pytest.raises(FileNotFoundError):
        load_benchmarks_pickle("nonexistent.pkl")

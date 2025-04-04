"""
Tests for Excel processor functionality.
Includes tests for hyperlink extraction from Excel files.
"""

import pytest
import pandas as pd
import logging
import re
import os
from pathlib import Path
from src.excel_processor import (
    process_excel_benchmarks,
    ExcelProcessingError,
    Benchmark,
    get_benchmark,
    save_benchmarks_pickle,
    load_benchmarks_pickle
)

# Get the project root directory (parent of the tests directory)
PROJECT_ROOT = Path(__file__).parent.parent
EXCEL_PATH = os.path.join(PROJECT_ROOT, "data", "raw", "BEST Math Extract.xlsx")

# Create a fixture for the benchmarks to avoid processing the Excel file multiple times
@pytest.fixture(scope="module")
def benchmarks():
    """Fixture to process Excel file once and reuse across tests."""
    if not Path(EXCEL_PATH).exists():
        pytest.skip(f"Excel file not found at {EXCEL_PATH}. Skipping Excel tests.")
    return process_excel_benchmarks(EXCEL_PATH)

def test_excel_file_exists():
    """Test that the Excel file exists in the correct location."""
    if not Path(EXCEL_PATH).exists():
        pytest.skip(f"Excel file not found at {EXCEL_PATH}. Skipping Excel tests.")
    assert True  # If we get here, the file exists

def test_process_excel_benchmarks(benchmarks):
    """Test processing of Excel file."""
    # Basic validation
    assert benchmarks, "No benchmarks were processed"
    assert isinstance(benchmarks, dict), "Benchmarks should be returned as dictionary"
    
    # Check a sample benchmark
    sample_id = next(iter(benchmarks))
    sample_benchmark = benchmarks[sample_id]
    assert isinstance(sample_benchmark, Benchmark)
    assert sample_benchmark.id == sample_id
    assert sample_benchmark.definition
    assert sample_benchmark.grade_level
    assert sample_benchmark.subject == "Mathematics"


def test_benchmark_attributes(benchmarks):
    """Test that processed benchmarks have required attributes."""
    # Get first benchmark
    sample_benchmark = next(iter(benchmarks.values()))
    
    # Check attributes
    assert hasattr(sample_benchmark, 'id')
    assert hasattr(sample_benchmark, 'definition')
    assert hasattr(sample_benchmark, 'grade_level')
    assert hasattr(sample_benchmark, 'subject')

def test_benchmark_format(benchmarks):
    """Test that benchmark IDs follow expected format."""
    # Check first benchmark ID format (e.g., MA.K.NSO.1.1)
    sample_id = next(iter(benchmarks.keys()))
    assert '.' in sample_id
    parts = sample_id.split('.')
    assert len(parts) >= 4
    assert parts[0] == "MA"

def test_get_benchmark(benchmarks):
    """Test retrieving a benchmark by ID."""
    sample_id = next(iter(benchmarks.keys()))
    
    # Test valid benchmark retrieval
    result = get_benchmark(sample_id, benchmarks)
    assert result is not None
    assert result.id == sample_id
    
    # Test nonexistent benchmark
    result = get_benchmark("INVALID.ID", benchmarks)
    assert result is None


def test_logging(caplog):
    """Test that appropriate logging occurs during processing."""
    # Set log level to INFO
    caplog.set_level(logging.INFO)
    
    # Process benchmarks directly to capture logs
    benchmarks = process_excel_benchmarks(EXCEL_PATH)
    
    # Check for expected log messages
    assert "Reading Excel file" in caplog.text
    assert "Successfully processed" in caplog.text

def test_pickle_save_load(tmp_path, benchmarks):
    """Test saving and loading benchmarks via pickle."""
    # Save to temporary pickle file
    pickle_path = tmp_path / "test_benchmarks.pkl"
    save_benchmarks_pickle(benchmarks, str(pickle_path))
    
    # Load from pickle file
    loaded_benchmarks = load_benchmarks_pickle(str(pickle_path))
    
    # Verify data integrity
    assert len(loaded_benchmarks) == len(benchmarks)
    assert list(loaded_benchmarks.keys()) == list(benchmarks.keys())
    
    # Check a sample benchmark
    sample_id = next(iter(benchmarks.keys()))
    assert loaded_benchmarks[sample_id].definition == benchmarks[sample_id].definition
    assert loaded_benchmarks[sample_id].grade_level == benchmarks[sample_id].grade_level

def test_pickle_file_not_found():
    """Test error handling when pickle file doesn't exist."""
    with pytest.raises(FileNotFoundError):
        load_benchmarks_pickle("nonexistent.pkl")

def test_url_extraction(benchmarks):
    """Test that URLs are correctly extracted from the Excel file."""
    # Check URL format for a sample of benchmarks instead of all
    sample_size = min(10, len(benchmarks))
    sample_benchmarks = dict(list(benchmarks.items())[:sample_size])
    
    # Check basic URL properties for the sample
    for benchmark_id, benchmark in sample_benchmarks.items():
        assert hasattr(benchmark, 'cpalms_url')
        assert benchmark.cpalms_url
        assert benchmark.cpalms_url.startswith("https://www.cpalms.org/PreviewStandard/Preview/")
        assert benchmark.cpalms_url.split("/")[-1].isdigit()
    
    # Check overall statistics instead of individual benchmarks
    empty_urls = sum(1 for b in benchmarks.values() if not b.cpalms_url)
    assert empty_urls == 0, f"{empty_urls} benchmarks have empty URLs"
    
    # Check URL format for all benchmarks without detailed error messages
    all_urls_valid = all(
        hasattr(b, 'cpalms_url') and 
        b.cpalms_url and 
        b.cpalms_url.startswith("https://www.cpalms.org/PreviewStandard/Preview/") and
        b.cpalms_url.split("/")[-1].isdigit()
        for b in benchmarks.values()
    )
    assert all_urls_valid, "Some benchmarks have invalid URLs"

def test_key_benchmarks(benchmarks):
    """Test that key benchmarks from different sections have valid URLs."""
    # List of key benchmarks from different sections
    key_benchmarks = [
        "MA.K.AR.1.1",       # Kindergarten section
        "MA.5.NSO.1.3",      # Grade 5 section
        "MA.912.AR.1.9",     # High school section
        "MA.912.T.4.7"        # Last benchmark in the file
    ]
    
    # Check each key benchmark
    for benchmark_id in key_benchmarks:
        if benchmark_id not in benchmarks:
            continue  # Skip if benchmark doesn't exist
            
        benchmark = benchmarks[benchmark_id]
        # Verify the benchmark has a valid CPALMS URL
        assert benchmark.cpalms_url
        assert benchmark.cpalms_url.startswith("https://www.cpalms.org/PreviewStandard/Preview/")
        assert benchmark.cpalms_url.split("/")[-1].isdigit()

def test_url_uniqueness(benchmarks):
    """Test that each benchmark has a unique URL and no 'Click Here' placeholders remain."""
    # Check for 'Click Here' placeholders (count instead of individual messages)
    click_here_count = sum(1 for b in benchmarks.values() if b.cpalms_url == "Click Here")
    assert click_here_count == 0, f"{click_here_count} benchmarks still have 'Click Here' placeholders"
    
    # Check URL uniqueness
    urls = [b.cpalms_url for b in benchmarks.values()]
    unique_urls = set(urls)
    
    # The number of unique URLs should match the number of benchmarks
    assert len(unique_urls) == len(benchmarks)
    
    # Additional check: verify total count matches expected
    assert len(benchmarks) == 642

"""
Excel processor for FL DOE Standards benchmarks.
Handles reading and processing of benchmark definitions from Excel source.
Provides functionality to save/load processed benchmarks via pickle.
"""

import pandas as pd
import pickle
import openpyxl
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import logging
import re
from dataclasses import dataclass

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class Benchmark:
    """Represents a benchmark definition and metadata."""
    id: str
    definition: str
    grade_level: str
    subject: str = "Mathematics"
    cpalms_url: str = ""

class ExcelProcessingError(Exception):
    """Custom exception for Excel processing errors."""
    pass

def extract_hyperlinks_from_excel(sheet, header_row: int, df: pd.DataFrame) -> Dict[str, str]:
    """
    Extract hyperlinks from Excel worksheet using benchmark IDs as keys.
    This approach completely decouples Excel row structure from DataFrame structure.
    
    Args:
        sheet: Excel worksheet
        header_row: Row number (1-indexed) containing column headers
        df: DataFrame containing benchmark data
        
    Returns:
        Dictionary mapping benchmark IDs to their hyperlink URLs
    """
    try:
        # Find the column indices for Benchmark ID and Direct Link
        benchmark_col = None
        link_col = None
        
        # Find the column indices
        for col in range(1, sheet.max_column + 1):
            cell_value = sheet.cell(row=header_row, column=col).value
            if cell_value:
                if 'Benchmark' in str(cell_value):
                    benchmark_col = col
                elif 'Direct Link' in str(cell_value):
                    link_col = col
        
        if not benchmark_col or not link_col:
            logger.warning(f"Could not find required columns. Benchmark col: {benchmark_col}, Link col: {link_col}")
            return {}
        
        # Dictionary to store all hyperlinks keyed by benchmark ID
        hyperlinks = {}
        
        # Dictionary to track the last seen benchmark ID for handling merged cells
        last_benchmark_id = None
        
        # Process ALL rows in the Excel file
        logger.info(f"Processing {sheet.max_row - header_row} rows in Excel file")
        
        # First pass: collect all benchmark IDs and their hyperlinks
        for row_idx in range(header_row + 1, sheet.max_row + 1):
            # Get the benchmark ID from this row
            benchmark_cell = sheet.cell(row=row_idx, column=benchmark_col)
            benchmark_id = benchmark_cell.value
            
            # If empty, use the last seen benchmark ID (for merged cells)
            if not benchmark_id and last_benchmark_id:
                benchmark_id = last_benchmark_id
            elif benchmark_id:
                # Update the last seen benchmark ID
                last_benchmark_id = benchmark_id
                
            # Skip if we couldn't determine the benchmark ID
            if not benchmark_id:
                continue
                
            # Convert to string and clean up
            benchmark_id = str(benchmark_id).strip()
            
            # Get the hyperlink from this row
            link_cell = sheet.cell(row=row_idx, column=link_col)
            
            # If the cell has a hyperlink, store it
            if hasattr(link_cell, 'hyperlink') and link_cell.hyperlink:
                hyperlinks[benchmark_id] = link_cell.hyperlink.target
        
        # Get all unique benchmark IDs in the DataFrame
        df_benchmark_ids = set(df['Benchmark#'].dropna().astype(str).str.strip())
        
        # Check for benchmark IDs in DataFrame but not in hyperlinks
        missing_in_hyperlinks = df_benchmark_ids - set(hyperlinks.keys())
        if missing_in_hyperlinks:
            logger.warning(f"Found {len(missing_in_hyperlinks)} benchmark IDs in DataFrame but not in hyperlinks")
            if len(missing_in_hyperlinks) < 10:
                logger.warning(f"Missing benchmark IDs: {', '.join(list(missing_in_hyperlinks))}")
        
        logger.info(f"Found {len(hyperlinks)} hyperlinks in Excel file")
        return hyperlinks
        
    except Exception as e:
        logger.error(f"Error extracting hyperlinks from Excel: {e}")
        return {}

def is_valid_url(url: str) -> bool:
    """
    Check if a string looks like a valid URL.
    
    Args:
        url: String to check
        
    Returns:
        True if the string looks like a URL, False otherwise
    """
    if not url:
        return False
    
    # Check if it starts with http:// or https://
    if url.startswith(('http://', 'https://')):
        return True
    
    # Check if it looks like a URL (contains domain-like pattern)
    url_pattern = re.compile(r'^(www\.)?[a-zA-Z0-9][-a-zA-Z0-9.]*\.[a-zA-Z]{2,}(/.*)?$')
    return bool(url_pattern.match(url))

def process_excel_benchmarks(file_path: str) -> Dict[str, Benchmark]:
    """
    Process BEST Math Extract Excel file into benchmark dictionary.
    
    Args:
        file_path: Path to the Excel file containing benchmark definitions
        
    Returns:
        Dictionary mapping benchmark IDs to Benchmark objects
        
    Raises:
        ExcelProcessingError: If there's an error reading or processing the Excel file
        FileNotFoundError: If the Excel file doesn't exist
    """
    try:
        # Convert string path to Path object
        excel_path = Path(file_path)
        
        if not excel_path.exists():
            raise FileNotFoundError(f"Excel file not found: {file_path}")
            
        logger.info(f"Reading Excel file: {file_path}")
        
        # Load workbook with openpyxl to access hyperlinks
        wb = openpyxl.load_workbook(str(excel_path), data_only=True)
        sheet = wb.active
        
        # Skip the first two rows and use the third row as column names
        df = pd.read_excel(excel_path, skiprows=2)
        
        # Find the column index for "Direct Link"
        direct_link_col = None
        for i, col_name in enumerate(df.columns):
            if col_name == "Direct Link":
                direct_link_col = i + 1  # +1 because openpyxl is 1-indexed
                logger.info(f"Found 'Direct Link' column at index {direct_link_col}")
                break
                
        if direct_link_col is None:
            logger.warning("Could not find 'Direct Link' column in Excel file")
        
        # Initialize dictionary for benchmarks
        benchmarks: Dict[str, Benchmark] = {}
        
        # Create a mapping of benchmark IDs to their URLs using the improved approach
        benchmark_urls = extract_hyperlinks_from_excel(sheet, header_row=3, df=df)
        
        # Third pass: process benchmarks and use the collected URLs
        current_benchmark = None
        current_description = []
        current_grade = None
        
        for idx, row in df.iterrows():
            try:
                # Check if this row has a benchmark ID
                benchmark_id = row['Benchmark#']
                
                # If this is a new benchmark and we have a previous one, save it
                if pd.notna(benchmark_id) and current_benchmark is not None:
                    # Get the URL for this benchmark
                    cpalms_url = benchmark_urls.get(current_benchmark, "")
                    
                    benchmarks[current_benchmark] = Benchmark(
                        id=current_benchmark,
                        definition=' '.join(current_description).strip(),
                        grade_level=current_grade or "Unknown",
                        cpalms_url=cpalms_url
                    )
                    # Reset for the new benchmark
                    current_description = []
                
                # If this is a benchmark row, update the current benchmark
                if pd.notna(benchmark_id):
                    current_benchmark = benchmark_id.strip()
                    current_grade = row['Grade'] if pd.notna(row['Grade']) else "Unknown"
                
                # Add description text if it exists
                if pd.notna(row['Description']):
                    current_description.append(str(row['Description']).strip())
                    
            except KeyError as e:
                logger.error(f"Missing required column in row {idx}: {e}")
                raise ExcelProcessingError(f"Excel format error: Missing column {e}")
            except Exception as e:
                logger.error(f"Error processing row {idx}: {e}")
                continue
        
        # Save the last benchmark if there is one
        if current_benchmark is not None and current_description:
            # Get the URL for this benchmark
            cpalms_url = benchmark_urls.get(current_benchmark, "")
                    
            benchmarks[current_benchmark] = Benchmark(
                id=current_benchmark,
                definition=' '.join(current_description).strip(),
                grade_level=current_grade or "Unknown",
                cpalms_url=cpalms_url
            )
                
        logger.info(f"Successfully processed {len(benchmarks)} benchmarks")
        return benchmarks
        
    except pd.errors.EmptyDataError:
        logger.error("Excel file is empty")
        raise ExcelProcessingError("Excel file contains no data")
    except Exception as e:
        logger.error(f"Error processing Excel file: {e}")
        raise ExcelProcessingError(f"Failed to process Excel file: {str(e)}")

def get_benchmark(benchmark_id: str, benchmarks: Dict[str, Benchmark]) -> Optional[Benchmark]:
    """
    Retrieve a benchmark by ID.
    
    Args:
        benchmark_id: The ID of the benchmark to retrieve
        benchmarks: Dictionary of benchmarks
        
    Returns:
        Benchmark object if found, None otherwise
    """
    return benchmarks.get(benchmark_id)

def save_benchmarks_pickle(benchmarks: Dict[str, Benchmark], file_path: str = "data/processed/benchmarks.pkl"):
    """
    Save processed benchmarks to pickle file.
    
    Args:
        benchmarks: Dictionary of benchmark objects
        file_path: Path to save pickle file
        
    Raises:
        IOError: If unable to write to file
    """
    try:
        with open(file_path, 'wb') as f:
            pickle.dump(benchmarks, f)
        logger.info(f"Saved {len(benchmarks)} benchmarks to {file_path}")
    except Exception as e:
        logger.error(f"Failed to save benchmarks pickle: {e}")
        raise

def load_benchmarks_pickle(file_path: str = "data/processed/benchmarks.pkl") -> Dict[str, Benchmark]:
    """
    Load benchmarks from pickle file.
    
    Args:
        file_path: Path to pickle file
        
    Returns:
        Dictionary of benchmark objects
        
    Raises:
        FileNotFoundError: If pickle file doesn't exist
        IOError: If unable to read file
    """
    try:
        with open(file_path, 'rb') as f:
            benchmarks = pickle.load(f)
        logger.info(f"Loaded {len(benchmarks)} benchmarks from {file_path}")
        return benchmarks
    except Exception as e:
        logger.error(f"Failed to load benchmarks pickle: {e}")
        raise

if __name__ == "__main__":
    try:
        # Process Excel file
        excel_path = "data/raw/BEST Math Extract.xlsx"
        benchmarks = process_excel_benchmarks(excel_path)
        logger.info(f"Total benchmarks processed: {len(benchmarks)}")
        
        # Save to pickle file
        save_benchmarks_pickle(benchmarks)
    except Exception as e:
        logger.error(f"Failed to process benchmarks: {e}")

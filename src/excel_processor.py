"""
Excel processor for FL DOE Standards benchmarks.
Handles reading and processing of benchmark definitions from Excel source.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional
import logging
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

class ExcelProcessingError(Exception):
    """Custom exception for Excel processing errors."""
    pass

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
        df = pd.read_excel(excel_path)
        
        # Initialize dictionary for benchmarks
        benchmarks: Dict[str, Benchmark] = {}
        
        # Process each row
        for idx, row in df.iterrows():
            try:
                benchmark_id = row['Benchmark'].strip()
                benchmarks[benchmark_id] = Benchmark(
                    id=benchmark_id,
                    definition=row['Description'],
                    grade_level=row['Grade']
                )
            except KeyError as e:
                logger.error(f"Missing required column in row {idx}: {e}")
                raise ExcelProcessingError(f"Excel format error: Missing column {e}")
            except Exception as e:
                logger.error(f"Error processing row {idx}: {e}")
                continue
                
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

if __name__ == "__main__":
    # Example usage
    try:
        excel_path = "data/raw/BEST Math Extract.xlsx"
        benchmarks = process_excel_benchmarks(excel_path)
        logger.info(f"Total benchmarks processed: {len(benchmarks)}")
    except Exception as e:
        logger.error(f"Failed to process benchmarks: {e}")

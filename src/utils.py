"""
Utility functions for FL DOE Standards Chat application.
"""

import re
from typing import List, Optional, Tuple
from fuzzywuzzy import process
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
BENCHMARK_PATTERN = r'\b([A-Z]{2}\.(?:\d{1,3}|K\d{1,2}|[A-Z])\.[A-Z]{1,3}\.\d+\.\d+)\b'
FUZZY_MATCH_THRESHOLD = 80

def normalize_benchmark_format(query: str) -> Optional[str]:
    """
    Normalize user input format (replace dashes, underscores, spaces with dots).
    
    Args:
        query: User input benchmark query
        
    Returns:
        Normalized benchmark string if valid format, None otherwise
    """
    try:
        query = query.upper().strip()
        query = re.sub(r'[-_ ]', '.', query)  # Convert to dot notation
        return query if re.match(BENCHMARK_PATTERN, query) else None
    except Exception as e:
        logger.error(f"Error normalizing benchmark format: {e}")
        return None

def find_closest_benchmark(query: str, benchmark_list: List[str]) -> Tuple[Optional[str], str]:
    """
    Finds the closest matching benchmark from list using fuzzy matching.
    
    Args:
        query: The benchmark to search for
        benchmark_list: List of valid benchmarks
        
    Returns:
        Tuple of (matched_benchmark, message)
        matched_benchmark is None if no match found
    """
    try:
        normalized_benchmark = normalize_benchmark_format(query)
        
        if not normalized_benchmark:
            return None, "Invalid benchmark format."
            
        # Exact match
        if normalized_benchmark in benchmark_list:
            return normalized_benchmark, f"Exact match found for {normalized_benchmark}."
            
        # Fuzzy matching
        if benchmark_list:
            best_match, score = process.extractOne(normalized_benchmark, benchmark_list)
            if score >= FUZZY_MATCH_THRESHOLD:
                return best_match, f"Did you mean {best_match}?"
                
        return None, "No matching benchmark found."
        
    except Exception as e:
        logger.error(f"Error in benchmark matching: {e}")
        return None, f"Error processing benchmark: {str(e)}"

def format_benchmark_response(response_data: dict) -> str:
    """
    Formats the benchmark response for display.
    
    Args:
        response_data: Dictionary containing benchmark response data
        
    Returns:
        Formatted string for display
    """
    try:
        formatted_output = (
            f"**Definition:** {response_data['benchmark_code']}: {response_data['definition']}\n\n"
            f"**In Other Words:**\n{response_data['in_other_words']}\n\n"
        )

        # Handle example section
        example = response_data.get('example')
        if isinstance(example, dict) and 'problem' in example and 'solution' in example:
            formatted_output += (
                f"**Example:**\n\n"
                f"**Problem:** {example['problem']}\n\n"
                f"**Solution:** {example['solution']}\n\n"
            )
        else:
            formatted_output += f"**Example:**\n{example}\n\n"
            
        return formatted_output
        
    except Exception as e:
        logger.error(f"Error formatting response: {e}")
        return "Error: Could not format response."

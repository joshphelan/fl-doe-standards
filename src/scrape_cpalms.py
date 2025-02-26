#!/usr/bin/env python
"""
Command-line script for scraping CPALMS resources and access points.
Provides functionality to run the scraper and resume from interruptions.
"""

import argparse
import logging
import sys
import time
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd

from src.db_manager import DatabaseManager
from src.cpalms_scraper import CPALMSScraper
from src.excel_processor import process_excel_benchmarks

# Set up logging to file and console
log_dir = os.path.join("data", "processed", "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f"cpalms_scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def load_benchmarks_with_urls(excel_path: str) -> Dict[str, Dict[str, Any]]:
    """
    Load benchmarks from Excel file including CPALMS URLs.
    
    Args:
        excel_path: Path to Excel file
        
    Returns:
        Dictionary of benchmark data
    """
    try:
        # Process Excel file to get benchmarks
        benchmarks = process_excel_benchmarks(excel_path)
        
        # Convert to dictionary format expected by scraper
        result = {}
        for benchmark_id, benchmark in benchmarks.items():
            result[benchmark_id] = {
                'id': benchmark.id,
                'grade_level': benchmark.grade_level,
                'definition': benchmark.definition,
                'subject': benchmark.subject,
                'cpalms_url': getattr(benchmark, 'cpalms_url', '')
            }
            
        return result
    except Exception as e:
        logger.error(f"Error loading benchmarks from Excel: {e}")
        raise

def report_progress(total: int, successful: int, failed: int, start_time: datetime) -> None:
    """
    Report scraping progress.
    
    Args:
        total: Total number of benchmarks processed
        successful: Number of successfully processed benchmarks
        failed: Number of failed benchmarks
        start_time: Start time of scraping
    """
    duration = datetime.now() - start_time
    hours, remainder = divmod(duration.total_seconds(), 3600)
    minutes, seconds = divmod(remainder, 60)
    
    logger.info("-" * 50)
    logger.info("CPALMS Scraper Progress Report")
    logger.info("-" * 50)
    logger.info(f"Total benchmarks processed: {total}")
    success_percent = (successful/total*100) if total > 0 else 0
    failed_percent = (failed/total*100) if total > 0 else 0
    logger.info(f"Successful: {successful} ({success_percent:.1f}%)")
    logger.info(f"Failed: {failed} ({failed_percent:.1f}%)")
    logger.info(f"Duration: {int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}")
    logger.info("-" * 50)

def main():
    """Main function to run the CPALMS scraper."""
    parser = argparse.ArgumentParser(description="Scrape CPALMS resources for benchmarks")
    parser.add_argument("--excel", default="data/raw/BEST Math Extract.xlsx", help="Path to Excel file")
    parser.add_argument("--db", default="data/processed/benchmarks.db", help="Path to SQLite database")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between requests in seconds")
    parser.add_argument("--resume", action="store_true", help="Resume from last successful benchmark")
    parser.add_argument("--start-from", help="Resume from specific benchmark ID")
    parser.add_argument("--retry-failed", action="store_true", help="Retry previously failed benchmarks")
    args = parser.parse_args()
    
    start_time = datetime.now()
    
    try:
        logger.info("Starting CPALMS scraper")
        logger.info(f"Excel file: {args.excel}")
        logger.info(f"Database: {args.db}")
        logger.info(f"Delay: {args.delay} seconds")
        
        # Initialize database manager
        db_manager = DatabaseManager(args.db)
        
        # Initialize scraper
        scraper = CPALMSScraper(db_manager, args.delay)
        
        # Load benchmarks from Excel
        logger.info(f"Loading benchmarks from {args.excel}")
        benchmarks = load_benchmarks_with_urls(args.excel)
        logger.info(f"Loaded {len(benchmarks)} benchmarks")
        
        # Store benchmarks in database
        for benchmark_id, benchmark in benchmarks.items():
            db_manager.store_benchmark(
                benchmark_id=benchmark['id'],
                grade_level=benchmark['grade_level'],
                definition=benchmark['definition'],
                cpalms_url=benchmark['cpalms_url'],
                subject=benchmark.get('subject', 'Mathematics')
            )
        
        # Determine starting point
        start_from = None
        if args.start_from:
            start_from = args.start_from
            logger.info(f"Resuming from specified benchmark: {start_from}")
        elif args.resume:
            start_from = scraper.load_state()
            if start_from:
                logger.info(f"Resuming from last successful benchmark: {start_from}")
            else:
                logger.info("No saved state found, starting from beginning")
                
        # If retrying failed, get list of failed benchmarks
        if args.retry_failed:
            failed_benchmarks = {}
            for benchmark_id, benchmark in benchmarks.items():
                status = db_manager.get_scrape_status(benchmark_id)
                if status and status['status'] == 'failed':
                    failed_benchmarks[benchmark_id] = benchmark
                    
            if failed_benchmarks:
                logger.info(f"Retrying {len(failed_benchmarks)} failed benchmarks")
                benchmarks = failed_benchmarks
            else:
                logger.info("No failed benchmarks to retry")
        
        # Run scraper
        logger.info("Starting scraping process")
        total_processed, total_successful = scraper.scrape_all_benchmarks(benchmarks, start_from)
        
        # Report progress
        total_failed = total_processed - total_successful
        report_progress(total_processed, total_successful, total_failed, start_time)
        
        logger.info("Scraping complete")
        
    except KeyboardInterrupt:
        logger.warning("Scraping interrupted by user")
        # Report progress before exiting
        # We don't have exact counts here, but we can estimate from the database
        successful = len([s for s in db_manager.get_all_benchmarks() if s.get('last_updated')])
        total = len(benchmarks)
        failed = sum(1 for b_id in benchmarks if db_manager.get_scrape_status(b_id) and db_manager.get_scrape_status(b_id)['status'] == 'failed')
        report_progress(total, successful, failed, start_time)
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Error in CPALMS scraper: {e}")
        sys.exit(1)
        
    finally:
        if 'db_manager' in locals():
            db_manager.close()

if __name__ == "__main__":
    main()

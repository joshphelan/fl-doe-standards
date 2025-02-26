#!/usr/bin/env python
"""
Test script for CPALMS scraper using hardcoded benchmark data.
"""

import os
import sys
import logging
import requests
import argparse
from datetime import datetime
from bs4 import BeautifulSoup
from pathlib import Path

# Add parent directory to Python path to allow imports from src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db_manager import DatabaseManager
from src.cpalms_scraper import CPALMSScraper

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def cleanup_test_artifacts():
    """Remove test artifacts created during testing."""
    # List of files to clean up
    artifacts = [
        "data/processed/test_scrape.db",
        "data/processed/cpalms_page.html"
    ]
    
    for artifact in artifacts:
        if os.path.exists(artifact):
            try:
                os.unlink(artifact)
                logger.info(f"Removed test artifact: {artifact}")
            except Exception as e:
                logger.error(f"Failed to remove {artifact}: {e}")

def main(keep_artifacts=False):
    """
    Run a manual test of the CPALMS scraper with hardcoded data.
    
    Args:
        keep_artifacts: If True, don't delete test artifacts after test
    """
    
    # Create a test database in the processed directory
    db_path = "data/processed/test_scrape.db"
    
    # Ensure the directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Delete existing database if it exists
    if os.path.exists(db_path):
        os.unlink(db_path)
        logger.info(f"Removed existing database: {db_path}")
    
    # Initialize database
    db_manager = DatabaseManager(db_path)
    logger.info(f"Created new database: {db_path}")
    
    # Hardcoded test benchmark
    test_benchmark = {
        'id': 'MA.K.NSO.1.1',
        'grade_level': 'K',
        'definition': 'Given a group of up to 20 objects, count the number of objects in that group and represent the number of objects with a written numeral.',
        'cpalms_url': 'https://www.cpalms.org/PreviewStandard/Preview/15454'
    }
    
    # Store the benchmark in the database
    success = db_manager.store_benchmark(
        benchmark_id=test_benchmark['id'],
        grade_level=test_benchmark['grade_level'],
        definition=test_benchmark['definition'],
        cpalms_url=test_benchmark['cpalms_url']
    )
    
    if success:
        logger.info(f"Added benchmark {test_benchmark['id']} to database")
    else:
        logger.error(f"Failed to add benchmark {test_benchmark['id']} to database")
        return
    
    # Initialize scraper with a short delay to be polite to the CPALMS server
    scraper = CPALMSScraper(db_manager, delay=1.0)
    
    # Start time
    start_time = datetime.now()
    logger.info(f"Starting scraper test at {start_time}")
    
    # Scrape the benchmark
    try:
        success = scraper.scrape_benchmark(
            benchmark_id=test_benchmark['id'],
            cpalms_url=test_benchmark['cpalms_url']
        )
        
        if success:
            # Print resources found
            resources = db_manager.get_resources_by_benchmark(test_benchmark['id'])
            logger.info(f"Found {len(resources)} resources for {test_benchmark['id']}")
            for i, resource in enumerate(resources, 1):
                logger.info(f"{i}. {resource['title']} ({resource['resource_type']}): {resource['url']}")
            
            # Print access points found
            access_points = db_manager.get_access_points_by_benchmark(test_benchmark['id'])
            logger.info(f"\nFound {len(access_points)} access points for {test_benchmark['id']}")
            for i, ap in enumerate(access_points, 1):
                logger.info(f"{i}. {ap}")
                
            # Print success summary
            end_time = datetime.now()
            duration = end_time - start_time
            logger.info(f"Scraping completed successfully in {duration.total_seconds():.2f} seconds")
        else:
            logger.error(f"Failed to scrape {test_benchmark['id']}")
    except Exception as e:
        logger.error(f"An error occurred while scraping: {e}")
    finally:
        # Close database connection
        db_manager.close()
        logger.info("Database connection closed")
        
        # Print database location for inspection
        logger.info(f"Test database created at: {os.path.abspath(db_path)}")
        logger.info("You can inspect this database to view the scraped resources and access points")

def examine_html():
    """Directly examine the HTML structure of a CPALMS page."""
    # URL to examine
    url = 'https://www.cpalms.org/PreviewStandard/Preview/15454'  # MA.K.NSO.1.1
    
    logger.info(f"Examining HTML structure of {url}")
    
    try:
        # Fetch the page
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Analyze the overall structure
        logger.info("Analyzing overall HTML structure...")
        
        # Find all divs with class attributes
        divs_with_class = soup.find_all('div', class_=True)
        class_counts = {}
        for div in divs_with_class:
            for class_name in div['class']:
                class_counts[class_name] = class_counts.get(class_name, 0) + 1
        
        logger.info("Common div classes found:")
        for class_name, count in sorted(class_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            logger.info(f"  - '{class_name}': {count} occurrences")
        
        # Look for headings that might indicate resource sections
        logger.info("Headings that might indicate resource sections:")
        for heading in soup.find_all(['h1', 'h2', 'h3']):
            heading_text = heading.get_text(strip=True)
            if any(keyword in heading_text.lower() for keyword in ['resource', 'lesson', 'assessment', 'access point']):
                logger.info(f"  - {heading.name}: '{heading_text}'")
                # Look at the parent element
                parent = heading.parent
                if parent.name == 'div' and 'class' in parent.attrs:
                    logger.info(f"    Parent: <{parent.name} class='{' '.join(parent['class'])}'>")
        
        # Look for links to resources
        logger.info("Analyzing resource links...")
        resource_links = soup.find_all('a', href=lambda href: href and ('Resource' in href or 'resource' in href))
        
        if resource_links:
            logger.info(f"Found {len(resource_links)} resource links")
            # Sample a few links
            for i, link in enumerate(resource_links[:5]):
                logger.info(f"  {i+1}. <a href='{link['href']}'>{link.get_text(strip=True)}</a>")
                # Look at the parent structure
                parent = link.parent
                if parent:
                    parent_class = f" class='{' '.join(parent['class'])}'" if 'class' in parent.attrs else ''
                    logger.info(f"    Direct parent: <{parent.name}{parent_class}>")
                    grandparent = parent.parent
                    if grandparent:
                        gp_class = f" class='{' '.join(grandparent['class'])}'" if 'class' in grandparent.attrs else ''
                        logger.info(f"    Grandparent: <{grandparent.name}{gp_class}>")
        
        # Look for elements containing "Type: Lesson Plan" or similar
        logger.info("Looking for elements with resource type indicators...")
        type_elements = soup.find_all(string=lambda s: s and ('Type:' in s))
        
        if type_elements:
            logger.info(f"Found {len(type_elements)} elements with 'Type:' text")
            for i, elem in enumerate(type_elements[:5]):
                logger.info(f"  {i+1}. '{elem.strip()}'")
                # Look at the parent structure
                parent = elem.parent
                if parent:
                    parent_class = f" class='{' '.join(parent['class'])}'" if 'class' in parent.attrs else ''
                    logger.info(f"    Direct parent: <{parent.name}{parent_class}>")
                    grandparent = parent.parent
                    if grandparent:
                        gp_class = f" class='{' '.join(grandparent['class'])}'" if 'class' in grandparent.attrs else ''
                        logger.info(f"    Grandparent: <{grandparent.name}{gp_class}>")
        
        # Save HTML for inspection
        html_file = "data/processed/cpalms_page.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        logger.info(f"Saved HTML to {html_file} for inspection")
        
    except Exception as e:
        logger.error(f"Error examining HTML: {e}")

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test CPALMS scraper with hardcoded data")
    parser.add_argument("--examine-html", action="store_true", help="Run HTML examination instead of scraper test")
    parser.add_argument("--keep-artifacts", action="store_true", help="Keep test artifacts after test")
    args = parser.parse_args()
    
    try:
        # Clean up any existing test artifacts
        cleanup_test_artifacts()
        
        # Choose which function to run
        if args.examine_html:
            examine_html()  # Run HTML examination
        else:
            main(keep_artifacts=args.keep_artifacts)  # Run scraper test
    finally:
        # Clean up test artifacts unless --keep-artifacts is specified
        if not args.keep_artifacts:
            cleanup_test_artifacts()

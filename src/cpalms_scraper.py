"""
CPALMS scraper module for FL DOE Standards project.
Handles scraping of CPALMS resource links and access points.
"""

import requests
from bs4 import BeautifulSoup
import logging
import time
import json
import os
import random
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

from src.db_manager import DatabaseManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CPALMSScraper:
    """Class for scraping CPALMS resources and access points."""
    
    def __init__(self, db_manager: DatabaseManager, delay: float = 5.0):
        """
        Initialize CPALMS scraper.
        
        Args:
            db_manager: Database manager instance
            delay: Delay between requests in seconds (default: 5.0)
        """
        self.db_manager = db_manager
        self.delay = delay
        self.state_file = "data/processed/scraper_state.json"
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        
        logger.info(f"Initialized CPALMS scraper with delay of {self.delay} seconds")
    
    def _make_request_with_retry(self, url: str, max_retries: int = 3, 
                                base_delay: float = 5.0, max_delay: float = 60.0, 
                                backoff_factor: float = 2.0) -> requests.Response:
        """
        Make HTTP request with exponential backoff retry logic.
        
        Args:
            url: URL to request
            max_retries: Maximum number of retry attempts
            base_delay: Initial delay between retries in seconds
            max_delay: Maximum delay between retries in seconds
            backoff_factor: Multiplier for exponential backoff
            
        Returns:
            Response object
            
        Raises:
            Exception if all retries fail
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        retry_count = 0
        retry_status_codes = [429, 500, 502, 503, 504]  # Rate limit and server errors
        
        while True:
            try:
                response = requests.get(url, headers=headers, timeout=30)
                
                # If we get a retry-able status code, raise an exception to trigger retry
                if response.status_code in retry_status_codes:
                    response.raise_for_status()  # This will raise an HTTPError
                
                # If we get here, the request was successful
                return response
                
            except (requests.exceptions.RequestException) as e:
                retry_count += 1
                if retry_count > max_retries:
                    logger.error(f"Max retries ({max_retries}) exceeded for {url}")
                    raise
                
                # Calculate delay with exponential backoff
                delay = min(max_delay, base_delay * (backoff_factor ** (retry_count - 1)))
                # Add jitter (±10%)
                jitter = random.uniform(-0.1, 0.1) * delay
                delay += jitter
                
                logger.warning(f"Request failed: {e}. Retrying in {delay:.2f} seconds (attempt {retry_count}/{max_retries})")
                time.sleep(delay)
    
    def scrape_benchmark(self, benchmark_id: str, cpalms_url: str) -> bool:
        """
        Scrape resources and access points for a benchmark.
        Uses exponential backoff for retries on network errors.
        
        Args:
            benchmark_id: Benchmark ID
            cpalms_url: URL to CPALMS page
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Update scrape status to 'pending'
            self.db_manager.update_scrape_status(
                benchmark_id,
                'pending',
                datetime.now()
            )
            
            # Fetch the page with retry logic
            logger.info(f"Fetching {cpalms_url} for benchmark {benchmark_id}")
            response = self._make_request_with_retry(cpalms_url)
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract resources
            resources_count = self._extract_and_store_resources(soup, benchmark_id)
            
            # Extract access points
            access_points_count = self._extract_and_store_access_points(soup, benchmark_id)
            
            # Update benchmark last_updated
            self.db_manager.store_benchmark(
                benchmark_id=benchmark_id,
                grade_level="",  # This will be updated by the caller if needed
                definition="",   # This will be updated by the caller if needed
                cpalms_url=cpalms_url,
                last_updated=datetime.now()
            )
            
            # Update scrape status to 'success'
            self.db_manager.update_scrape_status(
                benchmark_id,
                'success',
                datetime.now()
            )
            
            logger.info(f"Successfully scraped {resources_count} resources and {access_points_count} access points for {benchmark_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error scraping {cpalms_url} for {benchmark_id}: {e}")
            
            # Update scrape status to 'failed'
            self.db_manager.update_scrape_status(
                benchmark_id,
                'failed',
                datetime.now(),
                str(e)
            )
            
            return False
    
    def _extract_and_store_resources(self, soup: BeautifulSoup, benchmark_id: str) -> int:
        """
        Extract resources from HTML and store in database.
        
        Args:
            soup: BeautifulSoup object
            benchmark_id: Benchmark ID
            
        Returns:
            Number of resources found
        """
        count = 0
        
        try:
            # Find all resource items (classRelatedblock divs) directly
            resource_items = soup.find_all('div', class_='classRelatedblock')
            
            if not resource_items:
                logger.info(f"No classRelatedblock divs found for benchmark {benchmark_id}")
                return 0
            
            logger.info(f"Found {len(resource_items)} classRelatedblock divs")
            
            # Process resource items
            for item in resource_items:
                # Find the link
                link = item.find('a')
                
                if not link:
                    continue
                    
                url = link.get('href', '')
                title = link.get_text(strip=True)
                
                # Skip if no URL or title
                if not url or not title:
                    continue
                
                # Remove trailing colon from title if present
                if title.endswith(':'):
                    title = title[:-1]
                    
                # Ensure URL is absolute
                if not url.startswith('http'):
                    url = f"https://www.cpalms.org{url}"
                
                # Find resource type from paragraph containing "Type:"
                resource_type = 'Other'
                type_elem = item.find(string=lambda s: s and 'Type:' in s)
                
                if type_elem:
                    type_text = type_elem.strip()
                    if 'Lesson Plan' in type_text:
                        resource_type = 'Lesson Plan'
                    elif 'Formative Assessment' in type_text:
                        resource_type = 'Formative Assessment'
                else:
                    # Fallback to determining type from URL or title
                    resource_type = self._determine_resource_type(url, title, item)
                
                # Only process lesson plans and formative assessments
                if resource_type in ['Lesson Plan', 'Formative Assessment']:
                    # Try to extract description if available
                    description = ""
                    # Look for paragraphs that don't contain "Type:"
                    for p in item.find_all('p'):
                        p_text = p.get_text(strip=True)
                        if p_text and 'Type:' not in p_text:
                            description = p_text
                            break
                    
                    logger.info(f"Found resource: {title} ({resource_type})")
                    
                    # Store in database
                    if self.db_manager.store_resource(
                        benchmark_id=benchmark_id,
                        title=title,
                        url=url,
                        resource_type=resource_type,
                        description=description
                    ):
                        count += 1
                    
        except Exception as e:
            logger.error(f"Error extracting resources for benchmark {benchmark_id}: {e}")
            
        return count
    
    def _extract_and_store_access_points(self, soup: BeautifulSoup, benchmark_id: str) -> int:
        """
        Extract access points from HTML and store in database.
        
        Args:
            soup: BeautifulSoup object
            benchmark_id: Benchmark ID
            
        Returns:
            Number of access points found
        """
        count = 0
        
        try:
            # Look for any links that might be access points
            # Access points typically have a specific format like "MA.K.NSO.1.AP.1"
            # or contain "Access Point" in the text
            potential_ap_links = soup.find_all('a', href=lambda href: href and 'AccessPoint' in href)
            
            if not potential_ap_links:
                # Try a broader approach - look for links with text that matches access point patterns
                all_links = soup.find_all('a')
                potential_ap_links = []
                
                for link in all_links:
                    text = link.get_text(strip=True)
                    # Check if the text looks like an access point ID
                    # Access points often have a similar format to benchmarks but with "AP" in them
                    if 'AP' in text and '.' in text and len(text) > 5:
                        potential_ap_links.append(link)
            
            if not potential_ap_links:
                logger.info(f"No potential access point links found for benchmark {benchmark_id}")
                return 0
            
            logger.info(f"Found {len(potential_ap_links)} potential access point links")
                
            # Process access point items
            for link in potential_ap_links:
                access_point_id = link.get_text(strip=True)
                
                # Skip if no access point ID or if it doesn't look like an access point
                if not access_point_id or 'AP' not in access_point_id:
                    continue
                
                # Remove any trailing colon from the access point ID
                if access_point_id.endswith(':'):
                    access_point_id = access_point_id[:-1]
                
                logger.info(f"Found access point: {access_point_id}")
                    
                # Store in database
                if self.db_manager.store_access_point(
                    access_point_id=access_point_id,
                    benchmark_id=benchmark_id
                ):
                    count += 1
                    
        except Exception as e:
            logger.error(f"Error extracting access points for benchmark {benchmark_id}: {e}")
            
        return count
    
    def _determine_resource_type(self, url: str, title: str, item: BeautifulSoup) -> str:
        """
        Determine the type of resource.
        
        Args:
            url: Resource URL
            title: Resource title
            item: BeautifulSoup element for the resource item
            
        Returns:
            Resource type as string ('Lesson Plan', 'Formative Assessment', or 'Other')
        """
        # Look for type indicators in URL
        if 'LessonPlan' in url or 'ResourceLesson' in url:
            return 'Lesson Plan'
        elif 'FormativeAssessment' in url or 'ResourceAssessment' in url:
            return 'Formative Assessment'
            
        # Look for type indicators in title
        if 'Lesson Plan' in title:
            return 'Lesson Plan'
        elif 'Formative Assessment' in title:
            return 'Formative Assessment'
            
        # Look for type indicator in the item
        # First check for the new structure with "Type: X" in a paragraph
        for p in item.find_all('p'):
            text = p.get_text(strip=True)
            if 'Type:' in text:
                if 'Lesson Plan' in text:
                    return 'Lesson Plan'
                elif 'Formative Assessment' in text:
                    return 'Formative Assessment'
        
        # Then check for older structure with dedicated type elements
        type_elem = (
            item.find('div', class_='resource-type') or
            item.find('span', class_='resource-type') or
            item.find('div', class_='type')
        )
        
        if type_elem:
            type_text = type_elem.get_text(strip=True)
            if 'Lesson Plan' in type_text:
                return 'Lesson Plan'
            elif 'Formative Assessment' in type_text:
                return 'Formative Assessment'
                
        # Default
        return 'Other'
    
    def save_state(self, last_processed: str) -> bool:
        """
        Save the current scraper state for resumability.
        
        Args:
            last_processed: Last successfully processed benchmark ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            state_data = {
                'last_processed': last_processed,
                'timestamp': datetime.now().isoformat()
            }
            
            # Create a temporary file first to ensure atomic write
            temp_file = f"{self.state_file}.tmp"
            with open(temp_file, 'w') as f:
                json.dump(state_data, f, indent=2)
            
            # Rename the temp file to the actual state file (atomic operation)
            os.replace(temp_file, self.state_file)
            
            logger.info(f"Saved scraper state: last processed benchmark = {last_processed}")
            return True
        except Exception as e:
            logger.error(f"Error saving scraper state: {e}")
            return False
    
    def load_state(self) -> Optional[str]:
        """
        Load the scraper state for resumability.
        
        Returns:
            Last processed benchmark ID or None if not found
        """
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                last_processed = state.get('last_processed')
                timestamp = state.get('timestamp', 'unknown')
                logger.info(f"Loaded scraper state: last processed benchmark = {last_processed} (timestamp: {timestamp})")
                return last_processed
            
            logger.info("No saved state found, starting from the beginning")
            return None
        except Exception as e:
            logger.error(f"Error loading scraper state: {e}")
            return None
    
    def scrape_all_benchmarks(self, benchmarks: Dict[str, Dict], start_from: Optional[str] = None) -> Tuple[int, int]:
        """
        Scrape resources and access points for all benchmarks.
        
        Args:
            benchmarks: Dictionary of benchmarks {benchmark_id: benchmark_data}
            start_from: Optional benchmark ID to resume from
            
        Returns:
            Tuple of (total_processed, total_successful)
        """
        total_processed = 0
        total_successful = 0
        
        # Get list of benchmarks to process
        benchmark_ids = list(benchmarks.keys())
        benchmark_ids.sort()  # Ensure consistent order
        total_benchmarks = len(benchmark_ids)
        
        # If resuming, find the start index
        start_idx = 0
        if start_from and start_from in benchmark_ids:
            start_idx = benchmark_ids.index(start_from) + 1  # Start from the next benchmark
            benchmark_ids = benchmark_ids[start_idx:]
            logger.info(f"Resuming from benchmark {start_from} ({len(benchmark_ids)} benchmarks remaining out of {total_benchmarks})")
        else:
            logger.info(f"Starting fresh scrape of {len(benchmark_ids)} benchmarks")
        
        # Process benchmarks
        for i, benchmark_id in enumerate(benchmark_ids):
            benchmark = benchmarks[benchmark_id]
            cpalms_url = benchmark.get('cpalms_url', '')
            
            if not cpalms_url:
                logger.warning(f"No CPALMS URL for benchmark {benchmark_id}, skipping")
                continue
                
            current_position = start_idx + i + 1
            logger.info(f"Processing benchmark {benchmark_id} ({current_position}/{total_benchmarks})")
            
            try:
                # Scrape benchmark
                success = self.scrape_benchmark(benchmark_id, cpalms_url)
                total_processed += 1
                
                if success:
                    total_successful += 1
                    
                    # Save state for resumability
                    if not self.save_state(benchmark_id):
                        logger.warning(f"Failed to save state after processing {benchmark_id}")
                
                # Delay between requests
                delay_time = self.delay
                # Add small jitter (±10%)
                jitter = random.uniform(-0.1, 0.1) * delay_time
                actual_delay = delay_time + jitter
                logger.info(f"Waiting {actual_delay:.2f} seconds before next request")
                time.sleep(actual_delay)
                
            except Exception as e:
                logger.error(f"Unexpected error processing benchmark {benchmark_id}: {e}")
                # Try to save state even if there was an error
                self.save_state(benchmark_id)
                
        return total_processed, total_successful

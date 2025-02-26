"""
Test module for CPALMS scraper functionality.
"""

import os
import pytest
import tempfile
import requests
from unittest.mock import patch, MagicMock
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup

from src.db_manager import DatabaseManager
from src.cpalms_scraper import CPALMSScraper

def test_database_initialization():
    """Test that the database initializes correctly."""
    # Create a path for a temporary database in the current directory
    temp_db_path = os.path.join(tempfile.gettempdir(), f"test_db_{os.getpid()}_init.db")
    db_manager = None
    try:
        db_manager = DatabaseManager(temp_db_path)
        # Check that the connection is established
        assert db_manager.conn is not None
    except Exception as e:
        pytest.fail(f"Database initialization failed: {e}")
    finally:
        # Close connection if it was opened
        if db_manager:
            db_manager.close()
        # Clean up
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)

def test_store_benchmark():
    """Test storing a benchmark in the database."""
    # Create a path for a temporary database in the current directory
    temp_db_path = os.path.join(tempfile.gettempdir(), f"test_db_{os.getpid()}_benchmark.db")
    db_manager = None
    try:
        db_manager = DatabaseManager(temp_db_path)
        
        # Store a benchmark
        success = db_manager.store_benchmark(
            benchmark_id="MA.K.NSO.1.1",
            grade_level="K",
            definition="Test definition",
            cpalms_url="https://www.cpalms.org/test"
        )
        
        # Verify it was stored
        assert success is True
        
        # Retrieve it
        benchmark = db_manager.get_benchmark("MA.K.NSO.1.1")
        
        # Verify the retrieved data
        assert benchmark is not None
        assert benchmark['id'] == "MA.K.NSO.1.1"
        assert benchmark['grade_level'] == "K"
        assert benchmark['definition'] == "Test definition"
        assert benchmark['cpalms_url'] == "https://www.cpalms.org/test"
    except Exception as e:
        pytest.fail(f"Benchmark storage test failed: {e}")
    finally:
        # Close connection if it was opened
        if db_manager:
            db_manager.close()
        # Clean up
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)

def test_store_resource():
    """Test storing a resource in the database."""
    # Create a path for a temporary database in the current directory
    temp_db_path = os.path.join(tempfile.gettempdir(), f"test_db_{os.getpid()}_resource.db")
    db_manager = None
    try:
        db_manager = DatabaseManager(temp_db_path)
        
        # First, store a benchmark (foreign key constraint)
        db_manager.store_benchmark(
            benchmark_id="MA.K.NSO.1.1",
            grade_level="K",
            definition="Test definition"
        )
        
        # Store a resource
        success = db_manager.store_resource(
            benchmark_id="MA.K.NSO.1.1",
            title="Test Resource",
            url="https://www.cpalms.org/resource/123",
            resource_type="Lesson Plan",
            description="A sample resource"
        )
        
        # Verify it was stored
        assert success is True
        
        # Retrieve it
        resources = db_manager.get_resources_by_benchmark("MA.K.NSO.1.1")
        
        # Verify the retrieved data
        assert len(resources) == 1
        assert resources[0]['title'] == "Test Resource"
        assert resources[0]['url'] == "https://www.cpalms.org/resource/123"
        assert resources[0]['resource_type'] == "Lesson Plan"
        assert resources[0]['description'] == "A sample resource"
    except Exception as e:
        pytest.fail(f"Resource storage test failed: {e}")
    finally:
        # Close connection if it was opened
        if db_manager:
            db_manager.close()
        # Clean up
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)

def test_store_access_point():
    """Test storing an access point in the database."""
    # Create a path for a temporary database in the current directory
    temp_db_path = os.path.join(tempfile.gettempdir(), f"test_db_{os.getpid()}_access_point.db")
    db_manager = None
    try:
        db_manager = DatabaseManager(temp_db_path)
        
        # First, store a benchmark (foreign key constraint)
        db_manager.store_benchmark(
            benchmark_id="MA.K.NSO.1.1",
            grade_level="K",
            definition="Test definition"
        )
        
        # Store an access point
        success = db_manager.store_access_point(
            access_point_id="MA.K.NSO.1.AP.1",
            benchmark_id="MA.K.NSO.1.1"
        )
        
        # Verify it was stored
        assert success is True
        
        # Retrieve it
        access_points = db_manager.get_access_points_by_benchmark("MA.K.NSO.1.1")
        
        # Verify the retrieved data
        assert len(access_points) == 1
        assert access_points[0] == "MA.K.NSO.1.AP.1"
    except Exception as e:
        pytest.fail(f"Access point storage test failed: {e}")
    finally:
        # Close connection if it was opened
        if db_manager:
            db_manager.close()
        # Clean up
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)

def test_scrape_status():
    """Test updating and retrieving scrape status."""
    # Create a path for a temporary database in the current directory
    temp_db_path = os.path.join(tempfile.gettempdir(), f"test_db_{os.getpid()}_status.db")
    db_manager = None
    try:
        db_manager = DatabaseManager(temp_db_path)
        
        # First, store a benchmark
        db_manager.store_benchmark(
            benchmark_id="MA.K.NSO.1.1",
            grade_level="K",
            definition="Test definition"
        )
        
        # Update scrape status
        now = datetime.now()
        success = db_manager.update_scrape_status(
            benchmark_id="MA.K.NSO.1.1",
            status="success",
            last_attempt=now
        )
        
        # Verify it was stored
        assert success is True
        
        # Retrieve it
        status = db_manager.get_scrape_status("MA.K.NSO.1.1")
        
        # Verify the retrieved data
        assert status is not None
        assert status['benchmark_id'] == "MA.K.NSO.1.1"
        assert status['status'] == "success"
        assert status['attempt_count'] == 1
        
        # Update status again to test increment
        db_manager.update_scrape_status(
            benchmark_id="MA.K.NSO.1.1",
            status="failed",
            last_attempt=now,
            error_message="Test error"
        )
        
        # Retrieve updated status
        status = db_manager.get_scrape_status("MA.K.NSO.1.1")
        
        # Verify attempt count increased
        assert status['attempt_count'] == 2
        assert status['status'] == "failed"
        assert status['error_message'] == "Test error"
    except Exception as e:
        pytest.fail(f"Scrape status test failed: {e}")
    finally:
        # Close connection if it was opened
        if db_manager:
            db_manager.close()
        # Clean up
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)

def test_scraper_state_management():
    """Test the scraper's state management (save/load state)."""
    # Create a path for a temporary database in the current directory
    temp_db_path = os.path.join(tempfile.gettempdir(), f"test_db_{os.getpid()}_state.db")
    temp_dir = tempfile.mkdtemp()
    db_manager = None
    original_dir = os.getcwd()
    
    try:
        # Move to the temp directory to create state file there
        os.chdir(temp_dir)
        
        # Create necessary subdirectories
        os.makedirs(os.path.join("data", "processed"), exist_ok=True)
        
        db_manager = DatabaseManager(temp_db_path)
        scraper = CPALMSScraper(db_manager)
        
        # Save state
        success = scraper.save_state("MA.K.NSO.1.1")
        assert success is True
        
        # Verify state file was created
        assert os.path.exists(scraper.state_file)
        
        # Load state
        loaded_state = scraper.load_state()
        assert loaded_state == "MA.K.NSO.1.1"
    except Exception as e:
        pytest.fail(f"Scraper state management test failed: {e}")
    finally:
        # Restore original directory
        os.chdir(original_dir)
        # Close connection if it was opened
        if db_manager:
            db_manager.close()
        # Clean up
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)

def test_extract_resources():
    """Test extracting resources from HTML."""
    # Create a mock HTML with resources
    html = """
    <html>
    <body>
        <div class="classRelatedblock">
            <a href="/PreviewResourceLesson/Preview/123">Test Lesson Plan</a>
            <p>This is a description</p>
            <p>Type: Lesson Plan</p>
        </div>
        <div class="classRelatedblock">
            <a href="/PreviewResourceAssessment/Preview/456">Test Assessment</a>
            <p>This is another description</p>
            <p>Type: Formative Assessment</p>
        </div>
        <div class="classRelatedblock">
            <a href="/SomeOtherResource/789">Other Resource</a>
            <p>This is not a lesson plan or assessment</p>
            <p>Type: Other</p>
        </div>
    </body>
    </html>
    """
    
    # Create a temporary database
    temp_db_path = os.path.join(tempfile.gettempdir(), f"test_db_{os.getpid()}_extract.db")
    db_manager = None
    
    try:
        db_manager = DatabaseManager(temp_db_path)
        
        # Store a benchmark
        db_manager.store_benchmark(
            benchmark_id="MA.K.NSO.1.1",
            grade_level="K",
            definition="Test definition"
        )
        
        # Create scraper
        scraper = CPALMSScraper(db_manager)
        
        # Parse HTML
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract resources
        count = scraper._extract_and_store_resources(soup, "MA.K.NSO.1.1")
        
        # Verify correct number of resources extracted (should be 2 - lesson plan and assessment)
        assert count == 2
        
        # Verify resources were stored correctly
        resources = db_manager.get_resources_by_benchmark("MA.K.NSO.1.1")
        assert len(resources) == 2
        
        # Check first resource
        assert resources[0]['title'] == "Test Lesson Plan"
        assert resources[0]['url'] == "https://www.cpalms.org/PreviewResourceLesson/Preview/123"
        assert resources[0]['resource_type'] == "Lesson Plan"
        
        # Check second resource
        assert resources[1]['title'] == "Test Assessment"
        assert resources[1]['url'] == "https://www.cpalms.org/PreviewResourceAssessment/Preview/456"
        assert resources[1]['resource_type'] == "Formative Assessment"
        
    except Exception as e:
        pytest.fail(f"Resource extraction test failed: {e}")
    finally:
        # Close connection if it was opened
        if db_manager:
            db_manager.close()
        # Clean up
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)

def test_extract_access_points():
    """Test extracting access points from HTML."""
    # Create a mock HTML with access points
    html = """
    <html>
    <body>
        <div class="section">
            <h2>Related Access Points</h2>
            <a href="/AccessPoint/123">MA.K.NSO.1.AP.1:</a>
            <a href="/AccessPoint/456">MA.K.NSO.1.AP.2:</a>
            <a href="/OtherLink/789">Not an access point</a>
        </div>
    </body>
    </html>
    """
    
    # Create a temporary database
    temp_db_path = os.path.join(tempfile.gettempdir(), f"test_db_{os.getpid()}_ap_extract.db")
    db_manager = None
    
    try:
        db_manager = DatabaseManager(temp_db_path)
        
        # Store a benchmark
        db_manager.store_benchmark(
            benchmark_id="MA.K.NSO.1.1",
            grade_level="K",
            definition="Test definition"
        )
        
        # Create scraper
        scraper = CPALMSScraper(db_manager)
        
        # Parse HTML
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract access points
        count = scraper._extract_and_store_access_points(soup, "MA.K.NSO.1.1")
        
        # Verify correct number of access points extracted (should be 2)
        assert count == 2
        
        # Verify access points were stored correctly
        access_points = db_manager.get_access_points_by_benchmark("MA.K.NSO.1.1")
        assert len(access_points) == 2
        
        # Check access points (should have trailing colons removed)
        assert "MA.K.NSO.1.AP.1" in access_points
        assert "MA.K.NSO.1.AP.2" in access_points
        
    except Exception as e:
        pytest.fail(f"Access point extraction test failed: {e}")
    finally:
        # Close connection if it was opened
        if db_manager:
            db_manager.close()
        # Clean up
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)

def test_determine_resource_type():
    """Test determining resource type from different indicators."""
    # Create a temporary database
    temp_db_path = os.path.join(tempfile.gettempdir(), f"test_db_{os.getpid()}_resource_type.db")
    db_manager = None
    
    try:
        db_manager = DatabaseManager(temp_db_path)
        scraper = CPALMSScraper(db_manager)
        
        # Test URL indicators
        assert scraper._determine_resource_type(
            "https://www.cpalms.org/PreviewResourceLesson/Preview/123", 
            "Some Title", 
            BeautifulSoup("<div></div>", 'html.parser')
        ) == "Lesson Plan"
        
        assert scraper._determine_resource_type(
            "https://www.cpalms.org/PreviewResourceAssessment/Preview/456", 
            "Some Title", 
            BeautifulSoup("<div></div>", 'html.parser')
        ) == "Formative Assessment"
        
        # Test title indicators
        assert scraper._determine_resource_type(
            "https://www.cpalms.org/Preview/789", 
            "Lesson Plan: Math Activity", 
            BeautifulSoup("<div></div>", 'html.parser')
        ) == "Lesson Plan"
        
        # Test HTML content indicators
        html = '<div><p>Type: Lesson Plan</p></div>'
        assert scraper._determine_resource_type(
            "https://www.cpalms.org/Preview/789", 
            "Some Title", 
            BeautifulSoup(html, 'html.parser')
        ) == "Lesson Plan"
        
        # Test fallback to Other
        assert scraper._determine_resource_type(
            "https://www.cpalms.org/Preview/789", 
            "Some Title", 
            BeautifulSoup("<div></div>", 'html.parser')
        ) == "Other"
        
    except Exception as e:
        pytest.fail(f"Resource type determination test failed: {e}")
    finally:
        # Close connection if it was opened
        if db_manager:
            db_manager.close()
        # Clean up
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)

@patch('requests.get')
def test_scrape_benchmark(mock_get):
    """Test scraping a benchmark."""
    # Create a mock response
    mock_response = MagicMock()
    mock_response.text = """
    <html>
    <body>
        <div class="classRelatedblock">
            <a href="/PreviewResourceLesson/Preview/123">Test Lesson Plan</a>
            <p>This is a description</p>
            <p>Type: Lesson Plan</p>
        </div>
        <div class="section">
            <h2>Related Access Points</h2>
            <a href="/AccessPoint/123">MA.K.NSO.1.AP.1:</a>
        </div>
    </body>
    </html>
    """
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response
    
    # Create a temporary database
    temp_db_path = os.path.join(tempfile.gettempdir(), f"test_db_{os.getpid()}_scrape.db")
    db_manager = None
    
    try:
        db_manager = DatabaseManager(temp_db_path)
        
        # Store a benchmark
        db_manager.store_benchmark(
            benchmark_id="MA.K.NSO.1.1",
            grade_level="K",
            definition="Test definition",
            cpalms_url="https://www.cpalms.org/PreviewStandard/Preview/15454"
        )
        
        # Create scraper
        scraper = CPALMSScraper(db_manager)
        
        # Scrape benchmark
        success = scraper.scrape_benchmark(
            "MA.K.NSO.1.1", 
            "https://www.cpalms.org/PreviewStandard/Preview/15454"
        )
        
        # Verify scraping was successful
        assert success is True
        
        # Verify resources were extracted
        resources = db_manager.get_resources_by_benchmark("MA.K.NSO.1.1")
        assert len(resources) == 1
        assert resources[0]['title'] == "Test Lesson Plan"
        
        # Verify access points were extracted
        access_points = db_manager.get_access_points_by_benchmark("MA.K.NSO.1.1")
        assert len(access_points) == 1
        assert access_points[0] == "MA.K.NSO.1.AP.1"
        
        # Verify scrape status was updated
        status = db_manager.get_scrape_status("MA.K.NSO.1.1")
        assert status['status'] == "success"
        
    except Exception as e:
        pytest.fail(f"Benchmark scraping test failed: {e}")
    finally:
        # Close connection if it was opened
        if db_manager:
            db_manager.close()
        # Clean up
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)

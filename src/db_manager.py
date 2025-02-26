"""
Database manager module for FL DOE Standards project.
Handles SQLite database operations for benchmarks, resources, and access points.
"""

import sqlite3
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manager for SQLite database operations."""
    
    def __init__(self, db_path: str = "data/processed/benchmarks.db"):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = None
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialize database
        self.initialize_database()
    
    def initialize_database(self):
        """Create database tables if they don't exist."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            cursor = self.conn.cursor()
            
            # Create benchmarks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS benchmarks (
                    id TEXT PRIMARY KEY,
                    grade_level TEXT,
                    definition TEXT,
                    subject TEXT DEFAULT 'Mathematics',
                    cpalms_url TEXT,
                    last_updated TIMESTAMP
                )
            """)
            
            # Create resources table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS resources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    benchmark_id TEXT,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL,
                    resource_type TEXT NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (benchmark_id) REFERENCES benchmarks(id)
                )
            """)
            
            # Create access points table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS access_points (
                    access_point_id TEXT PRIMARY KEY,
                    benchmark_id TEXT,
                    FOREIGN KEY (benchmark_id) REFERENCES benchmarks(id)
                )
            """)
            
            # Create scrape status table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scrape_status (
                    benchmark_id TEXT PRIMARY KEY,
                    status TEXT,
                    attempt_count INTEGER DEFAULT 0,
                    last_attempt TIMESTAMP,
                    error_message TEXT,
                    FOREIGN KEY (benchmark_id) REFERENCES benchmarks(id)
                )
            """)
            
            # Create indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_resources_benchmark_id ON resources(benchmark_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_resources_type ON resources(resource_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_access_points_benchmark_id ON access_points(benchmark_id)")
            
            self.conn.commit()
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        if not self.conn:
            self.conn = sqlite3.connect(self.db_path)
        return self.conn
    
    def store_benchmark(self, benchmark_id: str, grade_level: str, definition: str, 
                        cpalms_url: str = "", subject: str = "Mathematics", 
                        last_updated: Optional[datetime] = None) -> bool:
        """
        Store a benchmark in the database.
        
        Args:
            benchmark_id: Benchmark ID (e.g., MA.K.NSO.1.1)
            grade_level: Grade level
            definition: Benchmark definition
            cpalms_url: URL to CPALMS page
            subject: Subject area
            last_updated: Timestamp of last update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO benchmarks 
                (id, grade_level, definition, subject, cpalms_url, last_updated)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    benchmark_id, 
                    grade_level, 
                    definition, 
                    subject, 
                    cpalms_url, 
                    last_updated.isoformat() if last_updated else None
                )
            )
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error storing benchmark {benchmark_id}: {e}")
            return False
    
    def get_benchmark(self, benchmark_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a benchmark by ID.
        
        Args:
            benchmark_id: Benchmark ID
            
        Returns:
            Dictionary with benchmark data or None if not found
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT id, grade_level, definition, subject, cpalms_url, last_updated FROM benchmarks WHERE id = ?",
                (benchmark_id,)
            )
            
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'grade_level': row[1],
                    'definition': row[2],
                    'subject': row[3],
                    'cpalms_url': row[4],
                    'last_updated': row[5]
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting benchmark {benchmark_id}: {e}")
            return None
    
    def get_all_benchmarks(self) -> List[Dict[str, Any]]:
        """
        Get all benchmarks.
        
        Returns:
            List of benchmark dictionaries
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT id, grade_level, definition, subject, cpalms_url, last_updated FROM benchmarks"
            )
            
            benchmarks = []
            for row in cursor.fetchall():
                benchmarks.append({
                    'id': row[0],
                    'grade_level': row[1],
                    'definition': row[2],
                    'subject': row[3],
                    'cpalms_url': row[4],
                    'last_updated': row[5]
                })
            
            return benchmarks
            
        except Exception as e:
            logger.error(f"Error getting all benchmarks: {e}")
            return []
    
    def store_resource(self, benchmark_id: str, title: str, url: str, 
                       resource_type: str, description: str = "") -> bool:
        """
        Store a resource in the database.
        
        Args:
            benchmark_id: Associated benchmark ID
            title: Resource title
            url: Resource URL
            resource_type: Type of resource (e.g., 'Lesson Plan')
            description: Resource description
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cursor = self.conn.cursor()
            now = datetime.now().isoformat()
            
            cursor.execute(
                """
                INSERT INTO resources 
                (benchmark_id, title, url, resource_type, description, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (benchmark_id, title, url, resource_type, description, now, now)
            )
            
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error storing resource for benchmark {benchmark_id}: {e}")
            return False
    
    def get_resources_by_benchmark(self, benchmark_id: str, resource_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get resources for a benchmark.
        
        Args:
            benchmark_id: Benchmark ID
            resource_type: Optional filter by resource type
            
        Returns:
            List of resource dictionaries
        """
        try:
            cursor = self.conn.cursor()
            
            if resource_type:
                cursor.execute(
                    """
                    SELECT id, title, url, resource_type, description
                    FROM resources
                    WHERE benchmark_id = ? AND resource_type = ?
                    """,
                    (benchmark_id, resource_type)
                )
            else:
                cursor.execute(
                    """
                    SELECT id, title, url, resource_type, description
                    FROM resources
                    WHERE benchmark_id = ?
                    """,
                    (benchmark_id,)
                )
            
            resources = []
            for row in cursor.fetchall():
                resources.append({
                    'id': row[0],
                    'title': row[1],
                    'url': row[2],
                    'resource_type': row[3],
                    'description': row[4]
                })
            
            return resources
            
        except Exception as e:
            logger.error(f"Error getting resources for benchmark {benchmark_id}: {e}")
            return []
    
    def store_access_point(self, access_point_id: str, benchmark_id: str) -> bool:
        """
        Store an access point in the database.
        
        Args:
            access_point_id: Access point ID (e.g., MA.912.AR.7.AP.1)
            benchmark_id: Associated benchmark ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO access_points
                (access_point_id, benchmark_id)
                VALUES (?, ?)
                """,
                (access_point_id, benchmark_id)
            )
            
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error storing access point {access_point_id}: {e}")
            return False
    
    def get_access_points_by_benchmark(self, benchmark_id: str) -> List[str]:
        """
        Get access points for a benchmark.
        
        Args:
            benchmark_id: Benchmark ID
            
        Returns:
            List of access point IDs
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT access_point_id
                FROM access_points
                WHERE benchmark_id = ?
                """,
                (benchmark_id,)
            )
            
            return [row[0] for row in cursor.fetchall()]
            
        except Exception as e:
            logger.error(f"Error getting access points for benchmark {benchmark_id}: {e}")
            return []
    
    def update_scrape_status(self, benchmark_id: str, status: str, 
                            last_attempt: datetime, error_message: str = "") -> bool:
        """
        Update the scrape status for a benchmark.
        
        Args:
            benchmark_id: Benchmark ID
            status: Status ('success', 'failed', 'pending')
            last_attempt: Timestamp of last attempt
            error_message: Error message if status is 'failed'
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cursor = self.conn.cursor()
            
            # Check if status record exists
            cursor.execute(
                "SELECT attempt_count FROM scrape_status WHERE benchmark_id = ?",
                (benchmark_id,)
            )
            
            row = cursor.fetchone()
            attempt_count = (row[0] + 1) if row else 1
            
            # Insert or update status
            cursor.execute(
                """
                INSERT OR REPLACE INTO scrape_status
                (benchmark_id, status, attempt_count, last_attempt, error_message)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    benchmark_id, 
                    status, 
                    attempt_count, 
                    last_attempt.isoformat(), 
                    error_message
                )
            )
            
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating scrape status for {benchmark_id}: {e}")
            return False
    
    def get_scrape_status(self, benchmark_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the scrape status for a benchmark.
        
        Args:
            benchmark_id: Benchmark ID
            
        Returns:
            Dictionary with status data or None if not found
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT benchmark_id, status, attempt_count, last_attempt, error_message
                FROM scrape_status
                WHERE benchmark_id = ?
                """,
                (benchmark_id,)
            )
            
            row = cursor.fetchone()
            if row:
                return {
                    'benchmark_id': row[0],
                    'status': row[1],
                    'attempt_count': row[2],
                    'last_attempt': row[3],
                    'error_message': row[4]
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting scrape status for {benchmark_id}: {e}")
            return None
    
    def get_pending_benchmarks(self) -> List[str]:
        """
        Get benchmarks that haven't been successfully scraped.
        
        Returns:
            List of benchmark IDs that need scraping
        """
        try:
            cursor = self.conn.cursor()
            
            # Get benchmarks with no scrape status or failed status
            cursor.execute(
                """
                SELECT b.id FROM benchmarks b
                LEFT JOIN scrape_status s ON b.id = s.benchmark_id
                WHERE s.status IS NULL OR s.status = 'failed' OR s.status = 'pending'
                ORDER BY b.id
                """
            )
            
            return [row[0] for row in cursor.fetchall()]
            
        except Exception as e:
            logger.error(f"Error getting pending benchmarks: {e}")
            return []

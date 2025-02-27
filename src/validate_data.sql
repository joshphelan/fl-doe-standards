-- FL DOE Standards Data Validation Script
-- Run with: sqlite3 data/processed/benchmarks.db < src/validate_data.sql
-- Output will be displayed in the terminal

-- Enable column headers in output
.headers on
.mode column
.width 30 10 10 10 10 10

-- Set output to show more readable results
.nullvalue NULL

-- Basic Coverage and Completeness Checks
SELECT '1. BASIC COVERAGE AND COMPLETENESS CHECKS' AS '';
SELECT '----------------------------------------' AS '';

-- 1.1 Overall counts
SELECT 
    (SELECT COUNT(*) FROM benchmarks) AS total_benchmarks,
    (SELECT COUNT(*) FROM benchmarks WHERE cpalms_url IS NOT NULL AND cpalms_url != '') AS benchmarks_with_url,
    (SELECT COUNT(*) FROM scrape_status WHERE status = 'success') AS successfully_scraped,
    (SELECT COUNT(*) FROM scrape_status WHERE status = 'failed') AS failed_scrapes,
    (SELECT COUNT(*) FROM resources) AS total_resources,
    (SELECT COUNT(*) FROM access_points) AS total_access_points;

-- 1.2 Identify benchmarks without scrape attempts
SELECT '1.2 Benchmarks without scrape attempts:' AS '';
SELECT id, grade_level, definition 
FROM benchmarks 
WHERE id NOT IN (SELECT benchmark_id FROM scrape_status)
ORDER BY id
LIMIT 10;

-- 1.3 Identify benchmarks with failed scrapes
SELECT '1.3 Benchmarks with failed scrapes:' AS '';
SELECT b.id, b.grade_level, s.error_message, s.attempt_count, s.last_attempt
FROM benchmarks b
JOIN scrape_status s ON b.id = s.benchmark_id
WHERE s.status = 'failed'
ORDER BY s.last_attempt DESC
LIMIT 10;

-- 1.4 Scrape status distribution
SELECT '1.4 Scrape status distribution:' AS '';
SELECT 
    status,
    COUNT(*) AS count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM scrape_status), 2) AS percentage
FROM scrape_status
GROUP BY status
ORDER BY count DESC;

-- Resource Distribution Analysis
SELECT '' AS '';
SELECT '2. RESOURCE DISTRIBUTION ANALYSIS' AS '';
SELECT '--------------------------------' AS '';

-- 2.1 Resource distribution per benchmark (top 10 and bottom 10)
SELECT '2.1 Top 10 benchmarks by resource count:' AS '';
SELECT 
    b.id,
    COUNT(r.id) AS resource_count,
    SUM(CASE WHEN r.resource_type = 'Lesson Plan' THEN 1 ELSE 0 END) AS lesson_plans,
    SUM(CASE WHEN r.resource_type = 'Formative Assessment' THEN 1 ELSE 0 END) AS assessments
FROM benchmarks b
LEFT JOIN resources r ON b.id = r.benchmark_id
GROUP BY b.id
ORDER BY resource_count DESC
LIMIT 10;

SELECT '2.1 Bottom 10 benchmarks by resource count (with resources):' AS '';
SELECT 
    b.id,
    COUNT(r.id) AS resource_count,
    SUM(CASE WHEN r.resource_type = 'Lesson Plan' THEN 1 ELSE 0 END) AS lesson_plans,
    SUM(CASE WHEN r.resource_type = 'Formative Assessment' THEN 1 ELSE 0 END) AS assessments
FROM benchmarks b
LEFT JOIN resources r ON b.id = r.benchmark_id
GROUP BY b.id
HAVING resource_count > 0
ORDER BY resource_count ASC
LIMIT 10;

-- 2.2 Benchmarks with no resources
SELECT '2.2 Count of benchmarks with no resources:' AS '';
SELECT COUNT(*) AS benchmarks_without_resources
FROM benchmarks b
LEFT JOIN resources r ON b.id = r.benchmark_id
WHERE r.id IS NULL AND EXISTS (SELECT 1 FROM scrape_status s WHERE s.benchmark_id = b.id AND s.status = 'success');

-- 2.3 Resource type distribution
SELECT '2.3 Resource type distribution:' AS '';
SELECT 
    resource_type, 
    COUNT(*) AS count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM resources), 2) AS percentage
FROM resources
GROUP BY resource_type
ORDER BY count DESC;

-- 2.4 Resource distribution by grade level
SELECT '2.4 Resource distribution by grade level:' AS '';
SELECT 
    b.grade_level,
    COUNT(DISTINCT b.id) AS benchmark_count,
    COUNT(r.id) AS resource_count,
    ROUND(COUNT(r.id) * 1.0 / COUNT(DISTINCT b.id), 2) AS avg_resources_per_benchmark
FROM benchmarks b
LEFT JOIN resources r ON b.id = r.benchmark_id
GROUP BY b.grade_level
ORDER BY b.grade_level;

-- 2.5 Access points distribution
SELECT '2.5 Access points distribution:' AS '';
SELECT 
    COUNT(DISTINCT benchmark_id) AS benchmarks_with_access_points,
    COUNT(*) AS total_access_points,
    ROUND(COUNT(*) * 1.0 / COUNT(DISTINCT benchmark_id), 2) AS avg_access_points_per_benchmark
FROM access_points;

-- Data Quality Checks
SELECT '' AS '';
SELECT '3. DATA QUALITY CHECKS' AS '';
SELECT '---------------------' AS '';

-- 3.1 Check for NULL values in critical fields
SELECT '3.1 NULL values in critical fields:' AS '';
SELECT 
    SUM(CASE WHEN id IS NULL THEN 1 ELSE 0 END) AS null_ids,
    SUM(CASE WHEN definition IS NULL OR definition = '' THEN 1 ELSE 0 END) AS null_definitions,
    SUM(CASE WHEN grade_level IS NULL OR grade_level = '' THEN 1 ELSE 0 END) AS null_grade_levels,
    SUM(CASE WHEN cpalms_url IS NULL OR cpalms_url = '' THEN 1 ELSE 0 END) AS null_cpalms_urls
FROM benchmarks;

-- 3.2 Check for NULL values in resources
SELECT '3.2 NULL values in resources:' AS '';
SELECT 
    SUM(CASE WHEN benchmark_id IS NULL THEN 1 ELSE 0 END) AS null_benchmark_ids,
    SUM(CASE WHEN title IS NULL OR title = '' THEN 1 ELSE 0 END) AS null_titles,
    SUM(CASE WHEN url IS NULL OR url = '' THEN 1 ELSE 0 END) AS null_urls,
    SUM(CASE WHEN resource_type IS NULL OR resource_type = '' THEN 1 ELSE 0 END) AS null_types
FROM resources;

-- 3.3 Check for duplicate resources (same URL for same benchmark)
SELECT '3.3 Duplicate resources (same URL for same benchmark):' AS '';
SELECT benchmark_id, url, COUNT(*) AS count
FROM resources
GROUP BY benchmark_id, url
HAVING COUNT(*) > 1
ORDER BY count DESC
LIMIT 10;

-- 3.4 Check for duplicate resources (same title for same benchmark)
SELECT '3.4 Duplicate resources (same title for same benchmark):' AS '';
SELECT benchmark_id, title, COUNT(*) AS count
FROM resources
GROUP BY benchmark_id, title
HAVING COUNT(*) > 1
ORDER BY count DESC
LIMIT 10;

-- 3.5 Check for resources with identical URLs but different titles
SELECT '3.5 Resources with identical URLs but different titles:' AS '';
SELECT r1.id AS id1, r2.id AS id2, r1.benchmark_id, r1.title, r2.title, r1.url
FROM resources r1
JOIN resources r2 ON r1.url = r2.url AND r1.id < r2.id
ORDER BY r1.url
LIMIT 10;

-- 3.6 Check for duplicate benchmark-access point relationships
SELECT '3.6 Duplicate benchmark-access point relationships:' AS '';
SELECT benchmark_id, access_point_id, COUNT(*) AS count
FROM access_points
GROUP BY benchmark_id, access_point_id
HAVING COUNT(*) > 1
ORDER BY count DESC
LIMIT 10;

-- 3.7 Check for inconsistent scrape status (success in scrape_status but no resources)
SELECT '3.7 Benchmarks with successful scrape but no resources:' AS '';
SELECT s.benchmark_id, s.status, COUNT(r.id) AS resource_count
FROM scrape_status s
LEFT JOIN resources r ON s.benchmark_id = r.benchmark_id
WHERE s.status = 'success'
GROUP BY s.benchmark_id, s.status
HAVING COUNT(r.id) = 0
LIMIT 10;

-- Statistical Analysis
SELECT '' AS '';
SELECT '4. STATISTICAL ANALYSIS' AS '';
SELECT '----------------------' AS '';

-- 4.1 Definition length statistics
SELECT '4.1 Definition length statistics:' AS '';
SELECT 
    MIN(LENGTH(definition)) AS min_length,
    MAX(LENGTH(definition)) AS max_length,
    AVG(LENGTH(definition)) AS avg_length
FROM benchmarks;

-- 4.2 Resource description length statistics
SELECT '4.2 Resource description length statistics:' AS '';
SELECT 
    resource_type,
    COUNT(*) AS count,
    MIN(LENGTH(description)) AS min_desc_length,
    MAX(LENGTH(description)) AS max_desc_length,
    AVG(LENGTH(description)) AS avg_desc_length
FROM resources
WHERE description IS NOT NULL AND description != ''
GROUP BY resource_type;

-- 4.3 Grade level distribution
SELECT '4.3 Grade level distribution:' AS '';
SELECT 
    grade_level, 
    COUNT(*) AS benchmark_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM benchmarks), 2) AS percentage
FROM benchmarks
GROUP BY grade_level
ORDER BY grade_level;

-- 4.4 Resource count distribution
SELECT '4.4 Resource count distribution:' AS '';
WITH resource_counts AS (
    SELECT 
        b.id,
        COUNT(r.id) AS resource_count
    FROM benchmarks b
    LEFT JOIN resources r ON b.id = r.benchmark_id
    GROUP BY b.id
)
SELECT 
    resource_count,
    COUNT(*) AS benchmark_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM benchmarks), 2) AS percentage
FROM resource_counts
GROUP BY resource_count
ORDER BY resource_count;

-- Referential Integrity Checks
SELECT '' AS '';
SELECT '5. REFERENTIAL INTEGRITY CHECKS' AS '';
SELECT '------------------------------' AS '';

-- 5.1 Check for resources referencing non-existent benchmarks
SELECT '5.1 Resources referencing non-existent benchmarks:' AS '';
SELECT r.id, r.benchmark_id, r.title
FROM resources r
LEFT JOIN benchmarks b ON r.benchmark_id = b.id
WHERE b.id IS NULL
LIMIT 10;

-- 5.2 Check for access points referencing non-existent benchmarks
SELECT '5.2 Access points referencing non-existent benchmarks:' AS '';
SELECT ap.access_point_id, ap.benchmark_id
FROM access_points ap
LEFT JOIN benchmarks b ON ap.benchmark_id = b.id
WHERE b.id IS NULL
LIMIT 10;

-- 5.3 Check for scrape_status entries referencing non-existent benchmarks
SELECT '5.3 Scrape status entries referencing non-existent benchmarks:' AS '';
SELECT ss.benchmark_id, ss.status
FROM scrape_status ss
LEFT JOIN benchmarks b ON ss.benchmark_id = b.id
WHERE b.id IS NULL
LIMIT 10;

-- Summary
SELECT '' AS '';
SELECT '6. VALIDATION SUMMARY' AS '';
SELECT '--------------------' AS '';

SELECT 
    'Total benchmarks' AS metric,
    (SELECT COUNT(*) FROM benchmarks) AS value
UNION ALL
SELECT 
    'Benchmarks with CPALMS URL',
    (SELECT COUNT(*) FROM benchmarks WHERE cpalms_url IS NOT NULL AND cpalms_url != '')
UNION ALL
SELECT 
    'Successfully scraped benchmarks',
    (SELECT COUNT(*) FROM scrape_status WHERE status = 'success')
UNION ALL
SELECT 
    'Failed scrape attempts',
    (SELECT COUNT(*) FROM scrape_status WHERE status = 'failed')
UNION ALL
SELECT 
    'Total resources',
    (SELECT COUNT(*) FROM resources)
UNION ALL
SELECT 
    'Total access points',
    (SELECT COUNT(*) FROM access_points)
UNION ALL
SELECT 
    'Benchmarks with no resources',
    (SELECT COUNT(*) FROM benchmarks b
     LEFT JOIN resources r ON b.id = r.benchmark_id
     WHERE r.id IS NULL AND EXISTS (SELECT 1 FROM scrape_status s WHERE s.benchmark_id = b.id AND s.status = 'success'))
UNION ALL
SELECT 
    'Benchmarks with access points',
    (SELECT COUNT(DISTINCT benchmark_id) FROM access_points)
UNION ALL
SELECT 
    'Average resources per benchmark',
    (SELECT ROUND(COUNT(*) * 1.0 / (SELECT COUNT(*) FROM benchmarks), 2) FROM resources)
UNION ALL
SELECT 
    'Data integrity issues',
    (SELECT COUNT(*) FROM resources r LEFT JOIN benchmarks b ON r.benchmark_id = b.id WHERE b.id IS NULL) +
    (SELECT COUNT(*) FROM access_points ap LEFT JOIN benchmarks b ON ap.benchmark_id = b.id WHERE b.id IS NULL) +
    (SELECT COUNT(*) FROM scrape_status ss LEFT JOIN benchmarks b ON ss.benchmark_id = b.id WHERE b.id IS NULL);

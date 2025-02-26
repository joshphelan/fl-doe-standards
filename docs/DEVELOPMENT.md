# Development Process

## Starting a Session

### 1. Repository Status
- [ ] Check current branch (`git checkout develop`)
- [ ] Pull latest changes (`git pull`)
- [ ] Review open tasks in ROADMAP.md

### 2. Documentation Review
- [ ] Check CHANGELOG.md for previous session's progress
- [ ] Review "Next Steps" from last session
- [ ] Verify current phase in ROADMAP.md

### 3. Environment Setup
- [ ] Verify .streamlit/secrets.toml configuration
- [ ] Check requirements.txt is up to date
- [ ] Ensure data files are in correct locations

## During Development

### 1. Code Changes
- [ ] Work on one task at a time
- [ ] Follow .clinerules guidelines
- [ ] Add type hints and docstrings
- [ ] Include error handling
- [ ] Add tests for new functionality

### 2. Testing
- [ ] Run unit tests
- [ ] Test locally with `streamlit run app.py`
- [ ] Verify changes meet requirements
- [ ] Check for edge cases

### 3. Documentation
- [ ] Update docstrings for new functions
- [ ] Note any configuration changes
- [ ] Document known limitations
- [ ] Update README.md if adding features

## Ending a Session

### 1. Code Review
- [ ] Run all tests
- [ ] Check code formatting
- [ ] Verify error handling
- [ ] Review changes for security issues

### 2. Documentation Updates
- [ ] Update CHANGELOG.md with session's work
- [ ] Add any new tasks to ROADMAP.md
- [ ] Update "Next Steps" section
- [ ] Mark completed tasks

### 3. Version Control
- [ ] Stage changes (`git add .`)
- [ ] Commit with clear message
- [ ] Push to develop branch
- [ ] Verify changes in development environment

## Git Commands

### Daily Development
```bash
# Start Development
git checkout develop
git pull origin develop
git status

# Making Changes
git add filename.py  # Stage specific files
git add .           # Stage all changes
git commit -m "Clear description of changes"  # Use semicolon (;) for chaining commands in PowerShell
git push origin develop
```

### Feature Branches
```bash
# Create feature branch
git checkout develop
git checkout -b feature/name-of-feature

# Push feature branch
git push -u origin feature/name-of-feature

# Merge to develop when complete
git checkout develop
git merge feature/name-of-feature
git push origin develop
```

### Example: Repository Restructure
1. Create feature branch
   ```bash
   git checkout -b feature/repo-restructure
   ```
2. Make and test changes:
   - Move files to correct directories
   - Update .gitignore
   - Remove legacy files
   - Test functionality
3. Update documentation:
   - Add changes to CHANGELOG.md
   - Update process in DEVELOPMENT.md
   - Review ROADMAP.md progress
4. Create pull request to develop
5. After review, merge to develop

This example shows how to:
- Isolate related changes in a feature branch
- Test changes before affecting develop
- Maintain clear documentation
- Follow proper git workflow

### Updating Production
```bash
# Test in development first
git checkout develop
git pull origin develop

# Update main branch
git checkout main
git pull origin main
git merge develop
git push origin main
```

## Data Processing Workflow

### Excel to Pickle Process
1. **Initial Data Processing**
   - Excel file is processed once using `process_excel_benchmarks()`
   - Benchmark data is extracted and structured
   - Results are serialized to pickle file using `save_benchmarks_pickle()`

2. **Application Data Loading**
   - App first attempts to load from pickle file using `load_benchmarks_pickle()`
   - Only falls back to Excel processing if pickle file is missing
   - This approach significantly improves startup performance

3. **Updating Benchmark Data**
   - When Excel source data changes:
     ```bash
     # Regenerate pickle file
     python src/excel_processor.py
     ```
   - This updates the pickle file with the latest data
   - No code changes required in app.py

4. **Benefits**
   - Faster application startup
   - Reduced processing overhead
   - Excel remains source of truth
   - Simple update process

### CPALMS Scraping Process
1. **Database Setup**
   - SQLite database is used to store scraped data
   - Database schema includes tables for benchmarks, resources, and access points
   - `DatabaseManager` class handles all database operations

2. **Scraping Resources and Access Points**
   - `CPALMSScraper` class handles scraping of CPALMS website
   - Resources (lesson plans, formative assessments) are extracted from benchmark pages
   - Access points (alternative standards) are also extracted when available
   - HTML parsing is done using BeautifulSoup with robust selector fallbacks

3. **Running the Scraper**
   - For testing a single benchmark:
     ```bash
     # Run the test script
     python tests/test_cpalms_scraper_manual.py
     ```
   - For scraping all benchmarks:
     ```bash
     # Run the full scraper
     python src/scrape_cpalms.py
     ```
   - The scraper supports resuming from interruptions and retrying failed benchmarks

4. **Integrating with Application**
   - Scraped resources and access points are stored in the database
   - Application can query the database to display relevant resources for each benchmark
   - This enhances the user experience by providing additional teaching resources

## Best Practices

1. **Commit Messages**
   - Start with verb (Add, Update, Fix, Refactor)
   - Be specific but concise
   - Reference issue numbers if applicable

2. **Branch Usage**
   - `main`: Production code only
   - `develop`: Primary development branch
   - `feature/*`: Larger changes

3. **Before Pushing**
   - Run tests
   - Update documentation
   - Review changes
   - Check for sensitive data

4. **Data Management**
   - Keep Excel files in data/raw/
   - Store processed data in data/processed/
   - Use pickle for serialization of processed data
   - Document data structure changes

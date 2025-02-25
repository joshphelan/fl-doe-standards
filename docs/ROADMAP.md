# Project Roadmap

## Overview
FL DOE Standards Chat is a tool for understanding education benchmarks, serving:
- School Admins: Quick benchmark verification during observations
- Teachers: Lesson planning and benchmark understanding

## Repository Structure
```
fl-doe-standards/
├── .clinerules                # Project guidelines
├── .streamlit/
│   └── secrets.toml          # Local config
├── README.md                 # Project overview
├── app.py                    # Main Streamlit app
├── src/
│   ├── excel_processor.py    # Excel data handling
│   └── utils.py             # Shared utilities
├── tests/
│   └── test_excel.py        # Basic tests
├── data/
│   ├── raw/                 # Source files
│   └── processed/           # Generated files
└── docs/
    ├── ROADMAP.md           # Development guide
    ├── DEVELOPMENT.md       # Process documentation
    └── CHANGELOG.md         # Session history
```

## Development Phases

### Phase 1: Excel Integration (Current Priority)
Goal: Establish Excel as the source of truth for benchmark definitions

Tasks:
- [ ] Switch from PDF to Excel data source
- [ ] Add error handling and logging
- [ ] Implement basic testing
- [ ] Update documentation

Key Deliverables:
- Excel data processor
- Reliable benchmark lookups
- Error handling system
- Basic test suite

### Phase 2: CPALMS Integration
Goal: Enhance benchmark information with official resources

Tasks:
- [ ] Add SQLite database for resource links
- [ ] Create CPALMS website scraper
- [ ] Store lesson plan links
- [ ] Store assessment links
- [ ] Display resource links in UI

Key Deliverables:
- SQLite database implementation
- CPALMS data scraper
- Resource link integration

### Phase 3: Multi-Subject Support
Goal: Expand beyond Mathematics to other subjects

Tasks:
- [ ] Add Language Arts support
- [ ] Add History support
- [ ] Update UI for subject selection
- [ ] Enhance data processing for multiple subjects
- [ ] Update documentation

Key Deliverables:
- Multi-subject data handling
- Subject-specific UI elements
- Enhanced search capabilities

### Phase 4: Access Points Integration
Goal: Enable exploration of relationships between benchmarks and their corresponding access points

Tasks:
- [ ] Map benchmarks to access points
- [ ] Display benchmark/access point relationships
- [ ] Show complexity adjustments
- [ ] Provide teaching strategies

Key Deliverables:
- Access points database integration
- Relationship visualization
- Teaching strategy suggestions

## Getting Started

1. **Setup Environment**
```bash
# Clone repository
git clone [repository-url]
cd fl-doe-standards

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt
```

2. **Configure Secrets**
Create `.streamlit/secrets.toml`:
```toml
[openai]
api_key = "your-api-key"
```

3. **Run Application**
```bash
streamlit run app.py
```

## Development Guidelines

1. **Code Standards**
- Use type hints
- Add docstrings
- Include error handling
- Keep functions focused
- Write tests for new features

2. **Documentation**
- Update relevant docs when modifying features
- Keep README.md in sync with capabilities
- Maintain CHANGELOG.md entries

3. **Version Control**
- Work in develop branch
- Create feature branches for larger changes
- Test before merging to main

4. **Testing**
- Run tests before commits
- Test locally before pushing
- Verify changes in development environment

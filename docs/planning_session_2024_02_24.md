# FL DOE Standards Project Planning Session - Feb 24, 2024

## Project Overview
A chatbot to define education benchmarks. Users input a benchmark (e.g., MA.K.NSO.1.1) and receive:
- Official benchmark definition
- "In Other Words" layman's explanation
- Example problem applying the benchmark

### User Types
1. School Admins (Assistant Principals)
   - Need to quickly understand what teachers should be teaching
   - Evaluate if lessons fall within benchmark scope

2. Teachers
   - Create lesson plans according to benchmarks
   - Need clear understanding of requirements

## Project Structure
```
fl-doe-standards/
├── .clinerules                # Project guidelines & standards
├── .streamlit/
│   └── secrets.toml          # Local development only
├── README.md                 # Project overview & setup
├── app.py                    # Main Streamlit app
├── src/
│   ├── excel_processor.py    # Excel data handling
│   └── utils.py             # Shared utilities
├── tests/
│   └── test_excel.py        # Basic tests
├── data/
│   ├── raw/
│   │   └── BEST Math Extract.xlsx
│   └── processed/
└── requirements.txt
```

## .clinerules Content
```markdown
# FL DOE Standards Guidelines

## Security
- Do not expose API keys or secrets
- Keep credentials in .streamlit/secrets.toml

## Code Standards
- Use type hints
- Add docstrings for functions
- Include basic error handling
- Keep functions focused

## Project Rules
- Excel is source of truth
- Test critical functions
- Update README.md with changes
```

## Implementation Roadmap

### Phase 1: Excel Integration
Priority: HIGH
- [ ] Switch to Excel as data source
- [ ] Add error handling
- [ ] Implement basic testing

### Phase 2: CPALMS Integration
Priority: MEDIUM
- [ ] Add SQLite database for storing links
- [ ] Create scraper for CPALMS website
- [ ] Add resource links to UI

### Phase 3: Multi-Subject Support
Priority: LOW
- [ ] Add Language Arts
- [ ] Add History
- [ ] Update UI for subject selection

## Development Process

1. **Each Session**
   - Check README.md for status
   - Work on one task at a time
   - Update README.md progress

2. **Making Changes**
   - Develop in `develop` branch
   - Test changes locally
   - Update production when ready

## Next Steps
1. Create development branch
2. Set up project structure
3. Begin Excel integration

This document captures the planning session discussion and serves as a reference for project development.

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
git commit -m "Clear description of changes"
git push origin develop
```

### Feature Branches
```bash
# Create feature branch
git checkout develop
git checkout -b feature/excel-integration

# Push feature branch
git push -u origin feature/excel-integration

# Merge to develop when complete
git checkout develop
git merge feature/excel-integration
git push origin develop
```

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

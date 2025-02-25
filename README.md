# FL DOE Standards Chat

A Streamlit chatbot that helps educators understand Florida B.E.S.T. education benchmarks. Users can input a benchmark (e.g., MA.K.NSO.1.1) and receive:
- Official benchmark definition
- Plain language explanation
- Example problem for teaching

## User Types

### School Administrators
- Quick reference for classroom observations
- Verify lesson alignment with benchmarks
- Support teacher evaluation

### Teachers
- Understand benchmark requirements
- Plan lessons effectively
- Access teaching examples

## Setup

1. Clone the repository
```bash
git clone [your-repository-url]
cd fl-doe-standards
```

2. Install requirements
```bash
pip install -r requirements.txt
```

3. Configure Streamlit secrets
Create `.streamlit/secrets.toml` with:
```toml
[openai]
api_key = "your-api-key"
```

4. Run the app
```bash
streamlit run app.py
```

## Project Status

Current Features:
- Benchmark lookup and definitions
- OpenAI-powered explanations
- Example problem generation

In Development:
- Excel-based benchmark source
- CPALMS resource integration
- Multi-subject support

## Contributing

1. Create a new branch from develop
2. Make your changes
3. Test locally
4. Submit a pull request

## License

[Your chosen license]

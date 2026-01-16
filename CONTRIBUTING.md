# Contributing to Locust Web Manager

Thank you for your interest in contributing to Locust Web Manager!

## Development Setup

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/your-username/locust_app.git
   cd locust_app
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your local configuration
   ```

5. **Run the application:**
   ```bash
   streamlit run app.py
   ```

## Code Style

- Follow [PEP 8](https://pep8.org/) guidelines
- Use English for all code, comments, and documentation
- Add type hints for function signatures
- Write docstrings for public functions using Google style or NumPy style

Example:
```python
def calculate_metrics(stats: dict) -> dict:
    """Calculate performance metrics from Locust statistics.

    Args:
        stats: Dictionary containing Locust statistics

    Returns:
        Dictionary with calculated metrics including:
        - success_rate: Percentage of successful requests
        - avg_response_time: Mean response time in ms
        - max_response_time: Maximum response time in ms

    Raises:
        ValueError: If stats dictionary is invalid
    """
    # Implementation here
```

## Project Structure

```
app/
├── core/          # Core business logic
│   ├── settings.py    # Configuration management
│   ├── runner.py      # Locust subprocess handling
│   ├── data.py        # Data loading and caching
│   ├── rp_listener.py # ReportPortal integration
│   └── hooks.py      # Locust event hooks
└── ui/            # Streamlit user interface
    ├── main.py       # Application entry point
    ├── auth.py       # Authentication logic
    ├── charts.py     # Visualization components
    └── tabs/        # Feature-specific tabs
```

## Adding New Features

### UI Changes

1. Create or modify files in `app/ui/tabs/`
2. Use Streamlit components for UI elements
3. Follow existing patterns for data loading and caching
4. Test the UI locally before committing

### Core Logic Changes

1. Modify files in `app/core/`
2. Write unit tests for new functionality (if applicable)
3. Ensure backward compatibility with existing features
4. Update documentation if needed

### New Locust Tests

1. Create test files in `locustfiles/files/` or `locustfiles/libs/`
2. Inherit from `BaseLocustUser` class
3. Define `@task` decorated methods
4. Test appears automatically in UI registry

## Testing

Before submitting a pull request:

1. **Test the application:**
   ```bash
   streamlit run app.py
   ```

2. **Verify all tabs work:**
   - Run Test
   - View Reports
   - Global Dashboard
   - History Runs
   - Setup

3. **Test ReportPortal integration** (if applicable):
   - Configure RP credentials in `.env`
   - Run a test with RP enabled
   - Verify results appear in ReportPortal

## Submitting Changes

1. **Create a descriptive branch name:**
   ```bash
   git checkout -b feature/add-dashboard-filters
   # or
   git checkout -b fix/locustfile-detection
   # or
   git checkout -b docs/update-readme
   ```

2. **Write clear commit messages:**
   ```
   feat: add filtering options to dashboard

   - Add filter by test file
   - Add filter by target server
   - Update documentation
   ```

3. **Push to your fork:**
   ```bash
   git push origin feature/add-dashboard-filters
   ```

4. **Open a Pull Request:**
   - Provide a clear description of changes
   - Reference related issues (if any)
   - Include screenshots for UI changes
   - Ensure all CI checks pass

## Commit Message Guidelines

Use [Conventional Commits](https://www.conventionalcommits.org/) format:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting, etc.)
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

Examples:
```
feat(dashboard): add performance trend chart
fix(runner): handle missing locustfile gracefully
docs(readme): update installation instructions
style(ui): improve tab layout
```

## Questions or Issues?

If you encounter issues or have questions:

- Check existing [GitHub Issues](https://github.com/your-username/locust_app/issues)
- Create a new issue with detailed description
- Include steps to reproduce if reporting a bug

## Code Review Process

1. Automated checks (linting, tests) must pass
2. At least one maintainer approval required
3. Address review feedback promptly
4. Squash commits if requested by maintainers

Thank you for contributing!

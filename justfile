# dbt-contracts justfile
# Run `just` to see all available commands

# Install package in dev mode with all dependencies
install:
    uv sync

# Run tests
test *args:
    uv run pytest {{ args }}

# Run tests with coverage
test-cov:
    uv run pytest --cov=dbt_contracts --cov-report=term-missing

# Run linter
lint:
    uv run ruff check src/ tests/

# Run formatter
format:
    uv run ruff format src/ tests/

# Check formatting without modifying files
format-check:
    uv run ruff format --check src/ tests/

# Run lint + test
check: lint format-check test

# Build documentation
docs:
    uv run zensical build

# Serve documentation locally with live reload
docs-serve:
    uv run zensical serve

# Build distribution packages
build:
    uv build

# Clean build artifacts and caches
clean:
    rm -rf dist/ site/ .pytest_cache/ .ruff_cache/
    find src/ tests/ -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    find src/ tests/ -type f -name "*.pyc" -delete 2>/dev/null || true

# Run the CLI (pass arguments after --)
run *args:
    uv run dbt-contracts {{ args }}

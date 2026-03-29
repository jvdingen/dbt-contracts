# Setup

## `pip install` fails with dependency conflicts

Ensure you're using Python 3.10 or later:

```bash
python --version
```

If using uv:

```bash
uv add dbt-contracts
```

## `dbt-contracts` command not found

If you installed with `pip install --user`, make sure your user bin directory is on your PATH. Alternatively, run via `python -m dbt_contracts`.

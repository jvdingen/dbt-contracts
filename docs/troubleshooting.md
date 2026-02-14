# Troubleshooting

## Common errors

??? question "ODPS directory not found"
    Run `dbt-contracts init` first, or check the `odps_dir` path in your [configuration](configuration.md).

??? question "No ODPS product files found"
    Make sure your product files use the `.odps.yaml` extension and are inside the configured `odps_dir`.

??? question "Contract not found"
    The `contractId` in your ODPS port doesn't match the `id` field of any `.odcs.yaml` file in `odcs_dir`. Check that both UUIDs match exactly.

??? question "Invalid configuration"
    Your config file has an unrecognized key. The tool rejects typos to prevent silent misconfiguration. Check spelling against the [configuration reference](configuration.md).

??? question "Validation FAILED"
    Run `dbt-contracts validate` to see which contracts fail and why. The error messages come from `datacontract-cli`'s lint checks. Common issues:

    - Missing required fields (`id`, `version`, `status`)
    - Invalid `apiVersion`
    - Malformed schema

## Generation

??? question "Why am I prompted for every file?"
    Your contracts have changed since the last `generate` run, so every output file shows a diff. If you trust the changes, use `--yolo-mode` to auto-accept all of them:

    ```sh
    dbt-contracts generate --yolo-mode
    ```

??? question "How do I preview changes without writing files?"
    Use the `--dry-run` flag. It shows the full drift report (NEW / UNCHANGED / CHANGED with diffs) but writes nothing to disk:

    ```sh
    dbt-contracts generate --dry-run
    ```

??? question "Staging SQL has the wrong source name"
    The `source()` references in staging SQL are rewritten based on `inputContracts` on the output port. Make sure each output port's `inputContracts` list correctly references the upstream contract IDs, and that those contracts are assigned to named input ports.

??? question "No staging SQL generated"
    Staging SQL is only generated for output ports whose contract has a `schema` section with at least one table. Check that the referenced ODCS contract includes schema definitions.

## Validation

??? question "How do I run live tests against my data?"
    Use the `--live` flag. This requires your ODCS contracts to have server configuration (connection details for the data source):

    ```sh
    dbt-contracts validate --live
    ```

## Configuration

??? question "Config changes not taking effect"
    Configuration is resolved in order: explicit `--config` flag > `dbt-contracts.toml` in the current directory > `[tool.dbt-contracts]` in `pyproject.toml` > built-in defaults. A higher-priority source overrides everything below it. Use `dbt-contracts config path` to see which file is active, and `dbt-contracts config` to see the resolved values.

??? question "How do I get more detail from commands?"
    Use the `--verbose` flag for additional output during execution:

    ```sh
    dbt-contracts --verbose generate
    ```

??? question "`dbt` commands leaking into PATH"
    If running `dbt` invokes dbt-core from the dbt-contracts installation, you installed with `pipx`, which exposes all entry points from transitive dependencies. Switch to `uv tool install` which only exposes the `dbt-contracts` entry point:

    ```sh
    pipx uninstall dbt-contracts
    uv tool install dbt-contracts
    ```

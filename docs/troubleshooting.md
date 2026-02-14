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

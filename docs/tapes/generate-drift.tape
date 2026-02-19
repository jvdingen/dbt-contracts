Set Shell "bash"
Set FontSize 14
Set Width 1200
Set Height 600
Set Theme "Catppuccin Mocha"
Set TypingSpeed 50ms

Output docs/assets/gifs/generate-drift.gif

# Set up a temporary project with contracts
Hide
Type "cd $(mktemp -d) && export REPO_ROOT=${REPO_ROOT:-$(pwd)}"
Enter
Sleep 300ms
Type "dbt-contracts init --adapter duckdb"
Enter
Sleep 2s
Type "cp $REPO_ROOT/tests/fixtures/odps/generation_product.odps.yaml contracts/products/"
Enter
Sleep 300ms
Type "cp $REPO_ROOT/tests/fixtures/odcs/customer_summary.odcs.yaml contracts/schemas/"
Enter
Sleep 300ms
Type "cp $REPO_ROOT/tests/fixtures/odcs/simple_table.odcs.yaml contracts/schemas/"
Enter
Sleep 300ms
Show

# First generate — all files are NEW
Type "dbt-contracts generate --yolo-mode"
Enter
Sleep 4s

# Modify a contract to introduce a change
Type "# Add a new column to the contract"
Enter
Sleep 500ms
Type@50ms "sed -i '/last_payment_date/a\\      - name: email\\n        logicalType: string\\n        physicalType: varchar\\n        required: false\\n        description: Customer email address' contracts/schemas/customer_summary.odcs.yaml"
Enter
Sleep 1s

# Second generate — shows CHANGED diff and per-file prompt
Type "dbt-contracts generate"
Enter
Sleep 3s

# Answer the per-file prompt
Type "y"
Enter
Sleep 2s

# Show dry-run mode
Type "dbt-contracts generate --dry-run"
Enter
Sleep 3s

Sleep 1s

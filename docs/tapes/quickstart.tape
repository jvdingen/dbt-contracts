Set Shell "bash"
Set FontSize 16
Set Width 900
Set Height 600
Set Theme "Catppuccin Mocha"
Set TypingSpeed 50ms

Output docs/assets/gifs/quickstart.gif

# Set up a temporary project directory
Hide
Type "cd $(mktemp -d) && export REPO_ROOT=${REPO_ROOT:-$(pwd)}"
Enter
Sleep 500ms
Show

# Initialize the project
Type "dbt-contracts init --adapter duckdb"
Enter
Sleep 3s

# Show the scaffolded structure
Type "tree -L 2"
Enter
Sleep 2s

# Copy in sample contract files from the repo fixtures
Hide
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

# Generate dbt artifacts
Type "dbt-contracts generate --yolo-mode"
Enter
Sleep 4s

# Show generated files
Type "tree models/ sources/"
Enter
Sleep 2s

# Show a generated model
Type "cat models/staging/stg_customer_summary.sql"
Enter
Sleep 3s

Sleep 1s

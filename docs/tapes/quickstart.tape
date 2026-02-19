Set Shell "bash"
Set FontSize 14
Set Width 1200
Set Height 600
Set Theme "Catppuccin Mocha"
Set TypingSpeed 50ms

Output docs/assets/gifs/quickstart.gif

# Create a temporary project directory
Type "mkdir /tmp/my-dbt-project && cd /tmp/my-dbt-project"
Enter
Sleep 500ms

# Initialize the project
Type "dbt-contracts init --adapter duckdb"
Enter
Sleep 3s

# Show the scaffolded structure
Type "tree -L 2"
Enter
Sleep 2s

# Copy in sample contract files
Type "cp -r ~/contracts/products/* contracts/products/"
Enter
Sleep 500ms
Type "cp -r ~/contracts/schemas/* contracts/schemas/"
Enter
Sleep 500ms

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

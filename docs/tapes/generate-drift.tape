Set Shell "bash"
Set FontSize 14
Set Width 1200
Set Height 600
Set Theme "Catppuccin Mocha"
Set TypingSpeed 50ms

Output docs/assets/gifs/generate-drift.gif

# First generate — all files are NEW
Type "dbt-contracts generate --yolo-mode"
Enter
Sleep 4s

# Modify a contract to introduce a change
Type "# Add a new column to the contract"
Enter
Sleep 500ms
Type@50ms "sed -i 's/columns:/columns:\n    - name: email\n      type: varchar/' contracts/schemas/customer_summary.odcs.yaml"
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

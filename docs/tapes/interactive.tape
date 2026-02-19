Set Shell "bash"
Set FontSize 16
Set Width 900
Set Height 600
Set Theme "Catppuccin Mocha"
Set TypingSpeed 50ms

Output docs/assets/gifs/interactive.gif

# Set up a temporary project
Hide
Type "cd $(mktemp -d)"
Enter
Sleep 300ms
Type "dbt-contracts init --adapter duckdb"
Enter
Sleep 2s
Show

# Launch interactive mode
Type "dbt-contracts"
Enter
Sleep 2s

# Navigate to Configuration
Down 3
Sleep 300ms
Enter
Sleep 2s

# Select "Edit a setting"
Down
Sleep 300ms
Enter
Sleep 2s

# Select a setting and change it
Down
Sleep 300ms
Enter
Sleep 1s

# Type a new value
Type "build"
Enter
Sleep 2s

# Navigate to Exit from the main menu
Down 4
Sleep 300ms
Enter
Sleep 1s

Sleep 1s

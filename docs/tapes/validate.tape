Set Shell "bash"
Set FontSize 14
Set Width 1200
Set Height 600
Set Theme "Catppuccin Mocha"
Set TypingSpeed 50ms

Output docs/assets/gifs/validate.gif

# Validate contracts — should pass
Type "dbt-contracts validate"
Enter
Sleep 3s

# Introduce an error in a contract
Type "# Break a contract by removing a required field"
Enter
Sleep 500ms
Type@50ms "sed -i '/^kind:/d' contracts/schemas/customer_summary.odcs.yaml"
Enter
Sleep 1s

# Validate again — should show failure
Type "dbt-contracts validate"
Enter
Sleep 3s

# Fix the contract
Type@50ms "sed -i '1i kind: DataContract' contracts/schemas/customer_summary.odcs.yaml"
Enter
Sleep 1s

# Validate once more — passes again
Type "dbt-contracts validate"
Enter
Sleep 3s

Sleep 1s

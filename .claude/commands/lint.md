# Lint and Format Code

Automatically format all modified Python files with Black and fix flake8 issues.

## Instructions

1. Run `git status --porcelain` to find modified Python files
2. Run `git diff --name-only HEAD` to find uncommitted changes
3. For all modified .py files:
   - Run `python3 -m black <file>` to format
   - Run `flake8 <file>` to check for remaining issues
4. Report what was fixed and any remaining issues that need manual attention
5. If there are critical errors, explain what needs to be fixed

Focus only on files that have been modified to keep it fast.

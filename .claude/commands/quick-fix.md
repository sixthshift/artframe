# Quick Fix

Automatically fix common issues: format code, fix imports, and run type checking.

## Instructions

1. Find all Python files that have been modified:
   - Run `git status --porcelain` and `git diff --name-only HEAD`
   - Include both staged and unstaged .py files
2. Auto-fix formatting and imports:
   - Run `python3 -m black <files>` to format all modified files
   - Run `python3 -m autoflake --remove-all-unused-imports --in-place <files>` if available
3. Run type checking:
   - Run `python -m mypy <files>` on modified files
   - Report any type errors that need manual fixing
4. Run quick smoke test:
   - Run `python -m pytest tests/unit/ -x` (stop on first failure)
5. Summary report:
   - What was auto-fixed
   - Any remaining issues requiring manual intervention
   - Test results

This is your "make it work" button for quick cleanup before committing.

# Run Smart Tests

Run pytest tests intelligently based on what files you've changed.

## Instructions

1. Check `git status` and `git diff --name-only HEAD` to see what files changed
2. Determine which test files are relevant:
   - If changes are in `src/artframe/display/*`, run tests in `tests/unit/test_display.py`
   - If changes are in `src/artframe/config.py`, run tests in `tests/unit/test_config.py`
   - If unsure or multiple areas changed, run all tests in `tests/unit/`
   - For integration-level changes, run `tests/integration/`
3. Run pytest with verbose output: `python -m pytest <test_files> -v`
4. Report results clearly:
   - Number of tests passed/failed
   - Any failures with clear explanations
   - Suggestions for fixes if tests fail

Keep it fast by only running relevant tests unless explicitly asked to run all.

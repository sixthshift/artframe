# Review Changes

Perform a thorough code review of all uncommitted changes before you commit.

## Instructions

1. Run `git diff HEAD` to see all uncommitted changes (staged and unstaged)
2. Analyze the changes for:
   - **Bugs**: Logic errors, off-by-one errors, null pointer issues, race conditions
   - **Security**: SQL injection, XSS, hardcoded secrets, insecure defaults
   - **Performance**: N+1 queries, unnecessary loops, memory leaks
   - **Code quality**: Naming, complexity, duplication, missing error handling
   - **Testing**: Missing tests for new features, edge cases not covered
   - **Documentation**: Missing docstrings, unclear comments, outdated docs
3. Check alignment with project patterns:
   - Read `CLAUDE.md` and follow any project-specific guidelines
   - Ensure consistency with existing code style
4. Provide a structured review:
   - **Critical Issues**: Must fix before committing (bugs, security)
   - **Suggestions**: Nice to have improvements
   - **Positive Notes**: What was done well
5. Be specific with file:line references for each issue

Be thorough but constructive - the goal is to catch issues before they're committed.

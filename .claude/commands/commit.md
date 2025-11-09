# Commit Staged Changes

You will create a git commit for the currently staged changes.

## Instructions

1. Run `git status` to verify there are staged changes
2. Run `git diff --staged` to see what changes are staged
3. Analyze the staged changes and generate a commit message following these best practices:
   - Use conventional commit format: `type(scope): description`
   - Common types: feat, fix, chore, docs, style, refactor, test, perf
   - Keep the first line under 72 characters
   - Use imperative mood ("add" not "added" or "adds")
   - Focus on WHY the change was made, not WHAT changed
   - Be concise and clear
4. Create the commit with your generated message
5. IMPORTANT: Do NOT include "Co-Authored-By: Claude" or any AI attribution in the commit message

## Example commit messages
- `feat(display): add live preview refresh functionality`
- `fix(web): resolve flickering issue in preview updates`
- `chore: update dependencies to latest versions`
- `refactor(routes): simplify preview endpoint logic`

After committing, show the user the commit message you created.

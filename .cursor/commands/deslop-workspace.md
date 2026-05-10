# Remove AI code slop (workspace)

Do not scope this cleanup by `git diff main`. Review the current workspace
files directly (tracked and untracked), then remove AI-generated slop from
files that are actively in development.

This includes:

- Extra comments that a human would not add or that are inconsistent with the
  rest of the file.
- Extra defensive checks or try/catch blocks that are abnormal for that area
  of the codebase (especially if called by trusted/validated codepaths).
- Casts to `Any` (or equivalent type escapes) used to bypass type issues.
- Any other style that is inconsistent with nearby code.

Keep behavioral intent the same unless a slop pattern is causing incorrect
behavior.

Avoid broad refactors; focus on high-confidence slop cleanup only.

Report at the end with only a 1-3 sentence summary of what you changed.

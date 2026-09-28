---
description: Review the branch diff against main for unnecessary AI-generated complexity.
---

# Remove AI code slop (main diff)

Check the diff against `main`, and remove AI-generated slop introduced in this
branch.

This includes:

- Extra comments that a human would not add or that are inconsistent with the
  rest of the file.
- Extra defensive checks or try/catch blocks that are abnormal for that area
  of the codebase (especially if called by trusted/validated codepaths).
- Casts to `Any` (or equivalent type escapes) used to bypass type issues.
- Any other style that is inconsistent with nearby code.

Keep behavioral intent the same unless a slop pattern is causing incorrect
behavior.

Report at the end with only a 1-3 sentence summary of what you changed.

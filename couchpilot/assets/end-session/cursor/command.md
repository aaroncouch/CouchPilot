---
description: Close the active CouchPilot implementation session.
---

# End Session

Close an active task session explicitly and move it out of indexed workspace context.

## Usage

`/couch-end-session task: <kebab-case-task-id> [optional completion note]`

Example:

`/couch-end-session task: p1-04-alert-threshold-hotfix completed and merged`

## Behavior

1. Read `.session/active-session.txt`.
2. Verify active `task_id` matches requested task.
   - If mismatch, ask for confirmation before proceeding.
3. Read `state_path`, `plan_path`, `review_path`, and `history_path` from the
   active pointer (default to `.session/STATE.md`, `.session/PLAN.md`,
   `.session/REVIEW.md`, `.session/HISTORY.md` when paths are omitted).
4. Resolve current ISO8601 timestamp (use ambient system timestamp context or
   run `date -u +"%Y-%m-%dT%H:%M:%SZ"` / `date -Iseconds`; never guess or
   extrapolate).
5. Update frontmatter in `STATE.md`, `PLAN.md`, `REVIEW.md`, and `HISTORY.md`
   before closing where present:
   - `last_updated: <ISO8601 now>`
   - `last_agent: end-session`
6. Update the `STATE.md` body before closing:
   - `Status: completed`: `/couch-end-session` is the only owner of this value
   - `Next action: none`
   - preserve every other field, including concise final validation and
     changed-file context
7. Append to `.session/HISTORY.md`:

```text
- <ISO8601> [end-session] Session ended. <optional note>
```

8. Ensure `.session/archive/<task_id>/` exists, then move the active session
   artifacts (native move; no read+rewrite) into that directory:
   - `STATE.md`, `PLAN.md`, `REVIEW.md`, `HISTORY.md`
   - Do not move `.session/.gitignore`, `active-session.txt`, or `archive/`.
9. Clear active pointer by rewriting `.session/active-session.txt`:

```text
task_id: (none)
state_path: (none)
plan_path: (none)
review_path: (none)
history_path: (none)
git_ref: (none)
```

10. Never archive/discard any other session files unless the operator asks.

## File operation policy (required)

- Prefer filesystem-native move/rename operations for archiving.
- Use shell-native move commands (`mv` on POSIX, `Move-Item` on PowerShell)
  when moving session artifacts into `archive/`.
- Do not create archive files by reading session content and rewriting it to a
  new destination path.
- If metadata must be updated before close, edit the four artifacts in place,
  then move those same file objects.
- Verify move success by confirming each source path is absent and the
  destination path exists.
- If native move fails (for example, cross-device), report the blocker and ask
  before using a copy+delete fallback.

## Output

Return:
- ended task id
- archived directory path (`.session/archive/<task_id>/`)
- whether active pointer was cleared

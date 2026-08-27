# End Session

Close an active task session explicitly and move it out of indexed workspace context.

## Usage

`/end-session task: <kebab-case-task-id> [optional completion note]`

Example:

`/end-session task: p1-04-alert-threshold-hotfix completed and merged`

## Behavior

1. Read `.cursor/scratch/active-session.txt`.
2. Verify active `task_id` matches requested task.
   - If mismatch, ask for confirmation before proceeding.
3. Read `handoff_path` and `log_path` from the active pointer.
   - If only legacy `path:` exists, treat it as a monolithic session log and use
     the legacy single-file close path.
4. Update frontmatter in `current-handoff.md` and `session-log.md` before closing:
   - `last_updated: <ISO8601 now>`
   - `last_agent: end-session`
5. Update the `current-handoff.md` body before closing:
   - `Status: completed`: `/end-session` is the only owner of this value
   - `Next action: none`
   - preserve every other field, including concise final validation and
     changed-file context
6. Append iteration log entry to `session-log.md`:

```text
- <ISO8601> [end-session] Session ended. <optional note>
```

7. Move the whole session directory (native move; no read+rewrite) to:
   - `.cursor/scratch/session-archive/<session-directory-name>/`
8. Clear active pointer by rewriting `.cursor/scratch/active-session.txt`:

```text
task_id: (none)
handoff_path: (none)
log_path: (none)
path: (none)
git_ref: (none)
```

9. Never archive/discard any other session files.

## File operation policy (required)

- Prefer filesystem-native move/rename operations for archiving.
- Use shell-native move commands (`mv` on POSIX, `Move-Item` on PowerShell)
  when moving the session directory.
- Do not create archive files by reading session content and rewriting it to a
  new destination path.
- If metadata must be updated before close, edit `current-handoff.md` and
  `session-log.md` in place, then move that same directory object.
- Verify move success by confirming the source path is absent and destination
  path exists.
- If native move fails (for example, cross-device), report the blocker and ask
  before using a copy+delete fallback.

## Output

Return:
- ended task id
- archived session directory path
- whether active pointer was cleared

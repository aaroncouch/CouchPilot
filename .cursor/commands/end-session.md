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
3. Read canonical session file from active pointer.
4. Update frontmatter before closing:
   - `last_updated: <ISO8601 now>`
   - `last_agent: end-session`
   - `status: completed`
5. Append iteration log entry:

```text
- <ISO8601> [end-session] Session ended. <optional note>
```

6. Move canonical session file (native move; no read+rewrite) to:
   - `session-archive/<filename>.md`
7. Clear active pointer by rewriting `.cursor/scratch/active-session.txt`:

```text
task_id: (none)
path: (none)
git_ref: (none)
```

8. Never archive/discard any other session files.

## File operation policy (required)

- Prefer filesystem-native move/rename operations for archiving.
- Use shell-native move commands (`mv` on POSIX, `Move-Item` on PowerShell)
  when moving the canonical session file.
- Do not create archive files by reading session content and rewriting it to a
  new destination path.
- If metadata must be updated before close, edit the canonical file in place
  once, then move that same file object.
- Verify move success by confirming the source path is absent and destination
  path exists.
- If native move fails (for example, cross-device), report the blocker and ask
  before using a copy+delete fallback.

## Output

Return:
- ended task id
- archived file path
- whether active pointer was cleared

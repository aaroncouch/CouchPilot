# Begin Session

Start or switch the active task session explicitly.

## Usage

`/begin-session task: <kebab-case-task-id> <short task description>`

Example:

`/begin-session task: p1-04-alert-threshold-hotfix start new task for alert threshold bug on current branch`

## Behavior

1. Resolve current git context:
   - branch name
   - short commit SHA
2. Build canonical session path:
   - `.cursor/scratch/sessions/<task_id>__<sanitized-branch>__<short-sha>.md`
3. Ensure `.cursor/scratch/.gitignore` exists with:

```text
*
!.gitignore
```

4. Ensure `.cursor/scratch/` is ignored by the target repo:
   - If the workspace has a root `.gitignore`, add `.cursor/scratch/` only if
     an equivalent ignore is missing.
   - If there is no root `.gitignore`, create one with `.cursor/scratch/`.
   - If any `.cursor/scratch/` files are already tracked by git, report that
     blocker; `.gitignore` does not untrack existing tracked files.

5. Create the canonical session file if missing with this scaffold:

```text
---
task_id: <task_id>
started_at: <ISO8601 now>
last_updated: <ISO8601 now>
last_agent: begin-session
status: in-progress
git_ref: <branch>@<short-sha>
---

# Task
<description from command>

# Plan
(planner fills this in)

# Findings
(reviewer fills this in)

# Project notes
(agents append conventions/locations)

# Iteration log
- <ISO8601> [begin-session] Session started.
```

6. Update active pointer file:
   - `.cursor/scratch/active-session.txt`
   - contents:

```text
task_id: <task_id>
path: .cursor/scratch/sessions/<task_id>__<sanitized-branch>__<short-sha>.md
git_ref: <branch>@<short-sha>
```

7. If active pointer already references a different task, do not archive/discard
   anything automatically; just switch pointer and report the old/new paths.

## Output

Return:
- active task id
- canonical session path
- whether created or reused
- whether root `.gitignore` already ignored or now ignores `.cursor/scratch/`
- previous active session path (if switched)

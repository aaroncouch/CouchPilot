---
description: Start or resume a CouchPilot implementation session.
---

# Begin Session

Start or switch the active task session explicitly.

## Usage

`/couch-begin-session task: <kebab-case-task-id> <task context, goals, constraints, and acceptance criteria>`

`/couch-begin-session use previous task brief`

Example:

`/couch-begin-session task: p1-04-alert-threshold-hotfix fix alert threshold bug on current branch; preserve existing API; add regression coverage`

`/couch-begin-session use previous task brief`

## Behavior

1. Resolve task context:
   - If invoked as `use previous task brief`, read
     `.cursor/scratch/task-brief.md`.
   - Use its `Suggested task id` as `<task_id>` and its structured sections as
     durable task context.
   - If the brief is missing, stale, lacks a usable task id, or has open
     questions that materially change scope/safety, ask for clarification before
     creating a session.
   - Otherwise use the explicit `task: <kebab-case-task-id>` and inline context.
2. Resolve current git context:
   - branch name
   - short commit SHA
3. Build canonical session directory:
   - `.cursor/scratch/sessions/<task_id>__<sanitized-branch>__<short-sha>/`
4. Ensure `.cursor/scratch/.gitignore` exists with:

```text
*
!.gitignore
```

5. Ensure `.cursor/scratch/` is ignored by the target repo:
   - If the workspace has a root `.gitignore`, add `.cursor/scratch/` only if
     an equivalent ignore is missing.
   - If there is no root `.gitignore`, create one with `.cursor/scratch/`.
   - If any `.cursor/scratch/` files are already tracked by git, report that
     blocker; `.gitignore` does not untrack existing tracked files.

6. Create `current-handoff.md` in the session directory if missing with this
   scaffold:

```text
---
task_id: <task_id>
started_at: <ISO8601 now>
last_updated: <ISO8601 now>
last_agent: begin-session
git_ref: <branch>@<short-sha>
log_path: .cursor/scratch/sessions/<session-id>/session-log.md
---

# Current handoff

Status: planning
Status vocabulary: planning | ready-for-code | ready-for-review | needs-fix | ready-to-close | blocked | completed
Active plan: none
Next action: Hand off to /couch-planner unless the operator explicitly chooses direct coding.
Review need: normal
Recommended Model: unassigned
Complexity: unassigned
Reasoning Depth: unassigned
Scope: <one sentence task boundary>
Open risks: none
Validation: not run
Changed files: none
Log reference: session-log.md#task
```

   Every agent that writes this file preserves all fields and updates values
   only. `Status vocabulary` is written once here so the file documents its own
   allowed values even when rules do not reach a subagent.

7. Create `session-log.md` in the session directory if missing with this scaffold:

```text
---
task_id: <task_id>
started_at: <ISO8601 now>
last_updated: <ISO8601 now>
last_agent: begin-session
git_ref: <branch>@<short-sha>
handoff_path: .cursor/scratch/sessions/<session-id>/current-handoff.md
---

# Task
<task-specific context from command: goals, constraints, acceptance criteria, relevant notes>

<!-- If created from /couch-task-brief, paste the structured task brief here. -->

# Plan
(planner keeps one active implementation contract here: goal, approach, decisions, behavior slices, files, tests, risks)

# Implementation notes
(coder appends changed files, validation results, blockers, and slice completion notes)

# Findings
(reviewer fills this in)

# Project notes
(agents append durable conventions/locations)

# Iteration log
- <ISO8601> [begin-session] Session started.
```

8. Update active pointer file:
   - `.cursor/scratch/active-session.txt`
   - contents:

```text
task_id: <task_id>
handoff_path: .cursor/scratch/sessions/<session-id>/current-handoff.md
log_path: .cursor/scratch/sessions/<session-id>/session-log.md
path: .cursor/scratch/sessions/<session-id>/session-log.md
git_ref: <branch>@<short-sha>
```

`path:` is retained as a legacy compatibility alias for `log_path` while older
session prompts are phased out.

9. If active pointer already references a different task, do not archive/discard
   anything automatically; just switch pointer and report the old/new paths.

## Main conversation role

While an active task pointer exists, the main chat is a dispatcher, not a coding
agent. The `session-main-agent` rule owns that policy in full: the role
boundary, session-file discipline, and the dispatch contract. It applies because
re-enters context every turn, while this command's text is injected only once.

Do not restate it here.

## Output

Return:
- active task id
- session directory
- current handoff path
- session log path
- whether created or reused
- whether root `.gitignore` already ignored or now ignores `.cursor/scratch/`
- previous active session path (if switched)

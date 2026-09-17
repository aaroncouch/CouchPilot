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
   - If invoked as `use previous task brief`, read `.session/task-brief.md`.
   - Use its `Suggested task id` as `<task_id>` and its structured sections as
     durable task context.
   - If the brief is missing, stale, lacks a usable task id, or has open
     questions that materially change scope/safety, ask for clarification before
     creating a session.
   - Otherwise use the explicit `task: <kebab-case-task-id>` and inline context.
2. Resolve current git context:
   - branch name
   - short commit SHA
3. Resolve current ISO8601 timestamp (use ambient system timestamp context or run `date -u +"%Y-%m-%dT%H:%M:%SZ"` / `date -Iseconds`; never guess or extrapolate).
4. Ensure `.session/` exists and `.session/.gitignore` contains:

```text
*
!.gitignore
```

5. Ensure `.session/` is ignored by the target repo:
   - If the workspace has a root `.gitignore`, add `.session/` only if an
     equivalent ignore is missing.
   - If there is no root `.gitignore`, create one with `.session/`.
   - If any `.session/` files are already tracked by git, report that blocker;
     `.gitignore` does not untrack existing tracked files.

6. Create `.session/STATE.md` if missing with this scaffold:

```text
---
task_id: <task_id>
started_at: <ISO8601 now>
last_updated: <ISO8601 now>
last_agent: begin-session
git_ref: <branch>@<short-sha>
---

# Session state

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
Active review findings: none (see REVIEW.md)
Plan reference: PLAN.md#active-task
```

   Every agent that writes this file preserves all fields and updates values
   only. `Status vocabulary` is written once here so the file documents its own
   allowed values even when rules do not reach a subagent.

6. Create `.session/PLAN.md` if missing with this scaffold:

```text
---
task_id: <task_id>
started_at: <ISO8601 now>
last_updated: <ISO8601 now>
last_agent: begin-session
git_ref: <branch>@<short-sha>
---

# Task requirements

<task-specific context from command: goals, constraints, acceptance criteria, relevant notes>

<!-- If created from /couch-task-brief, paste the structured task brief here. -->

# Active task

(planner keeps one active implementation contract here: goal, approach, decisions, behavior slices, files, tests, risks)

# Queued tasks

(future slices or follow-on work; empty when single-pass)
```

7. Create `.session/REVIEW.md` if missing with this scaffold:

```text
---
task_id: <task_id>
last_updated: <ISO8601 now>
last_agent: begin-session
---

# Open findings

(none)
```

8. Create `.session/HISTORY.md` if missing with this scaffold:

```text
---
task_id: <task_id>
started_at: <ISO8601 now>
---

# History

<!-- Append-only cold storage. Subagents do not read by default. -->

- <ISO8601> [begin-session] Session started.
```

9. Update active pointer file `.session/active-session.txt`:

```text
task_id: <task_id>
state_path: .session/STATE.md
plan_path: .session/PLAN.md
review_path: .session/REVIEW.md
history_path: .session/HISTORY.md
git_ref: <branch>@<short-sha>
```

10. If active pointer already references a different task, do not archive/discard
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
- `.session/` paths (`STATE.md`, `PLAN.md`, `REVIEW.md`, `HISTORY.md`)
- whether each file was created or reused
- whether root `.gitignore` already ignored or now ignores `.session/`
- previous active session task id (if switched)

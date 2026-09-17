---
description: Transition completed task to HISTORY.md and prepare STATE.md for next task.
---

# Checkpoint

Garbage-collect active agent context: collapse a **completed** task into cold
storage, prune warm artifacts, and regenerate a compact `STATE.md` for the next
queued work. Requires an active CouchPilot session (`.session/active-session.txt`
with `task_id` not `(none)`).

## Usage

`/couch-checkpoint [optional completion note]`

`/couch-checkpoint task: <kebab-case-subtask-id> [optional completion note]`

Use the bare form when completing the current `# Active task` in `PLAN.md`. Use
`task:` when the operator names a specific subtask or slice id to close.

## Preconditions

1. Read `.session/active-session.txt` and resolve `state_path`, `plan_path`,
   `review_path`, and `history_path`.
2. If no active session, stop and tell the operator to run `/couch-begin-session`.
3. Do not modify `.session/active-session.txt` except to update `git_ref` when
   the operator asks; checkpoint does not end the session.

## State transition (10 steps)

1. **Inspect runtime state:** Read `.session/STATE.md` and the `# Active task`
   section of `.session/PLAN.md`. Confirm which task or slice is being closed
   (current active task unless `task:` overrides and matches plan content).
2. **Verify completion evidence:** Require concrete evidence before treating
   the task as done: `Validation` on `STATE.md` names commands with real output,
   reviewer verdict when review was required, or explicit operator confirmation
   in the invocation. Do **not** mark complete solely because the coder reported
   done or status says `ready-for-review` without evidence you can cite.
3. **Resolve git context:** Record current branch and short commit SHA when git
   is available; use `(unknown)` when not.
4. **Project to `HISTORY.md`:** Append one dated bullet (or compact `##` entry)
   to `.session/HISTORY.md` with real ISO8601 timestamp (from system context or
   `date`; never guessed or estimated): task/slice id, outcome, durable
   decisions, validation summary, commit SHA, and optional completion note from
   the operator.
5. **Prune `REVIEW.md`:** Remove findings explicitly resolved for this task.
   Retain every open or unresolved finding. When unsure whether a finding is
   resolved, **keep it** and ask the operator.
6. **Archive completed plan detail (optional):** When the active task body is
   large, copy the full completed `# Active task` content to
   `.session/archive/<task-or-slice-id>.md` before pruning. Never delete without
   either this archive or a concise summary already written to `HISTORY.md`.
7. **Prune `PLAN.md`:** Remove implementation detail for the completed task from
   `# Active task`. Record a one-line completed marker under `# Queued tasks` or
   a `## Completed` stub if the plan template uses one. Do not leave stale steps
   in the active section.
8. **Advance the queue:** Promote the next entry from `# Queued tasks` into
   `# Active task`. If `# Queued tasks` is empty, set `# Active task` to
   `(none — plan next work or /couch-end-session)`.
9. **Stop for ordering conflicts:** If multiple queued tasks could be next and
   order is ambiguous, stop and ask the operator which to promote. Do not guess.
10. **Regenerate `STATE.md`:** Rewrite the body (preserve frontmatter fields and
    vocabulary) with compact sections:

```markdown
# Session state

Status: <ready-for-code | planning | ready-for-review | …>
Objective: <one sentence for the session or next slice>
Current task: <title or id from promoted # Active task>
Decisions: <bullets: durable choices relevant to the next task only>
Inputs: <exact files, paths, or anchors the next agent needs>
Acceptance criteria: <bullets mapped to the new active task>
Open findings: <summary from REVIEW.md or "none">
Blockers: <none or factual blockers>
Next action: <dispatch-slice-N | dispatch-single-pass | escalate-planning | …>
```

    Mirror planner/dispatcher fields already on the file (`Active plan`, `Review
    need`, `Recommended Model`, `Complexity`, `Reasoning Depth`, `Scope`, `Open
    risks`, `Validation`, `Changed files`) and reset task-local values (`Changed
    files`, `Validation`) when starting fresh work. Set `last_updated` and
    `last_agent: checkpoint` in frontmatter on every file you touch.

## Safety rules

| Scenario | Required Action | Prohibited Shortcut |
|---|---|---|
| Missing validation evidence | Stop; list what evidence is missing | Marking the task complete because status says so |
| Unresolved review finding | Keep in `REVIEW.md`; reflect in `STATE.md` | Dropping or paraphrasing away open findings |
| Ambiguous next task | Ask the operator which queued task is next | Picking arbitrarily among eligible tasks |
| No queued work left | Regenerate `STATE.md` for idle/planning; suggest planner or end-session | Leaving old active-task prose in `PLAN.md` |
| Archive or history write fails | Stop and report; do not prune `PLAN.md` first | Deleting completed detail with no durable copy |

## Output

Return:
- completed task or slice id
- `HISTORY.md` entry summary
- count of findings retained vs removed in `REVIEW.md`
- whether plan detail was archived (path if yes)
- next active task id or `(none)`
- updated `STATE.md` status and next action

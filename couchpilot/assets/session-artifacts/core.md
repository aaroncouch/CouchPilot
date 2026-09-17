---
description: Keep CouchPilot session artifacts accurate, durable, and concise.
family: rule
---

# Session files

**Principle:** History is storage. `STATE.md` is context.

**Inert unless a session is active.** If `.session/active-session.txt` does not
exist, or its `task_id` is `(none)`, ignore this rule.

This rule applies to every agent that reads or writes active session artifacts.
Scoping it to a particular host or workflow role would leave other writers
unguarded.

## `.session/` layout

Shared session state lives at the project root under `.session/` (ignored by git
via `.session/.gitignore`).

| File | Temperature | Role |
|---|---|---|
| `STATE.md` | Hot | Authoritative runtime read model (~300–800 tokens): active objective, current task, relevant decisions, file inputs, acceptance criteria, blockers, open review summary, next action |
| `PLAN.md` | Warm | Live workstream: task requirements, **active task only**, and **queued** tasks. Completed tasks leave `PLAN.md` |
| `REVIEW.md` | Warm | Unresolved, actionable review findings only. Resolved findings leave `REVIEW.md` |
| `HISTORY.md` | Cold | Append-only audit trail: completed outcomes, durable decisions, commit SHAs |
| `archive/` | Cold | Optional detailed records for ended sessions |
| `active-session.txt` | Pointer | Paths to the four artifacts above; only session-start/end workflows write it |
| `task-brief.md` | Staging | Optional pre-session brief from `/couch-task-brief` |

## Read order

- **`STATE.md` is read-first truth.** Read `.session/active-session.txt`, then
  `STATE.md`, before acting on session state.
- Read `PLAN.md` only for the **active task section** (and queued tasks when
  planning), not the whole file when a dispatch names a section anchor.
- Read `REVIEW.md` only for **open** findings relevant to the current task.
- **Subagents must NOT read `HISTORY.md`** unless the operator explicitly
  directs them to. Cold history must not bloat subagent context.
- The main conversation may read `HISTORY.md` when the operator asks for history
  or audit detail.

## Write rules

- Keep `STATE.md` compact; mirror status fields the handoff workflow expects
  (`Status`, `Next action`, `Review need`, `Recommended Model`, `Complexity`,
  `Reasoning Depth`, `Scope`, `Open risks`, `Validation`, `Changed files`).
  Preserve every field already present and update values only.
- Planner-owned execution fields start as `unassigned` at session creation and
  are filled from **## Execution Recommendation** in `PLAN.md` after planning.
- `PLAN.md` holds implementation contracts only for active and queued work.
  Do not append iteration narratives or resolved review threads to `PLAN.md`.
- `REVIEW.md` holds open findings with file:line anchors and severity. Remove
  or archive resolved items; do not grow a permanent findings log in `REVIEW.md`.
- Append dated entries to `HISTORY.md` for completed slices, durable decisions,
  and commit SHAs using real ISO8601 timestamps (from system context or `date`
  command; never estimated or guessed). Do not duplicate hot runtime fields
  into `HISTORY.md` unless they are durable audit facts.
- When writing ISO8601 timestamps (`started_at`, `last_updated`, `HISTORY.md`),
  resolve current time from ambient system timestamp context or by running
  `date -u +"%Y-%m-%dT%H:%M:%SZ"` (or `date -Iseconds`). Never guess or
  extrapolate elapsed time.
- Only the session-start and session-end workflows write
  `.session/active-session.txt`. Nothing else modifies the pointer.

Rule id: sf-1

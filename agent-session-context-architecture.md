# Context-Efficient Agent Session Architecture

## Purpose

This document describes a durable, auditable session workflow for an orchestrator that delegates planning, implementation, and review work to fresh subagents without forcing each subagent to consume the entire session history.

The core principle is:

> **History is storage. `STATE.md` is context.**

The durable session record and the active runtime context have different jobs and should be separate artifacts.

## The Problem

A single shared session log is useful for preserving:

- the overall objective;
- implementation plans;
- decisions and their rationale;
- completed work;
- review findings;
- blockers; and
- a historical task record.

However, that same file becomes a poor runtime input as it grows. If every fresh subagent reads the entire artifact, old plans, completed work, superseded decisions, resolved findings, and prior execution details immediately consume its new context window.

The issue is not merely the file's character count. The problem is that **durable history has become part of every agent's working set**.

This defeats much of the benefit of isolated subagents. Their internal exploration and tool output may remain isolated, but each worker begins by reloading the accumulated history.

## Design Model

The existing session log should be treated like an event store. Agents should normally consume a compact materialized view of that history rather than replaying it in full.

```text
Durable history
    HISTORY.md
        |
        | projected and summarized by /checkpoint
        v
Active state
    STATE.md
        |
        | scoped inputs
        v
Current subagent
```

Specialized live artifacts act as additional projections:

```text
                    HISTORY.md
                         |
                 +-------+-------+
                 |       |       |
                 v       v       v
              STATE.md PLAN.md REVIEW.md
                 |       |       |
                 +-------+-------+
                         |
                         v
                   Scoped subagent
```

## Recommended File Layout

```text
.session/
├── STATE.md          # Compact, authoritative current context
├── PLAN.md           # Active and near-future implementation work
├── REVIEW.md         # Unresolved review findings only
├── HISTORY.md        # Append-only durable historical record
└── archive/
    ├── task-001.md   # Optional detailed task archive
    ├── task-002.md
    └── ...
```

### Information temperature

| Artifact | Lifetime | Normal consumption rule |
|---|---|---|
| `STATE.md` | Current moment | Always read |
| `PLAN.md` | Current workstream | Read only the referenced task section |
| `REVIEW.md` | Until findings are resolved | Read only findings applicable to the active task |
| `HISTORY.md` | Permanent | Do not read unless explicitly required |
| `archive/` | Permanent, optional detail | Read only for targeted historical investigation |

Information is not deleted when work advances. It is moved from hot runtime context into colder durable storage.

## `STATE.md`: The Runtime Read Model

`STATE.md` is the middle layer between the durable record and disposable subagents. It should remain small, current, and sufficient to execute one task.

A reasonable target is approximately 300–800 tokens, although relevance matters more than a strict limit.

### Example

```markdown
# Session State

## Objective

Implement CloudWrapper affinity persistence and placement logic.

## Current Task

TASK-004 — Implement association repository methods.

Status: active

## Relevant Decisions

- PostgreSQL is authoritative.
- CloudFront-only sites reserve affinity but cannot create Akamai associations.
- Association writes must be idempotent.

## Inputs

- `src/cdn_api/cloudwrapper/models.py`
- `src/cdn_api/cloudwrapper/repository.py`
- `PLAN.md` § `TASK-004`

## Acceptance Criteria

- Create, update, and get operations are implemented.
- Duplicate writes are safe.
- Tests cover a nonexistent association.
- Tests cover a CloudFront-only site.

## Outstanding Review Findings

None.

## Blockers

None.

## Next

TASK-005 — Implement the placement service.
```

### Content rules

`STATE.md` should contain only facts that materially affect the active task:

- the current objective and task;
- the task status;
- relevant durable decisions;
- exact inputs and file references;
- acceptance criteria;
- unresolved findings applicable to the task;
- current blockers; and
- the likely next task.

It should not contain:

- completed-task narratives;
- exploratory reasoning that no longer affects implementation;
- resolved review discussions;
- terminal output;
- a copy of the full plan;
- old blockers; or
- decisions that have been superseded.

## `PLAN.md`: Live Work Only

`PLAN.md` should describe the active and queued implementation work, not serve as another historical log.

```markdown
# Implementation Plan

## TASK-005 — Placement service

Status: active

### Goal

Select an eligible CloudWrapper reservation for a site.

### Steps

1. Load the fingerprint affinity group.
2. Exclude reservations without available capacity.
3. Preserve an existing valid placement.
4. Return `NO_CAPACITY` when no eligible reservation exists.

### Acceptance Criteria

- Existing valid placements remain stable.
- Capacity is checked before a new placement.
- CloudFront-only sites do not create Akamai associations.

## TASK-006 — Reconciliation service

Status: queued

...
```

When a task completes, its detailed execution record should leave the live plan. `/checkpoint` condenses its outcome into `HISTORY.md` and optionally stores additional detail under `archive/`.

## `REVIEW.md`: Unresolved Findings Only

`REVIEW.md` is a work queue, not a transcript of every review ever performed.

```markdown
# Review Findings

## TASK-005

### R-005-01 — Capacity check is vulnerable to a race

Status: open
Severity: high

The selected reservation can exceed its association limit when two workers place sites concurrently.

Required outcome:

- Make capacity reservation atomic, or
- reject and retry safely after a conflicting write.
```

Once a finding is resolved and verified, `/checkpoint` records the concise result in history and removes the finding from the live document.

## `HISTORY.md`: Durable Audit Record

`HISTORY.md` preserves completed outcomes without remaining part of the default worker context.

```markdown
# Session History

## TASK-005 — 2026-09-16

Implemented the CloudWrapper placement service.

### Outcome

- Placement uses fingerprint affinity.
- Capacity is checked before association.
- CloudFront-only sites do not create Akamai associations.

### Durable Decisions

- Capacity exhaustion returns `NO_CAPACITY` rather than raising an exception.

### Review

- Corrected a race in capacity reservation.
- No unresolved findings remain.

### Commit

`abc1234`
```

Historical entries should preserve outcomes, consequential decisions, unresolved risks, and useful identifiers. They should not reproduce the entire task transcript.

## Agent Input and Output Contracts

Each role should receive the smallest complete input set needed to perform its job.

### Planner

Reads:

- `STATE.md`;
- relevant architecture or requirement documents; and
- the specific planning target.

Writes:

- active and queued task definitions in `PLAN.md`; and
- proposed decisions that require orchestrator acceptance.

Does not normally read:

- `HISTORY.md`; or
- unrelated completed tasks.

### Coder

Reads:

- `STATE.md`;
- only the active section of `PLAN.md`;
- applicable open findings in `REVIEW.md`; and
- source code and tests relevant to the active task.

Writes:

- code and tests;
- a concise completion result for the orchestrator; and
- blockers or decision requests that could not be resolved safely.

Suggested instruction:

```text
Read .session/STATE.md.

Execute only the active task.

Consult PLAN.md only for the section referenced by STATE.md.
Consult REVIEW.md only for findings referenced by STATE.md.
Do not read HISTORY.md unless explicitly instructed.
```

### Reviewer

Reads:

- `STATE.md`;
- the active task's acceptance criteria;
- the relevant diff;
- affected source and tests; and
- existing open findings for that task.

Writes:

- unresolved, actionable findings to `REVIEW.md`; and
- a concise review result for the orchestrator.

The reviewer does not need the implementation agent's conversational reasoning. This preserves a useful author-versus-critic boundary.

### Parent or Orchestrator

Owns:

- accepting or rejecting proposed decisions;
- deciding when a task is truly complete;
- moving information between live artifacts and history;
- selecting the next task;
- regenerating `STATE.md`; and
- preventing indiscriminate historical reads.

The repository and session artifacts provide shared durable state. A new worker can inspect the current code and scoped documentation without inheriting every earlier agent conversation.

## `/checkpoint`: The Transition Operation

The missing workflow primitive is a transition operation that collapses completed work into durable history and prepares the next bounded working set.

`/checkpoint` is a good name because it describes the semantic operation without tying it to a particular agent role.

### Responsibilities

1. Inspect the active task and its acceptance criteria.
2. Determine whether the task is completed, blocked, or still active.
3. Record a concise final outcome in `HISTORY.md`.
4. Preserve any new durable decisions.
5. Carry unresolved review findings forward in `REVIEW.md`.
6. Remove resolved findings from the live review document.
7. Remove completed-task detail from `PLAN.md` or move it to `archive/`.
8. Mark the completed task accordingly.
9. Select the next queued task when appropriate.
10. Rewrite `STATE.md` for the new active task.

### State transition

```text
TASK-004 active
       |
       | implementation and review complete
       v
  /checkpoint
       |
       +-- append concise outcome to HISTORY.md
       +-- preserve durable decisions
       +-- retain unresolved findings in REVIEW.md
       +-- remove completed detail from live artifacts
       +-- mark TASK-004 complete
       +-- mark TASK-005 active
       +-- regenerate STATE.md
       |
       v
TASK-005 active
```

Conceptually, `/checkpoint` is garbage collection for active agent context. It does not destroy information; it changes the information's temperature.

### Safety rules

`/checkpoint` should:

- never mark a task complete merely because a coder says it is done;
- verify required tests or acceptance evidence where possible;
- never discard unresolved findings;
- preserve decision rationale when it will matter later;
- avoid copying full transcripts into history;
- make `STATE.md` internally consistent after every transition; and
- stop for clarification if more than one next task is eligible and the choice is consequential.

## Minimal Always-Applied Rule

The always-loaded Cursor rule should remain short:

```markdown
# Session Workflow

Use `.session/STATE.md` as the authoritative current-session context.

Do not read `.session/HISTORY.md` unless:

1. `STATE.md` explicitly references historical information; or
2. the parent explicitly requests historical investigation.

Consult only the `PLAN.md` and `REVIEW.md` sections relevant to the active task.
```

The prohibition on default historical reads is important. Otherwise, a well-intentioned worker may read the entire history to "understand the project thoroughly" and recreate the original context problem.

## Example End-to-End Workflow

```text
/planner
    |
    v
PLAN.md contains active and queued work
    |
/checkpoint
    |
    v
STATE.md points to TASK-001
    |
/python-coder sonnet TASK-001
    |
    v
Implementation and tests
    |
/python-review opus TASK-001
    |
    v
REVIEW.md contains actionable open findings
    |
/python-coder sonnet resolve TASK-001 review findings
    |
    v
Fixes and verification
    |
/checkpoint
    |
    +-- HISTORY.md += TASK-001 outcome
    +-- resolved findings leave REVIEW.md
    +-- completed detail leaves PLAN.md
    +-- STATE.md = TASK-002
    |
    v
/python-coder sonnet TASK-002
```

## Adoption Plan

This can be introduced incrementally.

### Phase 1 — Split the artifacts

1. Preserve the existing session log as `HISTORY.md`.
2. Create a small `STATE.md` for the current task.
3. Move only active and queued work into `PLAN.md`.
4. Move only unresolved findings into `REVIEW.md`.
5. Add the rule that subagents do not read `HISTORY.md` by default.

### Phase 2 — Add a manual `/checkpoint`

Implement `/checkpoint` as an orchestrator command with the explicit responsibilities listed above. Keep the process prompt-driven until its semantics are stable.

### Phase 3 — Enforce bounds

Add validation such as:

- exactly one active task;
- every active task has acceptance criteria;
- every open review finding references a live task;
- `STATE.md` references only existing files and task identifiers;
- no completed task remains expanded in the live plan; and
- no resolved finding remains in `REVIEW.md`.

### Phase 4 — Automate lifecycle integration

After the transition semantics are proven, selected steps can be integrated with agent lifecycle hooks. Automation should enforce a stable workflow, not define an untested one.

## Practical Heuristics

- Keep decisions near the active task only while they affect current work.
- Store project-wide invariants in stable architecture or rules documents, not repeatedly in session history.
- Prefer exact file paths and task IDs over prose references.
- Let source code, tests, and commits carry implementation truth.
- Make completion summaries concise enough to scan but specific enough to audit.
- Archive detailed task records only when their detail has future diagnostic value.
- Retrieve history by targeted task ID, decision, date, or keyword rather than reading it sequentially.
- Treat an unexpected need to read all of `HISTORY.md` as a sign that the live projections may be missing important state.

## Summary

The durable log is valuable and should remain. The architectural change is to stop using it as the default runtime input for every disposable worker.

Use:

- `HISTORY.md` as the durable event record;
- `STATE.md` as the compact materialized view of the current task;
- `PLAN.md` for active and queued work;
- `REVIEW.md` for unresolved findings; and
- `/checkpoint` to transition work, preserve outcomes, and regenerate the next working set.

This preserves durability, auditability, and recoverability while allowing fresh subagents to stay focused on the work immediately in front of them.

## References

- [Cursor subagents](https://docs.cursor.com/agent/subagents)
- [Cursor customization](https://docs.cursor.com/context/rules)
- [Cursor hooks](https://docs.cursor.com/agent/hooks)

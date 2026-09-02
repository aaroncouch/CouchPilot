---
description: Develop a durable task brief before implementation begins.
---

# Task Brief Core

Distill rough task notes into a concise, durable brief that can seed later
session work.

# Behavior

1. Read the provided raw notes.
   - If no notes are provided, ask the operator to paste the task rambling or
     describe the problem.
2. Derive a structured brief with the sections below.
3. Ask clarification only when missing information would materially change the
   task boundary, safety, or likely implementation path.
   - If a detail is helpful but not required, keep it as `TBD` or an open
     question instead of blocking.
4. Write the latest brief to the host-defined CouchPilot staging path using the
   output contract below.
5. Do not create, switch, close, or modify an active session while preparing a
   task brief. The host wrapper defines staging and session-start behavior.

# Artifact Output Contract

Fill every section. Use `none known`, `none provided`, or `none` when a section
has no content — do not omit headings.

```markdown
---
created_at: <ISO8601 now>
last_updated: <ISO8601 now>
source: task-brief
status: ready-for-session
---

# Task brief

Suggested task id: <kebab-case-slug>

## Problem

<what is wrong or what needs to change>

## Desired outcome

<what success looks like>

## Constraints

- <hard constraint or "none known">

## Acceptance criteria

- <done-when statement>

## Important files / links / evidence

- <path, URL, issue, log snippet summary, or "none provided">

## Known risks

- <risk or "none known">

## Open questions

- <question or "none">

## Session seed

`task: <kebab-case-slug> <one concise paragraph containing the durable task context above>`
```

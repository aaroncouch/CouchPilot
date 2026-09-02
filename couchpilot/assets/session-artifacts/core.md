---
description: Keep CouchPilot session artifacts accurate, durable, and concise.
family: rule
---

# Session files

**Inert unless a session is active.** If `.cursor/scratch/active-session.txt`
does not exist, or its `task_id` is `(none)`, ignore this rule.

This rule applies to every agent that reads or writes active session artifacts.
Scoping it to a particular host or workflow role would leave other writers
unguarded.

- `current-handoff.md` is read-first truth. Read the pointer, then the handoff,
  before acting on session state.
- Read `session-log.md` only for excerpts the handoff references, or for an
  explicit history question.
- Top-level `#` headings in `session-log.md` are singletons. Append dated `##`
  entries inside the existing section, never a second `# Plan` or `# Findings`.
  If duplicates already exist, write to the first and recommend compaction.
- When rewriting `current-handoff.md`, preserve every field already present and
  update values only. The file declares its own status vocabulary. Planner-owned
  execution fields (`Recommended Model`, `Complexity`, `Reasoning Depth`) start as
  `unassigned` at session creation and are filled from `# Plan` **## Execution
  Recommendation** after planning.
- Only the session-start and session-end workflows write
  `.cursor/scratch/active-session.txt`. Nothing else modifies the pointer.

Rule id: sf-1

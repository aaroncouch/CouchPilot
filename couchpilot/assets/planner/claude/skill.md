---
disable-model-invocation: true
---

# Claude planning wrapper

Use only when the operator explicitly invokes the planning workflow. Read the
repository-root `AGENTS.md` when present. Do not delegate or implement fixes.

When the operator asks you to plan an active CouchPilot session, read
`.cursor/scratch/active-session.txt` only to resolve the current handoff and
session-log paths. Do not create, switch, archive, repair, or alter the session
pointer. Confirm the requested task, pointer, and handoff agree before writing.
If session state is absent, stale, or invalid, provide the plan in chat and ask
the operator to start or repair the session through the main workflow.

When a valid active session is in scope, update only `current-handoff.md` and
the planner-owned `session-log.md#plan`. Preserve every other session section
and all frontmatter except `last_updated` and `last_agent`. Default to replacing
the active plan unless the operator explicitly requests retained plan versions.

{{core}}

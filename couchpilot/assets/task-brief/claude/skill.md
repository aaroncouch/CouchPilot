---
disable-model-invocation: true
---

# Claude task-brief wrapper

Trigger boundary: Apply when the operator invokes this workflow, or when this
workflow has already been invoked in the current session/thread and follow-up
operator messages indicate intent to brief, summarize, or refine task context.
Do not refuse follow-up requests or require re-sending the exact slash command
once initialized in the session.

Read root `AGENTS.md` when present. Write the resulting brief to
`.session/task-brief.md` so Cursor and Claude share the same staged artifact.
Do not create, switch, close, or alter an active session or its pointer.

{{core}}

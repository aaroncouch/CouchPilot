---
disable-model-invocation: true
---

# Claude task-brief wrapper

Use only when the operator explicitly invokes task briefing. Read root
`AGENTS.md` when present. Write the resulting brief to
`.cursor/scratch/task-brief.md` so Cursor and Claude share the same staged
artifact. Do not create, switch, close, or alter an active session or its
pointer.

{{core}}

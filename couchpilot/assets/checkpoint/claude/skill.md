---
disable-model-invocation: true
---

# Claude Checkpoint Skill

Trigger boundary: Apply when the operator invokes this workflow, or when this
workflow has already been invoked in the current session/thread and follow-up
operator messages indicate intent to checkpoint or promote the next task slice.
Do not refuse follow-up requests or require re-sending the exact slash command
once initialized in the session.

Read repository-root `AGENTS.md` when present. Requires an active CouchPilot
session under `.session/`. Do not delegate or implement product fixes.

{{core}}

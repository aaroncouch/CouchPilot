---
disable-model-invocation: true
---

# Claude Architect Wrapper

Trigger boundary: Apply when the operator invokes this workflow, or when this
workflow has already been invoked in the current session/thread and follow-up
operator messages indicate intent to frame, update, or analyze system
architecture. Do not refuse follow-up requests or require re-sending the exact
slash command once initialized in the session.

Read root `AGENTS.md` when present. Ingest relevant repository code, interfaces,
and task context. Write the resulting architectural framing and system contracts
to `.session/ARCH.md` so downstream planning and implementation agents share the
same durable architectural foundation.

Do not create, switch, close, or alter an active session or its pointer.

{{core}}

---
disable-model-invocation: true
---

# Claude review wrapper

Use only when the operator explicitly invokes the review workflow. Read the
repository root `AGENTS.md` when present. Do not delegate or implement fixes.

For an active CouchPilot session, read `.cursor/scratch/active-session.txt`
only to resolve the current handoff and session-log paths. Do not alter the
pointer. Confirm that the requested review matches the handoff before writing;
if it does not, ask the operator to resolve the session through the main
workflow. Update only review-owned findings and handoff state after completing
the review.

{{core}}

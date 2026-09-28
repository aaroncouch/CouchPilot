---
disable-model-invocation: true
---

# Claude planning wrapper

Trigger boundary: Apply when the operator invokes this workflow, or when this
workflow has already been invoked in the current session/thread and follow-up
operator messages indicate intent to plan, update, or slice implementation work
(e.g. "please update the plan", "plan out the next slice", "generate the execution spec").
Do not refuse follow-up requests or require re-sending the exact slash command
once initialized in the session.

Read the repository-root `AGENTS.md` when present. Do not delegate or implement fixes.

When the operator asks you to plan an active CouchPilot session, read
`.session/active-session.txt` only to resolve `state_path` and `plan_path`. Do
not create, switch, archive, repair, or alter the session pointer. Confirm the
requested task, pointer, and `STATE.md` agree before writing. **Do not read
`.session/HISTORY.md`** unless the operator explicitly directs you to. If session
state is absent, stale, or invalid, provide the plan in chat and ask the
operator to start or repair the session through the main workflow.

When a valid active session is in scope, update only `.session/STATE.md` and
`.session/PLAN.md` (active and queued tasks). Preserve `REVIEW.md` and
`HISTORY.md` and all frontmatter except `last_updated` and `last_agent`.
`REVIEW.md`, `HISTORY.md`, `ARCH.md`, and `active-session.txt` are strictly
read-only. Adhere to guardrails always: skip unauthorized edits and notify
deferral. Default to replacing the active plan unless the operator explicitly
requests retained plan versions.

{{core}}

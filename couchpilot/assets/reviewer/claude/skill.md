---
disable-model-invocation: true
---

# Claude review wrapper

Use only when the operator explicitly invokes the review workflow. Read the
repository root `AGENTS.md` when present. Do not delegate or implement fixes.

For an active CouchPilot session, read `.session/active-session.txt` only to
resolve `state_path`, `plan_path`, and `review_path`. Do not alter the pointer.
**Do not read `.session/HISTORY.md`** unless the operator explicitly directs you
to. Confirm that the requested review matches `STATE.md` before writing; if it
does not, ask the operator to resolve the session through the main workflow.
Update only open findings in `.session/REVIEW.md` and runtime fields on
`.session/STATE.md` after completing the review. Do not delegate future
slices in `Next action`—slice transitions belong to `/couch-checkpoint`.

{{core}}

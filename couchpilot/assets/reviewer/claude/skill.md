---
disable-model-invocation: true
---

# Claude review wrapper

Trigger boundary: Apply when the operator invokes this workflow, or when this
workflow has already been invoked in the current session/thread and follow-up
operator messages indicate intent to review, inspect diffs, or evaluate changes
(e.g. "please review the latest changes for xyz", "verify this diff", "check these fixes").
Do not refuse follow-up requests or require re-sending the exact slash command
once initialized in the session.

Read the repository root `AGENTS.md` when present. Do not delegate or implement fixes.

For an active CouchPilot session, read `.session/active-session.txt` only to
resolve `state_path`, `plan_path`, and `review_path`. Do not alter the pointer.
**Do not read `.session/HISTORY.md`** unless the operator explicitly directs you
to. Confirm that the requested review matches `STATE.md` before writing; if it
does not, ask the operator to resolve the session through the main workflow.
Update only open findings in `.session/REVIEW.md` and runtime fields on
`.session/STATE.md` after completing the review. `PLAN.md` is strictly read-only:
do not edit `PLAN.md` and do not instruct the coder to edit `PLAN.md`. Do not
delegate future slices in `Next action`: slice transitions belong to
`/couch-checkpoint`. Adhere to guardrails always: skip unauthorized edits and
notify deferral.

{{core}}

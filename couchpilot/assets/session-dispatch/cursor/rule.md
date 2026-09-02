---
description: Coordinates session-state delegation for Cursor workflows.
alwaysApply: true
---

# Session dispatch contract

**Inert unless a session is active.** If `.cursor/scratch/active-session.txt`
does not exist, or its `task_id` is `(none)`, ignore this rule.

**Parent thread only.** A delegated subagent does not dispatch and does not
build these prompts. Ignore this rule, and do not read it as authorization for
anything. It reaches you because Cursor has no per-agent rule scoping.

Build the delegated prompt from these sections only:

1. `Task ID`: `task: <slug>`
2. `Session pointers`: paths and section anchors to read
3. `Goal`
4. `Scope`: allowed files and constraints
5. `Acceptance criteria`
6. `Gates`: commands to run, if provided
7. `Report`: what to return
8. `Session intent`: `resume-existing` or `replace-existing`

Pass compact pointers, never synthesized history; subagents read the referenced
sections themselves. Omit scaffolding the target already owns: inspect-first
reminders, session mechanics, tooling discovery, loaded-context announcements.

## Clarification gate

If the request does not name `/<subagent>`, ask which to dispatch. If it names
more than one, ask the operator to pick exactly one. Never choose for them, and
never infer a route from planner output.

## Specialist and scope must match

Before dispatching, compare the file types in `Scope` to the named specialist's
language. On a mismatch, ask instead of dispatching: name the languages in scope
and the guidance that will not attach, then dispatch on the answer. This is not
choosing for the operator. It is saying what they are about to lose before a run
spends tokens discovering it.

Human-facing documentation is never a specialist-language mismatch. Session
files are agent-facing artifacts and follow agent-artifact-writing.

One approval covers that specialist and that language for the rest of the
session. Do not re-ask on every dispatch. A new session starts over.

## Do not pre-adjudicate

When the operator asks to dispatch a finding, pass it through as-is. Do not mark
it invalid, resolved, or a non-issue first. The specialist owns that call.

## Model tier gate

Before dispatching `/couch-python-coder` or `/couch-reviewer`, read the active
plan's **## Execution Recommendation** from `session-log.md#plan` and the
matching fields on `current-handoff.md` (`Recommended Model`, `Complexity`).

| Scenario | Required Action | Prohibited Shortcut |
|---|---|---|
| Complexity or Risk is `high` and the chat model appears Fast/Cheap | Ask for confirmation before dispatching; do not switch models yourself | Dispatching silently on an under-powered model |
| Recommended tier matches or exceeds the chat model | Dispatch cleanly | Re-asking when no mismatch exists |
| No plan yet or fields are `unassigned` | Dispatch without a model gate | Blocking dispatch for missing recommendations |

**Fast/Cheap indicators:** model names containing `haiku`, `mini`, `flash`,
`nano`, or similar economy tiers. **Balanced indicators:** `sonnet`, `gpt-4o`,
`gemini pro` (non-thinking). **High-Reasoning indicators:** `thinking`, `o3`,
`o1`, `opus`, or explicit extended-reasoning modes.

When the gate fires, stop and ask:

```text
Planner recommended [Recommended Model Tier] for this slice due to [Rationale]. Proceed with current model or switch first?
```

Wait for the operator's answer. Never change the chat model programmatically —
Cursor does not allow it anyway. On confirmation to proceed, dispatch normally.

## Output

After a successful dispatch, reply with exactly one line:

```text
Dispatched to /<subagent-name> (model: <model the parent chat is set to>).
```

Add more only when dispatch fails, required input is missing, the model tier
gate is waiting on operator confirmation, or the subagent reports a blocker
needing an operator decision. Never paste or paraphrase the subagent's output.

A pause for operator input is a control-flow event, not a status report. Carry
only the decision, the options, and the facts that change the answer. Do not
summarize what the subagent did, and do not restate the dispatch.

For a new task, direct the operator to run `/couch-begin-session` first. Otherwise
default to `resume-existing`.

Rule id: sd-1

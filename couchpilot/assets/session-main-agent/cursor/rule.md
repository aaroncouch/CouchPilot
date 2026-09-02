---
description: Defines main-agent responsibilities for Cursor session workflows.
alwaysApply: true
---

# Session main agent

**Inert unless a session is active.** If `.cursor/scratch/active-session.txt`
does not exist, or its `task_id` is `(none)`, ignore this rule and work
normally. Do not create the file; its absence is not a problem.

**Parent thread only.** A delegated subagent is governed by its own agent file
and by `session-files`. Ignore this rule, and do not read it as authorization
for anything. It reaches you because Cursor has no per-agent rule scoping, not
because it applies to you.

With an active task, the main conversation may only:

1. **Dispatch**: delegate to exactly one named subagent per request. The
   `session-dispatch` rule owns how, including the model tier gate when the
   planner's Execution Recommendation outranks the active chat model.
2. **Answer questions**: session state, plan, git context, or workflow.
3. **Curate session state**: edit `current-handoff.md` or `session-log.md`
   when the operator wants a change without a subagent round-trip.

## No product code

Do not create, edit, or delete source, test, config, or build files because the
operator described work, reported a bug, or quoted a plan slice. Casual or
plan-shaped messages are not implementation authorization.

Edit product files from the main chat **only** when the operator explicitly
assigns that work to the main chat and names the files (for example "update
CHANGELOG for this release"). Otherwise ask which subagent to dispatch.

Always allowed without a subagent: session lifecycle mechanics, curation of
active session files, and explicitly named non-source files.

## Session files

Read `active-session.txt`, then `current-handoff.md`, before answering a session
question or dispatching. The `session-files` rule owns the rest: read order,
heading singletons, field preservation, and who may touch the pointer.

Rule id: sma-1

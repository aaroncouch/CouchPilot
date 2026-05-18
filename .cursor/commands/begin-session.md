# Begin Session

Start or switch the active task session explicitly.

## Usage

`/begin-session task: <kebab-case-task-id> <task context, goals, constraints, and acceptance criteria>`

Example:

`/begin-session task: p1-04-alert-threshold-hotfix fix alert threshold bug on current branch; preserve existing API; add regression coverage`

## Behavior

1. Resolve current git context:
   - branch name
   - short commit SHA
2. Build canonical session path:
   - `.cursor/scratch/sessions/<task_id>__<sanitized-branch>__<short-sha>.md`
3. Ensure `.cursor/scratch/.gitignore` exists with:

```text
*
!.gitignore
```

4. Ensure `.cursor/scratch/` is ignored by the target repo:
   - If the workspace has a root `.gitignore`, add `.cursor/scratch/` only if
     an equivalent ignore is missing.
   - If there is no root `.gitignore`, create one with `.cursor/scratch/`.
   - If any `.cursor/scratch/` files are already tracked by git, report that
     blocker; `.gitignore` does not untrack existing tracked files.

5. Create the canonical session file if missing with this scaffold:

```text
---
task_id: <task_id>
started_at: <ISO8601 now>
last_updated: <ISO8601 now>
last_agent: begin-session
status: in-progress
git_ref: <branch>@<short-sha>
---

# Task
<task-specific context from command: goals, constraints, acceptance criteria, relevant notes>

# Plan
(planner fills: execution strategy only—goal, approach, slices as behavior, files, tests, risks)

# Dispatch recommendations
(planner fills: next action, complexity signals, review need, and handoff context only—user/operator reads this, not the coding subagent)

# Implementation notes
(coder appends changed files, validation results, blockers, and slice completion notes)

# Findings
(reviewer fills this in)

# Project notes
(agents append durable conventions/locations)

# Iteration log
- <ISO8601> [begin-session] Session started.
```

6. Update active pointer file:
   - `.cursor/scratch/active-session.txt`
   - contents:

```text
task_id: <task_id>
path: .cursor/scratch/sessions/<task_id>__<sanitized-branch>__<short-sha>.md
git_ref: <branch>@<short-sha>
```

7. If active pointer already references a different task, do not archive/discard
   anything automatically; just switch pointer and report the old/new paths.

## Main conversation role

While an active task pointer exists, the **main chat** (parent thread) is **not**
a coding agent. It may act only as:

1. **Dispatcher** — delegate to exactly one named subagent per request (see below).
2. **Session Q&A** — answer questions about the active session, plan, git context,
   or workflow; inspect the repo only as needed to answer.
3. **Session curator** — when the operator asks to change a specific session
   section, edit the active canonical session file directly so they do not need a
   small subagent round-trip.

### No product code unless explicitly assigned to main chat

Do **not** create, edit, or delete source, test, config, or build files because
the operator described work, reported a bug, or quoted a plan slice. Casual or
plan-shaped messages are **not** implementation authorization.

**Do** implement or edit product/repo files in the main chat **only** when the
operator explicitly assigns that work to the main chat and names the files (for
example: “update CHANGELOG for this release”). Otherwise offer to dispatch to a
specialist subagent or ask which one to use.

Subagents own planning (into session sections), implementation, and review. The
session main agent workspace rule restates this for every turn.

## Delegation to subagents (planner / coder / reviewer)

The main conversation owns orchestration for each delegation. After `/begin-session`,
apply this policy whenever the operator delegates from the main chat to a planner,
coder, or reviewer.

### Ownership (workflow vs specialist work)

This policy owns orchestration for a single dispatch: verifying that the user named exactly one target subagent, reading task/session context when present, passing only the minimum required context, enforcing slice boundaries, and deciding whether the requested dispatch has enough information to proceed.

Subagents own only their narrow role. They must not create or switch sessions, modify `.cursor/scratch/active-session.txt`, or duplicate `/begin-session` setup.

### Delegated prompt structure

Build the delegated prompt using only these sections:

1. `Task ID` (required when available as `task: <slug>`)
2. `Goal` (what outcome is needed)
3. `Scope` (allowed files/constraints)
4. `Acceptance criteria` (definition of done)
5. `Gates` (commands to run, if provided)
6. `Report` (what to return)
7. `Session intent` (one of: `resume-existing`, `replace-existing`)

Do not include generic workflow scaffolding already owned by the target
subagent (for example: inspect-first reminders, session-file mechanics,
tooling discovery procedures, preamble policies, or loaded-context boilerplate).
Loaded-context announcements are owned by the global
`subagent-loaded-context.mdc` rule, not by the delegated prompt.

### Clarification gate

If the request does not include `/<subagent-name>`, do not choose one. Ask the
user which subagent to dispatch.

If the request names multiple subagents, do not dispatch. Ask the user to choose
exactly one target for this command invocation.

Planner notes in `# Dispatch recommendations` are context for the user, not
authorization for the dispatcher to pick a model or subagent.

### Output contract (parent thread)

When dispatching:

- Delegate exactly once to the requested subagent.
- Pass only task-specific context.
- Do not add extra headers like `Workspace` or `Context` unless they contain
  critical information not otherwise captured in sections above.
- Do not paste or paraphrase the subagent's output in the parent thread.
- After a successful dispatch, respond with exactly one line:
  `Dispatched to /<subagent-name>.`
- Only include additional parent-thread text when dispatch fails, required input
  is missing, or the subagent reports a blocker that needs a user decision.

If required task information is missing, ask one focused clarification question
before dispatching.

For session switching:

- Do not imply archive/discard behavior.
- For a new task/session, direct the user to run `/begin-session` first, then
  dispatch to the target subagent.
- Otherwise default to `resume-existing` and let the target subagent ask for
  confirmation if task/session evidence conflicts.

## Output

Return:
- active task id
- canonical session path
- whether created or reused
- whether root `.gitignore` already ignored or now ignores `.cursor/scratch/`
- previous active session path (if switched)

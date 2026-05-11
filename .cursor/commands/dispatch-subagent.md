# Dispatch Subagent

Delegate exactly one task to a specific subagent with a minimal, task-specific
handoff prompt.

## Ownership (workflow vs specialist work)

This command owns orchestration for a single dispatch: verifying that the user named exactly one target subagent, reading task/session context when present, passing only the minimum required context, enforcing slice boundaries, and deciding whether the requested dispatch has enough information to proceed.

Subagents own only their narrow role. They must not create or switch sessions, modify `.cursor/scratch/active-session.txt`, or duplicate `/begin-session` setup.

## Usage

`/dispatch-subagent /<subagent-name> <task request>`

Example:

`/dispatch-subagent /python-coder-composer Resolve reviewer findings for task: P1-03`

## Behavior

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
`subagent-loaded-context.mdc` rule, not by this dispatch prompt.

## Clarification Gate

If the request does not include `/<subagent-name>`, do not choose one. Ask the
user which subagent to dispatch.

If the request names multiple subagents, do not dispatch. Ask the user to choose
exactly one target for this command invocation.

Planner notes in `# Dispatch recommendations` are context for the user, not
authorization for the dispatcher to pick a model or subagent.

## Output Contract

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

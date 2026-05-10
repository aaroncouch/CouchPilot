# Dispatch Subagent

Delegate exactly one task to a specific subagent with a minimal, task-specific
handoff prompt.

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

## Output Contract

When dispatching:

- Delegate exactly once to the requested subagent.
- Pass only task-specific context.
- Do not add extra headers like `Workspace` or `Context` unless they contain
  critical information not otherwise captured in sections above.
- Return the subagent result as-is.

If required task information is missing, ask one focused clarification question
before dispatching.

For session switching:
- Do not imply archive/discard behavior.
- For a new task/session, direct the user to run `/begin-session` first, then
  dispatch to the target subagent.
- Otherwise default to `resume-existing` and let the target subagent ask for
  confirmation if task/session evidence conflicts.

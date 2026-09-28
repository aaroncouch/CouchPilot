---
description: Bootstrap or refresh a project-specific AGENTS.md guide.
---

# Curate project guide

Run only when the operator explicitly requests `bootstrap` or `refresh` mode.

This command manages the repository-root `AGENTS.md`. It curates durable,
project-specific guidance for future agents. It does not manage CouchPilot
agents, global policy, session state, model prompts, or chat formatting.

## Ownership and managed block

CouchPilot owns only this marked block. Preserve every byte outside it unless
the operator explicitly requests a broader edit.

```md
<!-- couchpilot:project-guide:start -->
## Project guide

### Project map

- <project-specific locations and their responsibilities>

### Local workflow

- `<command>`: <what it verifies or runs>

### Project conventions

- <specific convention, constraint, or compatibility rule>

### Review checks

- <project-specific check when changing a relevant area>

### Known traps

- <specific failure mode, prerequisite, or non-obvious constraint>
<!-- couchpilot:project-guide:end -->
```

Keep only relevant sections; do not retain empty headings. Keep entries short,
actionable, and specific to this repository.

## Evidence and scope

Build or revise entries only from evidence that is durable and attributable:

- repository structure and source ownership patterns;
- committed `README` files and project documentation;
- build, test, lint, packaging, CI, and deployment configuration;
- version-controlled scripts and automation;
- repeated, operator-confirmed feedback about this repository.

Use `tooling.md` only as a discovery aid. It is not authority: verify every
candidate command or convention against the repository before recording it.

Good entries identify project map, local workflow, project conventions, review
checks, or known traps. Include an entry only when it will plausibly prevent
future rediscovery or a real mistake.

## Exclusions

Never put any of the following in `AGENTS.md` or its managed block:

- generic CouchPilot, Cursor, Claude, or model policy;
- generic style, testing, or review standards that apply to every project;
- task-specific plans, findings, decisions, active-session pointers, or logs;
- secrets, tokens, local absolute paths, private credentials, or generated
  machine state;
- chat-response formatting, persona instructions, or delegation mechanics;
- unverified guesses, one-off debugging observations, or copied tool output.

Do not create a duplicate `CLAUDE.md` wrapper solely to include the guide.

## Bootstrap

1. Confirm the command mode is exactly `bootstrap`.
2. Check whether root `AGENTS.md` exists.
3. If it exists, stop without changing it and report that `refresh` is required
   to curate an existing guide.
4. Inspect targeted repository evidence. Do not perform a broad scan once the
   likely project map and workflow are clear.
5. Create `AGENTS.md` with the managed block and only evidence-backed entries.
   If there is not enough durable evidence for an entry, omit it rather than
   adding a placeholder.

## Refresh

1. Confirm the command mode is exactly `refresh`.
2. If root `AGENTS.md` is absent, stop without changing files and report that
   `bootstrap` is required.
3. Locate the managed block. If either marker is missing, duplicated, or out of
   order, stop and ask for operator direction; do not guess ownership.
4. Preserve all content outside the managed block exactly.
5. Re-check the evidence behind each managed entry that may be stale or
   incomplete. Make the smallest change that improves durable guidance.
6. Add new entries only when current evidence supports them. Rewrite existing
   entries only to improve accuracy, specificity, or compactness.
7. Remove an entry only when repository evidence proves it stale, it duplicates
   a more authoritative project instruction, or the operator directs removal.
   Do not remove an entry merely because it was not encountered during a
   targeted inspection.

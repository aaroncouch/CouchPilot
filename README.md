# CouchPilot

CouchPilot is a small, opinionated Cursor setup for planning, coding, and
reviewing Python work with less prompt babysitting.

Clone it, run one sync script, and your user-level Cursor config gets a compact
set of rules, skills, subagents, and slash commands. There is no package to
install, no wrapper CLI, and no project-level files to copy into every repo.

## TL;DR

```bash
git clone <this-repo> CouchPilot
cd CouchPilot
python sync.py
```

Then restart Cursor, open a Python project, and use the loop:

```text
/begin-session task: feat-foo-module implement foo workflow
/dispatch-subagent /planner-composer task: feat-foo-module plan the implementation
/dispatch-subagent /python-coder-composer task: feat-foo-module execute the plan
/dispatch-subagent /reviewer-codex task: feat-foo-module review the changes
/end-session task: feat-foo-module completed
```

Re-run `python sync.py` whenever you change this repo's `.cursor/` files. Use
`python sync.py --dry-run` to preview what would change.

## What This Is For

CouchPilot gives Cursor a reusable working style:

- Start a task with a clear task ID.
- Dispatch a planner for a concrete implementation plan.
- Dispatch that plan to a Python-focused coding subagent.
- Dispatch the diff to a reviewer subagent.
- Keep the handoff notes in simple scratch files instead of re-explaining the
  task every time.

The goal is not to build a heavy agent framework. It is a lightweight personal
toolkit for keeping Cursor's help consistent across machines and projects.

## What's Included

```text
CouchPilot/
  .cursor/
    rules/
      code-quality.mdc
      subagent-loaded-context.mdc
      python.mdc
      python-tests.mdc
    skills/
      python-style/SKILL.md
    agents/
      planner-composer.md
      planner-codex.md
      planner-gpt55.md
      python-coder-codex.md
      python-coder-composer.md
      reviewer-composer.md
      reviewer-codex.md
      reviewer-gpt55.md
    commands/
      begin-session.md
      end-session.md
      dispatch-subagent.md
      deslop-main-diff.md
      deslop-workspace.md
  sync.py
  README.md
```

After sync, those files are copied into `~/.cursor/`, where Cursor can use them
from any workspace.

### Rules

Rules are short guardrails Cursor can inject automatically.

- `code-quality.mdc` applies globally and keeps edits minimal, idiomatic, and
  low-noise.
- `subagent-loaded-context.mdc` applies globally and requires subagents to
  announce their active subagent identity, rules, and skills before task work.
- `python.mdc` applies to `*.py` files and captures the Python style and
  tooling baseline.
- `python-tests.mdc` applies to Python test files and adds pytest conventions.

### Skill

`python-style` is the longer "code the way I write code" reference. The Python
coder reads it before implementation work, and reviewers consult it when Python
is in scope.

### Subagents

| Subagent | Role | Model |
|---|---|---|
| `/planner-composer` | Fast bounded planning for clear tasks. | `composer-2` |
| `/planner-codex` | Middle-ground structured planning for moderate complexity. | `gpt-5.3-codex` |
| `/planner-gpt55` | Deep planning for ambiguous or high-risk work. | `gpt-5.5` |
| `/python-coder-codex` | Careful Python implementation for complex changes. | `gpt-5.3-codex` |
| `/python-coder-composer` | Implement Python changes after inspecting the project. | `composer-2` |
| `/reviewer-composer` | Fast review for low-risk changes. | `composer-2` |
| `/reviewer-codex` | Review a diff with line-anchored findings. | `gpt-5.3-codex` |
| `/reviewer-gpt55` | Review a diff with risk-first GPT-5.5 behavior. | `gpt-5.5` |

If your Cursor install exposes different model slugs, edit the `model:` line in
the relevant agent file and run `python sync.py` again.

### Commands

- `/begin-session` starts or switches the active task.
- `/end-session` archives the active task and clears the pointer.
- `/dispatch-subagent` is the required path for planner, coder, and reviewer
  subagent work. It carries the handoff structure and prompt metadata the parent
  agent needs when delegating.
- `/deslop-main-diff` runs an optional cleanup pass over branch changes.
- `/deslop-workspace` runs an optional cleanup pass across the workspace.

## Daily Workflow

Use one task ID for the whole loop. A short kebab-case slug works well:
`task: feat-foo-module`. After the session starts, always call planner, coder,
and reviewer subagents through `/dispatch-subagent`.

1. Start the task.

   ```text
   /begin-session task: feat-foo-module implement foo workflow
   ```

2. Plan the work.

   ```text
   /dispatch-subagent /planner-composer task: feat-foo-module add a Foo class that reads foo.json and exposes get(key)
   ```

3. Implement the plan.

   ```text
   /dispatch-subagent /python-coder-composer task: feat-foo-module execute the approved plan
   ```

4. Review the diff.

   ```text
   /dispatch-subagent /reviewer-codex task: feat-foo-module review the latest changes
   ```

5. Iterate if needed.

   ```text
   /dispatch-subagent /python-coder-composer task: feat-foo-module address the review findings
   ```

6. End the task.

   ```text
   /end-session task: feat-foo-module completed and merged
   ```

Always use `/dispatch-subagent` for subagent work. It keeps the parent chat
acting as a dispatcher and passes the task-specific sections and prompt metadata
the target subagent needs:

```text
/dispatch-subagent /python-coder-composer task: feat-foo-module address the review findings
```

## Workflow Selection

### Default Balanced

Use for normal Python work where the scope is clear or moderately complex:

```text
/planner-composer -> /python-coder-composer -> /reviewer-codex
```

Best for feature work, small refactors, tests, known bugs, and well-understood
behavior updates. Avoid for architecture, security, infrastructure, concurrency,
or vague tasks.

Examples: add schema validation, extract a shared helper, add pytest coverage,
or fix a known background job state bug.

Rationale: Composer keeps planning and implementation fast; Codex gives the
final review more depth.

### Serious / High-Risk

Use when a bad implementation would be expensive to unwind:

```text
/planner-gpt55 -> /python-coder-codex -> /reviewer-codex
```

Best for architecture changes, multi-file refactors, async workflows, job
orchestration, migrations, security-sensitive work, and production-risk changes.
Avoid for cleanup, formatting, one-file fixes, or docs-only updates.

Examples: redesign a worker pipeline, change deployment behavior, add migration
logic, or add concurrency controls around job processing.

Rationale: GPT-5.5 spends more effort on planning trade-offs while Codex handles
careful implementation and review.

### Cheap / Fast Iteration

Use when the task is small, obvious, low-risk, and easy to inspect manually:

```text
/planner-composer -> /python-coder-composer -> /reviewer-composer
```

Best for docs, simple tests, lint fixes, type hint cleanup, docstrings,
mechanical renames, and one-file changes. Avoid for production risk, complex
logic, credentials, deployment, concurrency, or migrations.

Examples: update README guidance, add a missing docstring, rename a helper, fix a
lint complaint, or test an existing pure function.

Rationale: Composer across the loop keeps simple iteration cheap and quick.

## How the Pieces Fit Together

```mermaid
flowchart TD
  start["Start work"] --> begin["/begin-session &lt;task&gt;"]
  begin --> pointer["active-session.txt"]
  begin --> session["Session file in .cursor/scratch/sessions/"]
  begin --> dispatchPlan["/dispatch-subagent"]
  dispatchPlan --> plan["/planner-composer, /planner-codex, or /planner-gpt55"]
  plan --> dispatchCode["/dispatch-subagent"]
  dispatchCode --> code["/python-coder-composer or /python-coder-codex"]
  code --> dispatchReview["/dispatch-subagent"]
  dispatchReview --> review["/reviewer-composer, /reviewer-codex, or /reviewer-gpt55"]
  review --> iterate{"More changes needed?"}
  iterate -- yes --> dispatchCode
  iterate -- no --> endcmd["/end-session &lt;task&gt;"]
  plan -.->|"plan hands off to"| code
  code -.->|"changes can be sent to"| review
  plan -->|"reads/writes active task via pointer"| session
  code -->|"reads/writes active task via pointer"| session
  review -->|"reads/writes active task via pointer"| session
  code -->|"reads on entry"| skill["Skill: python-style"]
  review -->|"reads when Python is in scope"| skill
  code -->|"edits .py files"| files["Python source"]
  files -->|"glob match"| rules["Rules: code-quality.mdc, subagent-loaded-context.mdc, python.mdc, python-tests.mdc"]
  rules -.->|"injected as guardrails"| code
  endcmd --> archive["session-archive/"]
  endcmd --> pointer
```

Think of the four Cursor pieces this way:

- Rules are reflexes.
- Skills are reference notes.
- Subagents are focused coworkers.
- Commands are explicit controls for starting, delegating, and closing work.

## Scratch Files

Subagents are one-shot workers. They do not automatically remember what another
subagent did earlier, so CouchPilot uses plain markdown scratch files as the
handoff record.

- Active pointer: `.cursor/scratch/active-session.txt`
- Task notes: `.cursor/scratch/sessions/*.md`
- Tooling cache: `.cursor/scratch/tooling.md`

The Python coder may create `.cursor/scratch/tooling.md` in a target project to
remember the formatter, linter, type checker, and test command it discovered.
`/begin-session` keeps `.cursor/scratch/` ignored by the target repo, and the
scratch directory also gets its own `.gitignore`.

This is intentionally not vector memory, semantic search, or cross-project
learning. It is just one task at a time in markdown.

## After Sync

Cursor can cache user-scope rules, skills, agents, and commands per chat
session. After running `sync.py`, restart Cursor or at least open a fresh chat
in a new window.

Each synced subagent is instructed to announce its active subagent identity,
rules, and skills before starting work. A healthy Python run looks roughly like:

```text
Loaded: subagent = python-coder-composer (composer-2); rules = code-quality.mdc, subagent-loaded-context.mdc, python.mdc, python-tests.mdc; skills = python-style
```

If `python.mdc` or `python-tests.mdc` is missing, make sure a matching Python
file is open or attached. Glob-scoped rules only appear when relevant files are
in context.

## Extending It

To add another language, copy the same pattern:

1. Add a language rule, such as `.cursor/rules/typescript.mdc`.
2. Add a style skill, such as `.cursor/skills/typescript-style/SKILL.md`.
3. Add a focused coder subagent, such as `.cursor/agents/typescript-coder.md`.
4. Run `python sync.py`.

Keep names specific enough that they do not collide with everyday slash command
usage. For example, prefer `/python-coder-composer` over `/python`.

## Intentionally Not Included

CouchPilot keeps the surface area small on purpose:

- No installable Python package or wrapper CLI.
- No project-scope sync into target repos.
- No persistent memory system.
- No `.couchpilot/tasks/` workspace.
- No formatter or linter config templates for target projects.
- No non-Python coder templates.

Add more only when a real workflow need earns the extra complexity.

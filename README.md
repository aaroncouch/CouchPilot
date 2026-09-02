# CouchPilot

CouchPilot is a small, opinionated setup for planning, coding, and reviewing
Python work with less prompt babysitting. It targets both Cursor and Claude
Code from one canonical asset source.

Clone it, run one sync script, and your user-level Cursor and/or Claude Code
config gets a compact set of rules, skills, subagents, and slash commands.
There is no package to install, no wrapper CLI, and no project-level files to
copy into every repo you work in.

## TL;DR

```bash
git clone <this-repo> CouchPilot
cd CouchPilot
python sync.py
```

`sync.py` compiles canonical sources in `couchpilot/assets/` and installs
rendered artifacts under `~/.cursor` and/or `~/.claude`. By default it
**autodetects** which host directories already exist on your machine — if you
only use Cursor, a lone `~/.cursor` directory is enough; `~/.claude` is not
required.

Then restart the app, open a Python project, and use the loop from Cursor's
main chat:

```text
/couch-task-brief <paste raw task notes>
/couch-begin-session task: feat-foo-module implement foo; goals, constraints, acceptance criteria
/couch-planner
/couch-python-coder
/couch-reviewer
/couch-end-session task: feat-foo-module completed
```

## Sync & Host Setup

### Autodetection

When you run `python sync.py` with no flags, `sync.py` checks whether
`~/.cursor` and/or `~/.claude` exist (paths come from `couchpilot/hosts.py`,
overridable via `couchpilot.json`). It syncs **only** the hosts it finds:

| Your machine | What happens |
|---|---|
| Only `~/.cursor` exists | Syncs Cursor only — no error, no Claude install attempted |
| Only `~/.claude` exists | Syncs Claude Code only |
| Both exist | Syncs both |
| Neither exists | Exits with an error; pass `--target cursor` or `--target all` to create one |

This keeps Cursor-only workflows frictionless.

### CLI flags

| Flag | Purpose |
|---|---|
| `--target cursor` | Sync Cursor only (even if Claude dir also exists) |
| `--target claude` | Sync Claude Code only |
| `--target all` | Sync every registered host profile |
| `--dry-run` | Compile and report without writing files |
| `--prune` | Delete manifest-tracked files CouchPilot no longer ships |

Sync records installed files in `<host-dir>/.couchpilot-manifest.json`. Only
manifest-claimed files are ever removed on `--prune`; hand-written config in
`~/.cursor` or `~/.claude` is never touched.

## What This Is For

CouchPilot keeps task context **on disk instead of in the chat window**.

A long chat accumulates the task description, the plan, every implementation
detail, and every review finding — all re-sent on every turn. When the window
fills, the model retraces the conversation to summarize it, and token usage
spikes precisely when the chat is already at its most expensive.

The loop avoids that by keeping the durable record in markdown:

- Start a task with a clear task ID.
- Delegate to a planner for a concrete implementation plan.
- Delegate that plan to a Python-focused coding subagent.
- Delegate the diff to a reviewer subagent.
- Each subagent reads only what it needs from `current-handoff.md`, does one
  job in its own fresh context, writes its result back to disk, and exits.

The main chat stays a thin dispatcher. It never holds the implementation
transcript, so it stays usable far longer before approaching the limit.

**Subagents require an active session.** A dispatch with no session has no
handoff to read and nowhere to write its result. Run `/couch-begin-session`
first, or handle the change directly in the main chat.

## When Not To Use It

For a quick question, a one-file fix, or anything that will not come close to
filling the window, skip the session loop. With no active session, session
rules go inert, the main chat writes code directly, and `couch-python` plus
`couch-python-style` still attach to any `*.py` file.

Rough test: if you would not mind re-explaining the task from scratch after a
context reset, you do not need a session.

## Host Profiles & `couchpilot.json`

Install targets are defined once in `couchpilot/hosts.py` as immutable
`HostProfile` dataclasses — not scattered through `sync.py` or the compiler.

| Profile | Class | Install dir | Notable defaults |
|---|---|---|---|
| `cursor` | `CursorHostProfile` | `~/.cursor` | `.mdc` rules, `alwaysApply`, `model: inherit` agents |
| `claude` | `ClaudeHostProfile` | `~/.claude` | `.md` rules, `disable-model-invocation: true` on manual skills |

Repo-root `couchpilot.json` optionally overrides per-host settings without
editing Python:

```json
{
  "hosts": {
    "cursor": {
      "install_dir": "~/.cursor",
      "style_dialect": "universal_xml",
      "default_frontmatter": { "agent": { "model": "inherit" } }
    }
  }
}
```

Supported override keys: `install_dir`, `style_dialect`, `extensions`,
`family_directories`, `default_frontmatter`, `wrapper_template`.

The compiler and `sync.py` call `get_host_profile(target)` for path mapping,
frontmatter validation, and install directories. See
[`couchpilot/FORMAT.md`](couchpilot/FORMAT.md) for the full schema.

## Two Hosts, One Source

CouchPilot is authored once under `couchpilot/assets/<asset-id>/` and compiled
per host by `sync.py`.

### Canonical shared rules (`core.md` only)

When rule logic is identical on Cursor and Claude, author **one file**:

```text
couchpilot/assets/code-quality/
└── core.md          # family: rule
```

```yaml
---
description: Apply concise, idiomatic code-quality guardrails across languages.
family: rule
---
```

Path-scoped rules add `globs` (string or YAML list):

```yaml
family: rule
globs: "**/*.py"
```

The compiler synthesizes host-native scope — no `cursor/rule.md` or
`claude/rule.md` boilerplate:

| `globs` | Cursor | Claude |
|---|---|---|
| absent | `alwaysApply: true` | global rule (no `paths`) |
| present | `alwaysApply: false` + `globs` | `paths: [...]` |

**Canonical shared rules:** `code-quality`, `test-integrity`, `project-guide`,
`agent-artifact-writing`, `session-artifacts`, `python`, `python-tests`.

### Explicit wrappers (when hosts diverge)

Use `core.md` plus platform wrappers only when roles or mechanics differ:

```text
couchpilot/assets/planner/
├── core.md
├── cursor/agent.md      # subagent + {{core}}
└── claude/skill.md      # manual skill + {{core}}
```

Single-platform tools (session rules, Cursor commands) use one wrapper with
no `core.md`:

```text
couchpilot/assets/session-dispatch/
└── cursor/rule.md
```

Installed names carry a `couch-` prefix. The two hosts play different roles:

- **Cursor** — day-to-day loop: session commands, planner/coder/reviewer
  subagents, always-on quality and session rules.
- **Claude Code** — manual-invocation bridge for high-reasoning workflows
  (`/couch-planner`, `/couch-reviewer`, `/couch-task-brief`) without leaving
  the on-disk session protocol.

## Polyglot Prompt Conventions

Core assets use structures that work across Anthropic, OpenAI, and Gemini:

| Convention | Purpose |
|---|---|
| Paired decision tables | `Scenario \| Required Action \| Prohibited Shortcut` instead of long prohibition lists |
| `<bad_example>` / `<good_example>` | Few-shot code is not confused with live instructions |
| `<agent_announcement>` | Loaded-context parsing survives reasoning preambles |
| Fenced artifact templates | Strict planner/coder/reviewer report schemas |
| `Rule id:` / `Skill id:` | Verification tokens at the end of rules and skills |

### Resilient context announcements

Subagents wrap loaded-context lines in `<agent_announcement>` tags at the
**beginning of the final response body**. Reasoning models (Claude Thinking,
o3-mini, Gemini Flash Thinking) may emit summaries or title blocks before the
report; the tag makes parsing robust:

```text
<agent_announcement>Loaded: subagent = python-coder; model = Sonnet 5; rules = couch-python.mdc:py-1; skills = couch-python-style:pys-1</agent_announcement>
```

Anything reported as `:MISSING` did not load. Host-specific announcement
protocols belong in wrappers, not in `core.md`.

## What's Included

```text
CouchPilot/
  .cursor/                    # project-scoped dev config (not installed by sync)
  couchpilot/
    assets/                   # canonical sources
      code-quality/core.md    # example: canonical shared rule
      planner/                # example: multi-target divergent asset
      session-dispatch/       # example: Cursor-only rule
    compiler.py
    hosts.py
    FORMAT.md
  couchpilot.json             # optional host overrides
  sync.py
  tests/test_compiler.py
```

Compiled install layout:

```text
~/.cursor/                        ~/.claude/
  rules/couch-*.mdc                  rules/couch-*.md
  skills/couch-*/SKILL.md            skills/couch-*/SKILL.md
  agents/couch-*.md                  agents/couch-*.md
  commands/couch-*.md                commands/couch-*.md
```

### Rules

- `couch-code-quality`, `couch-test-integrity`, `couch-project-guide`,
  `couch-agent-artifact-writing`, `couch-session-artifacts` — global.
- `couch-python` — `*.py` files.
- `couch-python-tests` — test file patterns.
- `couch-session-main-agent`, `couch-session-dispatch`, `couch-writing-voice`
  — Cursor-only session/workflow rules.

Session rules are **inert** without an active session (no
`.cursor/scratch/active-session.txt` or `task_id: (none)`).

### Skills, subagents, commands

| Role | Cursor | Claude Code |
|---|---|---|
| Plan | `/couch-planner` (subagent) | `/couch-planner` (manual skill) |
| Implement | `/couch-python-coder` (subagent) | — |
| Review | `/couch-reviewer` (subagent) | `/couch-reviewer` (manual skill) |
| Distill brief | `/couch-task-brief` (command) | `/couch-task-brief` (manual skill) |
| Curate `AGENTS.md` | `/couch-curate-project-guide` (command) | `/couch-curate-project-guide` (manual skill) |

Cursor subagents use `model: inherit` — they run whatever model the parent
chat is set to. Pin a specific model before dispatch; on Auto, `inherit`
inherits Auto's pick.

Other commands: `/couch-begin-session`, `/couch-end-session`,
`/couch-audit-test-integrity`, `/couch-deslop-main-diff`,
`/couch-deslop-workspace`.

## Daily Workflow

1. Optional: `/couch-task-brief` to distill raw notes into
   `.cursor/scratch/task-brief.md`.
2. `/couch-begin-session task: feat-foo-module …` (or `use previous task brief`).
3. `/couch-planner` — set the model picker first.
4. `/couch-python-coder` — execute the approved plan or slice.
5. `/couch-reviewer` — review the diff.
6. Iterate coder/reviewer as needed.
7. `/couch-end-session task: feat-foo-module completed`.

Keep delegated prompts short. The dispatcher curates from `current-handoff.md`
plus targeted `session-log.md` excerpts.

## Choosing Depth & Model Tier Gate

The loop is always `/couch-planner` → `/couch-python-coder` →
`/couch-reviewer`. What changes is the **model** you pick before each dispatch.

### Planner Execution Recommendation

After planning, `# Plan` includes **## Execution Recommendation**:

- **Complexity:** `low` | `medium` | `high`
- **Recommended Model Tier:** `Fast/Cheap` | `Balanced` | `High-Reasoning`
- **Reasoning Depth:** `minimal` | `standard` | `invariant-first`
- **Rationale:** one sentence

The planner mirrors `Recommended Model`, `Complexity`, and `Reasoning Depth`
onto `current-handoff.md` (starting as `unassigned` from `/couch-begin-session`).

### Dispatcher model tier gate

When dispatching `/couch-python-coder` or `/couch-reviewer`, `couch-session-dispatch`
checks the recommendation. If complexity or risk is `high` and the active chat
model looks Fast/Cheap (Haiku, mini, flash, nano, etc.), the dispatcher asks:

```text
Planner recommended [Recommended Model Tier] for this slice due to [Rationale]. Proceed with current model or switch first?
```

It never switches models for you — confirm to proceed or change the model
picker first. Clean dispatches reply with one line:

```text
Dispatched to /couch-python-coder (model: Sonnet 4).
```

### Tier guidance

| Tier | Good for | Avoid for |
|---|---|---|
| **Fast/Cheap** | Docs, lint fixes, one-file changes, renames | Production risk, invariants, concurrency, migrations |
| **Balanced** | Feature work, small refactors, known bugs | Architecture, security, vague tasks |
| **High-Reasoning** | Multi-file refactors, async, auth, production paths | Cleanup, formatting, docs-only |

## Scratch Files

- Active pointer: `.cursor/scratch/active-session.txt`
- Task brief: `.cursor/scratch/task-brief.md`
- Handoff: `.cursor/scratch/sessions/<session-id>/current-handoff.md`
- Log: `.cursor/scratch/sessions/<session-id>/session-log.md`
- Archive: `.cursor/scratch/session-archive/<session-id>/`
- Tooling cache: `.cursor/scratch/tooling.md`

Only session-start/end commands write the active pointer. Subagents read it
to locate handoff paths but never modify it.

## After Sync

Restart Cursor or Claude Code (or open a fresh chat) so cached rules reload.

Troubleshooting loaded-context announcements:

- `couch-python.mdc:MISSING` — open or attach a `*.py` file (glob-scoped rule).
- `couch-python-style:MISSING` — skill paths did not match, or skills are not
  reaching subagents in your Cursor version.
- Wrong `model` in announcement — parent chat was on Auto; `inherit` resolved
  to Auto's choice.

## Developing CouchPilot

The repository ships **project-scoped** Cursor configuration in `.cursor/`.
These files are version controlled and guide agents working on CouchPilot
itself. They are **not** installed by `sync.py` (distinct from `~/.cursor`
artifacts).

| Resource | Path | Purpose |
|---|---|---|
| Asset authoring rule | `.cursor/rules/asset-authoring.mdc` | Standards for `couchpilot/assets/**` |
| Compiler rule | `.cursor/rules/compiler-conventions.mdc` | Standards for Python toolchain |
| Validate command | `/validate-assets` | Run tests + `sync.py --dry-run` |
| New asset command | `/new-asset <id> <type>` | Scaffold a canonical asset |
| New asset skill | `.cursor/skills/new-asset/SKILL.md` | Full asset creation workflow |
| Extend host skill | `.cursor/skills/extend-host-profile/SKILL.md` | Register a new install target |

Project commands use unprefixed names (`/validate-assets`, `/new-asset`) so
they never collide with installed `couch-*` slash commands.

## Extending It

To add a new asset under `couchpilot/assets/<asset-id>/`:

1. **Shared rule (both hosts):** write `core.md` with `description`,
   `family: rule`, and optional `globs`. No wrapper folders.
2. **Path-scoped rule:** same as above with `globs: "**/*.py"` or a YAML list.
3. **Multi-target divergent:** write `core.md` plus explicit wrappers with
   exactly one `{{core}}` marker each (e.g. `cursor/agent.md` +
   `claude/skill.md`).
4. **Single-platform:** one wrapper only, no `core.md` (e.g. Cursor command).
5. Validate:

   ```bash
   python3 -m unittest discover -s tests
   python3 sync.py --dry-run
   ```

6. Install: `python sync.py` (or `--target cursor`).

See [`couchpilot/FORMAT.md`](couchpilot/FORMAT.md) for asset shapes and
[`tests/test_compiler.py`](tests/test_compiler.py) for worked examples.
Use `/new-asset` in this repo for guided scaffolding.

Keep asset ids specific (`python-coder`, not `python`) to avoid slash-command
collisions after the `couch-` prefix is applied.

## Intentionally Not Included

- No installable Python package or wrapper CLI.
- No project-scope sync into target repos you work in.
- No persistent memory beyond on-disk session scratch files.
- No formatter or linter config templates for target projects.
- No non-Python coder templates.

Add more only when a real workflow need earns the extra complexity.

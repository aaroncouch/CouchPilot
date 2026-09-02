# CouchPilot canonical asset format

`couchpilot/assets/` is the source layer `sync.py` compiles into installed
Cursor (`~/.cursor`) and Claude Code (`~/.claude`) artifacts. Nothing under
this directory is installed directly; `couchpilot/compiler.py` renders it.

See also the repository [`README.md`](../README.md) for sync, workflow, and
project-scoped development configuration.

## Folder-derived identity

Each asset is one kebab-case directory under `couchpilot/assets/<asset-id>/`.
Identity, target, and family come from the filesystem path — not from a
catalog file.

Installed names get a `couch-` prefix so they cannot collide with a user's
own personal commands, skills, agents, or rules. Cross-references in asset
prose to another installed slash command must use the prefixed name (e.g.
`` `/couch-begin-session` ``); the compiler does not rewrite prose.

## Asset shapes

### Shape A: Canonical shared rule (`core.md` only)

When rule logic is identical on Cursor and Claude, author a single file:

```text
couchpilot/assets/code-quality/
└── core.md          # family: rule (+ optional globs)
```

```yaml
---
description: Apply concise, idiomatic code-quality guardrails across languages.
family: rule
---
```

Path-scoped rules add `globs`:

```yaml
---
description: Apply the project's Python implementation conventions.
family: rule
globs: "**/*.py"
---
```

Or a YAML list for multiple patterns (see `python-tests/core.md`).

The compiler **synthesizes** per-host wrappers — do not create
`cursor/rule.md` or `claude/rule.md` boilerplate.

| `globs` in `core.md` | Cursor output | Claude output |
|---|---|---|
| absent | `alwaysApply: true` | global rule (no `paths`) |
| present | `alwaysApply: false` + `globs: "..."` | `paths: [...]` list |

Synthesis is implemented in `compiler.py::_synthetic_rule_frontmatter()`.

**Canonical shared rules in this repo:** `code-quality`, `test-integrity`,
`project-guide`, `agent-artifact-writing`, `session-artifacts`, `python`,
`python-tests`.

### Shape B: Multi-target divergent asset

When hosts differ in family or mechanics, use `core.md` plus explicit wrappers:

```text
couchpilot/assets/planner/
├── core.md
├── cursor/
│   └── agent.md       # subagent + {{core}}
└── claude/
    └── skill.md       # manual skill + {{core}}
```

Wrappers hold host-specific frontmatter and protocols (`<agent_announcement>`,
session pointer rules, `disable-model-invocation`, etc.). `core.md` stays
host-neutral.

**Examples:** `planner`, `reviewer`, `curate-project-guide`, `task-brief`.

### Shape C: Single-platform asset

When only one host uses the asset, put the complete prompt in one wrapper with
no `core.md`:

```text
couchpilot/assets/session-dispatch/
└── cursor/
    └── rule.md        # complete prompt; no {{core}}
```

**Examples:** `session-dispatch`, `session-main-agent`, `writing-voice`,
Cursor-only commands (`begin-session`, `end-session`, …).

### Shape D: Cursor-only skill with optional core

Reference skills often use `cursor/skill.md` with an optional shared `core.md`:

```text
couchpilot/assets/python-style/
└── cursor/
    └── skill.md       # worked examples; may reference a separate core-less body
```

### Full wrapper map (when explicit wrappers exist)

```text
couchpilot/assets/<asset-id>/
├── core.md              # optional: host-neutral shared body
├── cursor/
│   ├── rule.md           # -> ~/.cursor/rules/couch-<asset-id>.mdc
│   ├── command.md        # -> ~/.cursor/commands/couch-<asset-id>.md
│   ├── agent.md          # -> ~/.cursor/agents/couch-<asset-id>.md
│   └── skill.md          # -> ~/.cursor/skills/couch-<asset-id>/SKILL.md
└── claude/
    ├── rule.md           # -> ~/.claude/rules/couch-<asset-id>.md
    ├── command.md        # -> ~/.claude/commands/couch-<asset-id>.md
    ├── agent.md          # -> ~/.claude/agents/couch-<asset-id>.md
    └── skill.md          # -> ~/.claude/skills/couch-<asset-id>/SKILL.md
```

An asset needs at least one target wrapper **or** a synthesizable `core.md`
with `family: rule|command|agent|skill`.

## `core.md` and wrapper composition

`core.md` holds host-neutral instructions: goal, personality, process,
constraints, output contract. It must not contain:

- `<agent_announcement>` blocks or loaded-context protocols
- Cursor slash-command operational syntax as host mechanics
- Claude `disable-model-invocation` semantics

Every explicit wrapper for an asset that has a `core.md` must contain exactly
one `{{core}}` marker. The compiler replaces it with the core body verbatim.

When `core.md` declares `family: rule` and no wrapper directories exist, the
compiler synthesizes virtual wrappers from `HostProfile.wrapper_template`.

## Frontmatter rules

Frontmatter is direct YAML between `---` markers. No wrapping envelope.

| Field | Location | Notes |
|---|---|---|
| `description` | `core.md` when present | Wrappers must not duplicate |
| `family` | `core.md` for synthesis | `rule`, `command`, `agent`, or `skill` |
| `globs` | `core.md` for path-scoped rules | Compiler maps to host scope fields |
| `alwaysApply` / `globs` | synthesized or explicit Cursor rule wrapper | Never hand-author on shared rules |
| `paths` | synthesized or explicit Claude rule wrapper | List of glob strings |
| `model` | Cursor agent wrapper | Required on agents |
| `disable-model-invocation` | Claude skill wrapper | Required on shipped manual skills |

The compiler merges frontmatter as: core `description` (when present),
followed by wrapper fields. Authoring fields `family` and `globs` stay in
`core.md` only — they do not appear in rendered install artifacts.

## Host profiles (`couchpilot/hosts.py`)

Install behavior is centralized in `couchpilot/hosts.py`:

```python
@dataclass(frozen=True)
class HostProfile:
    name: str
    default_install_dir: str
    extensions: dict[str, str]
    family_directories: dict[str, str]
    default_frontmatter: dict[str, dict]
    style_dialect: str
    wrapper_template: dict[str, str]
```

Built-in profiles:

| Key | Class | Install dir | Validation highlights |
|---|---|---|---|
| `cursor` | `CursorHostProfile` | `~/.cursor` | rules need `alwaysApply`; agents need `model` |
| `claude` | `ClaudeHostProfile` | `~/.claude` | shipped skills need `disable-model-invocation: true` |

`load_host_profiles()` merges optional overrides from repo-root
`couchpilot.json`. Both `compiler.py` and `sync.py` call
`get_host_profile(target)` for validation, path mapping, and install dirs.

## `couchpilot.json` schema

Optional declarative overrides at the repository root:

```json
{
  "hosts": {
    "cursor": {
      "install_dir": "~/.cursor",
      "style_dialect": "universal_xml",
      "extensions": { "rule": "mdc" },
      "family_directories": { "rule": "rules" },
      "default_frontmatter": {
        "rule": { "alwaysApply": true },
        "agent": { "model": "inherit" }
      },
      "wrapper_template": { "rule": "{{core}}\n" }
    },
    "claude": {
      "install_dir": "~/.claude",
      "style_dialect": "anthropic_xml",
      "default_frontmatter": {
        "skill": { "disable-model-invocation": true }
      }
    }
  }
}
```

All keys under each host entry are optional; unspecified fields keep built-in
defaults from `create_default_profiles()`. Invalid JSON or missing files fall
back silently to defaults.

## Compiler pipeline

`couchpilot/compiler.py` is pure stdlib — no filesystem writes outside
reading `couchpilot/assets/`:

1. **Discover** — walk asset dirs; synthesize wrappers when `core.md` declares
   `family` and no explicit wrappers exist.
2. **Validate** — collect every schema violation across every asset before
   aborting (missing markers, stray files, misplaced `description`, invalid
   host frontmatter).
3. **Render** — merge frontmatter, substitute `{{core}}`, serialize YAML +
   body.
4. **Map paths** — `destination_for(target, family, asset_id)` via
   `HostProfile`.

`sync.py` calls `compile_assets()`, then writes rendered artifacts under each
resolved host install dir using hash-compare, manifest tracking, and optional
`--prune`.

## Polyglot prompt conventions

`style_dialect` hints which cross-model structures an asset family prefers:

| Convention | Purpose |
|---|---|
| Paired decision tables | `Scenario \| Required Action \| Prohibited Shortcut` |
| `<bad_example>` / `<good_example>` | Unambiguous few-shot delimiters |
| `<agent_announcement>` | Preamble-resilient loaded-context parsing |
| Fenced artifact templates | Strict planner/coder/reviewer report schemas |
| `Rule id:` / `Skill id:` | Verification tokens at end of rules/skills |

Separate **Analysis Guidelines** (how to evaluate) from **Artifact Output
Contracts** (strict templates for files and chat). Host-specific mechanics
belong in wrappers, not in `core.md`.

## Session execution profile

The planner persists **## Execution Recommendation** under `# Plan`:

```markdown
## Execution Recommendation

- **Complexity:** low | medium | high
- **Recommended Model Tier:** Fast/Cheap | Balanced | High-Reasoning
- **Reasoning Depth:** minimal | standard | invariant-first
- **Rationale:** <one sentence>
```

`current-handoff.md` mirrors `Recommended Model`, `Complexity`, and
`Reasoning Depth`. The Cursor `session-dispatch` rule gates
`/couch-python-coder` and `/couch-reviewer` when a high-complexity plan
recommends a tier above the active chat model.

## Project-scoped development config

The CouchPilot repository itself ships project-level Cursor configuration in
`.cursor/` (version controlled, **not** installed by `sync.py`):

| Path | Purpose |
|---|---|
| `.cursor/rules/asset-authoring.mdc` | Standards for `couchpilot/assets/**` |
| `.cursor/rules/compiler-conventions.mdc` | Standards for compiler/sync Python |
| `.cursor/commands/validate-assets.md` | `/validate-assets` — run tests + dry-run |
| `.cursor/commands/new-asset.md` | `/new-asset` — scaffold a canonical asset |
| `.cursor/skills/new-asset/SKILL.md` | Guided new-asset workflow |
| `.cursor/skills/extend-host-profile/SKILL.md` | Add a new host target |

Project commands use unprefixed names to avoid colliding with installed
`couch-*` slash commands.

## Testing

`tests/test_compiler.py` exercises discovery, synthesis, validation, rendering,
and path mapping with synthetic fixtures. Run:

```bash
python3 -m unittest discover -s tests
python3 sync.py --dry-run
```

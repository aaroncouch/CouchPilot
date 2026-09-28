---
name: new-asset
description: Scaffold a new canonical CouchPilot asset under couchpilot/assets/.
---

# New Canonical Asset

Guided workflow for adding an asset to `couchpilot/assets/<asset-id>/`.
Read `couchpilot/FORMAT.md` and `.cursor/rules/asset-authoring.mdc` before starting.

## Step 1: Choose Asset ID

- kebab-case slug: `my-feature`, `audit-widget`, `python-lint-helper`
- Must not collide with an existing directory under `couchpilot/assets/`
- Installed name will be `couch-<asset-id>`

## Step 2: Choose Asset Role

| Role | When to use | Scaffold |
|---|---|---|
| **Shared rule** | Same logic on Cursor and Claude; global or path-scoped | `core.md` with `family: rule` only |
| **Path-scoped rule** | Rule applies to specific file patterns | `core.md` with `family: rule` + `globs` |
| **Cursor subagent** | Delegated worker (planner, coder, reviewer pattern) | `core.md` + `cursor/agent.md` with `{{core}}` |
| **Cursor command** | Slash command workflow | `core.md` + `cursor/command.md` with `{{core}}`, or command-only |
| **Cursor reference skill** | Worked examples for a rule | `cursor/skill.md` (+ optional `core.md`) |
| **Multi-target manual skill** | Cursor agent + Claude manual skill (planner/reviewer pattern) | `core.md` + `cursor/agent.md` + `claude/skill.md` |
| **Single-platform rule** | One host only (session-dispatch pattern) | `cursor/rule.md` only, no `core.md` |

## Step 3: Scaffold Files

### Shared Global Rule

```text
couchpilot/assets/<asset-id>/core.md
```

```yaml
---
description: <one-line summary>
family: rule
---

# <Title>

<host-neutral body>

Rule id: <unique-id>
```

### Shared Path-Scoped Rule

```yaml
---
description: <one-line summary>
family: rule
globs: "**/*.py"
---
```

Or use a YAML list for multiple globs (see `python-tests/core.md`).

### Multi-Target Subagent (Cursor + Claude)

```text
couchpilot/assets/<asset-id>/
  core.md
  cursor/agent.md
  claude/skill.md
```

`cursor/agent.md`:

```yaml
---
model: inherit
---

# Cursor wrapper

<host-specific session/announcement protocol>

{{core}}
```

`claude/skill.md`:

```yaml
---
disable-model-invocation: true
---

# Claude wrapper

<host-specific invocation notes>

{{core}}
```

### Cursor-Only Command

```text
couchpilot/assets/<asset-id>/
  core.md          # optional shared body
  cursor/command.md
```

## Step 4: Author Content

Apply polyglot conventions from asset-authoring:

- Paired decision tables for guardrails
- `<bad_example>` / `<good_example>` for few-shot pairs
- Trailing `Rule id:` or `Skill id:` verification tokens
- Host neutrality in `core.md`

## Step 5: Validate

```bash
python3 -m unittest discover -s tests
python3 sync.py --dry-run
```

Fix every compiler error. Inspect rendered frontmatter:

- Global rules: Cursor `alwaysApply: true`; Claude no `paths`
- Path-scoped: Cursor `alwaysApply: false` + `globs`; Claude `paths: [...]`

## Step 6: Sync (Operator)

After merge, the operator runs `python sync.py` to install to `~/.cursor`
and/or `~/.claude`. Project `.cursor/` config is separate and version-controlled.

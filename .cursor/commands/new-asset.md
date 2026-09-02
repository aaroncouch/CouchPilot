---
description: Scaffold a new canonical CouchPilot asset directory.
---

# New Asset

Create a starter directory under `couchpilot/assets/<asset-id>/`.

## Usage

```text
/new-asset <asset-id> <type>
```

**Types:** `rule` | `path-rule` | `agent` | `command` | `skill` | `multi-target`

Examples:

```text
/new-asset widget-lint rule
/new-asset python-utils path-rule
/new-asset fixer-bot agent
/new-asset run-checks command
/new-asset widget-examples skill
/new-asset architect multi-target
```

## Behavior

1. Confirm `<asset-id>` is kebab-case and does not already exist under
   `couchpilot/assets/`.
2. Load the **new-asset** skill (`.cursor/skills/new-asset/SKILL.md`) for
   the full workflow and polyglot authoring standards.
3. Scaffold the directory for the requested type:

| Type | Files created |
|---|---|
| `rule` | `core.md` with `family: rule` |
| `path-rule` | `core.md` with `family: rule` and placeholder `globs` |
| `agent` | `core.md`, `cursor/agent.md` with `{{core}}` |
| `command` | `core.md`, `cursor/command.md` with `{{core}}` |
| `skill` | `cursor/skill.md` (and `core.md` if shared body needed) |
| `multi-target` | `core.md`, `cursor/agent.md`, `claude/skill.md` |

4. Assign a unique placeholder `Rule id:` or `Skill id:` token.
5. Run validation:

   ```bash
   python3 -m unittest discover -s tests
   python3 sync.py --dry-run
   ```

6. Report created paths and any validation errors.

## Guardrails

- Do not create `cursor/rule.md` / `claude/rule.md` for shared rules — use
  `family: rule` in `core.md` instead.
- Do not edit `~/.cursor` or `~/.claude` directly; assets compile via `sync.py`.
- Project commands use unprefixed names (`/new-asset`, `/validate-assets`) to
  avoid colliding with installed `couch-*` slash commands.

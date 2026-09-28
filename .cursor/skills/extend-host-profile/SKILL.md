---
name: extend-host-profile
description: Register a new CouchPilot install host target in hosts.py and couchpilot.json.
---

# Extend Host Profile

Workflow for adding a new install target (e.g. a future Codex or Aider host)
to CouchPilot's centralized profile registry.

Read `couchpilot/hosts.py`, `couchpilot.json`, and `couchpilot/FORMAT.md`
before starting.

## Step 1: Define the Profile Subclass

In `couchpilot/hosts.py`, create a frozen dataclass subclass when the host
needs custom frontmatter validation:

```python
@dataclass(frozen=True)
class NewHostProfile(HostProfile):
    """NewHost-specific host profile."""

    def validate_family_frontmatter(
        self, family: str, frontmatter: dict[str, Any]
    ) -> list[str]:
        errors: list[str] = []
        # Add host-specific required fields per family
        return errors
```

Use the base `HostProfile` directly when no custom validation is needed.

## Step 2: Register in `create_default_profiles()`

Add an entry to the dict returned by `create_default_profiles()`:

```python
"newhost": NewHostProfile(
    name="newhost",
    default_install_dir="~/.newhost",
    extensions={"rule": "md", "command": "md", "agent": "md", "skill": "md"},
    family_directories=dict(_FAMILY_DIRECTORIES),
    default_frontmatter={
        "rule": {},
        "command": {},
        "agent": {"model": "inherit"},
        "skill": {},
    },
    style_dialect="universal_xml",
    wrapper_template=dict(_WRAPPER_TEMPLATE),
),
```

Required `HostProfile` fields:

| Field | Purpose |
|---|---|
| `name` | Target key used by `get_host_profile()` and `sync.py --target` |
| `default_install_dir` | Install root (supports `~/` prefix) |
| `extensions` | File extension per family (`rule`, `command`, `agent`, `skill`) |
| `family_directories` | Subdir under install root per family |
| `default_frontmatter` | Defaults merged into synthesized wrappers |
| `style_dialect` | Prompt convention hint (`universal_xml`, `anthropic_xml`, etc.) |
| `wrapper_template` | Body template per family (usually `{{core}}\n`) |

## Step 3: Add `couchpilot.json` Override (Optional)

```json
{
  "hosts": {
    "newhost": {
      "install_dir": "~/.newhost",
      "style_dialect": "universal_xml",
      "default_frontmatter": {
        "agent": { "model": "inherit" }
      }
    }
  }
}
```

`load_host_profiles()` merges these overrides onto built-in defaults.

## Step 4: Wire Sync Target

Ensure `sync.py` recognizes the new target name (it reads from
`HOST_PROFILES` keys). Pass `--target newhost` to compile and install only
that host.

## Step 5: Add Tests

In `tests/test_compiler.py`:

1. Assert the new profile appears in `HOST_PROFILES` / `create_default_profiles()`.
2. Test `validate_family_frontmatter` for required and valid frontmatter.
3. Test `destination_for("newhost", family, asset_id)` path mapping.
4. If config overrides apply, add a `LoadHostProfilesTests` case.

Run:

```bash
python3 -m unittest discover -s tests
python3 sync.py --dry-run --target cursor
```

Add `--target newhost` once the profile is registered and sync supports it.

## Checklist

- [ ] Subclass validates host-specific frontmatter (if any)
- [ ] Registered in `create_default_profiles()`
- [ ] Optional entry in `couchpilot.json`
- [ ] Tests cover validation, paths, and config merge
- [ ] `FORMAT.md` updated if install layout differs from Cursor/Claude

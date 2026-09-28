---
description: Run CouchPilot compiler validation and sync dry-run.
---

# Validate Assets

Verify that all canonical assets under `couchpilot/assets/` compile cleanly.

## Usage

```text
/validate-assets
```

## Behavior

1. Run the full unit test suite:

   ```bash
   python3 -m unittest discover -s tests
   ```

2. Run a sync dry-run to validate every asset renders without writing files:

   ```bash
   python3 sync.py --dry-run
   ```

3. Report results:
   - If both pass: confirm test count and dry-run artifact count.
   - If either fails: paste the failing output and identify which asset or
     test case broke. Do not claim success.

## When to Use

- After editing any file under `couchpilot/assets/`
- After changing `couchpilot/compiler.py` or `couchpilot/hosts.py`
- Before opening a PR that touches canonical prompts or compile logic

## Output Contract

```markdown
## Validation Results

- **Tests:** <pass | fail> — `<command>` → <summary>
- **Dry-run:** <pass | fail> — `<command>` → <artifact count or error>

<If fail: list each error with asset path or test name>
```

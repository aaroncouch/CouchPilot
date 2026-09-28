---
description: Adjudicate external review comments (e.g. Copilot, PR comments) against code and record substantiated findings.
---

# Adjudicate Review Core

Evaluate external automated or human review comments (e.g. GitHub Copilot, PR
review bots, peer comments) against the actual codebase, plan invariants, and
tests. Filter out false positives, substantiate valid issues, and record
actionable findings to `.session/REVIEW.md`.

## Usage

`/couch-adjudicate-review <path-to-external-review-file-or-notes>`

Example:

`/couch-adjudicate-review .session/copilot-review.json`
`/couch-adjudicate-review .session/pr-comments.md`

## Preconditions

1. Active CouchPilot session (`.session/active-session.txt` with valid `task_id`).
2. Target review file or input text exists and contains external comments.
3. Access to current codebase and diff to inspect referenced lines and context.

## Adjudication Protocol

### 1. Ingest Comments

Read the external review artifact. Parse individual comments:
- File path and line reference
- Comment body / suggested change
- Author / tool source (e.g. GitHub Copilot, reviewer)

### 2. Verify Against Code & Invariants

For each comment, inspect the referenced code, tests, and active plan:
1. Check if the comment reflects actual behavior or an incorrect assumption/hallucination.
2. Check if the issue violates project contracts, code quality rules, or test integrity.
3. Check if the issue is already handled elsewhere in the call path.
4. Check if the comment suggests out-of-scope refactoring or invalid changes.

### 3. Classify Each Comment

Assign exactly one adjudication status:

| Classification | Meaning | Action |
|---|---|---|
| `[BLOCKING]` | Valid bug, regression, security risk, broken invariant, or missing critical test | Record to `.session/REVIEW.md` as `[BLOCKING]` |
| `[SUGGESTION]` | Valid non-blocking improvement (clarity, typing, docstring) within scope | Record to `.session/REVIEW.md` as `[SUGGESTION]` |
| `[DISMISSED]` | False positive, hallucination, incorrect premise, already fixed, or out-of-scope | Do not write to `REVIEW.md`; justify in chat report |

### 4. Update Session State

1. **Update `.session/REVIEW.md`:**
   - Preserve existing unresolved findings.
   - Append newly substantiated `[BLOCKING]` and `[SUGGESTION]` findings.
   - Do not write `[DISMISSED]` items to `REVIEW.md`.
2. **Update `.session/STATE.md`:**
   - If any `[BLOCKING]` finding was substantiated: set `Status: needs-fix`, `Next action: dispatch-python-coder to address review findings`.
   - If only `[SUGGESTION]` findings were substantiated: set `Status: ready-to-close` (or `ready-for-code` if operator wants suggestions applied).
   - If all comments were `[DISMISSED]`: preserve current status and note zero actionable findings.
   - Set `last_updated: <ISO8601 now>` (resolved from system context or `date -u +"%Y-%m-%dT%H:%M:%SZ"` / `date -Iseconds`), `last_agent: adjudicate-review`.

## Artifact Output Contract

Fill this template for the chat report:

```markdown
## External Review Adjudication: `<path-or-source>`

### Substantiated Findings

#### `<path>`

- `[BLOCKING]` `<path>:<line>`: <concise description of verified defect and why it matters>
- `[SUGGESTION]` `<path>:<line>`: <verified non-blocking improvement>

<!-- Repeat per file in line order. If none substantiated: "No blocking or suggestion findings substantiated." -->

### Dismissed Comments

- `<path>:<line>`: **Dismissed** (<reason: false-positive | already-fixed | incorrect-assumption | out-of-scope>) - <one-line technical justification citing code reality>

### Summary & State Update

- **Total evaluated:** <count>
- **Substantiated blocking:** <count>
- **Substantiated suggestions:** <count>
- **Dismissed:** <count>
- **REVIEW.md:** <updated with N new findings | unchanged>
- **STATE.md:** <new status and next action>

Verdict: <approve | approve with comments | request changes>
```

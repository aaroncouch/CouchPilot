---
description: Migrate a legacy .cursor/scratch session to the context-efficient .session layout.
---

# Migrate Session

Convert a legacy monolithic session (`.cursor/scratch/current-handoff.md`,
`.cursor/scratch/session-log.md`, `.cursor/scratch/active-session.txt`) into the
modern four-artifact `.session/` format (`STATE.md`, `PLAN.md`, `REVIEW.md`,
`HISTORY.md`, `active-session.txt`).

## Usage

`/couch-migrate-session [optional task-id or path override]`

Example:

`/couch-migrate-session`
`/couch-migrate-session task: p1-04-alert-threshold-hotfix`

## Preconditions

1. Locate the legacy session files:
   - Primary source: `.cursor/scratch/`
   - Files to inspect:
     - `.cursor/scratch/active-session.txt` (or `.session/active-session.txt` if partially migrated)
     - `.cursor/scratch/current-handoff.md` (or `handoff.md`)
     - `.cursor/scratch/session-log.md`
2. If legacy files are missing or no active task can be resolved, report the
   blocker and stop.
3. Ensure `.session/` exists and `.session/.gitignore` contains:

```text
*
!.gitignore
```

4. Ensure `.session/` is ignored by root `.gitignore` (add `.session/` if absent).

## Migration Procedure

### 1. Parse Legacy Artifacts

Read and extract:
- **Task Identity:** `task_id`, `started_at`, `git_ref` from legacy `active-session.txt` or `current-handoff.md`.
- **Handoff State:** `Status`, `Next action`, `Review need`, `Recommended Model`, `Complexity`, `Reasoning Depth`, `Scope`, `Open risks`, `Validation`, `Changed files` from `current-handoff.md`.
- **Log Structure:** Split `session-log.md` into sections:
  - `# Task requirements` / initial context
  - `# Plan` / execution plans / slices
  - `# Findings` / review discussions / verdicts
  - Dated entries / step logs / progress narratives

### 2. Disambiguation & Operator Queries

Because legacy logs often interleave historical narratives with live work,
**stop and ask the operator** if any of the following are ambiguous:
- **Active vs. Completed Work:** If multiple plans, steps, or slices appear in
  `session-log.md` and it is unclear which step is currently active vs completed.
- **Review Findings:** If findings exist under `# Findings` or review logs but
  it is unclear which are open/blocking vs already resolved.
- **Durable Decisions:** If architectural decisions or constraints are buried
  inside conversation notes and may need promotion to `STATE.md` or `HISTORY.md`.

*When asking, present specific excerpts and choices rather than open-ended questions.*

### 3. Project to the 4 Artifacts

Resolve current ISO8601 timestamp (use ambient system timestamp context or run
`date -u +"%Y-%m-%dT%H:%M:%SZ"` / `date -Iseconds`; never guess or extrapolate).

1. **`STATE.md` (Hot Runtime Context):**
   - Populate frontmatter (`task_id`, `started_at`, `last_updated: <ISO8601 now>`, `last_agent: migrate-session`, `git_ref`).
   - Populate status fields from `current-handoff.md` (mapping legacy status to standard vocabulary).
   - Set `Objective`, `Current task`, `Decisions`, `Inputs`, `Acceptance criteria`, `Open findings`, `Blockers`, `Next action`.

2. **`PLAN.md` (Live Workstream):**
   - Extract `# Task requirements` from the legacy log or handoff.
   - Extract the active plan or active slice into `# Active task`.
   - Place remaining pending slices into `# Queued tasks`.
   - Exclude completed steps and historical commentary.

3. **`REVIEW.md` (Open Work Queue):**
   - Extract only currently **open, unresolved** findings into `# Open findings`.
   - If all past findings were resolved or none exist, write `(none)`.

4. **`HISTORY.md` (Cold Audit Trail):**
   - Condense completed slices, historical step narratives, past review approvals, and session creation events into chronological append-only bullets or entries.
   - Append: `- <ISO8601> [migrate-session] Migrated session from legacy .cursor/scratch format.`

5. **`active-session.txt` (Pointer):**
   - Write `.session/active-session.txt` pointing to `.session/STATE.md`, `.session/PLAN.md`, `.session/REVIEW.md`, and `.session/HISTORY.md`.

### 4. Legacy Cleanup & Archiving

- Back up legacy files by moving `.cursor/scratch/current-handoff.md` and
  `.cursor/scratch/session-log.md` to `.session/archive/legacy-<ISO8601-timestamp>/`
  (or `.cursor/scratch/archive/`).
- If `.cursor/scratch/active-session.txt` exists, remove or clear it so tools do
  not detect dual session pointers.

## Output

Return:
- migrated task id
- created `.session/` file paths
- summary of open findings preserved in `REVIEW.md`
- summary of active vs queued tasks in `PLAN.md`
- location of archived legacy files

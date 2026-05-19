# Task Brief

Distill rough task notes into a concise brief that can later seed
`/begin-session`.

## Usage

`/task-brief <raw task notes, rambling, logs, links, constraints, and questions>`

Example:

`/task-brief I need to fix the flaky nightly report job. It sometimes double-sends emails after retries. Preserve current API; probably look at report_worker.py and tests around retry state.`

## Behavior

1. Read the provided raw notes.
   - If no notes are provided, ask the operator to paste the task rambling or
     describe the problem.
2. Derive a structured brief with:
   - suggested `task_id` in kebab-case
   - problem
   - desired outcome
   - constraints
   - acceptance criteria
   - important files / links / evidence
   - known risks
   - open questions
3. Ask clarification only when missing information would materially change the
   task boundary, safety, or likely implementation path.
   - If a detail is helpful but not required, keep it as `TBD` or an open
     question instead of blocking.
4. Ensure `.cursor/scratch/.gitignore` exists with:

```text
*
!.gitignore
```

5. Ensure `.cursor/scratch/` is ignored by the target repo:
   - If the workspace has a root `.gitignore`, add `.cursor/scratch/` only if
     an equivalent ignore is missing.
   - If there is no root `.gitignore`, create one with `.cursor/scratch/`.
   - If any `.cursor/scratch/` files are already tracked by git, report that
     blocker; `.gitignore` does not untrack existing tracked files.
6. Write the latest brief to `.cursor/scratch/task-brief.md` with this scaffold:

```text
---
created_at: <ISO8601 now>
last_updated: <ISO8601 now>
source: task-brief
status: ready-for-session
---

# Task brief

Suggested task id: <kebab-case-slug>

## Problem
<what is wrong or what needs to change>

## Desired outcome
<what success looks like>

## Constraints
- <hard constraint or "none known">

## Acceptance criteria
- <done-when statement>

## Important files / links / evidence
- <path, URL, issue, log snippet summary, or "none provided">

## Known risks
- <risk or "none known">

## Open questions
- <question or "none">

## Begin-session seed
`/begin-session task: <kebab-case-slug> <one concise paragraph containing the durable task context above>`
```

7. Do not create, switch, close, or modify any active session.
   - Do not edit `.cursor/scratch/active-session.txt`.
   - If an active session already exists, leave it untouched and report that the
     brief is staged for a future `/begin-session`.

## Output

Return:
- suggested task id
- brief path
- whether clarification is still recommended
- the exact `/begin-session task: ...` seed, or say to run
  `/begin-session use previous task brief`

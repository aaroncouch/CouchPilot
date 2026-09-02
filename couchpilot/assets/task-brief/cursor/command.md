# Cursor task-brief wrapper

Use raw task notes, logs, links, constraints, and questions as input. Ensure
`.cursor/scratch/.gitignore` contains `*` and `!.gitignore`. Ensure the target
repository ignores `.cursor/scratch/` without changing already tracked files.

Write the brief to `.cursor/scratch/task-brief.md`. Do not alter
`.cursor/scratch/active-session.txt`; if a session is active, stage the brief
for later use. Return the suggested task ID, brief path, clarification status,
and a `begin-session` workflow seed using the task ID and durable context.

{{core}}

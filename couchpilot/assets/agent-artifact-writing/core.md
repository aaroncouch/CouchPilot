---
description: Write agent-facing artifacts as concise, factual operational records.
family: rule
---

# Agent Artifact Writing

Apply to agent-facing artifacts: `.cursor/**`, `.claude/**`, `.cursor/scratch/**`,
`AGENTS.md`, prompts, commands, rules, skills, session state, and generated
task/session artifacts. Do not apply human-facing writing guidance.

## Formatting Rules

| Rule | Required Action | Prohibited Shortcut |
|---|---|---|
| Uncertainty | Preserve uncertainty; state what is known | Inferring causes, ownership, timelines, risks, or completion |
| Evidence | Prefer paths, anchors, identifiers, exact commands, and actual results | Paraphrasing tool output or omitting command evidence |
| Scope | Record decisions, constraints, changed state, and validation evidence | Pasting an implementation transcript or chat narrative |
| Tone | Compact, factual, operational | Introductions, conclusions, greetings, closing offers, filler, or nonessential excerpts |
| Structure | Preserve established headings, fields, and status vocabulary | Renaming fields or inventing parallel status terms |
| `AGENTS.md` | Keep concise, project-specific, and evidence-backed | Generic CouchPilot policy, model prompts, session state, or chat formatting |

## `.cursor/scratch/**` Files

Session scratch files are durable operational records, not chat logs.

- One fact per line or bullet where possible.
- Use the file's declared field names and status vocabulary exactly.
- Timestamp dated `##` entries in ISO8601 when appending to logs.
- Record gate results as `<command>` → `<last line of real output>`.
- Keep handoff fields (`Status`, `Next action`, `Review need`, `Open risks`) current and mutually consistent.
- Do not duplicate content already in `session-log.md` unless the handoff requires a read-first summary.

Rule id: aaw-1

---
description: Maintain a concise, project-specific AGENTS.md guide for future agents.
family: rule
---

# Repository Project Guide

## Before broad workspace changes

| Scenario | Required Action | Prohibited Shortcut |
|---|---|---|
| Planning, reviewing, or changing repository files | Read root `AGENTS.md` if present before proceeding | Applying CouchPilot defaults alone when the repository defines its own guidance |
| Repository guidance conflicts with CouchPilot defaults | Follow repository-specific guidance; it wins on conflict | Ignoring or overriding documented project conventions |
| Agent-facing documentation needed | Treat `AGENTS.md` as an agent-facing artifact under the agent-artifact-writing contract | Creating a duplicate `CLAUDE.md` wrapper solely to include it |

Root `AGENTS.md` is additive to CouchPilot defaults. Inspect it early — before scoping work, before large refactors, and before assuming default conventions apply.

Rule id: pg-1

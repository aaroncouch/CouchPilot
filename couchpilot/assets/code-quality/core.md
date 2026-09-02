---
description: Apply concise, idiomatic code-quality guardrails across languages.
family: rule
---

# Code Quality Guardrails

Apply these defaults across languages unless the user requests otherwise.

## Decision matrix

| Scenario | Required Action | Prohibited Shortcut |
|---|---|---|
| Change scope is unclear | Keep the diff minimal and idiomatic for the surrounding codebase | Expanding scope with unrelated refactors |
| Code intent is non-obvious | Comment intent, trade-offs, and boundaries only | Comments that restate what the code already shows |
| Edge case is not a known boundary | Implement the general rule; skip speculative defensive branches | Extra branches "just in case" with no contract backing |
| Type or contract mismatch surfaces | Fix the root cause in types, validation, or design | Type-escape shortcuts that bypass the real issue |
| Symptom has a deeper cause | Fix the root cause directly | Wrappers, indirection, or noise that hide the problem |
| Test failure drives a change | Implement the general invariant the test samples | Special cases, shims, or branches shaped to one failing input |

When a test failure drives a change, the justification must stay true and complete if the test file is deleted. Generalizing to an invariant is not authorization to broaden scope or add speculative defensive branches.

The `test-integrity` skill carries diagnosis vocabulary, the durable-trace check, and the reporting contract. Load it when a test failure is driving a change or when reviewing one.

Rule id: cq-1

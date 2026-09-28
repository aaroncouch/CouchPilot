---
description: Apply the project's Python implementation conventions.
family: rule
globs: "**/*.py"
---

# Python Guardrails

Write to pylint's standard. Even when a project gates on ruff or on nothing at
all, pylint discipline is the authoring standard here. The value is the
feedback loop, not the tool.

## Design caps

Pylint stock defaults, line length 100, target py3.12. Honor the project's own
config when it differs; these apply when it has none.

| Check | Cap |
|---|---|
| `R0913` too-many-arguments | 5 |
| `R0902` too-many-instance-attributes | 7 |
| `R0912` too-many-branches | 12 |
| `R0914` too-many-locals | 15 |
| `R0911` too-many-return-statements | 6 |
| `R0915` too-many-statements | 50 |

**Caps are failure lines, not targets.** A function at 10 branches wants
splitting even though 12 still passes.

## Pre-delivery verification checklist

Every public change must pass these checks before delivery:

| Code | Check | Required state |
|---|---|---|
| `C0103` | invalid-name | snake_case functions/variables, PascalCase classes, UPPER_CASE constants; names state intent (`pending_origins`, not `data`) |
| `E722` | bare-except | Catch specific exception types only |
| `W0718` | broad-exception-caught | Catch specific types; never swallow with a broad handler |
| `R1710` | inconsistent-return-statements | One return shape per function |
| `R1705` | no-else-return | Early returns instead of nested else branches |
| `W0611` | unused-import | No unused imports |
| `W0612` | unused-variable | No unused variables |
| `W0613` | unused-argument | No unused arguments |
| `W0603` | global-statement | Pass dependencies through the constructor, not module globals |
| `C0115` | missing-class-docstring | Public classes documented |
| `C0116` | missing-function-docstring | Public functions and methods documented |

`C0114` module docstrings are optional.

## Linter disable gate

| Scenario | Required Action | Prohibited Shortcut |
|---|---|---|
| A pylint check triggers on your change | Refactor the code until the check passes cleanly | Adding `# pylint: disable=`, `# noqa`, or `# type: ignore` without authorization |
| A disable is strictly unavoidable | Stop and request explicit operator authorization before adding any inline disable | Silencing the check to avoid redesign |

A disable is a request to change the code, not the config.

## Typing

Type-hint every public function, method, and return value. Avoid `Any`; justify
it in one line when unavoidable.

Architecture guidance and worked examples live in the `python-style` skill,
which attaches on the same files. Test conventions live in the `python-tests`
rule.

Rule id: py-1

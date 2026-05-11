---
name: python-style
description: Explicit deep reference for the project owner's Python style. Read only when a prompt asks for the detailed Python style guide.
disable-model-invocation: true
---

# Python Coding Style

The goal: code so plain that intent is obvious on first read, and so
clean that running the project's lint and format tools produces zero
findings.

This skill is intentionally explicit rather than automatically selected. The
automatic layer lives in the rules: cross-language quality defaults, Python
guardrails, and Python test conventions. Treat those rules as authoritative for
everything they cover; this skill only adds details that do not fit cleanly in a
rule.

## Documentation

- Every public class, method, and function has a docstring.
- Docstrings describe intent, arguments, return value, and raised
  exceptions.
- Pick one docstring style (Google or NumPy) and apply it consistently
  across the module.
- Comments explain *why*, not *what*. The code already shows what.
- Module docstrings state the module's purpose in two or three
  sentences.

## Anti-patterns to avoid

- Long procedural top-level scripts that should be classes.
- Magic numbers and string literals scattered through code; promote to
  named constants.
- Vague names (`data`, `info`, `obj`, `do_stuff`).
- Broad `except Exception` that swallows errors silently.
- Mutating shared state across module boundaries.
- Returning different types from the same function based on input.
- Functions with five or more positional parameters; introduce a
  dataclass.
- Comments that restate the next line of code.
- Boolean parameters that flip behavior; prefer two named methods.

## Reporting back

When the task is complete, summarize:

- What changed, in one or two sentences.
- The actual results from each quality gate that ran (lint score, test
  result, etc.) — there should be no remaining findings.
- Any tests added or updated.
- Anything the user should review or decide on next.

Python coder subagents should also report resolved project tooling and its
provenance. Use the "Project tooling discovery" section in the active Python
coder subagent prompt.

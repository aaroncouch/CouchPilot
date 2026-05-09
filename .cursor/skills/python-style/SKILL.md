---
name: python-style
description: Use when writing or editing Python code so it matches the project owner's style, simple, OOP-first, well-documented, and PyLint-clean. Authoritative reference for the /python-coder subagent.
---

# Python Coding Style

This skill is the authoritative reference for *how* Python code should be
written. Read it once on entry to any Python authoring or editing task, then
follow it strictly while implementing.

The goal is code so plain that intent is obvious on first read, and so clean
that running `black` and `pylint` produces zero findings.

The concrete tooling baselines (line length, design caps, PyLint configuration
values) live in the `python` rule at `~/.cursor/rules/python.mdc`. This skill
covers the philosophy and the patterns; the rule covers the numbers.

## 1. When to use

Apply this skill on any task that creates, edits, refactors, or reviews Python
source. It governs both production code and test code, with a small extension
for tests covered by the `python-tests` rule.

## 2. Voice and clarity

- Write the simplest code that solves the problem; cleverness is a cost, not a feature.
- Names describe intent, not type or implementation. `pending_orders` beats `data`.
  `load_config` beats `process`.
- One idea per function. If a function needs the word "and" to describe it, split it.
- Keep functions short enough to read on one screen. Aim for under 30 lines of body.
- Keep modules narrow. A module with one clear job is easier to test and reuse.
- Use early returns to flatten control flow; avoid deeply nested conditionals.

## 3. Architecture: prefer OOP over procedural

For any non-trivial logic, model the domain with classes that own both state
and the behavior that operates on it.

- A class should have one clear responsibility, expressible in a short sentence.
- Keep public surface small. Anything not part of that surface is `_private`.
- Prefer composition over inheritance. Inherit only when there is a true
  is-a relationship and the parent is designed for extension.
- Pass dependencies in via the constructor; do not reach for module-level globals.
- Put data and the operations on that data in the same class. If a free function
  keeps reaching for the same dict or tuple, that is a class waiting to exist.
- Use `@dataclass` for value objects. Use a regular class when behavior matters.
- Keep procedural top-level scripts to thin entrypoints (`main()` plus argparse);
  delegate real work to classes immediately.

## 4. Typing

- Type-hint every public function, method, and return value.
- Add explicit types for non-trivial internal helpers as well.
- Avoid `Any`. When unavoidable, leave a one-line comment justifying it.
- Prefer narrow concrete types over broad unions. `list[Path]` beats `Iterable[Any]`.
- Keep public signatures stable; breaking them requires updating tests.

## 5. Documentation

- Every public class, method, and function has a docstring.
- Docstrings describe intent, arguments, return value, and raised exceptions.
- Use the same docstring style consistently across the module (Google or NumPy
  style is fine; pick one and stick with it).
- Comments explain *why*, not *what*. The code already shows what it does.
- Module docstrings state what the module is for in two or three sentences.

## 6. Error handling

- Raise specific exception types (`ValueError`, `FileNotFoundError`, custom
  domain exceptions); never `raise Exception(...)`.
- Error messages are actionable: state what failed, what was expected, and
  ideally what the caller can do about it.
- Never use bare `except:` or `except Exception:` as a catch-all unless you
  re-raise or log with full traceback and have a deliberate reason.
- Validate inputs at the boundary of the system; trust them inside.
- Fail fast on programmer errors; recover gracefully from environmental ones.

## 7. Quality gates

Before declaring a task done, run the project's quality tools and report
results. The tools depend on the project: see section 11 for the discovery
procedure and fallback chain.

The user-scope **baseline** (used when a project declares no tooling of its
own) is `black` for format, `pylint` for lint, `pytest` for tests.

Rules of engagement, regardless of which specific tools the project uses:

- A finding means the code needs to change, not the linter.
- Do **not** add inline disables (`# pylint: disable=...`, `# noqa`,
  `# type: ignore`) without explicit user approval. If a disable is
  genuinely warranted, ask first and explain why the underlying code
  cannot be fixed.
- If you must restructure for a lint score, prefer extracting a helper class
  or method over hiding the warning.
- If a test fails, fix the underlying code (or the test if it was wrong);
  do not skip or `xfail` without approval.

The numerical baselines (line length, py-version, design caps) come from the
`python` rule. Code should sit comfortably under those caps, not press against
them, regardless of how strict the project's actual config is.

## 8. Tests

- When behavior changes, update or add tests in the same change.
- For full test conventions (pytest, fixtures, regression coverage, determinism)
  see the `python-tests` rule, which is auto-applied to test files.

## 9. Anti-patterns to avoid

- Long procedural top-level scripts that should be classes.
- Magic numbers and string literals scattered through code; promote to named constants.
- Vague names (`data`, `info`, `obj`, `do_stuff`).
- Broad `except Exception` that swallows errors silently.
- Mutating shared state across module boundaries.
- Returning different types from the same function based on input.
- Functions with five or more positional parameters; introduce a dataclass.
- Comments that restate the next line of code.
- Boolean parameters that flip behavior; prefer two named methods.

## 10. Reporting back

When the task is complete, summarize:

- What changed, in one or two sentences.
- The discovered project tooling (or "user-scope baseline" if no project
  config was found) and whether it came from cache or fresh discovery.
- The actual results from running each gate (lint score, test result, etc.).
- Any tests added or updated.
- Anything the user should review or decide on next.

## 11. Discovering project tooling

The user-scope baseline is `black`, `pylint`, `pytest`. External projects
often enforce something different (`ruff`, `flake8`, `mypy`, `pyright`,
`pytest-cov`, custom `make` targets). The project's enforcement always
wins over the user-scope baseline. Before running any quality gate, find
out what the project actually uses.

### Cache first

Look for `.cursor/scratch/tooling.md` at the project root. If it exists,
read its YAML frontmatter, which contains a fingerprint of every tooling
configuration file the previous discovery considered. Re-fingerprint the
same files now (sha256 of contents, or `<absent>` if missing). If every
fingerprint still matches, **trust the cache** and use the recorded
tooling for this task. Skip the rest of this section.

If the cache is missing, the fingerprint differs, or a previously-absent
file now exists (or vice versa), the cache is stale. Run discovery below
and rewrite the cache.

### Discovery procedure (only on cache miss/staleness)

Walk this priority order; use the first result that covers each category
(format / lint / type-check / test). Stop probing within a category once
you have a confident answer.

1. **Project automation.** A `Makefile`, `justfile`, or `Taskfile.yml` with
   targets like `lint`, `format`, `test`, `typecheck`. If found, prefer
   those targets over invoking tools directly. The targets are the
   project author's interface; respect them.

2. **`pyproject.toml` tool sections.**
   - Format: `[tool.black]`, `[tool.ruff.format]`, `[tool.autopep8]`, `[tool.yapf]`.
   - Lint: `[tool.pylint]`, `[tool.ruff.lint]`, `[tool.flake8]`.
   - Type check: `[tool.mypy]`, `[tool.pyright]`.
   - Test: `[tool.pytest.ini_options]`, `[tool.coverage]`.

3. **Standalone config files.** `.flake8`, `.pylintrc`, `mypy.ini`,
   `pyrightconfig.json`, `pytest.ini`, `tox.ini`, `.ruff.toml`,
   `setup.cfg`, `.pre-commit-config.yaml`.

4. **CI hints (sanity check, not primary source).**
   `.github/workflows/*.yml`, `.gitlab-ci.yml`, `Jenkinsfile`. Use these
   to confirm what the project actually runs in CI; if CI runs `ruff`
   but `pyproject.toml` only declares `black`, prefer what CI runs.

5. **Fall back to the user-scope baseline.** `black`, `pylint`, `pytest`.
   Note explicitly in your final report that discovery turned up no
   project config so the user knows.

### Cache file format

`.cursor/scratch/tooling.md` looks like this:

````
---
discovered_at: 2026-05-09T15:30:00-04:00
fingerprint:
  Makefile: a3b2c1d...
  pyproject.toml: 4f5e6d...
  justfile: <absent>
  .pylintrc: <absent>
  .flake8: <absent>
  mypy.ini: <absent>
  pyrightconfig.json: <absent>
  pytest.ini: <absent>
  tox.ini: <absent>
  setup.cfg: <absent>
  .ruff.toml: <absent>
  .pre-commit-config.yaml: <absent>
---
# Project tooling

## Format
- Command: `make format`
- Underlying: `ruff format` per Makefile target

## Lint
- Command: `make lint`
- Underlying: `ruff check` per Makefile target

## Type check
- Command: `mypy src/`
- Config: `[tool.mypy]` in pyproject.toml (strict = true)

## Test
- Command: `make test PATTERN=<pattern>`
- Underlying: `pytest -k <pattern>` with coverage via `--cov=src`

## Notes
- No black; `ruff format` only.
- Coverage threshold 80% per `[tool.coverage.report]`.
````

The frontmatter `fingerprint` block lists **every** path in the priority
chain above (whether present or absent), so a future newly-added file is
detected as a fingerprint mismatch.

### Self-contained `.gitignore`

The first time you write `.cursor/scratch/tooling.md`, also create
`.cursor/scratch/.gitignore` with the content:

```
*
!.gitignore
```

This makes the scratch folder gitignore everything inside itself except
its own `.gitignore`, so the tooling cache never gets accidentally
committed regardless of the project's existing gitignore conventions.
You do not need to touch the project's root `.gitignore`.

### State your tooling decision up front

After discovery (or after a cache hit), state the tooling explicitly at
the start of your work, so the user can correct you before you run
anything. Example:

> Tooling for this project (from cache, fingerprint matched):
> `make lint` (ruff via Makefile), `mypy src/` (type check),
> `make test PATTERN=...` (pytest with coverage). No formatter target
> found; using `ruff format` directly.

### Coverage and secondary tools

Run coverage, security audits (`bandit`, `pip-audit`), or other secondary
tools **only** if a project automation target invokes them, or if the
user explicitly asks. Do not add them on your own initiative; that's
scope creep.

### When discovery is genuinely ambiguous

If you cannot determine the project's tooling and a quality gate matters
for the task, ask the user one focused question rather than guessing.

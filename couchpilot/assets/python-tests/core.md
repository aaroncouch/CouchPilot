---
description: Apply Python test design and maintenance conventions.
family: rule
globs:
  - "**/tests/**/*.py"
  - "**/test_*.py"
  - "**/*_test.py"
  - "**/conftest.py"
---

# Python Test Guardrails

These guardrails apply to test files only. They extend the core Python rule
with conventions specific to writing tests. Cross-language anti-slop defaults
are enforced globally by the quality rule.

## Framework and structure

| Area | Required Action | Prohibited Shortcut |
|---|---|---|
| Framework | Use pytest | Mixing in `unittest.TestCase` style unless the codebase already does so |
| Shape | Structure each test as Arrange / Act / Assert with blank lines between sections | Dense blocks where setup, action, and assertion blur together |
| Scope | One behavior per test; name describes the behavior in plain language (`test_loader_raises_when_file_missing`) | Multi-behavior tests or opaque names like `test_loader_2` |

## Fixtures

| Area | Required Action | Prohibited Shortcut |
|---|---|---|
| Shared setup | Prefer pytest fixtures over duplicated setup blocks | Copy-pasted arrange blocks across tests |
| Fixture scope | Keep fixtures narrow — one concern each | Fixtures that do five unrelated things |
| Reuse | Place reusable fixtures in `conftest.py` at the appropriate scope | Inline setup that belongs in shared fixtures |

## Parametrization and coverage

| Area | Required Action | Prohibited Shortcut |
|---|---|---|
| Regression | Add a regression test for every bug fix; it must fail on broken code and pass on the fix | Fixing without a test that would have caught the bug |
| Edge cases | Cover empty input, single-element input, boundary values, and documented failure paths | Happy-path-only coverage |
| Contract focus | Assert on observable behavior, not internal call sequences, unless the call sequence is the contract | Testing implementation details that are not part of the public contract |

## Isolation and determinism

| Area | Required Action | Prohibited Shortcut |
|---|---|---|
| Determinism | Keep tests deterministic: no real network, no real clock unless frozen | Reliance on live services, wall clock, or ambient filesystem state outside `tmp_path` |
| Dependencies | Use `monkeypatch`, `tmp_path`, and explicit dependency injection | Global mutable state or call-order-dependent setup |
| Independence | Tests must be independent of one another and of execution order | Shared mutable fixtures or implicit ordering assumptions |

## Assertion style and test integrity

The `test-integrity` rule governs test integrity in full. In test files specifically:

| Scenario | Required Action | Prohibited Shortcut |
|---|---|---|
| Expected value is wrong | Fix the expectation; cite an authoritative source other than the current implementation | Changing expected values to match observed output |
| Assertion is too strict or wrong | Correct the assertion to match the documented contract | Loosening assertions, widening tolerances, `skip`/`xfail`, or dropping parametrize cases to get past a failure |
| External dependency needed | Mock collaborators at the boundary | Mocking the unit under test — a test that passes when the unit is deleted asserts nothing |

## Quality

- Tests are code too: same typing, naming, and clarity standards as production
  code, and the same pylint contract from the `python` rule.
- `W0621` redefined-outer-name fires constantly on fixtures used as parameters.
  That is the pytest idiom, not a defect. Leave it to project config rather
  than adding a disable comment.
- Run `pylint` over the test directory; treat findings as blocking unless the
  user has explicitly accepted a relaxed config for tests.

Rule id: pyt-1

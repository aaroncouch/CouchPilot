---
description: Preserve test integrity and avoid misleading validation.
family: rule
---

# Test Integrity

Optimize for the behavior the tests are intended to verify, not for test passage.

## Decision matrix

Decide which diagnosis applies before writing code, and name it in the report.

| Diagnosis | Scenario | Required Action | Prohibited Shortcut |
|---|---|---|---|
| `implementation-defect` | Code violates the intended invariant; the test caught it | Fix the code to satisfy the general rule | Hardcoding the fixture value, adding a test-only branch, or special-casing one input |
| `incorrect-test` | Test asserts something the specification does not say | Fix the test; cite an authoritative source other than the current implementation | Changing expected values to match observed output, loosening assertions, `skip`/`xfail`, dropping cases, or mocking the unit under test |
| `wrong-assumption` | The requested change rests on something untrue about the system | Stop and report; the task needs restating | Implementing anyway to force the suite green |
| `architecture-conflict` | The correct fix requires changing a contract or structure outside assigned scope | Stop and escalate; operator decision needed | Loosening tests, adding shims, or forcing green despite contract conflict |

The last two diagnoses end the run. Reaching for `implementation-defect` because it lets you keep working is how a special case gets written.

## Invariant framing

When a test failure drives a production change:

- Implement the **general invariant** the test samples, not the failing case alone.
- State a **justification** that stays true and complete if the test file is deleted.
- Put the rule on a durable trace: a validator, exception type, signature, or docstring — not only on the line that fixed the failure.

Generalizing to an invariant is not authorization to broaden scope or add speculative defensive branches.

The `test-integrity-examples` skill shows what these failures look like in Python diffs. Load it when reviewing or implementing test-driven changes.

Rule id: ti-1

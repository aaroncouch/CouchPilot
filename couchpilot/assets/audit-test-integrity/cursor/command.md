---
description: Audit a test suite for integrity and meaningful validation.
---

# Audit test integrity

Read-only audit for code shaped to pass tests rather than to implement the
behavior the tests verify. Changes nothing. It produces a remediation list a
coder can be dispatched against.

## Usage

- `/couch-audit-test-integrity` audits the diff against `main`.
- `/couch-audit-test-integrity workspace` audits tracked and untracked working files.
- `/couch-audit-test-integrity <paths>` audits the named files or directories.

Runs with or without an active session. It does not create, switch, or modify
session state, and it does not write to `session-log.md` or
`current-handoff.md`. Findings land in their own file so reviewer-owned sections
stay reviewer-owned.

## Method

Read the production change and the test that covers it together. A production
change on its own is not enough to judge: the question is whether the code
encodes a rule or encodes what a specific test observed.

For each changed production behavior, try to state why it is correct without
naming a test. Then locate where the rule lives. A rule that exists only on the
line that fixed the failure is a special case wearing a general name.

### Production side

- A literal that matches a fixture value rather than a named constant or a
  configured value.
- A branch keyed to a test-only condition: `PYTEST_CURRENT_TEST`, `"pytest" in
  sys.modules`, a sentinel id, a caller name, a debug flag only tests set.
- A special case reproducing the shape of the fixture instead of the rule the
  fixture samples.
- An early return, a broadened `except`, or a new default that satisfies an
  assertion without the checked behavior existing.
- A shim, adapter, or duplicated path added only where the tested call enters.
- An invariant enforced at one call site when other call sites reach the same
  code with the same exposure.

### Test side

- An expected value changed to match current output, with no source other than
  the implementation.
- Assertions loosened: equality to membership, exact to inequality, a widened
  tolerance.
- `skip`, `xfail`, or removed parametrize cases introduced alongside a code
  change.
- The unit under test mocked, so the assertion exercises the mock.
- A test narrowed to the input that passes.

## Not findings

Not every small change is overfit. A one-line fix that implements a general rule
is correct and should not be flagged. Neither should a genuinely narrow
requirement, a documented special case, or a constant that reads the same in the
fixture because both come from the same specification.

Flag on the justification, not on the size of the diff.

## Do not

- Do not edit source, tests, config, or docs. This command reports only.
- Do not run tests, formatters, or linters.
- Do not dispatch subagents.

## Output

Write `.cursor/scratch/test-integrity-audit.md`, overwriting any previous run:

```text
---
audited: <ISO8601 now>
scope: main-diff | workspace | paths
git_ref: <branch>@<short-sha>
findings: <count>
---

# Test integrity audit

## <relative path>:<line>

- **Severity:** blocking | suspect
- **Observed:** <what the code does>
- **Tie to a test:** <the specific test and the specific dependence>
- **Diagnosis:** implementation-defect | incorrect-test | wrong-assumption | architecture-conflict
- **Invariant that should hold:** <the general rule, stated over inputs>
- **Test-independent justification:** <why that rule is correct, or `none available`>
- **Uncovered input:** <a plausible input the visible tests miss>
- **Remediation:** <what a coder should change, and where the rule should live>
```

Severity:

- `blocking` when no test-independent justification exists for the change.
- `suspect` when a justification exists but the implementation is narrower than
  the invariant it claims, or the rule leaves no durable trace.

When nothing is found, still write the file with `findings: 0` and a one-line
note of what was audited.

Then reply in chat with the counts, the files involved, and one verdict line:

- `Verdict: clean`
- `Verdict: <n> blocking, <n> suspect. See .cursor/scratch/test-integrity-audit.md`

Do not paste the findings into chat. The file is the artifact; dispatch a coder
against it when you want the remediation done.

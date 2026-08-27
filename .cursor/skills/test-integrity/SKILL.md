---
name: test-integrity
description: Worked examples for the test-integrity rule. Shows what shaping code to a test looks like in Python, how to state a behavioral invariant instead, when a failing test is itself the defect, and how to justify a change without referring to a test. Applies when a test failure is driving a code change or when reviewing one.
paths: "**/*.py"
---

# Test Integrity

The `test-integrity` rule carries the enforceable contract and is authoritative
for everything it covers. This skill shows what the failure actually looks like
in Python, because "do not overfit to tests" is an adjective and a diff is not.

The failure is rarely deliberate. It looks like progress: the suite went from
red to green, the change was small, nothing else broke. What makes it a defect
is that the code now encodes *what the test observed* rather than *the rule the
test was sampling*.

## The check that catches it

Two questions, in this order:

1. Delete the test file. Is the change still justified, and is the justification
   still complete?
2. Where does the rule live now? Point at a validator, an exception type, a
   signature, or a docstring. If the only place is the line that fixed the
   failure, it is a special case.

Question 1 is cheap to pass with careful wording. Question 2 is not.

## Diagnosis vocabulary

A failure means one of four things. Decide which before writing code, and name
it in the report:

- `implementation-defect`: the code is wrong and the test caught it. Fix the
  code. This is the common case.
- `incorrect-test`: the test asserts something the specification does not say.
  Fix the test, and name a source other than the current implementation.
- `wrong-assumption`: the requested change itself was based on something untrue
  about the system. Stop and report; the task needs restating.
- `architecture-conflict`: the correct fix requires changing a contract or a
  structure outside the assigned scope. Stop and report.

The last two end the run. Reaching for `implementation-defect` because it is the
one that lets you keep working is how a special case gets written.

## Hardcoding what the fixture happened to contain

<bad_example>

```python
# BAD
def resolve_ttl(self, path: str) -> int:
    if path == "/assets/app.js":
        return 3600
    return self._default_ttl
```

</bad_example>

<good_example>

```python
# GOOD
def resolve_ttl(self, path: str) -> int:
    """Return the TTL in seconds from the most specific behavior matching ``path``."""
    for behavior in self._behaviors_by_specificity():
        if behavior.matches(path):
            return behavior.ttl_seconds
    return self._default_ttl
```

</good_example>

The fixture used `/assets/app.js` because it needed *some* path. The rule being
sampled is "most specific matching behavior wins." The first version is correct
for exactly one input.

## Branching on the test environment

Any condition that is true only under test is disqualifying, however it is
spelled.

<bad_example>

```python
# BAD
if os.getenv("PYTEST_CURRENT_TEST"):
    return _STUB_RESPONSE
if "pytest" in sys.modules:
    timeout = 0
if site_id == "test-site":
    return True
```

</bad_example>

<good_example>

```python
# GOOD
class DistributionService:
    """Reads and writes CDN distributions through an injected client."""

    def __init__(self, client: CdnClient, timeout_seconds: float = 30.0) -> None:
        self._client = client
        self._timeout_seconds = timeout_seconds
```

</good_example>

The need under test was a seam. Injection is the seam. A branch is a second code
path that production never exercises and no one ever reviews.

## A special case where the invariant belongs

The user-facing symptom is one endpoint rejecting bad input. The rule is that no
request without a stable identifier reaches a worker.

<bad_example>

```python
# BAD
def enqueue(self, payload: dict) -> str:
    if not payload.get("site_id"):
        raise ValueError("missing site_id")
    return self._queue.put(payload)
```

</bad_example>

<good_example>

```python
# GOOD
@dataclass(frozen=True)
class WorkRequest:
    """A request accepted for processing.

    Workers key all state on ``site_id``, so a request without one cannot be
    routed, retried, or attributed. Construction rejects it rather than letting
    it fail later in a worker.
    """

    site_id: str
    payload: dict

    def __post_init__(self) -> None:
        if not self.site_id:
            raise MissingSiteIdError("Work requests require a site_id")
```

</good_example>

Both make the test pass. The first enforces the rule at one call site, so the
next entry point that reaches a worker is unprotected. The second puts it on the
type, and the docstring is the durable trace.

Justification for the second, with no test named: *workers key all state on
`site_id`, so a request without one cannot be routed or retried; rejecting it at
construction fails the request at the boundary instead of inside a worker.*

Justification available for the first: *`test_missing_site_id` expects a
`ValueError` from `enqueue`.* That is the tell.

## Bending the test instead

<bad_example>

```python
# BAD
def test_invalidation_batches_paths():
    result = client.invalidate(paths=make_paths(300))
    assert result.request_count >= 1          # was == 3
```

</bad_example>

<good_example>

```python
# GOOD
def test_invalidation_batches_paths():
    result = client.invalidate(paths=make_paths(300))

    assert result.request_count == 3
```

</good_example>

`>= 1` is true for a batching implementation and equally true for one that
ignores the limit and sends a single oversized request. Widening an assertion
removes the only thing that was checking the behavior.

The same applies to changing an expected value to the observed one, adding
`@pytest.mark.skip` or `xfail` alongside a code change, and deleting the
parametrize case that fails.

## Mocking away the thing under test

<bad_example>

```python
# BAD
def test_retries_on_throttle(monkeypatch):
    monkeypatch.setattr(client, "invalidate", lambda paths: Result(attempts=2))

    assert client.invalidate(["/a"]).attempts == 2
```

</bad_example>

<good_example>

```python
# GOOD
def test_retries_on_throttle():
    transport = FakeTransport(responses=[Throttled(), Accepted()])
    client = CdnClient(transport=transport)

    result = client.invalidate(["/a"])

    assert result.attempts == 2
```

</good_example>

Mock the collaborator, never the unit. The first test passes if `invalidate` is
deleted.

## Swallowing the failure

<bad_example>

```python
# BAD
try:
    return self._client.get_distribution(dist_id)
except Exception:
    return DEFAULT_DISTRIBUTION
```

</bad_example>

A broadened `except`, a new default, or an early return that makes an assertion
pass is the same move as a special case: the behavior the test checked for still
does not exist. `W0718` catches the broad form; the narrow form with a
plausible-looking default is the one to watch for.

## When the test is the defect

`incorrect-test` is a real diagnosis and refusing to use it is its own failure
mode. A test is wrong when it asserts something the specification does not say,
depends on an implementation detail that was never a contract, or encodes an
earlier bug.

Change it, and state the source that makes the current expectation wrong:

```text
Diagnosis: incorrect-test
test_resolve_ttl_prefers_first_match asserts registration order wins. The
documented rule in behaviors.py:41 is most-specific-match. The test encodes the
pre-refactor implementation, not the contract. Updated the expectation.
```

What is not available: deciding a test is wrong because the code disagrees with
it. The source has to be something other than the current implementation.

## When to stop

Stop and report instead of implementing when the correct fix would violate the
public contract, break other callers, require an architectural change outside
the assigned slice, or when the requested behavior and the existing design
cannot both be right.

```text
Diagnosis: architecture-conflict
test_worker_reads_site_config expects WorkerPool to read config per job.
Config is loaded once at pool construction (pool.py:22) and shared across
threads. Per-job reads mean either a per-job pool or a locked reload, both
outside this slice. Not implemented. Operator decision needed.
```

That report is a successful run. Forcing the suite green there is not.

## The uncovered input

Before reporting done, name one plausible input or path the visible tests do not
cover, and say whether the change handles it. Empty input, a second call site, a
concurrent caller, a value at the boundary, the same feature combined with
another flag.

```text
Uncovered input: enqueue() called through the bulk import path, which builds
requests directly rather than from HTTP payloads. Handled: it constructs
WorkRequest, so the same rejection applies.
```

If nothing comes to mind, the change is probably shaped to what was visible.

## Reporting back

For each production change driven by a failing test:

- **Diagnosis:** one of `implementation-defect`, `incorrect-test`,
  `wrong-assumption`, `architecture-conflict`.
- **Invariant:** the general rule implemented, stated over inputs.
- **Justification:** why that rule is correct, naming no test.
- **Uncovered input:** one path the visible tests miss, and whether it holds.

Keep it to a few lines per change. This is a record someone can check, not a
narrative.

Skill id: tis-1

---
name: python-style
description: The project owner's Python style reference. Covers worked pylint examples, docstring conventions, anti-patterns pylint cannot catch, and how to report back after a Python task. Applies when writing, editing, or reviewing Python code.
paths: "**/*.py"
---

# Python Coding Style

The goal: code so plain that intent is obvious on first read, and clean enough
that pylint has nothing to say about it.

This skill is the worked-examples layer. The `python.mdc` rule carries the
enforceable contract (caps, codes, the no-disables policy) and is
authoritative for everything it covers. What follows shows what those codes
actually look like in practice, because a message code is easier to satisfy
than an adjective.

For anything that is prose rather than code, `writing-voice` and
`plainspoken-writing` are authoritative. This skill only adds Python formatting
on top: Google sections, where a docstring is required, and what belongs in one.
It does not set the voice, and nothing here overrides the voice those two
establish.

Every pair below is a real pylint check unless marked otherwise. Fix the code;
never silence the check.

## Docstrings

Google style. Required on public classes, methods, and functions (`C0115`,
`C0116`). Module docstrings are optional (`C0114` is off). Private helpers need
one only when intent isn't obvious from the signature.

```python
def resolve_ttl(self, path: str) -> int:
    """Return the cache TTL in seconds that applies to ``path``.

    Args:
        path: Request path, leading slash included.

    Returns:
        TTL in seconds from the most specific matching behavior.

    Raises:
        NoMatchingBehaviorError: If no behavior matches ``path``.
    """
```

Comments explain *why*. The code already shows *what*.

## Architecture

- Classes own state and the behavior over it, one responsibility each.
- Composition over inheritance; pass dependencies through the constructor.
- `@dataclass` for value objects, regular classes when behavior matters.
- Top-level scripts stay thin (`main()` + argparse) and delegate to classes.

## R0913 too-many-arguments

Past five parameters, the signature is carrying a concept that wants a name.

<bad_example>

```python
# BAD
def create_distribution(name, origin, ttl, compress, ipv6, logging, comment):
    ...
```

</bad_example>

<good_example>

```python
# GOOD
@dataclass
class DistributionSpec:
    """Desired state for a CDN distribution."""

    name: str
    origin: str
    ttl_seconds: int = 86_400
    compress: bool = True
    ipv6: bool = True


def create_distribution(spec: DistributionSpec) -> Distribution:
    """Create a distribution matching ``spec``."""
```

</good_example>

## R0912 too-many-branches and R1705 no-else-return

Guard clauses flatten nesting and drop the branch count at the same time.

<bad_example>

```python
# BAD
def validate(self, spec):
    if spec.origin:
        if spec.ttl_seconds > 0:
            if spec.name not in self._existing:
                return True
            else:
                return False
        else:
            return False
    else:
        return False
```

</bad_example>

<good_example>

```python
# GOOD
def validate(self, spec: DistributionSpec) -> bool:
    """Return True when ``spec`` describes a distribution we can create."""
    if not spec.origin:
        return False
    if spec.ttl_seconds <= 0:
        return False
    return spec.name not in self._existing
```

</good_example>

## W0718 broad-exception-caught

A bare `except Exception` turns a specific failure into a silent one.

<bad_example>

```python
# BAD
try:
    return self._client.get_distribution(dist_id)
except Exception:
    return None
```

</bad_example>

<good_example>

```python
# GOOD
try:
    return self._client.get_distribution(dist_id)
except (ClientError, TimeoutError) as error:
    raise DistributionLookupError(
        f"Could not read distribution {dist_id}"
    ) from error
```

</good_example>

`raise ... from error` preserves the cause. Callers get an actionable message
instead of a `None` they have to guess about.

## R1710 inconsistent-return-statements

One return shape per function. Callers should not have to type-check the result.

<bad_example>

```python
# BAD
def find_origin(self, name):
    if name in self._origins:
        return self._origins[name]
    if name in self._aliases:
        return False
    # implicit None on fallthrough
```

</bad_example>

<good_example>

```python
# GOOD
def find_origin(self, name: str) -> Origin:
    """Return the origin registered under ``name``.

    Raises:
        UnknownOriginError: If ``name`` is not registered.
    """
    if name in self._origins:
        return self._origins[name]
    raise UnknownOriginError(f"No origin registered for {name!r}")
```

</good_example>

## C0103 invalid-name

The name should say what the value *is*, not what type it is.

<bad_example>

```python
# BAD
data = self._fetch()
tmp = [x for x in data if x["s"] != "ok"]
```

</bad_example>

<good_example>

```python
# GOOD
distributions = self._fetch()
failed_distributions = [d for d in distributions if d["status"] != "ok"]
```

</good_example>

## W0603 global-statement

Module-level mutable state makes call order load-bearing and tests flaky.

<bad_example>

```python
# BAD
_CLIENT = None

def get_client():
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = build_client()
    return _CLIENT
```

</bad_example>

<good_example>

```python
# GOOD
class DistributionService:
    """Reads and writes CDN distributions through an injected client."""

    def __init__(self, client: CdnClient) -> None:
        self._client = client
```

</good_example>

## C0209 consider-using-f-string

<bad_example>

```python
# BAD
message = "Invalidation %s failed for %d paths" % (job_id, len(paths))
```

</bad_example>

<good_example>

```python
# GOOD
message = f"Invalidation {job_id} failed for {len(paths)} paths"
```

</good_example>

## Not a pylint check: boolean flag parameters

A flag that switches behavior is two functions wearing one name. `sync(True)`
tells the reader nothing at the call site.

<bad_example>

```python
# BAD
def sync(self, dry_run: bool = False) -> SyncResult:
    ...
```

</bad_example>

<good_example>

```python
# GOOD
def sync(self) -> SyncResult:
    """Apply pending changes and return what was written."""

def preview_sync(self) -> SyncResult:
    """Return what a sync would write, without applying it."""
```

</good_example>

## Not a pylint check: magic numbers

<bad_example>

```python
# BAD
if ttl > 86400:
    raise ValueError("ttl too large")
```

</bad_example>

<good_example>

```python
# GOOD
MAX_TTL_SECONDS = 86_400

if ttl_seconds > MAX_TTL_SECONDS:
    raise ValueError(f"TTL {ttl_seconds}s exceeds the {MAX_TTL_SECONDS}s maximum")
```

</good_example>

## Not a pylint check: comments that restate code

<bad_example>

```python
# BAD
# increment the counter
counter += 1
```

</bad_example>

<good_example>

```python
# GOOD
# Akamai rejects invalidation requests over 128 paths, so batch below that.
for batch in chunked(paths, MAX_PATHS_PER_REQUEST):
    self._submit_invalidation(batch)
```

</good_example>

## R0903 too-few-public-methods

The one common false positive. A `@dataclass` with no methods is correct design,
not a smell. Leave it as a dataclass rather than adding a disable comment or
inventing a method to satisfy the check. If the project runs pylint as a gate
and this fires, raise it with the operator. The fix belongs in project config,
not in the source file.

## Reporting back

When the task is complete, summarize:

- What changed, in one or two sentences.
- The actual results from each quality gate that ran, with the command and its
  real output. There should be no remaining findings.
- Any tests added or updated.
- Anything the user should review or decide on next.

Python coder subagents should also report resolved project tooling and its
provenance. Use the "Project tooling discovery" section in the active Python
coder subagent prompt.

Skill id: pys-1

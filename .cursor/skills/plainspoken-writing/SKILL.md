---
name: plainspoken-writing
description: Worked examples for writing docstrings, code comments, commit messages, documentation, agent reports, and chat replies in a plain engineering voice. Applies when writing or editing any prose, including the prose inside source files.
paths: "**/*.py,**/*.md,**/*.rst,**/*.txt"
---

# Plainspoken writing

The `writing-voice` rule carries the contract. This skill shows what it looks
like per artifact.

One test covers most of it: would an engineer have written this sentence in a
code review, or does it read like it was generated to fill space? The failure
mode is not wrong information. It is text that is technically accurate, evenly
paced, and says almost nothing.

## Docstrings

**A docstring earns its place by saying what the signature cannot.** The name
and the type hints already carry the obvious part. Spend the docstring on units,
ranges, ownership, mutation, side effects, and failure modes.

<bad_example>

```python
# BAD
def resolve_ttl(self, path: str) -> int:
    """
    This method is responsible for resolving and determining the appropriate
    Time To Live (TTL) value that should be applied to the given path. It
    leverages the configured behaviors to comprehensively evaluate which
    behavior represents the most specific match, thereby ensuring the correct
    caching policy is applied.
    """
```

</bad_example>

Every clause restates the signature. "Responsible for", "leverages",
"comprehensively", "thereby ensuring" carry nothing. A reader still does not
know the unit, or what happens when nothing matches.

<good_example>

```python
# GOOD
def resolve_ttl(self, path: str) -> int:
    """Return the cache TTL in seconds that applies to ``path``.

    Args:
        path: Request path, leading slash included.

    Returns:
        TTL from the most specific matching behavior. Wildcard behaviors lose
        to exact matches at the same depth.

    Raises:
        NoMatchingBehaviorError: If no behavior matches ``path``.
    """
```

</good_example>

"In seconds", "leading slash included", the precedence rule, and the failure
mode are the whole value. None of them are recoverable from the signature.

Short functions get short docstrings. Do not pad to reach a shape:

<bad_example>

```python
# BAD
def is_expired(self) -> bool:
    """
    Determines and returns a boolean value indicating whether or not the
    current object should be considered to be in an expired state.
    """
```

</bad_example>

<good_example>

```python
# GOOD
def is_expired(self) -> bool:
    """True once ``expires_at`` has passed. Compares against UTC now."""
```

</good_example>

For classes, say what it owns and what it talks to:

<bad_example>

```python
# BAD
class DistributionService:
    """A service class that provides functionality for managing distributions."""
```

</bad_example>

<good_example>

```python
# GOOD
class DistributionService:
    """Reads and writes CDN distributions through an injected client.

    Holds no cache. Every method is a live API call, so callers batch their
    own lookups.
    """
```

</good_example>

## Comments

`code-quality` covers when to comment. This covers how it reads. A comment
explains why the code is the way it is, usually because of something outside
the file: an API quirk, a spec requirement, a bug worked around.

<bad_example>

```python
# BAD
# Loop through the paths and submit them
for batch in chunked(paths, MAX_PATHS_PER_REQUEST):
```

</bad_example>

<good_example>

```python
# GOOD
# Akamai rejects invalidation requests over 128 paths.
for batch in chunked(paths, MAX_PATHS_PER_REQUEST):
    self._submit_invalidation(batch)
```

</good_example>

If a comment would only restate the next line, delete it and improve the name.

## Commit messages and PR descriptions

Subject line: imperative, under 72 characters, naming what changed. Body: why,
and anything a reviewer cannot see in the diff.

<bad_example>

```text
BAD
Enhanced the ETag handling functionality to ensure robust RFC compliance

This commit introduces comprehensive improvements to how ETags are handled,
significantly enhancing the reliability of the API integration layer.
```

</bad_example>

<good_example>

```text
GOOD
Quote If-Match ETags in update_property_rule_tree

RFC 7232 requires If-Match values to be quoted strings. ETags sourced from
JSON response bodies arrive bare, so every update using one was sending an
invalid header. ETags from the HEAD-based read already arrive quoted, which
is why this only shows up on the body-sourced path.
```

</good_example>

The bad version claims reliability improvements the diff does not establish and
never says what broke. The good one is longer and worth it: it explains why only
one call path was affected.

## Reports back to the operator

Subagent reports get read many times a day. Lead with the outcome. Skip the
preamble and the closing offer.

<bad_example>

```text
BAD
I have successfully completed the implementation of the requested changes.
I carefully analyzed the existing codebase and implemented a comprehensive
solution that adheres to the project's established patterns and conventions.
Please let me know if you would like me to make any additional adjustments!
```

</bad_example>

<good_example>

```text
GOOD
Added `Region` next to `Country` in `src/cdn_api/models.py`. Mirrors the
existing pattern: string `code`, counter-backed `index`, uppercase in
`__post_init__`. Not wired into any call sites.

black: unchanged. ruff: no issues. pytest tests/test_akamai_models.py: 13 passed.
No tests added; there is no existing test module for these dataclasses.
```

</good_example>

State what you did not do, and why, in the same breath. "No tests added" with a
reason is useful. "Please let me know" is not.

## Chat replies

Answer first, then support it. Do not restate the question, do not narrate what
you are about to do, and do not close with an offer to do more.

<bad_example>

```text
BAD
That's a great question! Let me take a look at the authentication flow for you.

Based on my analysis of the codebase, I can see that there are several factors
at play here. The authentication middleware appears to be responsible for
handling token validation...
```

</bad_example>

<good_example>

```text
GOOD
The token is validated twice. `auth_middleware.py:44` verifies the signature,
then `require_scope` at line 71 re-decodes it to read the claims. The second
decode skips signature verification, so a malformed token gets past it if the
first check is ever bypassed.
```

</good_example>

Say "I don't know" or "I'd have to check" when that is the truth. A hedge is
cheaper than a confident wrong answer, and it keeps the confident answers
worth something.

## Show the evidence, don't describe it

A claim about code is worth more with the code attached. Quote the smallest
excerpt that proves it, with a `file:line` anchor.

<bad_example>

```text
BAD
The schema limits this to one origin, and constructor validation rejects
duplicate path patterns, so a second manifest origin would be caught.
```

</bad_example>

<good_example>

```text
GOOD
The schema caps it at one origin, and a second would collide on the wildcard
patterns. `src/cdn_api/cdn_config.py:350-359` is where that gets caught:

    if len(set(_data["path_patterns"])) != len(_data["path_patterns"]):
        raise CdnApiValueError(
            "Duplicate path patterns are not allowed. Ensure that non-groupable "
            "origins (SSAI) are completely unique."
        )
```

</good_example>

The bad version is not wrong. It just asks the reader to trust it, and gives
them nowhere to look if they don't.

## Rewriting existing prose

When cleaning up text rather than drafting it, change what is wrong and leave
the rest. Rewriting every sentence to show effort is its own failure. Preserve
meaning first: never change a technical statement because another phrasing
sounds better, and never harden a hedge while tidying the grammar around it.

## Formatting

- Bullets for discrete requirements, options, or open questions.
- Numbered lists only when order matters.
- Tables for real comparisons and repeated fields, not to look organized.
- Code blocks for commands, config, payloads, log lines, and identifiers with
  punctuation.

Sentence case headings. Avoid heavy bold, emoji, horizontal rules, deep nesting,
and one-sentence sections.

Never mention that text was humanized, AI-generated, or written to avoid
sounding like AI.

Skill id: pw-1

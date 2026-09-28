---
description: Rewrite human-facing project prose in a direct, plainspoken voice.
---

# Plainspoken writing

The `writing-voice` rule carries the contract. This skill shows what it looks
like per human-facing project artifact.

Do not apply this skill merely because a file is Markdown, reStructuredText, or
text. It does not govern `.cursor/**`, `.claude/**`, `.cursor/scratch/**`,
`AGENTS.md`, agent prompts, commands, rules, skills, session artifacts, or chat
replies. Those use the `agent-artifact-writing` rule.

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

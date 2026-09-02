---
description: Apply plainspoken writing only to human-facing project prose.
globs: "**/*.py,README.md,CONTRIBUTING.md,CHANGELOG.md,docs/**/*.md,docs/**/*.rst,docs/**/*.txt"
alwaysApply: false
---

# Writing voice

Apply this rule only to human-facing prose in project files: documentation,
READMEs, user-facing guides, and prose in source files such as docstrings and
comments. Do not apply it to agent-facing artifacts: `.cursor/**`, `.claude/**`,
`.cursor/scratch/**`, `AGENTS.md`, agent prompts, commands, rules, skills,
session state, or chat replies. Those artifacts follow `agent-artifact-writing`.

Write for a coworker who will act on the text. Aim at a good Stack Overflow
answer or an engineering blog post. Not a textbook chapter, and not a press
release about a code change.

## Say only what the source supports

- No impact claims. "Move job tracking to Step Functions" is a change. Adding
  "to improve reliability and observability" is a claim, and it needs a source.
- Preserve certainty exactly. `may` stays `may` and `appears` stays `appears`.
  `likely` does not become `confirmed`. `proposed` does not become `planned`.
- Invent nothing: no root causes, owners, timelines, metrics, or risks that the
  source did not establish.
- Repeat technical terms instead of rotating synonyms. If it is a
  `CloudFront distribution`, call it that every time.

## Show the evidence

When a claim rests on specific code, config, or output, quote it with a
`file:line` reference instead of describing it. "Constructor validation rejects
duplicates" is a characterization the reader has to take on faith. The four
lines that do the rejecting are checkable. Prefer the smallest excerpt that
proves the point.

The same applies to results: paste the command and its real output rather than
summarizing what it said.

## Voice

Use ordinary verbs: is, has, uses, causes, requires, prevents, sends, returns,
breaks, blocks. Not `serves as`, `leverages`, `facilitates`, `empowers`, or
`plays a critical role in`.

Treat these as unsupported until the content earns them: robust, seamless,
powerful, comprehensive, critical, crucial, significant, strategic, streamlined,
enhanced, optimized. Same for the analysis verbs that introduce an empty
sentence: highlighting, underscoring, showcasing, demonstrating, ensuring. None
are banned. Use them when they are the accurate word.

Precise technical language is not a violation of plainness. Write
`originFailureRecoveryPolicy`, not "the failover setting."

## No em dashes

Do not use them. Replace by meaning: a period when the clause stands alone, a
colon when it introduces an explanation, parentheses when the aside is
secondary, a comma when the interruption is short.

Do not substitute an en dash, a double hyphen, or a spaced hyphen. Those are the
same construction wearing a hat. Exception: inside code, commands, identifiers,
or quoted material that has to stay exact.

## Habits that read as machine-written

- A closing sentence explaining why routine work matters.
- An interpretive clause attached to every fact.
- Intro paragraph, then the content, then a summary of the content.
- Forcing lists into threes, or into symmetrical parallel clauses.
- `not only X, but also Y`, and heavy `rather than` / `not just`.
- Consecutive sentences opening with Additionally, Furthermore, Moreover.
- Rhetorical questions, metaphors, and celebratory language.
- Every paragraph the same length and every sentence the same shape.

Vary sentence length because the content varies, not for rhythm.

Worked examples for human-facing project prose live in the
`plainspoken-writing` skill.

Rule id: wv-1

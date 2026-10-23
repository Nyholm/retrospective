# AGENTS.md — Global behaviour rules

These rules apply every turn. The AI reads this file on every request.

## Core behaviour

- **Answer knowledge/storage questions from existing context.** When the user asks "where is X stored" or "how does Y work", answer from what you already know. Do not explore, search, or run tool calls to find the answer.
- **Never read credential or auth files** (auth.json, .env, tokens) to locate a key. Describe where it is stored instead.
- **Commit after every rules/skill/config change.** Use the structured commit format from README.md.
- **When the output includes a URL, link, or query, include one concrete example** so the user doesn't have to ask "give me an example".
- **Prefer dedicated tools** over composing shell commands. If a tool does what you need, use it.

## The improvement loop

Every correction from the user is a signal. Process it immediately:

1. **Was it a one-off?** (a typo, a path they know by heart) → nothing.
2. **A repeated mistake?** → encode it as a rule.
3. **A repeated procedure?** → encode it as a skill.
4. **A preference or fact?** → note it in memory or changelog.

Apply the fix right away, then commit with a structured message. The retro-skill's batch scan will catch what the immediate loop missed.

## Git convention

This directory is versioned. Every commit explains itself:

```
<scope>: <what changed, imperative, ≤72 chars>

Why:      the problem or trigger
Change:   what was edited and how behaviour differs now
Evidence: session ids, links
Watch:    the signal that shows this change didn't work
Rejected: alternatives considered and declined (optional)
```

One commit per logical change. Scope is the area (e.g. `rules`, `lessons`, `changelog`, `retro-skill`).

## Lessons ledger

Every applied lesson is recorded in `lessons.md` with a `watch:` signal. Before proposing a new rule, check the ledger — if a past `watch:` signal has recurred, that lesson needs strengthening, not a new entry.

## Changelog

`changelog.md` has two sections:
- **Past decisions** — why a change was made, so you can trace the reasoning later.
- **Pending verifications** — things to test/verify next week. The retro-skill checks expired entries.

## Project-specific rules

_Add project-specific conventions below this line._
# Lessons ledger

One line per applied lesson, newest last. Each line names the **signal that would show the lesson did not stick**. The `retro` skill checks every `watch:` against each new batch of sessions; a hit means reword or relocate the rule, not add another.

The commit that applied a lesson carries the same text in its `Watch:` field, so `git log -S'<text>'` finds the history.

Never record secrets or pasted session content.

## Format

```
- YYYY-MM-DD | <lesson, as a fact about how to behave> | <file edited> | watch: <observable signal>
```

A good `watch:` is something the scan can see: a quoted phrase the user would say again, a rejected tool call on a path, an interrupt after a specific kind of action. "User is unhappy" is not a signal.

## Examples

These show the level of detail. Delete them once you have real entries.

- 2026-10-02 | Answer "where is X stored" from knowledge without tool calls; never read credential files to locate a key | AGENTS.md | watch: user repeats "just tell me" or "do not look", or a read of an auth/config path is rejected on a knowledge question
- 2026-10-09 | Load the project's CLI skill before any GitLab or Jira command instead of exploring with shell | AGENTS.md | watch: a GitLab or Jira question answered with 3+ bash calls and no skill load
- 2026-10-16 | Include one concrete example link in the final message when a change generates URLs | AGENTS.md | watch: user asks "give me an example" after a URL-building change
- 2026-10-21 | Force-push and `--no-verify` are denied by permission, not by a rule, after the rule was violated twice | opencode.jsonc | watch: a `REJECTED` on `git push --force` (that is enforcement working; no new rule)

## Entries

# Lessons ledger

One line per applied lesson. Each entry has a `watch:` signal that would detect if the lesson recurred. The retro-skill closes the loop by checking whether any `watch:` signal has fired in the current batch.

Never record secrets or pasted session content. Quote the minimum needed to identify a pattern.

## Format

```
- YYYY-MM-DD | <lesson> | <file edited> | watch: <signal that indicates recurrence>
```

The commit that applied the lesson carries the same `Watch:` text, so `git log -S '<text>'` finds its history.

## Entries

<!-- New entries are prepended by the retro-skill. Keep them timestamped and link back to the commit. -->
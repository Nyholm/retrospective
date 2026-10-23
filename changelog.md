# Changelog

Two sections: **Past decisions** (backward-looking) and **Pending verifications** (forward-looking).

Never record secrets. Quote the minimum needed.

---

## Past decisions

Why each change was made. This lets you trace back "we set this timeout to 30s" → "because the upstream API was slow in region X".

### Format

```
- YYYY-MM-DD | <what changed> | <why it changed> | <trigger / session / ticket>
```

### Entries

<!-- New entries prepended here by the retro-skill. -->

---

## Pending verifications

Things to check next week / next sprint. The retro-skill checks these on every run and flags expired entries.

### Format

```
- YYYY-MM-DD | <what changed> | <what to verify> | by: <date or event trigger>
```

When verified:
- **Pass** → keep the decision in changelog, remove from pending.
- **Fail** → revert or adjust, record in lessons.md.

### Entries

<!-- New entries prepended here. Expired entries are flagged by the retro-skill and removed once verified. -->
# Changelog

Why rules, skills, permissions and model choices changed, and how to judge or revert each change. Newest first. The `retro` skill reads this on every run: entries whose judge date has arrived get measured and a keep/revert proposal.

`lessons.md` says *what* was learned. This file says *why* a change was made and *how to know it worked*.

Never record secrets.

---

## Pending verifications

"Remember to test this next week." One entry per open question, with a date or event that decides it. When decided, move it to Decisions (keep) or record the revert.

### Format

```
## YYYY-MM-DD: <short title>

**Why.** The trigger. A session, a correction, a number.
**Changed.** What is different now, and in which file.
**Judge it by** <measurement> on or after <date or event>. Revert by <exact undo>.
```

### Example (delete once you have a real one)

## 2026-10-23: scan output goes to a file, never a pipe

**Why.** Two retros in a row lost the end of the scan because `opencode api` truncates large output on a pipe. The watermark line was missing both times and the next run re-read the same sessions.

**Changed.** `skills/retro/SKILL.md` Step 2 redirects to `$(mktemp)` and reads the file. `retro.py` does the same internally for every API call.

**Judge it by** the next three retro runs each ending with a `WATERMARK=` line, on or after 2026-11-13. Revert by restoring the pipe form if the file form causes a different failure.

---

## Decisions

Settled changes. Keep the same three fields so a later reader can still tell why.

### Example (delete once you have a real one)

## 2026-10-16: knowledge questions get a one-reply answer

**Why.** Four sessions in two weeks had the user say "just tell me" or "do not look" after the agent started exploring the filesystem to answer "where does X store its config". Twice the exploration touched an auth file and was rejected.

**Changed.** `AGENTS.md` gains one line: answer where-is / how-does questions from knowledge, in one reply, without tool calls; never read credential files to locate a key.

**Judged by** zero "just tell me" cues in the 2026-10-23 batch (12 sessions). Kept.

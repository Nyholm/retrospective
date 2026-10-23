# retro-skill

Two feedback loops that encode corrections so they stick:

- **Immediate loop** — per-correction. The user says something, you encode it right away.
- **Batch loop** — periodic. Scan recent sessions, find patterns, propose rules.

---

## Immediate loop (per-correction)

Triggers: the user corrects you, says "stop", "don't do that", "next time do X", or any explicit behaviour feedback.

### 1. Classify the correction

| Type | Action |
|---|---|
| **One-off** — typo, specific path they know, transient detail | Nothing. No rule needed. |
| **Repeated mistake** — they've said this before, or it matches a pattern | Encode it as a rule. |
| **Repeated procedure** — "always do this multi-step thing" | Encode it as a skill / document. |
| **Preference or fact** — "I prefer this", "this project uses that" | Note it. No rule needed, but remember it. |

### 2. Apply

- **Rule** → edit `AGENTS.md`. Add one line at the relevant section. Keep it short and actionable.
- **Document/skill** → create a file or edit the relevant reference.
- **No action** → note in the changelog why it was one-off (optional).

### 3. Record

Append to the commit message:

```
Why:      the user said "<verbatim correction>" in session <id>
Change:   added rule: <text>
Watch:    <what signal would show it didn't stick>
```

Commit. One commit per lesson.

---

## Batch loop (periodic review)

Triggers: "run a retro", "review my sessions", "what patterns do you see", "what have you learned from how I work", or periodically (every N sessions / days).

### Step 1. Load context

Read the current state so you don't duplicate existing rules:

- `AGENTS.md` — existing rules (global + project).
- `lessons.md` — past lessons with `watch:` signals.
- `changelog.md` — past decisions and pending verifications.
- **If the config directory is a git repo**, review commits since the last retro. Every commit should have `Why:`, `Change:`, `Watch:`. For each `Watch:` label, check whether that signal appears in the current batch. If it does, the lesson didn't stick.

### Step 2. Scan

Review recent sessions / interactions. Look for:

| Signal | What it usually means |
|---|---|
| User repeated the same ask in one session | The agent ignored or misread the request |
| User interrupted the agent (`^`, "stop", "no") | The agent went in the wrong direction or did too much |
| A tool call was rejected | A boundary the agent crossed. Repeat on the same tool → missing rule |
| "just tell me", "don't look", "do not explore" | The user wanted an answer from knowledge, not investigation |
| User supplied detail only after a failed attempt | The agent should have asked, or a rule should hold that detail |
| High cost with small outcome, many tool errors | Wrong-path detour |
| Session finished with no pushback | Positive signal. Note what the agent did |

### Step 3. Find patterns

- A pattern needs **2+ sessions** to act on. Single occurrences are noted but not encoded unless the user stated an explicit preference.
- Group the same request phrased differently ("check the MR comments" and "are the review comments valid?" are one workflow).
- Check coverage before proposing anything new. Search existing rules and files:

  ```
  grep -rni "<distinctive phrase>" AGENTS.md lessons.md retro-skill/
  ```

| Coverage | Proposal |
|---|---|
| No rule, 2+ sessions | New rule |
| A rule exists but was not followed | Strengthen it or move it earlier in AGENTS.md |
| The same correction keeps recurring | Edit the rule, reword it |
| Repeated successful sequence across sessions | A skill or documented procedure |
| One occurrence | Note it, do not codify |

- **Close the loop.** For every lesson in `lessons.md`, check whether its `watch:` signal recurred in this batch. If it did, the lesson did not stick — reword or relocate that entry instead of adding a new one.
- **Check pending verifications** in `changelog.md`. Any expired? Flag them: "You asked me to verify X by this week. Here's what I found…"

### Step 4. Present

Collect everything into a findings table:

| Behaviour | Evidence | Coverage | Proposal | Expected saving |
|---|---|---|---|---|
| _What happened_ | _# sessions + ids_ | _none / rule <text>_ | _new rule / edit rule / nothing_ | _reduced corrections, faster sessions_ |

Then list:
1. **What went well** — one or two lines.
2. **Pending verifications** — expired entries from changelog, with results.
3. **Proposed changes** — each with exact target file and wording.

### Step 5. Apply

Only apply what the user approves.

| Lesson type | Where it goes |
|---|---|
| Behaviour rule, all projects | `AGENTS.md` — short, one line |
| Project-specific convention | Bottom of `AGENTS.md` under "Project-specific rules" |
| Repeated successful workflow | Document it in a new file or in the relevant reference |
| "Test this next week" | `changelog.md` → Pending verifications |
| Why a decision was made | `changelog.md` → Past decisions |
| One-off | Nothing |

### Step 6. Record

1. Append one line to `lessons.md`:
   ```
   - YYYY-MM-DD | <lesson> | <file edited> | watch: <signal>
   ```
2. Update `changelog.md`:
   - Move verified entries from **Pending** to **Past decisions** (or revert).
   - Add new past decisions.
3. **Commit** with structured message:

   ```
   <scope>: <what changed, imperative, ≤72 chars>
   
   Why:      the trigger, with the user's correction quoted verbatim
   Change:   what is different now
   Evidence: session ids, dates
   Watch:    the same text as the lessons.md line
   Rejected: proposals the user declined (so they're not re-proposed)
   ```

   One commit per lesson. No secrets, no pasted session content.

4. Save progress: record the last-scanned timestamp so the next retro picks up where this one stopped.

---

## Handling session content

Sessions may contain pasted configs, tokens, and private data. Quote only the minimum needed to identify a pattern. Redact secrets in findings and in anything written to a rule or ledger.
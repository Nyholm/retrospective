---
name: retro
description: Turn corrections into durable rules. Two modes - immediate (the user just corrected you, says "reflect", "capture that", "don't do that again") and batch (review sessions since the last run, find repeated requests, corrections, rule violations and expensive detours, propose rules or skills). Use for "retro", "retrospective", "review my sessions", "what have you learned from how I work", "audit my rules", "why was that expensive".
---

# retro

Agents improve when corrections become repo edits: work → correct → **reflect** → commit → better next run. This skill is that loop, in two speeds.

| Mode | When | Output |
|---|---|---|
| **Immediate** | A correction just happened | One rule, skill edit, or note. Committed now. |
| **Batch** | Weekly, or on request | A findings table. Nothing written without approval. |

Scripts (Python 3, no dependencies): `scripts/retro.py` scans sessions through the local OpenCode API, `scripts/turn-cost.py` breaks down cost. Paths below assume the skill lives at `~/.config/opencode/skills/retro/`.

Files it maintains, all in `~/.config/opencode/`:

| File | Holds | Test |
|---|---|---|
| `AGENTS.md` | How to behave. One-line imperatives, read every turn. | "Would the agent act differently?" |
| `memory/<topic>.md` | What is true about this user and environment. Indexed by one line each under `# Memory` in `AGENTS.md`. | "Is this a fact, not an instruction?" |
| `lessons.md` | What was learned and the `watch:` signal that shows if it stopped working. | "Can the scan see the signal?" |
| `changelog.md` | Why a change was made, how to judge it, how to revert it. | "Could a stranger decide keep or revert from this?" |

State that must not be committed (the scan watermark) lives in `~/.local/share/opencode/retro/state.json`.

---

## Immediate mode

Run at the end of any task where the user corrected you, said you went wrong, or said it took too long.

### 1. Name the failure

One sentence: what did the agent do wrong or slowly, and what should it have done? Quote the correction verbatim. The wording is the evidence.

### 2. Classify

Pick the first that holds:

| Lesson | Where it goes |
|---|---|
| **One-off** — typo, momentary confusion, a detail only this task needed | Nothing. Say so and stop. |
| **Repeated behaviour mistake** — seen before, or clearly a class of mistake | One line in `AGENTS.md`. Project-specific → that project's `AGENTS.md`. |
| **Repeated procedure** — steps, tools, decision points | A skill. Edit an existing one if it almost covered it. |
| **Preference or fact** about the user or environment | `memory/<topic>.md`, plus one pointer line under `# Memory` in `AGENTS.md`. See below. |
| **"Check this later"** | `changelog.md` → Pending verifications, with a judge date. |

Two lessons, two edits. Do not bundle.

**Memory.** Create `~/.config/opencode/memory/` the first time there is a fact to store; do not create it empty. One file per topic (`environment.md`, `models.md`, `writing.md`), short, factual, no steps. The index line in `AGENTS.md` is `- <topic>: <what is in it, ≤ 12 words>: memory/<topic>.md`. The index is capped at **8 lines**; at the cap, merge topics before adding. Not memory: anything with steps (a skill), anything one skill owns (that skill's `references/`), anything secret.

### 3. Write the smallest edit

- **Encode the process failure, not the instance.** If the rule only fires on the exact thing that just broke ("check TTL arithmetic"), generalise the trigger class ("re-derive the diff's own logic before pushing"). Fix processes, not symptoms.
- Rules are imperatives, one line. No history, no justification in the rule itself. That goes in the commit.
- If the correction contradicts an existing rule, edit the old rule. Never stack a second one.
- Never write secrets, credential paths, or private data.

### 4. Record and commit

Append to `lessons.md`:

```
- YYYY-MM-DD | <lesson> | <file edited> | watch: <signal that would show it recurred>
```

Commit with the message written to a temp file (`git commit -F <file>`), one commit per lesson:

```
<scope>: <what changed, imperative, ≤72 chars>

Why:      the user said "<verbatim>" in session <id>, <date>
Change:   what is different now
Watch:    <same text as the lessons.md line>
```

Rule edits apply on the next turn. Skill edits need an OpenCode restart; say so.

---

## Batch mode

Scan since the last run, find patterns, propose. Present first; apply only what the user approves.

**Cost note.** The scan is read-heavy and conclusion-only. Run Steps 1–4 in a subagent on a cheap model and keep only the report in the main context. Never pipe the scan output; redirect to a file and read the file.

### Step 1. Load context

```bash
python3 ~/.config/opencode/skills/retro/scripts/retro.py state get lastRun   # ms epoch; empty on first run → 7 days
OUT=$(mktemp) && python3 ~/.config/opencode/skills/retro/scripts/retro.py changes > "$OUT"; cat "$OUT"
```

Read `AGENTS.md`, `lessons.md`, `changelog.md`. The `changes` output lists every commit since the last run with its `Why:` / `Watch:` / `Rejected:` body. Use it to:

- check each `Watch:` signal against this batch — a recurrence means the lesson did not stick;
- tell whether a new problem started *after* a rule or skill changed (blame the change, not the user);
- avoid re-proposing anything under `Rejected:`.

### Step 2. Scan

```bash
OUT=$(mktemp) && python3 ~/.config/opencode/skills/retro/scripts/retro.py scan > "$OUT"; cat "$OUT"
```

Options: `--days N` / `--since MS`, `--max N` (default 12 sessions per run), `--include-active`. The running session and subagent sessions are excluded. Output is oldest-first and ends with `WATERMARK=<ms>`; when the cap cuts the batch short, a rerun continues from the watermark. Sessions that fail to load are listed as `SKIPPED`.

Each digest shows: model, cost, duration, tools used, linked PR/MR URLs, **friction** (`interrupted by user`, `REJECTED` permission prompts, tool errors) and the user messages with `!` on a correction cue and `^` on a message sent right after an interrupt.

After the digests, **repeated requests** are grouped two ways:

- **across sessions** — the same ask in 2+ sessions. Counted by *fork family*: a forked or resumed session replays the same messages and is not a second occurrence. These are workflow candidates.
- **within one session** — the user had to ask again. These are ignored or misread requests.

For a flagged session read it in full: `retro.py session <id>`. For wider lexical evidence over a longer window: `retro.py patterns --days 30 > file`.

### Step 3. Read the signals

| Signal | Usually means |
|---|---|
| Same ask repeated in one session | The agent ignored or misread it |
| Interrupt (`^`) | Wrong direction, or did too much |
| `REJECTED` tool call | A boundary crossed. Repeated on the same tool or path → missing rule or permission |
| "just tell me", "don't look", "stop" | The user wanted an answer from knowledge, not exploration |
| Detail supplied only after a failed first try | The agent should have asked, or a rule should hold that detail |
| Cost above the batch median **and** a correction cue | Wrong-path detour. Open it with `turn-cost.py all <id>` |
| Cost above the batch median, no commit or MR linked | Spent without a deliverable. Ask what happened |
| Work done by hand that an existing skill covers | **Skill-trigger miss**: fix the description, do not add a skill |
| Finished with no pushback | Positive. Note what the agent did |

Correction cues are candidates, not verdicts. "I do not see logs" is description, not correction. Compare models when sessions used different ones: a pattern confined to one model is a model note, not a rule.

### Step 4. Find patterns

- A pattern needs **2+ fork families**. One occurrence is noted as `watching`, not encoded, unless the user stated an explicit preference.
- Grouping is lexical. Read the raw messages and merge the same workflow phrased differently ("see the open comments on this MR, are they valid?" and "double check the review comments" are one workflow).
- **Check the rule existed** before calling anything a violation. A rule added after the session is not a violation:
  ```bash
  git -C ~/.config/opencode log --before="<session date>" -1 --format=%H -- AGENTS.md
  ```
- Check coverage before proposing anything new:
  ```bash
  grep -rniI "<distinctive phrase>" ~/.config/opencode/AGENTS.md ~/.config/opencode/skills/*/SKILL.md
  ```
- Repeated *successful* multi-step sequences count too. They are skill candidates and the cheapest wins.

| Coverage | Proposal |
|---|---|
| No rule or skill, 2+ families | New rule or new skill |
| A skill exists but was not loaded | Sharpen its description or triggers |
| A rule exists and was violated once | Reword it, or move it earlier |
| A rule exists and was violated 2+ times | **Enforce it**: a `permission` entry in `opencode.jsonc` or a plugin hook. Stronger wording has already failed |
| The same correction repeated | Rule edit, or skill edit when it has steps |
| One occurrence | `watching`. Do not codify |

**Close the loop.** For every `lessons.md` line, check whether its `watch:` signal fired in this batch. Fired → reword or relocate that entry; do not add a new one.

**Pending verifications.** For every `changelog.md` entry whose judge date has arrived, run the measurement it names and propose keep or revert. Entries with no judge date are standing checks: verify only when this batch touches that behaviour.

### Step 5. Audit the rules (every 4th run, or when AGENTS.md passes ~40 lines)

Report only. Contradictions first, they lose silently:

- For every "never/always" rule, grep skills for the banned pattern. A skill that teaches what a rule forbids is a finding; quote both sides and let the user choose which wins.
- A prose rule that `opencode.jsonc` permissions do not enforce is a finding, but do **not** default to proposing enforcement; the user may keep it loose on purpose.

Then bloat:

- **Duplicates** — two rules saying the same thing. Keep the sharper one.
- **Dead rules** — tools or workflows no longer in use; exhortations that never change behaviour ("write good code").
- **Wrong layer** — a procedure spelled out as a rule (→ skill); a fact written as a rule (→ memory); a memory topic that is really a standing instruction (→ rule); a fact that only one skill uses (→ that skill's `references/`).
- **Memory index** — over 8 lines, or a pointer whose file no longer exists, or a topic file with no pointer. Merge topics; do not raise the cap.
- **Stale directives** — dated `(user directive …)` lines older than six months with no recurrence. Ask whether they still hold.

Do not flag security or trust-boundary rules. List those separately as "touch only on request".

### Step 6. Present

1. **Findings table**

   | behaviour | evidence | coverage | proposal | expected saving |
   |---|---|---|---|---|

   `evidence` = number of fork families plus ids and dates. `coverage` = `none`, `rule`, `skill <name>` (loaded or not). `proposal` = new rule, edit rule, new skill, edit skill, description fix, permission, hook, watching, nothing. `expected saving` = corrections avoided, turns saved, or dollars.

2. **Cost** — total for the batch, top three sessions, and for each: what it bought.
3. **Pending verifications** — each due entry with its measurement and a keep/revert proposal.
4. **Audit findings** (when Step 5 ran) — ranked, contradictions first.
5. **What went well** — one or two lines.
6. **Skipped sessions** — every `SKIPPED` id, so nothing is silently missed.
7. **Proposed edits** — exact file and wording for each.

### Step 7. Apply and record

Apply only what was approved. Before writing a rule, check for an existing one and edit it in place.

1. `lessons.md`: one line per applied lesson.
2. `changelog.md`: move verified entries from Pending to Decisions (or record the revert); add a Decisions entry for every rule, skill or permission change made today.
3. Commit, one per lesson, message via `git commit -F`:

   ```
   <scope>: <what changed, imperative, ≤72 chars>

   Why:      the trigger; the user's correction quoted verbatim; session ids and dates
   Change:   what is different now
   Evidence: fork families, cost, links
   Watch:    same text as the lessons.md line
   Rejected: proposals the user declined, so they are not re-proposed
   ```

   Stage explicit paths. Never `git add -A`.
4. Save the watermark: `retro.py state set lastRun <WATERMARK>`. If the scan reported remaining sessions, offer another pass.

---

## Cost analysis

Cost driver is almost always **context size × number of requests**, not prompt length. Every request re-reads the whole context, so a tool dump stays in context and is billed again on every later turn.

```bash
python3 ~/.config/opencode/skills/retro/scripts/turn-cost.py --since 7d        # all sessions, subagents rolled up, by model
python3 ~/.config/opencode/skills/retro/scripts/turn-cost.py all <session-id>   # one row per turn
python3 ~/.config/opencode/skills/retro/scripts/turn-cost.py <n> <session-id>   # one row per model request in turn n
```

Per-request columns: `ctx` (input + cache read + cache write), `w` (cache write), `out` (output tokens), tools called.

| Pattern | Means | Fix |
|---|---|---|
| `ctx` climbs row over row | Tool results piling up | Targeted reads with offset/limit, grep with limits, compact before long tool-heavy phases |
| One turn with 50+ requests | A serial single-command shell loop late in a session | Batch independent commands into one call; compact before the build/fix phase |
| Many rows, 1–2 tools each | Exploratory loop | Name the file, symbol or command in the prompt |
| Large `out` | Verbose model output | Ask for terse |
| Large `w` | Context prefix changed mid-session (rules or skills edited) and the cache was rewritten | Batch config edits; make them at the end of a session |
| Big session, tiny deliverable | Wrong-path detour | Read the session; usually a missing rule or a question that should have been asked |

Plan-mode turns carry no token records and show as $0.

---

## Handling session content

Sessions contain pasted configs, tokens and private data. Quote only the minimum needed to identify a pattern. Redact secrets in findings and in anything written to a rule, ledger or commit.

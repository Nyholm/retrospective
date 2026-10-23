# retrospective

Your AI agent repeats the same mistakes. You correct it. Next session, it does them again. Nothing persists between sessions, so every week is Groundhog Day.

This repo fixes that. It gives your agent a memory: a retro skill that captures every correction as a rule, scans your sessions for repeated requests and expensive detours, and keeps a ledger so the same lesson is never learned twice.

## How it solves it

| File | What it does for you |
|---|---|
| `AGENTS.md` | Rules your agent reads every turn. Stops it exploring instead of answering, reading your auth files, retrying failed commands, or working around boundaries. |
| `lessons.md` | A ledger of what was learned — one line per lesson, each with a `watch:` signal that detects if the lesson stopped working. |
| `changelog.md` | Why decisions were made, how to judge if they worked, how to revert. Plus "verify this next week" items so nothing slips. |
| `skills/retro/SKILL.md` | Two feedback loops: immediate (right after a correction, distill it into a rule) and batch (weekly scan for patterns across sessions). Includes a rules audit and cost analysis. |
| `scripts/retro.py` | Scans sessions through the local OpenCode API — intercepts corrections, interrupts, rejected tool calls, repeated requests, cost. |
| `scripts/turn-cost.py` | Shows where your money goes: per session, per turn, per model request. |
| `githooks/commit-msg` | Rejects commits that don't explain *why* a rule changed. The retro reads that history to tell whether a rule is working. |

## Install / Try it

**Try it first.** Give your agent this prompt in any project:

> Look at https://github.com/Nyholm/retrospective, take inspiration and add it here.

It reads the repo over raw.githubusercontent.com and adapts what fits — usually a project `AGENTS.md` and a `lessons.md`. No download, no commit. See if the pattern works before investing.

**Install the full thing when you're ready.** One copy, no cloning:

```bash
BASE="https://raw.githubusercontent.com/Nyholm/retrospective/main"
DEST="$HOME/.config/opencode"

mkdir -p "$DEST/skills/retro/scripts" "$DEST/.githooks"
for f in AGENTS.md lessons.md changelog.md skills/retro/SKILL.md skills/retro/scripts/retro.py skills/retro/scripts/turn-cost.py; do
  curl -sSfL "$BASE/$f" -o "$DEST/$f"
done
curl -sSfL "$BASE/githooks/commit-msg" -o "$DEST/.githooks/commit-msg"
chmod +x "$DEST/.githooks/commit-msg" "$DEST/skills/retro/scripts/*.py"

cd "$DEST"
git init -q 2>/dev/null
git config core.hooksPath .githooks
git add AGENTS.md lessons.md changelog.md skills/retro
git commit -q -F - <<'EOF'
config: add retro skill, rules, lessons ledger and changelog

Why:      bootstrap the improvement loop from Nyholm/retrospective
Change:   AGENTS.md rules, lessons.md and changelog.md ledgers, retro skill with scan and cost scripts
EOF
echo "done — restart OpenCode, then read $DEST/AGENTS.md and delete the rules you disagree with"
```

If you already have an `AGENTS.md`, download ours to a temp path and merge by hand. Rules you did not choose are rules you will fight.

## First week

General things to do with your agent that unlock the whole system:

1. **Read `AGENTS.md` and delete what you disagree with.** Twenty lines you believe beat forty you tolerate.
2. **Correct in words, not in silence.** "No, use X" costs one sentence and becomes a rule. Quietly fixing it yourself teaches nothing.
3. **After a correction, say "reflect".** The retro skill in immediate mode names the failure, writes one rule, commits it.
4. **After a week, say "retro".** It scans the sessions since last time and shows what it found. Approve what you want. Reject the rest; the rejection is recorded so it's not proposed again.
5. **Name the file, symbol or command in your first message.** The single biggest cost lever. "Fix the login bug" costs ten exploratory turns; "fix the null check in `LoginHandler::authenticate`" costs one.

## Usage

| You say | What happens |
|---|---|
| "reflect" / "capture that" / "don't do that again" | Immediate mode. One correction becomes one rule, one edit, one commit. |
| "retro" / "review my sessions" | Batch mode. Scans since the last run, presents a findings table, applies what you approve. |
| "audit my rules" | Contradictions, duplicates, dead rules, wrong-layer entries — reported, nothing changed without approval. |
| "why was turn 7 expensive" / "what did I spend this week" | Cost breakdown: per session, per turn, per request. |

**How often.** Run "retro" once a week, or after any session that felt expensive or frustrating. The scan checks 10–12 sessions per run (oldest first) and picks up where it left off, so weekly is enough. Run "reflect" every time you correct something — that's the hot-fix, it takes 30 seconds.

Scripts also run directly:

```bash
python3 ~/.config/opencode/skills/retro/scripts/retro.py scan --days 7 > /tmp/scan.txt
python3 ~/.config/opencode/skills/retro/scripts/turn-cost.py --since 7d
```

## A worked example

You're three days into a new project. The agent has been writing views without tests. You correct it twice. Finally you say "retro". This is what happens:

```
# retro scan: since 2026-10-20 sessions=9 shown=9

## ses_xyz — Fix dashboard layout
cost=$1.74 span=22min user_msgs=7 assistant_msgs=31 compactions=0
user messages (! = correction cue, ^ = sent after an interrupt):
  [0]  Make the dashboard header sticky
  [1]  Can you also sort the table by date descending
  [2] ! That's not what I asked. The header should be sticky on scroll

## ses_abc — Add search endpoint
cost=$2.81 span=45min user_msgs=15 assistant_msgs=48
friction (3):
  - REJECTED: shell 'git push --force' — permission denied
  - tool error: composer install — timeout
  - interrupted by user
user messages:
  [0]  Add a /search endpoint that takes a query param
  [1]  Great
  [2] ^ 
  [3] ! I said query *param*, not a JSON body

(sessions 3-9 truncated for brevity)

# repeated requests
## across sessions (2) — workflow candidates
- ×3 in 2 sessions (10-20..10-22): Can you also add tests for the controller
  ids: ses_xyz ses_abc
## within one session (1) — request was ignored or misread
- ×2 in ses_abc: I said query *param*, not a JSON body

WATERMARK=1792729000000
```

From this the agent proposes:

| Behaviour | Evidence | Coverage | Proposal |
|---|---|---|---|
| Agent writes views without tests until told | 2 sessions (10-20, 10-22) | none | Rule: "Write tests for every controller/view. If the user didn't ask, say 'I'll add tests — approve or skip.'" |
| Agent misreads "query param" as JSON body | 1 session | — | Watching (one-off or pattern?) |
| `git push --force` blocked by permission | works as intended | enforcement | Nothing (permission already works) |

You approve the test rule. The agent edits `AGENTS.md`, appends a line to `lessons.md` with `watch: user asks "can you also add tests"`, commits, and the next session starts with the rule in place.

If you reject the rule, the commit carries a `Rejected:` field and it is not proposed again. Nothing is written without your approval.
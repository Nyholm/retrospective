# retrospective

Sessions are ephemeral. Corrections you make in one session are lost by the next. This repo gives your agent a durable memory — rules stored in `AGENTS.md`, a lessons ledger, a changelog of decisions, and a retro skill that encodes corrections so they stick.

## Files

| File | Purpose |
|---|---|
| `AGENTS.md` | Behaviour rules read every turn. Prevents common failure modes: exploring instead of answering, reading auth files, retrying failed commands. |
| `lessons.md` | One line per applied lesson, each with a `watch:` signal that flags if the lesson stopped working. |
| `changelog.md` | Why each change was made, how to judge it, how to revert. Includes forward-looking "verify this next week" entries. |
| `skills/retro/SKILL.md` | Two feedback loops: immediate (after a correction, distill it into a rule) and batch (weekly scan for patterns). Includes a rules audit and cost analysis. |
| `scripts/retro.py` | Scans sessions via the local OpenCode API: corrections, interrupts, rejected tool calls, repeated requests, session cost. |
| `scripts/turn-cost.py` | Cost breakdown per session, per turn, per request. Shows context build-up, cache writes, tool counts. |
| `githooks/commit-msg` | Rejects commits without `Why:` and `Change:`. The retro reads commit history to detect whether a lesson recurred. |

## Install

Two paths, depending on whether you already have an `~/.config/opencode` setup.

### Start from scratch

You have nothing yet. This creates `~/.config/opencode` with everything you need:

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
git init -q
git config core.hooksPath .githooks
git add AGENTS.md lessons.md changelog.md skills/retro
git commit -q -F - <<'EOF'
config: add retro skill, rules, lessons ledger and changelog

Why:      bootstrap the improvement loop from Nyholm/retrospective
Change:   AGENTS.md rules, lessons.md and changelog.md ledgers, retro skill with scan and cost scripts
EOF
```

Restart OpenCode, then read `$DEST/AGENTS.md` and delete what you disagree with.

### Add to an existing setup

You already have an `AGENTS.md`, skills, or other files in `~/.config/opencode`. Download only the retro skill pieces:

```bash
BASE="https://raw.githubusercontent.com/Nyholm/retrospective/main"
DEST="$HOME/.config/opencode"

mkdir -p "$DEST/skills/retro/scripts"
for f in skills/retro/SKILL.md skills/retro/scripts/retro.py skills/retro/scripts/turn-cost.py; do
  curl -sSfL "$BASE/$f" -o "$DEST/$f"
done
curl -sSfL "$BASE/githooks/commit-msg" -o "$DEST/.githooks/commit-msg" 2>/dev/null; chmod +x "$DEST/.githooks/commit-msg" 2>/dev/null; true

chmod +x "$DEST/skills/retro/scripts/*.py"
```

Then copy the relevant lines from `AGENTS.md`, `lessons.md` and `changelog.md` into your existing files — or read them for reference and keep your own. Rules you did not choose are rules you will fight.

## Usage

| Say | What happens |
|---|---|
| "reflect" / "capture that" / "don't do that again" | Immediate mode. One correction becomes one rule, one edit, one commit. |
| "retro" / "review my sessions" | Batch mode. Scans since the last run, presents a findings table, applies only what you approve. |
| "audit my rules" | Contradictions, duplicates, dead rules, wrong-layer entries. Reported, nothing changed without approval. |
| "why was turn 7 expensive" | Cost breakdown for that turn: context size, cache writes, output tokens, tools called. |

**How often.** Run `retro` once a week, or after any session that felt expensive or frustrating. It processes sessions oldest-first, 10–12 per run, and picks up where it left off. Run `reflect` every time you correct something — it takes 30 seconds. Run `audit` when `AGENTS.md` passes ~40 lines.

### First steps

1. **Read `AGENTS.md` and delete what you disagree with.** Twenty lines you believe beat forty you tolerate.
2. **Correct in words, not in silence.** "No, use X" costs one sentence and becomes a rule. Quietly fixing it yourself teaches nothing.
3. **After a correction, say "reflect".** The immediate mode names the failure, writes one rule, commits it.
4. **After a week, say "retro".** It scans the sessions since last time and shows what it found. Approve what you want. Reject the rest — the rejection is recorded so it is not proposed again.
5. **Name the file, symbol or command in your first message.** The single biggest cost lever. "Fix the login bug" costs ten exploratory turns; "fix the null check in `LoginHandler::authenticate`" costs one.

## Try it without installing

To adopt the pattern in a single project without downloading anything, give your agent this prompt:

> Look at https://github.com/Nyholm/retrospective, take inspiration and add it here.

The agent reads the repo over raw.githubusercontent.com and adapts the pieces that fit: usually a project `AGENTS.md` and a `lessons.md`. The scan scripts stay global — for those you need the full install.
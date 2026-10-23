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

Not shipped, created on first use: `memory/<topic>.md` for facts about your environment that are not rules (what is installed, which models you use, how you like docs written). `AGENTS.md` carries one pointer line per topic, capped at 8, so rules and facts stay in separate files.

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

You already have an agent and a config directory. Paste this to your agent:

> Install the retro skill from https://github.com/Nyholm/retrospective into my OpenCode config. Fetch the README first and follow its "For agents" section exactly. Fetch raw files, do not clone. Do not overwrite my existing AGENTS.md; merge the rules I do not already have. Create lessons.md and changelog.md only if they are missing. Install the commit-msg hook, commit with a Why:/Change: message, then show me a list of every file you created or changed.

The agent does the download, merge and commit. Review the diff it shows you and delete any rule you disagree with.

#### For agents

You are installing this repo into a user's OpenCode config. `BASE=https://raw.githubusercontent.com/Nyholm/retrospective/main`, `DEST=~/.config/opencode`. Fetch files with curl from `BASE`; do not `git clone`.

1. **Skill** — fetch into `DEST/skills/retro/`: `skills/retro/SKILL.md`, `skills/retro/scripts/retro.py`, `skills/retro/scripts/turn-cost.py`. `chmod +x` the scripts. Overwrite if present; the skill is not user-edited.
2. **Rules** — fetch `AGENTS.md` to a temp path. If `DEST/AGENTS.md` exists, append only the rules whose meaning is not already covered, under a heading `## From Nyholm/retrospective`; keep the user's file order and wording. If it does not exist, copy the file as is.
3. **Ledgers** — fetch `lessons.md` and `changelog.md` into `DEST` only if they are missing. Never overwrite them; they hold the user's history.
4. **Hook** — fetch `githooks/commit-msg` to `DEST/.githooks/commit-msg`, `chmod +x`. If `DEST` is not a git repo, `git init`. Run `git config core.hooksPath .githooks`. If `core.hooksPath` is already set to something else, leave it and tell the user.
5. **Commit** — stage only the paths you touched (never `git add -A`). Message: subject `config: add retro skill from Nyholm/retrospective`, body with `Why:` and `Change:` lines.
6. **Report** — list every file created, changed or skipped, the rules you appended, and remind the user to restart OpenCode so the skill loads. Do not run the retro.

Other agents (Claude Code, Codex, Cursor): put the rules in that tool's global instructions file instead of `DEST/AGENTS.md`, keep steps 3–6, skip step 1 (the scripts need the OpenCode API).

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


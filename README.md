# retrospective

A retro skill for AI coding agents. It turns your corrections into rules that stick, reviews your sessions for repeated requests and expensive detours, and keeps a ledger so the same lesson is never learned twice.

Built for [OpenCode](https://opencode.ai). The `AGENTS.md` convention is shared with Claude Code, Codex and Cursor, so the rules file works there too; the scan scripts need OpenCode.

## What you get

| File | Purpose |
|---|---|
| `AGENTS.md` | Global rules, read every turn. One line each. Starts with the rules most teams learn the hard way. |
| `lessons.md` | What was learned, one line each, with a `watch:` signal that shows if the lesson stopped working. |
| `changelog.md` | Why each change was made, how to judge it, how to revert it. Plus "verify this next week" items. |
| `skills/retro/SKILL.md` | The process. Immediate mode after a correction; batch mode weekly. Includes a rules audit and a cost analysis. |
| `skills/retro/scripts/retro.py` | Scans sessions through the local OpenCode API: corrections, interrupts, rejected tool calls, repeated requests, cost. |
| `skills/retro/scripts/turn-cost.py` | Cost per session, per turn, per model request. Shows why a turn was expensive. |
| `githooks/commit-msg` | Rejects a commit to the config repo that has no `Why:` and `Change:`. |

## Install (copy, no clone)

```bash
BASE="https://raw.githubusercontent.com/Nyholm/retrospective/main"
DEST="$HOME/.config/opencode"

mkdir -p "$DEST/skills/retro/scripts" "$DEST/.githooks"
for f in AGENTS.md lessons.md changelog.md skills/retro/SKILL.md \
         skills/retro/scripts/retro.py skills/retro/scripts/turn-cost.py; do
  curl -sSfL "$BASE/$f" -o "$DEST/$f"
done
curl -sSfL "$BASE/githooks/commit-msg" -o "$DEST/.githooks/commit-msg"
chmod +x "$DEST/.githooks/commit-msg" "$DEST"/skills/retro/scripts/*.py

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

1. **Read `AGENTS.md` and delete what you disagree with.** Twenty lines you believe beat forty you tolerate.
2. **Correct in words, not in silence.** "No, use X" costs one sentence and becomes a rule. Fixing it yourself quietly teaches nothing.
3. **After a correction, say "reflect".** The skill names the failure, writes one line, commits it.
4. **After a week, say "retro".** It scans the sessions since last time, shows a findings table, and waits. Approve what you want. Reject the rest; the rejection is recorded so it is not proposed again.
5. **Name the file, symbol or command in your first message.** The single biggest cost lever. "Fix the login bug" costs ten exploratory turns; "fix the null check in `LoginHandler::authenticate`" costs one.

## Usage

| Say | What happens |
|---|---|
| "reflect" / "capture that" / "don't do that again" | Immediate mode. One lesson, one edit, one commit. |
| "retro" / "review my sessions" | Batch mode. Scans since the last run, presents findings, applies what you approve. |
| "audit my rules" | The rules audit alone: contradictions, duplicates, dead rules, wrong layer. |
| "why was turn 7 expensive" / "what did I spend this week" | Cost analysis via `turn-cost.py`. |

Scripts run directly too:

```bash
python3 ~/.config/opencode/skills/retro/scripts/retro.py scan --days 7 > /tmp/scan.txt
python3 ~/.config/opencode/skills/retro/scripts/turn-cost.py --since 7d
```

## Adopting the pattern in a project

Give your agent this prompt inside the project:

> Look at https://github.com/Nyholm/retrospective, take inspiration and add it here.

It reads this repo over raw.githubusercontent.com and adapts the pieces that fit: usually a project `AGENTS.md`, sometimes a `lessons.md`. The scan scripts stay global.

## Commit convention

The retro skill reads the config repo's history to learn why things changed, so every commit explains itself:

```
<scope>: <what changed, imperative, ≤72 chars>

Why:      the problem or trigger (a session, a correction, a number)
Change:   what was edited and how behaviour differs now
Evidence: session ids, links, cost. Quote the minimum.
Watch:    the signal that shows this did not work (same text as the lessons.md line)
Rejected: alternatives considered and dropped, so they are not re-proposed
```

`Why:` and `Change:` are required; the hook rejects a commit without them. Scope is the area: `rules`, `lessons`, `changelog`, `retro`, `config`. One logical change per commit. No secrets, no pasted session content.

## Design notes

- **Two speeds.** A single correction is best captured while the context is hot. Patterns only show across sessions. Both loops write to the same files.
- **Evidence before rules.** A pattern needs two independent sessions. Forked sessions replay the same messages and count once.
- **Rules escalate.** Wording, then reworded, then enforced by a permission or hook. A rule violated twice does not get a third paragraph.
- **Every lesson carries its own test.** The `watch:` signal is checked on every later run. Lessons that stop working are reworded, not duplicated.
- **Rules are rent.** `AGENTS.md` is read on every turn. The audit step keeps it short.
- **State stays out of the repo.** The scan watermark lives in `~/.local/share/opencode/retro/state.json`.

Inspired by [Nyholm/ai-rules](https://gitlab.com/Nyholm/ai-rules) (`reflect`, `retro`, `rules-audit`, `turn-cost`) and the pstack `reflect` skill.

## License

MIT. See `LICENSE`.

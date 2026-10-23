# retrospective

A portable retro skill for AI coding agents — rules, lessons, changelog, and a review process that encodes corrections so they stick.

Use this to bootstrap day one. No cloning needed.

## Quick start

Copy the files to your local config directory in one shot:

```bash
BASE="https://raw.githubusercontent.com/Nyholm/retrospective/main"

# Download files
curl -sS "$BASE/AGENTS.md" -o ~/.config/opencode/AGENTS.md
curl -sS "$BASE/lessons.md" -o ~/.config/opencode/lessons.md
curl -sS "$BASE/changelog.md" -o ~/.config/opencode/changelog.md
mkdir -p ~/.config/opencode/retro-skill
curl -sS "$BASE/retro-skill/SKILL.md" -o ~/.config/opencode/retro-skill/SKILL.md

echo "Copied retrospective skill. Next: edit AGENTS.md to suit your project."
```

Then version the config directory in git:

```bash
cd ~/.config/opencode
git init
git add AGENTS.md lessons.md changelog.md retro-skill/SKILL.md
git commit -m "config: add retro skill, agents rules, lessons ledger, changelog"
```

## Files

| File | Purpose |
|---|---|
| `AGENTS.md` | Global behaviour rules. The AI reads this on every turn. |
| `lessons.md` | Backward-looking ledger: what was learned, with `watch:` signals to detect recurrence. |
| `changelog.md` | Forward-looking record: why decisions were made, plus pending verifications. |
| `retro-skill/SKILL.md` | The retro process: review sessions, find patterns, encode lessons. |

## Adopting into a project

To apply the patterns from this repo to a project, give your AI agent this prompt:

> Look at https://github.com/Nyholm/retrospective, take inspiration and add it here.

It will read the files in this repo and adapt them to your project's structure and conventions.

## Commit convention

Every change to the rules/lessons should be committed with a structured message:

```
<scope>: <what changed, imperative, ≤72 chars>

Why:      the problem or trigger
Change:   what was edited and how behaviour differs now
Evidence: session ids, links, quotes (minimum needed)
Watch:    the signal that shows this change didn't work
Rejected: alternatives considered and declined (optional)
```

Scope is the area: `retro-skill`, `config`, `rules`, `lessons`, `changelog`.

A `commit-msg` git hook can enforce `Why:` and `Change:` — see `githooks/commit-msg` in the repo.
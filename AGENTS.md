# Rules

Read every turn. One line per rule, imperative, no history. Keep this file under ~40 lines; longer explanations belong in a skill or in `changelog.md`.

## Behaviour

- Answer "where is X stored" / "how does Y work" / "just tell me" from knowledge, in one reply, without tool calls. If unsure, say so and offer to check.
- Never read credential or auth files (`auth.json`, `.env`, tokens) to locate a key. Describe where it is stored instead.
- Only do what was asked. Never install, remove or change software or system state unless told to. "What should I install?" is a question.
- Never retry a failed command unchanged. After two identical failures, change the approach or ask.
- When declining or deferring, give the reason and the next step in the same reply.
- When a change builds a URL, link or query, include one concrete example in the final message.
- Prefer dedicated tools over shell commands. Batch independent shell probes into one call.
- Read only the block you need (`offset`/`limit`), not the whole file. Cap search output before widening.
- Load a skill before acting whenever a task matches its trigger. Never freestyle a covered workflow.

## Improvement loop

- When corrected, told you went wrong, or told a task took too long: run the `retro` skill in immediate mode before finishing.
- A rule violated twice gets enforcement (a permission entry or hook), not stronger wording.
- Commit after every edit to this directory. Message has `Why:` and `Change:`; see README. Stage explicit paths, never `git add -A`.
- Lessons go in `lessons.md` with a `watch:` signal. Decisions and "verify later" items go in `changelog.md`.

## Git

- Do not commit secrets or credentials.
- Never force-push, `--no-verify`, or rewrite pushed history unless explicitly asked.
- Never open, merge, approve or close a PR/MR unless explicitly asked. "You can merge it" is permission, not an instruction.

## Project-specific

_Add rules that apply only here. Date preferences: `(user directive YYYY-MM-DD)`._

## Memory

_Facts about this user and environment, one pointer per topic, max 8. Detail lives in `memory/<topic>.md`. Facts, not rules._

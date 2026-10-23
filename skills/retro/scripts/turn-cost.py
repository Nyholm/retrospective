#!/usr/bin/env python3
"""Cost breakdown of OpenCode sessions and turns.

  turn-cost.py --since 48h             every session active in the window, subagents rolled up, by-model totals
  turn-cost.py all [session-id]        one row per turn of a session
  turn-cost.py <turn-n> [session-id]   one row per model request in that turn

Turn numbers match the TUI sidebar's Cost section (#n = nth user message).
Without a session id, uses the newest session in the current project.
Exports go through a file because a pipe truncates large sessions.

Adapted from Nyholm/ai-rules scripts/turn-cost.py (MIT).
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from collections import defaultdict
from urllib.parse import quote

EXPORT_DIR = os.path.join(tempfile.gettempdir(), "opencode-retro")


def newest() -> str:
    out = subprocess.run(["opencode", "session", "list"], capture_output=True, text=True).stdout
    m = re.search(r"ses_\w+", out)
    if not m:
        sys.exit("no session found; pass a session id")
    return m.group(0)


def export(sid: str) -> dict:
    os.makedirs(EXPORT_DIR, exist_ok=True)
    path = f"{EXPORT_DIR}/turn-cost-{sid}.json"
    err = None
    for _ in range(3):
        with open(path, "w") as f:
            subprocess.run(["opencode", "session", "export", sid], stdout=f, check=True)
        try:
            with open(path) as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            err = e
    sys.exit(f"export never produced valid JSON (live session being written?): {err}")


def turns(msgs):
    n, text, cur = 0, "", []
    for msg in msgs:
        if msg.get("type") == "user":
            if n:
                yield n, text, cur
            n, text, cur = n + 1, msg.get("text") or "", []
        elif msg.get("cost") is not None:
            cur.append(msg)
    if n:
        yield n, text, cur


def model(s: dict) -> str:
    return ((s.get("model") or {}).get("id") or "?").split("/")[-1]


def api(path: str) -> dict:
    # `opencode api` truncates large output on a pipe; a file is complete
    with tempfile.TemporaryFile() as f:
        subprocess.run(["opencode", "api", "get", path], stdout=f, check=True)
        f.seek(0)
        return json.load(f)


def sessions_since(cut: float) -> list:
    rows, cur = [], None
    while True:
        d = api("/api/session?limit=100&order=desc" + (f"&cursor={quote(cur)}" if cur else ""))
        for s in d["data"]:
            if (s.get("time") or {}).get("updated", 0) < cut:
                return rows
            rows.append(s)
        cur = (d.get("cursor") or {}).get("next")
        if not cur or not d["data"]:
            return rows


def since(window: str) -> None:
    m = re.fullmatch(r"(\d+)([hd])", window)
    if not m:
        sys.exit("window must look like 48h or 7d")
    cut = (time.time() - int(m.group(1)) * (3600 if m.group(2) == "h" else 86400)) * 1000
    rows = sessions_since(cut)
    byid = {s["id"]: s for s in rows}

    def root(s):
        seen = set()
        while s.get("parentID") in byid and s["id"] not in seen:
            seen.add(s["id"])
            s = byid[s["parentID"]]
        return s

    kids = defaultdict(list)
    for s in rows:
        if root(s) is not s:
            kids[root(s)["id"]].append(s)
    by_model = defaultdict(float)
    total = 0.0
    print(f"sessions active in the last {window} — cost is lifetime, * = started before the window")
    for s in sorted((s for s in rows if root(s) is s), key=lambda s: -(s.get("cost") or 0)):
        ch = kids.get(s["id"], [])
        star = "*" if (s.get("time") or {}).get("created", 0) < cut else " "
        print(
            f"  ${s.get('cost') or 0:>7.2f}{star} +${sum(c.get('cost') or 0 for c in ch):>5.2f} in {len(ch):>2} subagents"
            f"  {model(s):<24} {s['id']}  {s.get('title', '')[:50]}"
        )
        for x in [s, *ch]:
            by_model[model(x)] += x.get("cost") or 0
            total += x.get("cost") or 0
    print("  by model: " + "  ".join(f"{k} ${v:.2f}" for k, v in sorted(by_model.items(), key=lambda x: -x[1])))
    print(f"  total ${total:.2f}")


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    if sys.argv[1] == "--since":
        return since(sys.argv[2] if len(sys.argv) > 2 else "48h")
    turn = None if sys.argv[1] == "all" else int(sys.argv[1])
    sid = sys.argv[2] if len(sys.argv) > 2 else newest()
    data = export(sid)
    print(f"session {sid}")
    total = 0.0
    if turn is None:
        for n, text, cur in turns(data["messages"]):
            cost = sum(m.get("cost") or 0 for m in cur)
            total += cost
            print(f"  #{n:<3} ${cost:.4f}  {len(cur):>3} req  {text[:60]!r}")
        print(f"  total ${total:.4f}")
        return
    n = 0
    for n, text, cur in turns(data["messages"]):
        if n != turn:
            continue
        print(f"turn #{n}: {text[:70]}")
        for msg in cur:
            t = msg.get("tokens") or {}
            c = t.get("cache") or {}
            ctx = (t.get("input") or 0) + c.get("read", 0) + c.get("write", 0)
            tools = [p.get("name") or "?" for p in (msg.get("content") or []) if p.get("type") == "tool"]
            cost = msg.get("cost") or 0
            total += cost
            print(
                f"  ${cost:.4f}  ctx {ctx / 1000:.1f}k (w {c.get('write', 0) / 1000:.1f}k)"
                f"  out {t.get('output', 0)}  tools: {', '.join(tools) or '-'}"
            )
        print(f"  total ${total:.4f}")
        return
    sys.exit(f"session has only {n} turns")


if __name__ == "__main__":
    main()

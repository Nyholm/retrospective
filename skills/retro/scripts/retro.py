#!/usr/bin/env python3
"""Digest OpenCode sessions for the retro skill.

  retro.py scan [--since MS | --days N] [--max N] [--include-active]
  retro.py patterns [--since MS | --days N]    repeated requests across all sessions in the window
  retro.py session <id>                        full user messages + friction for one session
  retro.py state get|set <key> [value]
  retro.py changes [--since MS | --days N]     commits in the config repo (rules, skills, lessons) with full bodies

Talks to the local OpenCode server through `opencode api`; never opens opencode.db.
Config repo defaults to ~/.config/opencode; override with RETRO_CONFIG_DIR.
State (last run watermark) lives outside the repo in ~/.local/share/opencode/retro/state.json.
"""
import argparse, json, os, re, subprocess, sys, tempfile, time
from collections import Counter
from urllib.parse import quote

STATE = os.path.expanduser("~/.local/share/opencode/retro/state.json")
CONFIG_DIR = os.path.expanduser(os.environ.get("RETRO_CONFIG_DIR", "~/.config/opencode"))
CUES = re.compile(
    r"\b(nope|wrong|actually|stop|don'?t|do not|not what|i said|revert|undo|"
    r"that'?s not|incorrect|shouldn'?t|why did|why are you|too (much|long|verbose))\b"
    r"|^\s*no\b",
    re.I,
)
LINKS = re.compile(r"https?://[^\s\"')>]+/(?:pull/\d+|-/merge_requests/\d+)")
URL = re.compile(r"https?://\S+")
PATH = re.compile(r"~?/[\w.@-]+(?:/[\w.@-]+)+")
NUM = re.compile(r"\b\d+\b")
STOP = set("a an the to of is it in on and or i you my me we our please can could would do does did this that "
           "for with at be are was there here as so just now then also if how what "
           "yes yeah yep ok okay sure thanks thank them go ahead".split())
MIN_TOKENS, MIN_CROSS_TOKENS, MAX_CHARS, SIMILAR = 2, 3, 400, 0.6


class ApiError(Exception):
    pass


def api(path):
    # `opencode api` truncates large output on a pipe; a file redirect is complete.
    for attempt in (1, 2):
        with tempfile.TemporaryFile() as f:
            r = subprocess.run(["opencode", "api", "get", path], stdout=f, stderr=subprocess.PIPE)
            f.seek(0)
            raw = f.read()
        try:
            if r.returncode or not raw:
                raise ValueError(r.stderr.decode()[:200] or "empty response")
            return json.loads(raw)
        except ValueError as e:
            if attempt == 2:
                raise ApiError(f"{path}: {e}")


def pages(path):
    cur = None
    while True:
        d = api(path + (f"&cursor={quote(cur)}" if cur else "&order=asc"))
        if not d["data"]:
            return
        yield from d["data"]
        cur = (d.get("cursor") or {}).get("next")
        if not cur:
            return


def list_sessions(since, until):
    out, cur = [], None
    while True:
        d = api("/api/session?limit=100&order=desc" if not cur else f"/api/session?limit=100&cursor={quote(cur)}")
        stop = False
        for s in d["data"]:
            if s["time"]["updated"] < since:
                stop = True
                break
            if s["time"]["updated"] < until:
                out.append(s)
        cur = (d.get("cursor") or {}).get("next")
        if stop or not cur or not d["data"]:
            return out


def short(t, n):
    t = " ".join((t or "").split())
    return t if len(t) <= n else t[: n - 1] + "…"


def gist(inp):
    if not isinstance(inp, dict):
        return ""
    for k in ("command", "filePath", "path", "pattern", "url", "name", "id"):
        if k in inp:
            return short(str(inp[k]), 90)
    return short(json.dumps(inp), 90)


def collect(s, users_only=False):
    d = {"s": s, "users": [], "friction": [], "tools": Counter(), "links": set(), "types": Counter()}
    aborted = False
    suffix = "&type=user" if users_only else ""
    for m in pages(f"/api/session/{s['id']}/message?limit=100{suffix}"):
        t = m["type"]
        d["types"][t] += 1
        if t == "user":
            text = m.get("text") or ""
            d["links"].update(LINKS.findall(text))
            d["users"].append({"text": text, "cue": bool(CUES.search(text)), "after_abort": aborted})
            aborted = False
        elif t == "assistant":
            if (m.get("error") or {}).get("type") == "aborted":
                d["friction"].append("interrupted by user")
                aborted = True
            elif m.get("error"):
                d["friction"].append("error: " + short(json.dumps(m["error"]), 120))
            for c in m.get("content") or []:
                if c["type"] == "text":
                    d["links"].update(LINKS.findall(c.get("text") or ""))
                elif c["type"] == "tool":
                    d["tools"][c["name"]] += 1
                    st = c.get("state") or {}
                    for blk in st.get("content") or []:
                        if blk.get("type") == "text":
                            d["links"].update(LINKS.findall(blk.get("text") or ""))
                    if st.get("status") == "error":
                        msg = (st.get("error") or {}).get("message", "")
                        kind = "REJECTED" if "rejected permission" in msg else "tool error"
                        d["friction"].append(f"{kind}: {c['name']} {gist(st.get('input'))} — {short(msg, 100)}")
    return d


def render(d, full=False):
    s, users = d["s"], d["users"]
    cap, width = (10**6, 4000) if full else (30, 280)
    keep = list(range(len(users)))
    if len(users) > cap:
        flagged = [i for i, u in enumerate(users) if u["cue"] or u["after_abort"]]
        keep = sorted(set(range(5)) | set(flagged[: cap - 8]) | set(range(len(users) - 3, len(users))))
    mins = (s["time"]["updated"] - s["time"]["created"]) / 60000
    print(f"## {s['id']} — {short(s.get('title'), 80)}")
    print(
        f"dir={s['location']['directory']} agent={s.get('agent')} model={s['model']['id'] if s.get('model') else '?'} "
        f"cost=${s.get('cost') or 0:.2f} span={mins:.0f}min user_msgs={len(users)} "
        f"assistant_msgs={d['types']['assistant']} compactions={d['types']['compaction']} "
        f"outcome={s.get('outcome') or 'n/a'}"
    )
    if d["types"]["skill"]:
        print(f"user-activated skills: {d['types']['skill']}")
    if d["tools"]:
        print("tools: " + ", ".join(f"{k}×{v}" for k, v in d["tools"].most_common(8)))
    if d["links"]:
        print("links: " + " ".join(sorted(d["links"])[:6]))
    if d["friction"]:
        print(f"friction ({len(d['friction'])}):")
        for f, n in list(Counter(d["friction"]).items())[: 100 if full else 12]:
            print(f"  - {f}" + (f" ×{n}" if n > 1 else ""))
    print("user messages (! = correction cue, ^ = sent right after an interrupt):")
    prev = -1
    for i in keep:
        if i != prev + 1:
            print("  …")
        u = users[i]
        flag = ("!" if u["cue"] else " ") + ("^" if u["after_abort"] else " ")
        print(f"  [{i}]{flag} {short(u['text'], width) if not full else u['text'][:width]}")
        prev = i
    print()


def tokens(text):
    t = URL.sub(" url ", text.lower())
    t = PATH.sub(" path ", t)
    t = NUM.sub(" n ", t)
    return frozenset(w for w in re.sub(r"[^a-z0-9' ]+", " ", t).split() if w not in STOP)


def similar(a, b):
    return len(a & b) / len(a | b) >= SIMILAR


def families(collected):
    """Map session id -> fork family root. A fork replays its parent's messages, so a family counts once."""
    fork = {d["s"]["id"]: (d["s"].get("fork") or {}).get("sessionID") for d in collected}
    def root(i):
        seen = set()
        while fork.get(i) and i not in seen:
            seen.add(i)
            i = fork[i]
        return i
    return {i: root(i) for i in fork}


def patterns(collected):
    fam = families(collected)
    groups = []
    for d in collected:
        sid = d["s"]["id"]
        for i, u in enumerate(d["users"]):
            if len(u["text"]) > MAX_CHARS:
                continue
            tok = tokens(u["text"])
            if len(tok) < MIN_TOKENS:
                continue
            for g in groups:
                if similar(tok, g["tok"]):
                    break
            else:
                g = {"tok": tok, "example": u["text"], "hits": []}
                groups.append(g)
            g["hits"].append((sid, d["s"]["time"]["updated"], i))
    cross, within = [], []
    for g in groups:
        by_session = Counter(h[0] for h in g["hits"])
        fams = {fam[h[0]] for h in g["hits"]}
        if len(fams) >= 2 and len(g["tok"]) >= MIN_CROSS_TOKENS:
            cross.append((len(fams), g, by_session))
        if any(n >= 2 for n in by_session.values()):
            within.append((g, by_session))
    cross.sort(key=lambda x: (-x[0], -len(x[1]["hits"])))
    within.sort(key=lambda x: -max(x[1].values()))

    def day(ms):
        return time.strftime("%m-%d", time.localtime(ms / 1000))

    print("# repeated requests")
    print(f"## across sessions ({len(cross)}) — workflow candidates; counts are fork families\n")
    for n, g, bs in cross[:10]:
        dates = sorted(h[1] for h in g["hits"])
        print(f"- ×{len(g['hits'])} in {n} sessions ({day(dates[0])}..{day(dates[-1])}): {short(g['example'], 200)}")
        print("  ids: " + " ".join(list(bs)[:6]))
    if not cross:
        print("none")
    print(f"\n## within one session ({len(within)}) — request was ignored or misread\n")
    for g, bs in within[:10]:
        sid, n = bs.most_common(1)[0]
        print(f"- ×{n} in {sid}: {short(g['example'], 200)}")
    if not within:
        print("none")
    print()


def load_state():
    try:
        return json.load(open(STATE))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def window(a):
    now = int(time.time() * 1000)
    since = a.since or (now - int(a.days * 86400000) if a.days else int(load_state().get("lastRun") or now - 7 * 86400000))
    active = set() if getattr(a, "include_active", False) else set(api("/api/session/active")["data"])
    found = [s for s in list_sessions(since, now) if s["id"] not in active and not s.get("parentID")]
    found.sort(key=lambda s: s["time"]["updated"])
    return now, since, active, found


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("scan", "patterns"):
        p = sub.add_parser(name)
        p.add_argument("--since", type=int)
        p.add_argument("--days", type=float)
        p.add_argument("--include-active", action="store_true")
        if name == "scan":
            p.add_argument("--max", type=int, default=12)
    se = sub.add_parser("session")
    se.add_argument("id")
    ch = sub.add_parser("changes")
    ch.add_argument("--since", type=int)
    ch.add_argument("--days", type=float)
    st = sub.add_parser("state")
    st.add_argument("op", choices=["get", "set"])
    st.add_argument("key")
    st.add_argument("value", nargs="?")
    a = ap.parse_args()

    if a.cmd == "state":
        state = load_state()
        if a.op == "get":
            print(state.get(a.key, ""))
        else:
            state[a.key] = a.value
            os.makedirs(os.path.dirname(STATE), exist_ok=True)
            json.dump(state, open(STATE, "w"), indent=2)
        return

    if a.cmd == "changes":
        now = int(time.time() * 1000)
        since = a.since or (now - int(a.days * 86400000) if a.days else int(load_state().get("lastRun") or now - 7 * 86400000))
        stamp = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(since / 1000))
        out = subprocess.run(
            ["git", "-C", CONFIG_DIR, "log", f"--since={stamp}", "--date=short", "--stat=100", "--format=commit %h  %ad%n%B"],
            capture_output=True, text=True,
        )
        if out.returncode != 0 and "does not have any commits" not in out.stderr:
            sys.exit(out.stderr.strip() or f"git log failed (is {CONFIG_DIR} a git repo?)")
        print(f"# config changes since {stamp}\n")
        print(out.stdout.strip() or "none")
        return

    if a.cmd == "session":
        render(collect(api(f"/api/session/{a.id}")["data"]), full=True)
        return

    now, since, active, found = window(a)
    stamp = time.strftime("%Y-%m-%d %H:%M", time.localtime(since / 1000))
    collected, skipped = [], []

    if a.cmd == "patterns":
        print(f"# retro patterns: since={since} ({stamp}) sessions={len(found)}\n")
        for s in found:
            try:
                collected.append(collect(s, users_only=True))
            except ApiError as e:
                skipped.append(f"{s['id']} ({e})")
        patterns(collected)
        for x in skipped:
            print(f"SKIPPED {x}")
        return

    batch, rest = found[: a.max], found[a.max :]
    print(f"# retro scan: since={since} ({stamp}) sessions={len(found)} shown={len(batch)} skipped_active={len(active)}\n")
    for s in batch:
        try:
            d = collect(s)
        except ApiError as e:
            skipped.append(f"{s['id']} ({e})")
            continue
        collected.append(d)
        if d["users"]:
            render(d)
    patterns(collected)
    for x in skipped:
        print(f"SKIPPED {x}")
    watermark = batch[-1]["time"]["updated"] if rest else now
    print(f"WATERMARK={watermark}" + (f"  # {len(rest)} newer sessions remain; rerun after saving" if rest else ""))


if __name__ == "__main__":
    main()

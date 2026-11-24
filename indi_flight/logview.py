#!/usr/bin/env python3
"""Readable view of the orchestrator's session logs (run-*.jsonl, stream-json).

  indi_flight/logview.py                      table of the sessions in indi_flight/logs
  indi_flight/logview.py --dir indi_project/logs      same for the stage-1 archive
  indi_flight/logview.py RUN.jsonl            one session as a transcript
  indi_flight/logview.py --last               the most recent session
  indi_flight/logview.py --last --follow      the most recent session, live (Ctrl-C to quit)
  indi_flight/logview.py --dashboard          live project status: owner decisions and blockers, gates, usage
                                              against its targets, supervisor actions, session agents, flights;
                                              full screen, scroll with arrows/PgUp/PgDn/Home/End or the wheel, q quits
  indi_flight/logview.py --dashboard --once   the same, printed once (no colors, no refresh)
  indi_flight/logview.py --export OUTDIR [--dir DIR]   one Markdown transcript per session plus INDEX.md

Colors are on when stdout is a terminal (--color always|never to force). Options for a transcript: --subs shows what subagents did step by step (default: only their launch and result),
--results N shows up to N lines of each tool result (default 3, 0 hides them), --thinking shows reasoning.
Reads only; partial or corrupt lines (a session cut off mid-write) are skipped.
"""
import argparse
import glob
import io
import re
import shutil
import signal
import json
import os
import sys
import textwrap
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
WIDTH = 110


def events(path, follow=False, superseded=None):
    with open(path, errors="replace") as f:
        while True:
            line = f.readline()
            if not line:
                if not follow or (superseded and superseded()):
                    return
                time.sleep(1.0)
                continue
            if not line.endswith("\n") and follow:
                # partial line still being written: wait for the rest
                rest = ""
                while not rest.endswith("\n"):
                    time.sleep(0.5)
                    rest += f.readline()
                line += rest
            try:
                yield json.loads(line)
            except ValueError:
                continue


def local_time(ts):
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone().strftime("%H:%M:%S")
    except (AttributeError, ValueError):
        return "        "


def one_line(s, n):
    s = " ".join(str(s).split())
    return s if len(s) <= n else s[: n - 1] + "…"


def wrap(text, indent):
    out = []
    for para in str(text).strip().splitlines():
        if not para.strip():
            out.append("")
            continue
        out.extend(textwrap.wrap(para, WIDTH - len(indent), initial_indent=indent, subsequent_indent=indent,
                                 break_long_words=False, break_on_hyphens=False) or [indent])
    return "\n".join(out)


def tool_summary(name, inp):
    if name in ("Agent", "Task"):
        return None
    if name == "Bash":
        d = inp.get("description")
        c = one_line(inp.get("command", ""), 150)
        return f"{d}\n{'':14}$ {c}" if d else f"$ {c}"
    for k in ("file_path", "path", "pattern", "query", "url", "skill", "notebook_path"):
        if k in inp:
            extra = f"  ({inp['pattern']})" if k != "pattern" and "pattern" in inp else ""
            return one_line(inp[k], 150) + extra
    return one_line(json.dumps(inp, ensure_ascii=False), 150)


def result_text(block):
    c = block.get("content")
    if isinstance(c, list):
        c = "\n".join(x.get("text", "") for x in c if isinstance(x, dict))
    return str(c or "")


class Transcript:
    def __init__(self, out, subs=False, results=3, thinking=False, markdown=False, color=False):
        self.out, self.subs, self.results, self.thinking, self.md = out, subs, results, thinking, markdown
        self.color = color
        self.agents = {}      # tool_use_id -> short label
        self.pending = {}     # tool_use_id -> tool name
        self.n_agents = 0
        self.stats = dict(tools=0, agents=0, cost=None, result=None, start=None, end=None, model=None, title=None,
                          first_say=None, last_say=None)
        self.last_usage = None

    def c(self, code, s):
        return f"\033[{code}m{s}\033[0m" if self.color and code else s

    def p(self, s="", code=None):
        if code and self.color:
            s = "\n".join(self.c(code, l) if l else l for l in str(s).split("\n"))
        print(s, file=self.out, flush=True)

    def who(self, e):
        parent = e.get("parent_tool_use_id")
        return self.agents.get(parent, "sub") if parent else None

    def feed(self, e):
        t = e.get("type")
        ts = e.get("timestamp")
        if ts:
            self.stats["start"] = self.stats["start"] or ts
            self.stats["end"] = ts
        hhmm = local_time(ts)
        if t == "system":
            st = e.get("subtype")
            if st == "init":
                self.stats["model"] = e.get("model")
            elif st == "session_title_changed":
                self.stats["title"] = e.get("title")
            elif st == "task_notification":
                label = self.agents.get(e.get("tool_use_id"), "agent")
                self.p(f"\n{hhmm}  <<< {label} {e.get('status', '')}: {one_line(e.get('summary', ''), 160)}", "35")
            return
        if t == "rate_limit_event":
            w = (e.get("rate_limit_info") or {}).get("unifiedWindows") or {}
            parts = [f"{k.replace('_', '-')} {round(100 * v.get('utilization', 0))} %" for k, v in w.items()
                     if isinstance(v, dict) and "utilization" in v]
            five = round(100 * (w.get("five_hour") or {}).get("utilization", 0))
            # shown only when the 5-hour window moved by 5 points, otherwise it clutters the transcript
            if parts and (self.last_usage is None or abs(five - self.last_usage) >= 5):
                self.last_usage = five
                self.p(f"{'':10}[usage: {', '.join(parts)}]", "2")
            return
        if t == "result":
            self.stats["cost"] = e.get("total_cost_usd")
            self.stats["result"] = e.get("subtype")
            ok = e.get("subtype") == "success"
            self.p("\n" + "=" * WIDTH, "1;32" if ok else "1;31")
            self.p(f"SESSION END  result: {e.get('subtype')}   cost: ${e.get('total_cost_usd', 0):.2f}   "
                   f"turns: {e.get('num_turns', '?')}   duration: {round((e.get('duration_ms') or 0) / 60000)} min",
                   "1;32" if ok else "1;31")
            if e.get("result"):
                self.p(wrap(e["result"], "  "))
            return
        sub = self.who(e)
        if sub and not self.subs:
            return
        pre = f"    [{sub}] " if sub else ""
        if t == "assistant":
            for b in (e.get("message") or {}).get("content") or []:
                bt = b.get("type")
                if bt == "text" and b.get("text", "").strip():
                    if not sub:
                        self.stats["first_say"] = self.stats["first_say"] or one_line(b["text"], 140)
                        self.stats["last_say"] = one_line(b["text"], 240)
                        self.p(f"\n{hhmm}  {'**ORCHESTRATOR**' if self.md else 'ORCHESTRATOR'} " + "─" * 70, "1;36")
                        self.p(wrap(b["text"], "          "))
                    else:
                        self.p(f"{hhmm}  {pre}{one_line(b['text'], 200)}", "2")
                elif bt == "thinking" and self.thinking and b.get("thinking", "").strip():
                    self.p(f"{hhmm}  {pre}(thinking) {one_line(b['thinking'], 400)}", "2;3")
                elif bt == "tool_use":
                    name, inp = b.get("name", "?"), b.get("input") or {}
                    self.pending[b.get("id")] = name
                    if name in ("Agent", "Task"):
                        self.n_agents += 1
                        self.stats["agents"] += 1
                        label = f"agent {self.n_agents} ({inp.get('model', 'model?')})"
                        self.agents[b.get("id")] = label
                        self.p(f"\n{hhmm}  {pre}>>> LAUNCH {label}: {inp.get('description', '')}", "1;35")
                        self.p(wrap(one_line(inp.get("prompt", ""), 600), "              | "), "35")
                    else:
                        self.stats["tools"] += 1
                        self.p(f"{self.c('2', hhmm)}  {pre}  {self.c('1;33', f'{name:<6}')} {tool_summary(name, inp)}")
        elif t == "user":
            content = (e.get("message") or {}).get("content")
            if not isinstance(content, list):
                return
            for b in content:
                if b.get("type") != "tool_result":
                    continue
                name = self.pending.pop(b.get("tool_use_id"), "")
                text = result_text(b).strip()
                err = bool(b.get("is_error"))
                if name in ("Agent", "Task"):
                    label = self.agents.get(b.get("tool_use_id"), "agent")
                    self.p(f"\n{hhmm}  {pre}<<< {label} {'FAILED' if err else 'returned'}:", "1;31" if err else "1;35")
                    self.p(wrap(one_line(text, 900), "              | "), "35")
                    continue
                if not text or (self.results == 0 and not err):
                    continue
                lines = text.splitlines()
                shown = lines[: max(self.results, 6 if err else self.results)]
                tag = "ERROR" if err else "     "
                for ln in shown:
                    self.p(f"{'':10}{pre}{tag} > {one_line(ln, 150)}", "31" if err else "2")
                    tag = "     "
                if len(lines) > len(shown):
                    self.p(f"{'':10}{pre}      > … {len(lines) - len(shown)} more lines", "2")


def summarise(path):
    tr = Transcript(open(os.devnull, "w"))
    for e in events(path):
        tr.feed(e)
    s = tr.stats
    dur = ""
    try:
        a = datetime.fromisoformat(s["start"].replace("Z", "+00:00"))
        b = datetime.fromisoformat(s["end"].replace("Z", "+00:00"))
        dur = f"{round((b - a).total_seconds() / 60)} min"
        s["when"] = a.astimezone().strftime("%m-%d %H:%M")
    except (AttributeError, ValueError):
        s["when"] = os.path.basename(path)[4:17]
    s["dur"] = dur
    return s


def table(directory, out=sys.stdout, markdown=False, links=None):
    files = sorted(glob.glob(os.path.join(directory, "run-*.jsonl")))
    if not files:
        print(f"no run-*.jsonl in {directory}", file=out)
        return
    total = 0.0
    if markdown:
        print("| # | start | duration | cost | agents | tools | result | what it did |\n|---|---|---|---|---|---|---|---|",
              file=out)
    else:
        print(f"{'#':>3}  {'start':<11} {'dur':>7} {'cost':>6} {'agt':>3} {'tools':>5}  {'result':<12} what it did", file=out)
    for i, f in enumerate(files, 1):
        s = summarise(f)
        cost = s["cost"]
        total += cost or 0
        res = {"success": "ok", "error_max_budget_usd": "budget cap", None: "cut off"}.get(s["result"], s["result"])
        what = s["last_say"] or s["first_say"] or s["title"] or ""
        c = f"${cost:.2f}" if cost is not None else "?"
        if markdown:
            name = f"[{i}]({links[f]})" if links else str(i)
            print(f"| {name} | {s['when']} | {s['dur']} | {c} | {s['agents']} | {s['tools']} | {res} | "
                  f"{one_line(what, 220).replace('|', '/')} |", file=out)
        else:
            print(f"{i:>3}  {s['when']:<11} {s['dur']:>7} {c:>6} {s['agents']:>3} {s['tools']:>5}  {res:<12} "
                  f"{one_line(what, 110)}", file=out)
    print(("\n" if markdown else "") + f"Total: {len(files)} sessions, ${total:.2f}", file=out)


def render(path, out, follow=False, superseded=None, **kw):
    tr = Transcript(out, **kw)
    tr.p(f"SESSION {os.path.basename(path)}", "1")
    tr.p("=" * WIDTH, "1")
    try:
        for e in events(path, follow, superseded):
            tr.feed(e)
    except KeyboardInterrupt:
        return False
    return True


def latest(directory):
    files = sorted(glob.glob(os.path.join(directory, "run-*.jsonl")))
    return files[-1] if files else None


# ---------------------------------------------------------------------------------------------------------------
# Status dashboard (--dashboard): what the owner needs at a glance. Supervisor actions, session and agents, flights
# and simulations running, gates, usage against its targets, and anything that waits on the owner or blocks.
# Reads only: supervisor.log, the latest run-*.jsonl, STATE.md, QUESTIONS.md, MISSION.md, GATE_STATUS.tsv, the
# control files (WAIT_OWNER, STOP, DONE, BYPASS_*) and /proc for the flights and simulators that are running.

REPO = os.path.dirname(HERE)
ANSI = re.compile(r"(\033\[[0-9;]*m)")
GREEN, YELLOW, RED, CYAN, MAGENTA, DIM, BOLD = "32", "33", "31", "36", "35", "2", "1"


class Paint:
    def __init__(self, on):
        self.on = on

    def __call__(self, code, s):
        return f"\033[{code}m{s}\033[0m" if self.on and code else str(s)


def clip(line, n):
    """Cut a line to n visible characters, ANSI codes kept."""
    out, vis = [], 0
    for part in ANSI.split(line):
        if ANSI.fullmatch(part or "x"):
            out.append(part)
            continue
        if vis + len(part) > n:
            out.append(part[: max(n - vis - 1, 0)] + "…" + ("\033[0m" if ANSI.search(line) else ""))
            return "".join(out)
        out.append(part)
        vis += len(part)
    return "".join(out)


def read(path, tail=None):
    try:
        with open(path, errors="replace") as f:
            if tail:
                f.seek(max(os.path.getsize(path) - tail, 0))
            return f.read()
    except OSError:
        return ""


def lock_held(path):
    try:
        import fcntl
        with open(path) as lk:
            try:
                fcntl.flock(lk, fcntl.LOCK_EX | fcntl.LOCK_NB)
                fcntl.flock(lk, fcntl.LOCK_UN)
                return False
            except OSError:
                return True
    except (OSError, ImportError):
        return False


def hhmm(t):
    return datetime.fromtimestamp(t).strftime("%H:%M") if t else "--:--"


def ago(t):
    s = max(int(time.time() - t), 0)
    return f"{s}s" if s < 90 else f"{s // 60} min" if s < 5400 else f"{s / 3600:.1f} h"


def bar(frac, width, target=None):
    frac = min(max(frac, 0.0), 1.0)
    cells = ["█" if i < round(frac * width) else "░" for i in range(width)]
    if target is not None and target < 1:
        cells[min(int(target * width), width - 1)] = "│"
    return "".join(cells)


# --- supervisor.log -------------------------------------------------------------------------------------------

def _min(s):
    return f"{round(int(s) / 60)} min"


def _at(s):
    try:
        return datetime.strptime(s.strip()[:19], "%Y-%m-%d %H:%M:%S").strftime("%a %H:%M")
    except ValueError:
        return s


# regex -> (text, color); text None hides the line (repeated or covered by another panel)
SUP_RULES = [
    (r"^preflight ok: .*model (\S+), effort (\w+)", lambda m: (f"supervisor started ({m[1]}, effort {m[2]})", GREEN)),
    (r"^usage: 5-hour ([\d.]+), weekly ([\d.]+), headroom \$(-?[\d.]+)",
     lambda m: (f"usage check: 5 h {float(m[1]):.0%}, week {float(m[2]):.0%}, headroom ${float(m[3]):.1f}", DIM)),
    (r"^run (\d+): launching orchestrator with a \$([\d.]+) cap",
     lambda m: (f"launched session {m[1]} (cap ${float(m[2]):.0f})", "1;36")),
    (r"^run (\d+): exit (\d+) after (\d+)s, result (\S+), cost \$([\d.]+|\?)",
     lambda m: (f"session {m[1]} ended: {'ok' if m[4] == 'success' else m[4]}, {_min(m[3])}, "
                f"${float(m[5]) if m[5] != '?' else 0:.2f}", GREEN if m[4] == "success" else RED)),
    (r"^run \d+: indi_flight/results has (\d+) dirty", lambda m: (f"told: tidy {m[1]} uncommitted results", YELLOW)),
    (r"^run \d+: left (\d+) dirty", lambda m: (f"{m[1]} uncommitted results left", YELLOW)),
    (r"^run \d+: GATE_STATUS.tsv unchanged for (\d+)",
     lambda m: (f"told: route check (gates unchanged {m[1]} sessions)", YELLOW)),
    (r"^run \d+: GATE_STATUS.tsv changed: (G\d)\t([^\t]+)", lambda m: (f"GATE CHANGE: {m[1]} -> {m[2]}", "1;32")),
    (r"^run \d+: STATE.md is (\d+) bytes", lambda m: ("told: trim STATE.md", YELLOW)),
    (r"^run \d+: G3 chain", lambda m: (None, None)),
    (r"^calibration: a 5-hour window holds about \$([\d.]+)", lambda m: (f"calibrated: ${float(m[1]):.1f} per 5-hour window", DIM)),
    (r"^relaunching in (\d+)s", lambda m: (f"next launch in {m[1]} s", DIM)),
    (r"^waiting for the owner", lambda m: ("WAITING FOR OWNER (QUESTIONS.md)", "1;31")),
    (r"^stopped by", lambda m: ("stopped by indi_flight/STOP", "1;31")),
    (r"^orchestrator reported completion", lambda m: ("DONE reported", "1;32")),
    (r"^ABORT: (.*)", lambda m: (f"ABORT: {m[1]}", "1;31")),
    (r"^G3 flight chain flying", lambda m: ("idle: flight chain holds the lock", YELLOW)),
    (r"^G3 flight chain holds its lock", lambda m: ("flight chain stuck > 1 h: session to diagnose", RED)),
    (r"^targets: (.*)", lambda m: (f"usage targets: {m[1]}", "1;36")),
    (r"^WARNING indi_flight/USAGE_TARGETS: (.*)", lambda m: (f"USAGE_TARGETS ignored: {m[1]}", RED)),
    (r"^indi_flight/USAGE_TARGETS changed", lambda m: (None, None)),
    (r"^calibration: a weekly window holds about \$([\d.]+)",
     lambda m: (f"calibrated: ${float(m[1]):.0f} per weekly window", DIM)),
    (r"^weekly window at ([\d.]+) >= paced limit ([\d.]+) \(target ([\d.]+)\), waiting for the pace until (.*)",
     lambda m: (f"paused: weekly pace limit {float(m[2]):.0%} reached, until {_at(m[4])}", YELLOW)),
    (r"^weekly window at ([\d.]+) >= share ([\d.]+), waiting for its reset at (.*)",
     lambda m: (f"paused: weekly target {float(m[2]):.0%} reached, until {_at(m[3])}", "1;33")),
    (r"^weekly window at .* lifted", lambda m: (None, None)),
    (r"^5-hour headroom below .*last stretch before its reset at (.*)",
     lambda m: (f"paused: 5 h headroom low, until {_at(m[1])}", YELLOW)),
    (r"^5-hour headroom below .*reset at (.*)", lambda m: (f"paused: 5 h headroom low, until {_at(m[1])}", YELLOW)),
    (r"^a usage window is exhausted, waiting until (.*)", lambda m: (f"paused: usage limit hit, until {_at(m[1])}", RED)),
    (r"^usage probe failed", lambda m: ("usage probe failed, retry in 30 min", YELLOW)),
]


def supervisor_events(text):
    """[(epoch, raw message, short text, color)] for each supervisor.log line."""
    out = []
    for line in text.splitlines():
        m = re.match(r"^\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)\] (.*)", line)
        if not m:
            continue
        t = datetime.strptime(m[1], "%Y-%m-%d %H:%M:%S").timestamp()
        msg = m[2]
        for pat, fmt in SUP_RULES:
            mm = re.match(pat, msg)
            if mm:
                text_, code = fmt(mm)
                break
        else:
            text_, code = one_line(msg, 90), DIM
        out.append((t, msg, text_, code))
    return out


def purpose_line(text):
    """The one-sentence "Purpose: ..." line (MISSION.md, "How to work with subagents"), if the text has one."""
    m = re.search(r"^[ \t*_>#-]*Purpose:\**[ \t]*(\S.*)$", text, re.M)
    return m[1].strip(" *_") if m else None


# --- latest session log, read incrementally --------------------------------------------------------------------

class SessionWatch:
    """Agents, background tasks, cost, usage and last words of one run-*.jsonl, fed as the file grows."""

    def __init__(self, path):
        self.path, self.pos = path, 0
        self.ts = None                # latest event timestamp seen (system events carry none)
        self.tasks = {}               # task_id -> dict
        self.order = []
        self.agent_model = {}         # Agent tool_use id -> model
        self.agent_purpose = {}       # Agent tool_use id -> "Purpose:" line of its brief (MISSION.md rule)
        self.agent_effort = {}        # Agent tool_use id -> effort passed at launch (None: the agent's default)
        self.agent_parent = {}        # nested Agent tool_use id -> tool_use id of the agent that launched it
        self.purpose = None           # the orchestrator's latest "Purpose:" line
        self.cost = None
        self.say = None               # (epoch, text) of the orchestrator's latest message
        self.windows = None           # latest rate-limit windows
        self.start = None

    def update(self):
        try:
            with open(self.path, errors="replace") as f:
                f.seek(self.pos)
                while True:
                    line = f.readline()
                    if not line.endswith("\n"):
                        break
                    self.pos = f.tell()
                    try:
                        self.feed(json.loads(line))
                    except (ValueError, AttributeError, TypeError):
                        continue
        except OSError:
            pass

    def epoch(self):
        try:
            return datetime.fromisoformat(self.ts.replace("Z", "+00:00")).timestamp()
        except (AttributeError, ValueError):
            return time.time()

    def feed(self, e):
        t = e.get("type")
        if e.get("timestamp"):
            self.ts = e["timestamp"]
            self.start = self.start or self.epoch()
        if t == "rate_limit_event":
            self.windows = (e.get("rate_limit_info") or {}).get("unifiedWindows") or self.windows
        elif t == "result":
            c = e.get("total_cost_usd")
            if c is not None:
                self.cost = max(self.cost or 0, c)
        elif t == "assistant":
            parent = e.get("parent_tool_use_id")
            for b in (e.get("message") or {}).get("content") or []:
                if b.get("type") == "text" and b.get("text", "").strip() and not parent:
                    self.say = (self.epoch(), b["text"])
                    self.purpose = purpose_line(b["text"]) or self.purpose
                elif b.get("type") == "tool_use" and b.get("name") in ("Agent", "Task"):
                    inp = b.get("input") or {}
                    self.agent_model[b.get("id")] = inp.get("model") or "default"
                    self.agent_purpose[b.get("id")] = purpose_line(inp.get("prompt") or "")
                    self.agent_effort[b.get("id")] = inp.get("effort")
                    if parent:
                        self.agent_parent[b.get("id")] = parent
        elif t == "user" and not e.get("parent_tool_use_id"):
            # a foreground agent ends with its tool result (background ones with a task_notification)
            for b in (e.get("message") or {}).get("content") or []:
                if isinstance(b, dict) and b.get("type") == "tool_result":
                    txt = result_text(b)
                    for k in self.tasks.values():
                        if k["tuid"] == b.get("tool_use_id") and not txt.startswith(("Async agent launched",
                                                                                      "Command running in background")):
                            self._end(k, "failed" if b.get("is_error") else "completed", txt)
        elif t == "system":
            st, tid = e.get("subtype"), e.get("task_id")
            if st == "task_started" and tid:
                self.tasks[tid] = dict(desc=e.get("description") or "?", kind=e.get("task_type") or "?",
                                       sub=bool(e.get("owned_by_subagent")), tuid=e.get("tool_use_id"),
                                       start=self.epoch(), end=None, status="running", tools=0, last="", summary="")
                self.order.append(tid)
            elif tid in self.tasks:
                k = self.tasks[tid]
                if st == "task_progress":
                    k["tools"] = (e.get("usage") or {}).get("tool_uses", k["tools"])
                    k["last"] = e.get("last_tool_name") or k["last"]
                elif st == "task_updated":
                    s = (e.get("patch") or {}).get("status")
                    if s and s != "running":
                        self._end(k, s, "", (e.get("patch") or {}).get("end_time"))
                elif st == "task_notification":
                    self._end(k, e.get("status") or "completed", e.get("summary") or "")

    def _end(self, k, status, summary, end_ms=None):
        k["status"] = status
        k["summary"] = summary or k["summary"]
        k["end"] = k["end"] or (end_ms / 1000 if end_ms else self.epoch())

    def why(self, k):
        return self.agent_purpose.get(k["tuid"])

    def effort(self, k):
        return self.agent_effort.get(k["tuid"]) or "default"

    def model(self, k):
        return self.agent_model.get(k["tuid"], "agent") if k["kind"] == "local_agent" else "watch"


# --- project files -----------------------------------------------------------------------------------------------

def gate_names():
    names = {}
    for m in re.finditer(r"^- \*\*(G\d) ([^.*]+)\.", read(os.path.join(HERE, "MISSION.md")), re.M):
        names[m[1]] = m[2].strip()
    return names


def gate_refs(text):
    """Gates a stage paragraph names: "Gate G1" or a list "G2, G3" (a lone G1 is the control-effectiveness gain)."""
    refs = re.findall(r"\bGates? (G\d(?:(?:, | and )G\d)*)", text) + re.findall(r"\b(G\d(?:, G\d)+)", text)
    return sorted(set(re.findall(r"G\d", " ".join(refs))))


def stages():
    """[(number, name, [gates])] from MISSION.md "Order of work" (**Stage N, name.** paragraphs)."""
    txt = read(os.path.join(HERE, "MISSION.md"))
    out = []
    for m in re.finditer(r"^\*\*Stage (\d+), (.+?)\.\*\*(.*?)(?=^\*\*Stage |^## |\Z)", txt, re.S | re.M):
        out.append((int(m[1]), m[2][0].upper() + m[2][1:], gate_refs(m[3])))
    return out


def state_status():
    """(stage sentence, [(gates, question)] waits, [sentences that say blocked])"""
    txt = read(os.path.join(HERE, "STATE.md"))
    m = re.search(r"^## Status\n(.*?)(?=^## )", txt, re.S | re.M)
    body = " ".join(m[1].split()) if m else ""
    stage = ""
    ms = re.search(r"Stage: ([^.]+\.(?: ?FREEZE-\d+)?)", body)
    if ms:
        stage = ms[1]
    waits = []
    for mw in re.finditer(r"((?:G\d(?:, | and |,? ?))+)[^.;]*?\bwait(?:s|ing)? on (Q\d+)", body):
        waits.append((re.findall(r"G\d", mw[1]), mw[2]))
    blocked = [s.strip() for s in re.split(r"(?<=\.) ", body) if re.search(r"\bBLOCKED\b", s)]
    return stage, waits, blocked


def questions():
    """[(id, title, answered)] for the Q sections still in QUESTIONS.md."""
    out = []
    txt = read(os.path.join(HERE, "QUESTIONS.md"))
    for m in re.finditer(r"^## (Q\d+) \(([^)]*)\): (.*?)$(.*?)(?=^## |\Z)", txt, re.S | re.M):
        answered = bool(re.search(rf"\*\*Owner answer {m[1]}\b", m[4]))
        out.append((m[1], m[3].strip(), answered))
    return out


def gates():
    rows = []
    for line in read(os.path.join(HERE, "GATE_STATUS.tsv")).splitlines()[1:]:
        f = line.split("\t")
        if len(f) >= 4 and re.match(r"G\d", f[0]):
            rows.append((f[0], f[1], f[3]))
    return rows


# --- flights and simulators: /proc ------------------------------------------------------------------------------

def processes():
    try:
        btime = int(re.search(r"^btime (\d+)", read("/proc/stat"), re.M)[1])
        hz = os.sysconf("SC_CLK_TCK")
    except (TypeError, ValueError, OSError):
        btime, hz = None, 100
    out = []
    for pid in os.listdir("/proc"):
        if not pid.isdigit():
            continue
        try:
            with open(f"/proc/{pid}/cmdline", "rb") as f:
                args = [a.decode(errors="replace") for a in f.read().split(b"\0") if a]
            with open(f"/proc/{pid}/stat") as f:
                start = int(f.read().rsplit(")", 1)[1].split()[19])
        except (OSError, IndexError, ValueError):
            continue
        if args:
            out.append(dict(pid=int(pid), args=args, start=btime + start / hz if btime else None))
    return out


def arg(args, flag):
    try:
        return args[args.index(flag) + 1]
    except (ValueError, IndexError):
        return None


def results_group(path):
    """Top directory under indi_flight/results that a path belongs to, or None."""
    m = re.search(r"indi_flight/results/([^/\s'\"]+)", path or "")
    return m[1] if m else None


def flights():
    """One entry per results directory with a flight chain, batch or simulator running."""
    groups = {}

    def g(name):
        return groups.setdefault(name, dict(name=name, chains=set(), sims=[], start=None))

    for p in processes():
        a = p["args"]
        exe = os.path.basename(a[0])
        if "claude" in exe or any(len(x) > 400 for x in a):
            continue
        if "g3_chain.sh" in " ".join(a[:3]) and "_run" in a:
            d = arg(a, "_run")
            name = results_group(d)
            if name:
                gr = g(name)
                gr["chains"].add(d if os.path.isabs(d) else os.path.join(REPO, d))
                gr["start"] = min(filter(None, [gr["start"], p["start"]]), default=None)
        elif exe.startswith("python") and len(a) > 1 and a[1].endswith("run_scenario.py"):
            out = arg(a, "--out") or ""
            name = results_group(out) or "(outside results/)"
            g(name)["sims"].append(dict(scenario=arg(a, "--scenario"), ctrl=arg(a, "--controller"),
                                        model=arg(a, "--model"), rate=arg(a, "--rate-hz"),
                                        run=os.path.basename(out.rstrip("/")), start=p["start"]))
    # batch scripts between two chains: progress.txt with a live BATCH_START pid
    for d in glob.glob(os.path.join(HERE, "results", "*", "progress.txt")):
        m = None
        for m in re.finditer(r"BATCH_START pid=(\d+)", read(d, tail=20000)):
            pass
        if m and os.path.exists(f"/proc/{m[1]}"):
            g(os.path.basename(os.path.dirname(d)))
    return list(groups.values())


def batch_progress(gdir):
    """(done, total, current) from a batch progress.txt (BATCH_START indices/sets, then start/end/skip lines)."""
    txt = read(os.path.join(gdir, "progress.txt"))
    starts = list(re.finditer(r"BATCH_START.*indices: ([\d ]+?)\s+sets: ([\w ]+)", txt))
    if not starts:
        return None
    m = starts[-1]
    total = len(m[1].split()) * len(m[2].split())
    rest = txt[m.end():]
    done = {(s, i) for s, i in re.findall(r"set=(\S+) idx=(\S+) (?:end|skip)", rest)}
    cur = re.findall(r"set=(\S+) idx=(\S+) start", rest)
    return len(done), total, (f"set {cur[-1][0]} idx {cur[-1][1]}" if cur else "")


def purpose(gdir):
    txt = read(os.path.join(gdir, "README.md"))
    title = re.search(r"^# (.+)$", txt, re.M)
    why = re.search(r"^Purpose: (.+)$", txt, re.M)
    return (title[1] if title else ""), (why[1] if why else "")


# --- screen ------------------------------------------------------------------------------------------------------

def _git_head():
    try:
        import subprocess
        r = subprocess.run(["git", "-C", REPO, "log", "-1", "--format=%ct%x09%s"], capture_output=True, text=True,
                           timeout=5)
        t, s = r.stdout.strip().split("\t", 1)
        return int(t), s
    except (OSError, ValueError, Exception):
        return None


class Dashboard:
    def __init__(self, directory, color):
        self.dir, self.c = directory, Paint(color)
        self.watch = None
        self.git, self.git_t = None, 0

    def section(self, title, cols, note=""):
        c = self.c
        head = f"── {title} "
        tail = f" {note} ──" if note else ""
        return c("1;34", head + "─" * max(cols - len(head) - len(tail), 3)) + c(DIM, tail)

    def screen(self, cols):
        c, now = self.c, time.time()
        L = []
        flags = {n: os.path.exists(os.path.join(HERE, n)) for n in ("WAIT_OWNER", "STOP", "DONE", "BYPASS_5H",
                                                                      "BYPASS_7D")}
        sup_txt = read(os.path.join(self.dir, "supervisor.log"), tail=400000)
        sup = supervisor_events(sup_txt)
        sup_alive = lock_held(os.path.join(self.dir, ".lock"))

        # current session: the last launch without a matching exit
        run_file, run_no, run_t, running, last_exit = None, None, None, False, None
        for t, msg, *_ in sup:
            m = re.match(r"run (\d+): launching .*\(log: (\S+)\)", msg)
            if m:
                run_no, run_file, run_t, running = m[1], os.path.join(REPO, m[2]), t, True
            elif re.match(r"run (\d+): exit", msg):
                running, last_exit = False, (t, msg)
        running = running and sup_alive
        path = run_file if run_file and os.path.exists(run_file) else latest(self.dir)
        if path and (self.watch is None or self.watch.path != path):
            self.watch = SessionWatch(path)
        if self.watch:
            self.watch.update()
        w = self.watch

        # targets from the latest preflight line; live usage from the session log, else the supervisor probe
        # (the "targets:" line is logged at start and whenever indi_flight/USAGE_TARGETS changes them)
        share5, stretch, share7, pace, slack = 0.8, 3600, 0.7, False, 0.0
        for t, msg, *_ in sup:
            m = re.search(r"shares 5h ([\d.]+) \(1\.0 in the last (\d+)s.*?/ weekly ([\d.]+)", msg)
            if m:
                share5, stretch, share7, pace, slack = float(m[1]), int(m[2]), float(m[3]), False, 0.0
            m = re.match(r"targets: 5h ([\d.]+), weekly ([\d.]+), pacing (on|off) \(slack ([\d.]+)\)", msg)
            if m:
                share5, share7, pace, slack = float(m[1]), float(m[2]), m[3] == "on", float(m[4])
        u5 = u7 = r5 = r7 = None
        probe_t = 0
        for t, msg, *_ in sup:
            m = re.match(r"usage: 5-hour ([\d.]+), weekly ([\d.]+)", msg)
            if m:
                u5, u7, probe_t = float(m[1]), float(m[2]), t
        if w and w.windows:
            five, seven = w.windows.get("five_hour") or {}, w.windows.get("seven_day") or {}
            r5, r7 = five.get("resetsAt"), seven.get("resetsAt")
            if running or os.path.getmtime(w.path) > probe_t:
                u5, u7 = five.get("utilization", u5), seven.get("utilization", u7)
        if r5 and r5 < now:
            u5, r5 = 0.0, None     # window reset since the last reading
        if r7 and r7 < now:
            u7, r7 = 0.0, None
        tgt5 = 1.0 if flags["BYPASS_5H"] or (r5 and r5 - now <= stretch) else share5
        tgt7 = None if flags["BYPASS_7D"] else share7
        lim7 = tgt7         # paced weekly limit now (same formula as weekly_limit in run_orchestrator.sh)
        if tgt7 is not None and pace and r7:
            lim7 = tgt7 * min(1.0, max(0.0, 1 - (r7 - now) / 604800) + slack)

        qs = questions()
        stage, waits, blocked = state_status()
        g_rows = gates()
        stale = int(read(os.path.join(self.dir, "gate_status.stale")).strip() or 0) if read(
            os.path.join(self.dir, "gate_status.stale")).strip().isdigit() else 0
        fl = flights()

        # ---- header
        if now - self.git_t > 30:
            self.git, self.git_t = _git_head(), now
        L.append(c("1;37", "INDI flight · project status") + "   " + c(DIM, datetime.now().strftime("%a %Y-%m-%d %H:%M:%S")))
        if self.git:
            L.append(c(DIM, f"last commit {hhmm(self.git[0])} ({ago(self.git[0])} ago): {self.git[1]}"))

        # ---- attention: owner decisions and blockers first
        att = []
        open_q = [q for q in qs if not q[2]]
        if flags["DONE"]:
            att.append((GREEN, "DONE: the orchestrator reports the project complete (STATE.md opens with the summary)"))
        if flags["WAIT_OWNER"]:
            which = ", ".join(q[0] for q in open_q) or "see QUESTIONS.md"
            att.append(("1;37;41", f" OWNER DECISION WANTED: {which} · answer in indi_flight/QUESTIONS.md, "
                                   f"then rm indi_flight/WAIT_OWNER "))
        for q in open_q:
            att.append((RED if flags["WAIT_OWNER"] else YELLOW, f"open question {q[0]}: {q[1]}"))
        if flags["STOP"]:
            att.append(("1;31", "STOPPED: indi_flight/STOP present (rm it, then start run_orchestrator.sh)"))
        elif not sup_alive and not flags["DONE"]:
            att.append(("1;31", "SUPERVISOR NOT RUNNING: start indi_flight/run_orchestrator.sh"))
        asked = {q[0] for q in qs}
        for gs, q in waits:
            state = "not yet asked, orchestrator preparing it" if q not in asked else (
                "answered, being acted on" if any(x[0] == q and x[2] for x in qs) else "awaiting owner")
            att.append((YELLOW, f"waiting on {q} ({state}): {', '.join(gs)} verdicts"))
        for s in blocked[-2:]:
            att.append((RED, "BLOCKED: " + s))
        if sup:
            t, msg, txt, code = sup[-1]
            if txt and txt.startswith("paused"):
                att.append((YELLOW if code != RED else RED, txt))
        if tgt7 is not None and u7 is not None and u7 >= tgt7:
            att.append(("1;33", f"weekly usage {u7:.0%} at its {tgt7:.0%} target: no launch before the weekly reset"))
        elif lim7 is not None and u7 is not None and u7 >= lim7:
            att.append(("1;33", f"weekly usage {u7:.0%} ahead of its pace (limit now {lim7:.0%}, target {tgt7:.0%}): "
                                f"launches resume as the week goes on"))
        for gr in fl:
            for d in gr["chains"]:
                if os.path.exists(os.path.join(d, "CHAIN_HALTED")):
                    att.append((RED, f"flight chain halted: {os.path.relpath(d, HERE)} (CHAIN_HALTED gives the reason)"))
        if stale >= 2:
            att.append((YELLOW, f"no gate moved for {stale} sessions (GATE_STATUS.tsv): route check ordered"))
        L.append(self.section("ATTENTION", cols))
        if not att:
            L.append("  " + c(GREEN, "nothing waits on the owner, nothing blocks"))
        for code, txt in att:
            L.append("  " + c(code, "▶ " + txt))

        # ---- project: stage and gates, compact
        n_pass = sum(1 for g_ in g_rows if g_[1].upper() == "PASSED")
        st_list = stages()
        cur = re.match(r"(\d+)", stage or "")
        cur = int(cur[1]) if cur else None
        L.append(self.section("PROJECT", cols, f"{n_pass}/{len(g_rows) or 8} gates passed"))
        g_state = {g_[0]: g_[1].upper() for g_ in g_rows}

        def gcode(gid):
            up = g_state.get(gid, "?")
            return GREEN if up == "PASSED" else RED if "NOT" in up or "FAIL" in up else YELLOW

        by_n = {n: (name, gs) for n, name, gs in st_list}
        line = "  " + c(BOLD, "stage ")
        if cur in by_n:
            fr = re.search(r"FREEZE-\d+", stage)
            line += c("1;36", f"▶ {cur}/{len(st_list)} {by_n[cur][0]}") + (c(DIM, f" ({fr[0]})") if fr else "")
            if cur + 1 in by_n:
                nx = by_n[cur + 1]
                line += c(DIM, f"   next {cur + 1} {nx[0]}" + (f" ({', '.join(nx[1])})" if nx[1] else ""))
        else:
            line += stage or "?"
        if qs:
            line += "   " + c(BOLD, "owner ") + " ".join(
                c(GREEN, f"{q[0]} answered") if q[2] else c("1;31", f"{q[0]} AWAITING ANSWER") for q in qs)
        L.append(line)
        sym = {GREEN: "✔", RED: "✘", YELLOW: "○"}
        tags = " ".join(c(gcode(g_[0]), f"{g_[0]}{sym[gcode(g_[0])]}") for g_ in g_rows)
        wait_q = {}
        for gs, q in waits:
            wait_q.setdefault(q, []).extend(gs)
        tags += "".join(c(YELLOW, f"   ⏸ {' '.join(dict.fromkeys(gs))} wait on {q}") for q, gs in wait_q.items())
        L.append("  " + c(BOLD, "gates ") + tags)
        names = gate_names()
        for gid, st, note in g_rows:
            if gcode(gid) == RED:
                L.append(f"    {c(RED, '✘ ' + gid + ' ' + names.get(gid, ''))}: " + c(DIM, one_line(note, cols - 30)))

        # ---- usage against its targets
        wusd = read(os.path.join(self.dir, "window_usd")).strip()
        L.append(self.section("USAGE", cols, f"≈ ${wusd} per 5-hour window" if wusd else ""))
        for label, u, tgt, reset, why in (
                ("5-hour", u5, tgt5, r5, "BYPASS_5H" if flags["BYPASS_5H"] else
                 "last hour before reset" if tgt5 == 1.0 and tgt5 != share5 else ""),
                ("weekly", u7, lim7, r7, "BYPASS_7D, no limit" if flags["BYPASS_7D"] else
                 f"paced, weekly target {tgt7:.0%}" if lim7 is not None and lim7 < tgt7 - 1e-9 else "")):
            if u is None:
                L.append(f"  {label:<7} n/a")
                continue
            lim = tgt if tgt is not None else 1.0
            code = RED if u >= lim else YELLOW if u >= lim - 0.1 else GREEN
            tgt_s = f"target {tgt:.0%}" if tgt is not None else "no target"
            if why:
                tgt_s += f" ({why})"
            rs = f"resets {datetime.fromtimestamp(reset).strftime('%a %H:%M')}" if reset else ""
            L.append(f"  {label:<7} {c(code, bar(u, 30, tgt))} {c(code, f'{u:>4.0%}')}  {tgt_s}   {c(DIM, rs)}")
        try:
            hd = f"headroom in this 5-hour window ≈ ${(tgt5 - u5) * float(wusd):.2f} · "
        except (TypeError, ValueError):
            hd = ""
        today = datetime.now().strftime("%Y-%m-%d")
        spent = [float(m[1]) for line in sup_txt.splitlines() if line.startswith(f"[{today}")
                 for m in [re.search(r"run \d+: exit .*cost \$([\d.]+)", line)] if m]
        L.append(c(DIM, f"  {hd}today {len(spent)} sessions, ${sum(spent):.2f}"))

        # ---- supervisor: state in the title, last actions below
        state = ("waiting for the owner" if flags["WAIT_OWNER"] else "session running" if running else
                 "stopped" if flags["STOP"] else "not running" if not sup_alive else
                 (sup[-1][2] if sup and sup[-1][2] else "between sessions"))
        L.append(self.section("SUPERVISOR", cols, state))
        acts, last = [], None
        for t, msg, txt, code in sup:
            if not txt or code == DIM:      # routine lines (usage checks, relaunch timers) left out
                continue
            if last and last[1] == txt:
                last[3] += 1
                continue
            last = [t, txt, code, 1]
            acts.append(last)
        for t, txt, code, n in acts[-3:]:
            L.append(f"  {c(DIM, hhmm(t))}  {c(code, txt)}" + (c(DIM, f"  ×{n}") if n > 1 else ""))

        # ---- session and agents
        if w:
            name = os.path.basename(w.path)[:-6]
            if running:
                el = ago(run_t or w.start or now)
                note = f"running {el} · ≥ ${w.cost or 0:.2f} spent"
            else:
                note = "ended" + (f" {hhmm(last_exit[0])}" if last_exit else "")
            L.append(self.section("SESSION " + name, cols, note))
            # the orchestrator in the agents' layout: model on its row, effort under it, then its purpose
            o_model, o_effort = "?", "?"
            for t, msg, *_ in sup:
                m = re.match(r"preflight ok: .*model (\S+), effort (\w+)", msg)
                if m:
                    o_model, o_effort = m[1], m[2]
            o_model = (re.match(r"claude-([a-z]+)", o_model) or [None, o_model])[1]
            L.append(f"  {c('1;36', '◆')} {c(MAGENTA, f'{o_model:<7}')} {c(DIM, '|')} {c(CYAN, 'orchestrator')}")
            L.append(f"    {c(DIM, f'{o_effort:<7}')} {c(DIM, '|')} " + (f"{c(CYAN, 'why: ')}{one_line(w.purpose, cols - 20)}"
                                                                if w.purpose else ""))
            if w.say:
                L.append(f"  {c(DIM, hhmm(w.say[0]))}  {c(CYAN, 'orchestrator:')} {one_line(w.say[1], cols - 25)}")
            ks = [w.tasks[i] for i in w.order]
            top = [k for k in ks if not k["sub"]]
            # agents launched by an agent, listed under it
            kids = {}
            for k in ks:
                if k["sub"] and k["kind"] == "local_agent" and w.agent_parent.get(k["tuid"]):
                    kids.setdefault(w.agent_parent[k["tuid"]], []).append(k)

            def why_line(k, depth):
                # effort under the model column, then the purpose of the brief
                ind = 4 if depth == 0 else 6 + 4 * depth   # column of the model on the agent's own row
                why = (c(CYAN, "why: ") + one_line(w.why(k), cols - ind - 16)) if w.why(k) else ""
                L.append(" " * ind + c(DIM, f"{w.effort(k):<7}") + " " + c(DIM, "|") + " " + why)

            def nested(k, depth=1):
                for s_ in kids.get(k["tuid"], []):
                    live = s_["status"] == "running" and running
                    ok = s_["status"] in ("running", "completed")
                    mark = c(GREEN, "●") if live else c(GREEN if ok else RED, "✓" if ok else "✗")
                    when = ("since " + hhmm(s_["start"])) if live else hhmm(s_["end"] or s_["start"])
                    L.append(" " * (2 + 4 * depth) + f"└ {mark} {c(MAGENTA if live else DIM, f'{w.model(s_):<7}')} {c(DIM, '|')} "
                             f"{one_line(s_['desc'], 38 - 4 * depth):<{38 - 4 * depth}} {c(DIM, when)}")
                    why_line(s_, depth)
                    nested(s_, depth + 1)

            act = [k for k in top if k["status"] == "running"] if running else []
            done = [k for k in top if k["status"] != "running" and k["kind"] == "local_agent"]
            n_ag = sum(1 for k in top if k["kind"] == "local_agent")
            sub_bg = sum(1 for k in ks if k["sub"] and k["kind"] != "local_agent" and k["status"] == "running") if running else 0
            n_run = sum(1 for k in act if k["kind"] == "local_agent")
            n_watch = len(act) - n_run
            L.append(f"  agents: {c('1;32' if n_run else DIM, f'{n_run} running')}, {n_ag} launched this session"
                     + (f", {n_watch} background wait{'s' if n_watch > 1 else ''}" if n_watch else "")
                     + (c(DIM, f" · {sub_bg} subagent background commands") if sub_bg else ""))
            for k in act:
                is_agent = k["kind"] == "local_agent"
                extra = f"{k['tools']} tools, last {k['last']}" if is_agent and k["tools"] else ""
                L.append(f"  {c(GREEN if is_agent else DIM, '●' if is_agent else '◌')} {c(MAGENTA, f'{w.model(k):<7}')} {c(DIM, '|')} "
                         f"{one_line(k['desc'], 42):<42} {c(DIM, 'since ' + hhmm(k['start']) + '  ' + extra)}")
                if is_agent:
                    why_line(k, 0)
                    nested(k)
            for k in done[-4:]:
                ok = k["status"] == "completed"
                # with a purpose line the agent's purpose replaces the clipped start of its report
                tail = "" if w.why(k) else "  " + one_line(k["summary"], 70)
                L.append(f"  {c(GREEN if ok else RED, '✓' if ok else '✗')} {c(DIM, f'{w.model(k):<7}')} {c(DIM, '|')} "
                         f"{one_line(k['desc'], 42):<42} " + c(DIM, f"{hhmm(k['end'])}{tail}"))
                why_line(k, 0)
                nested(k)
        else:
            L.append(self.section("SESSION", cols))
            L.append("  no session log yet")

        # ---- flights and simulations
        n_sim = sum(len(gr["sims"]) for gr in fl)
        L.append(self.section("FLIGHTS / SIMULATIONS", cols, f"{n_sim} simulator{'s' if n_sim != 1 else ''} up"))
        if not fl:
            L.append("  " + c(DIM, "nothing flying"))
        for gr in fl:
            gdir = os.path.join(HERE, "results", gr["name"])
            title, why = purpose(gdir)
            L.append(f"  {c('1;32', '✈')} {c(BOLD, gr['name'])}" + (f"  {title}" if title else ""))
            if why:
                L.append("      " + c(CYAN, "why: ") + one_line(why, cols - 14))
            bp = batch_progress(gdir)
            if bp:
                done_n, total, cur = bp
                L.append(f"      batch {c(GREEN, bar(done_n / total if total else 0, 24))} {done_n}/{total} done"
                         + (f"   now {cur}" if cur else ""))
            for d in sorted(gr["chains"]):
                try:
                    s = json.loads(read(os.path.join(d, "chain_status.json")) or "{}")
                except ValueError:
                    s = {}
                eta = s.get("eta", "")
                eta = eta[11:16] if isinstance(eta, str) and len(eta) >= 16 else eta
                L.append(f"      chain {os.path.relpath(d, gdir)}: {s.get('state', '?')}, idx {s.get('current_idx')} "
                         f"{s.get('phase', '')}, {s.get('done', 0)}/{s.get('idx_last', 0) - s.get('idx_first', 0) + 1}"
                         f" flown, failed {s.get('failed', 0)}, ETA {eta}")
            for sm in gr["sims"]:
                L.append(f"      sim {sm['scenario']} · {sm['ctrl']} · {sm['model']} @ {sm['rate']} Hz · {sm['run']}"
                         + c(DIM, f"   up {ago(sm['start'])}" if sm["start"] else ""))
        return [clip(l, cols) for l in L]


KEYS = [(r"\033\[A|k", -1), (r"\033\[B|j", 1), (r"\033\[5~|b", "-page"), (r"\033\[6~| ", "page"),
        (r"\033\[H|\033\[1~|g", "home"), (r"\033\[F|\033\[4~|G", "end"),
        (r"\033\[<64;\d+;\d+[Mm]", -3), (r"\033\[<65;\d+;\d+[Mm]", 3), (r"q|Q", "quit")]


def dashboard(directory, interval=3.0, once=False):
    """Full-screen status, scrollable: arrows or j/k, PgUp/PgDn or b/space, Home/End or g/G, mouse wheel; q quits."""
    interactive = sys.stdout.isatty() and sys.stdin.isatty() and not once
    d = Dashboard(directory, interactive)
    if not interactive:
        print("\n".join(d.screen(min(shutil.get_terminal_size((WIDTH, 50))[0], 160))))
        return
    import select
    import termios
    import tty
    fd = sys.stdin.fileno()
    saved = termios.tcgetattr(fd)
    off, lines, due = 0, [], 0.0
    pat = re.compile("|".join(f"({p})" for p, _ in KEYS))
    try:
        tty.setcbreak(fd)
        # alternate screen, hidden cursor, mouse wheel reporting (SGR); all undone on exit
        sys.stdout.write("\033[?1049h\033[?25l\033[?1000h\033[?1006h")
        while True:
            cols, rows = shutil.get_terminal_size((WIDTH, 50))
            if time.time() >= due:
                lines, due = d.screen(min(cols, 160)), time.time() + interval
            view = max(rows - 1, 1)
            off = min(max(off, 0), max(len(lines) - view, 0))
            shown = lines[off:off + view]
            below = len(lines) - off - len(shown)
            foot = (f" ▼ {below} more lines below" if below else " (end)") + (f" · ▲ {off} above" if off else "")
            foot += " · scroll: ↑↓ PgUp PgDn Home End, wheel · q quits "
            out = "\033[H" + "\n".join(l + "\033[K" for l in shown) + "\033[J"
            out += f"\033[{rows};1H\033[7m" + clip(foot, cols - 1) + "\033[0m\033[K"
            sys.stdout.write(out)
            sys.stdout.flush()
            r, _, _ = select.select([fd], [], [], min(max(due - time.time(), 0.05), 0.5))
            if not r:
                continue
            data = os.read(fd, 256).decode(errors="ignore")
            for m in pat.finditer(data):
                act = KEYS[m.lastindex - 1][1]
                if act == "quit":
                    return
                off = {"page": off + view - 1, "-page": off - view + 1, "home": 0,
                       "end": len(lines)}.get(act, off + act if isinstance(act, int) else off)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\033[?1006l\033[?1000l\033[?25h\033[?1049l")
        sys.stdout.flush()
        termios.tcsetattr(fd, termios.TCSADRAIN, saved)


def main():
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)    # `| head` ends quietly
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run", nargs="?")
    ap.add_argument("--dir", default=os.path.join(HERE, "logs"))
    ap.add_argument("--last", action="store_true")
    ap.add_argument("--follow", action="store_true")
    ap.add_argument("--subs", action="store_true")
    ap.add_argument("--thinking", action="store_true")
    ap.add_argument("--results", type=int, default=3)
    ap.add_argument("--dashboard", action="store_true")
    ap.add_argument("--once", action="store_true", help="--dashboard: print the status once and exit")
    ap.add_argument("--interval", type=float, default=3.0, help="--dashboard: refresh period in seconds")
    ap.add_argument("--color", choices=["auto", "always", "never"], default="auto",
                    help="ANSI colors for a transcript (auto: only on a terminal)")
    ap.add_argument("--export", metavar="OUTDIR")
    a = ap.parse_args()
    kw = dict(subs=a.subs, results=a.results, thinking=a.thinking)
    color = a.color == "always" or (a.color == "auto" and sys.stdout.isatty())
    if a.dashboard:
        dashboard(a.dir, a.interval, a.once)
        return
    if a.export:
        os.makedirs(a.export, exist_ok=True)
        links = {}
        for f in sorted(glob.glob(os.path.join(a.dir, "run-*.jsonl"))):
            name = os.path.basename(f)[:-6] + ".md"
            links[f] = name
            with open(os.path.join(a.export, name), "w") as out:
                out.write("```text\n")
                render(f, out, markdown=False, **kw)
                out.write("```\n")
        with open(os.path.join(a.export, "INDEX.md"), "w") as out:
            out.write(f"# Orchestrator sessions in `{os.path.relpath(a.dir, os.path.dirname(HERE))}`\n\n")
            table(a.dir, out, markdown=True, links=links)
        print(f"wrote {len(links)} transcripts and INDEX.md to {a.export}")
        return
    path = a.run
    if a.last:
        path = latest(a.dir)
        if not path:
            sys.exit(f"no run-*.jsonl in {a.dir} yet")
    if path and a.last and a.follow:
        # the supervisor starts a new run-*.jsonl per session: hop to it once the current one is drained
        while path:
            if not render(path, sys.stdout, follow=True, superseded=lambda p=path: latest(a.dir) != p, color=color, **kw):
                break
            path = latest(a.dir)
    elif path:
        render(path, sys.stdout, follow=a.follow, color=color, **kw)
    else:
        table(a.dir)


if __name__ == "__main__":
    main()

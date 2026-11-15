#!/usr/bin/env python3
"""Readable view of the orchestrator's session logs (run-*.jsonl, stream-json).

  indi_flight/logview.py                      table of the sessions in indi_flight/logs
  indi_flight/logview.py --dir indi_project/logs      same for the stage-1 archive
  indi_flight/logview.py RUN.jsonl            one session as a transcript
  indi_flight/logview.py --last               the most recent session
  indi_flight/logview.py --last --follow      the most recent session, live (Ctrl-C to quit)
  indi_flight/logview.py --export OUTDIR [--dir DIR]   one Markdown transcript per session plus INDEX.md

Options for a transcript: --subs shows what subagents did step by step (default: only their launch and result),
--results N shows up to N lines of each tool result (default 3, 0 hides them), --thinking shows reasoning.
Reads only; partial or corrupt lines (a session cut off mid-write) are skipped.
"""
import argparse
import glob
import json
import os
import sys
import textwrap
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
WIDTH = 110


def events(path, follow=False):
    with open(path, errors="replace") as f:
        while True:
            line = f.readline()
            if not line:
                if not follow:
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
    def __init__(self, out, subs=False, results=3, thinking=False, markdown=False):
        self.out, self.subs, self.results, self.thinking, self.md = out, subs, results, thinking, markdown
        self.agents = {}      # tool_use_id -> short label
        self.pending = {}     # tool_use_id -> tool name
        self.n_agents = 0
        self.stats = dict(tools=0, agents=0, cost=None, result=None, start=None, end=None, model=None, title=None,
                          first_say=None, last_say=None)
        self.last_usage = None

    def p(self, s=""):
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
                self.p(f"\n{hhmm}  <<< {label} {e.get('status', '')}: {one_line(e.get('summary', ''), 160)}")
            return
        if t == "rate_limit_event":
            w = (e.get("rate_limit_info") or {}).get("unifiedWindows") or {}
            parts = [f"{k.replace('_', '-')} {round(100 * v.get('utilization', 0))} %" for k, v in w.items()
                     if isinstance(v, dict) and "utilization" in v]
            five = round(100 * (w.get("five_hour") or {}).get("utilization", 0))
            # shown only when the 5-hour window moved by 5 points, otherwise it clutters the transcript
            if parts and (self.last_usage is None or abs(five - self.last_usage) >= 5):
                self.last_usage = five
                self.p(f"{'':10}[usage: {', '.join(parts)}]")
            return
        if t == "result":
            self.stats["cost"] = e.get("total_cost_usd")
            self.stats["result"] = e.get("subtype")
            self.p("\n" + "=" * WIDTH)
            self.p(f"SESSION END  result: {e.get('subtype')}   cost: ${e.get('total_cost_usd', 0):.2f}   "
                   f"turns: {e.get('num_turns', '?')}   duration: {round((e.get('duration_ms') or 0) / 60000)} min")
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
                        self.p(f"\n{hhmm}  {'**ORCHESTRATOR**' if self.md else 'ORCHESTRATOR'}")
                        self.p(wrap(b["text"], "          "))
                    else:
                        self.p(f"{hhmm}  {pre}{one_line(b['text'], 200)}")
                elif bt == "thinking" and self.thinking and b.get("thinking", "").strip():
                    self.p(f"{hhmm}  {pre}(thinking) {one_line(b['thinking'], 400)}")
                elif bt == "tool_use":
                    name, inp = b.get("name", "?"), b.get("input") or {}
                    self.pending[b.get("id")] = name
                    if name in ("Agent", "Task"):
                        self.n_agents += 1
                        self.stats["agents"] += 1
                        label = f"agent {self.n_agents} ({inp.get('model', 'model?')})"
                        self.agents[b.get("id")] = label
                        self.p(f"\n{hhmm}  {pre}>>> LAUNCH {label}: {inp.get('description', '')}")
                        self.p(wrap(one_line(inp.get("prompt", ""), 600), "              | "))
                    else:
                        self.stats["tools"] += 1
                        self.p(f"{hhmm}  {pre}  {name:<6} {tool_summary(name, inp)}")
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
                    self.p(f"\n{hhmm}  {pre}<<< {label} returned:")
                    self.p(wrap(one_line(text, 900), "              | "))
                    continue
                if not text or (self.results == 0 and not err):
                    continue
                lines = text.splitlines()
                shown = lines[: max(self.results, 6 if err else self.results)]
                tag = "ERROR" if err else "     "
                for ln in shown:
                    self.p(f"{'':10}{pre}{tag} > {one_line(ln, 150)}")
                    tag = "     "
                if len(lines) > len(shown):
                    self.p(f"{'':10}{pre}      > … {len(lines) - len(shown)} more lines")


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


def render(path, out, follow=False, **kw):
    tr = Transcript(out, **kw)
    tr.p(f"SESSION {os.path.basename(path)}")
    tr.p("=" * WIDTH)
    try:
        for e in events(path, follow):
            tr.feed(e)
    except KeyboardInterrupt:
        pass


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run", nargs="?")
    ap.add_argument("--dir", default=os.path.join(HERE, "logs"))
    ap.add_argument("--last", action="store_true")
    ap.add_argument("--follow", action="store_true")
    ap.add_argument("--subs", action="store_true")
    ap.add_argument("--thinking", action="store_true")
    ap.add_argument("--results", type=int, default=3)
    ap.add_argument("--export", metavar="OUTDIR")
    a = ap.parse_args()
    kw = dict(subs=a.subs, results=a.results, thinking=a.thinking)
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
        files = sorted(glob.glob(os.path.join(a.dir, "run-*.jsonl")))
        if not files:
            sys.exit(f"no run-*.jsonl in {a.dir} yet")
        path = files[-1]
    if path:
        render(path, sys.stdout, follow=a.follow, **kw)
    else:
        table(a.dir)


if __name__ == "__main__":
    main()

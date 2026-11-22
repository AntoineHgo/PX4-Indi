#!/usr/bin/env python3
"""Readable view of the orchestrator's session logs (run-*.jsonl, stream-json).

  indi_flight/logview.py                      table of the sessions in indi_flight/logs
  indi_flight/logview.py --dir indi_project/logs      same for the stage-1 archive
  indi_flight/logview.py RUN.jsonl            one session as a transcript
  indi_flight/logview.py --last               the most recent session
  indi_flight/logview.py --last --follow      the most recent session, live (Ctrl-C to quit)
  indi_flight/logview.py --dashboard          live status screen: run state, usage, supervisor, recent events
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


COLORS = [(r"^\S+\s+(?:\[[^]]*\]\s+)?ERROR|> ERROR", "31"), (r">>> LAUNCH", "35"), (r"<<<", "35"),
          (r"ORCHESTRATOR", "1;36"), (r"SESSION END", "1;32"), (r"\[usage", "2")]


def paint(line, color):
    if not color:
        return line
    for pat, code in COLORS:
        if re.search(pat, line):
            return f"\033[{code}m{line}\033[0m"
    return line


def usage_line(path):
    """Latest rate-limit windows seen in the run, with their reset time."""
    w = None
    for e in events(path):
        if e.get("type") == "rate_limit_event":
            w = (e.get("rate_limit_info") or {}).get("unifiedWindows") or w
    if not w:
        return "usage: n/a"
    parts = []
    for k, v in w.items():
        if isinstance(v, dict) and "utilization" in v:
            reset = ""
            if v.get("resetsAt"):
                reset = " (resets " + datetime.fromtimestamp(v["resetsAt"]).strftime("%a %H:%M") + ")"
            parts.append(f"{k.replace('_', '-')} {round(100 * v['utilization'])} %{reset}")
    return "usage: " + "   ".join(parts)


def chain_lines(directory, cols):
    """G3 flight chain panel (bench/g3_chain.sh): state, counts, ETA, failing indices, last progress lines."""
    try:
        with open(os.path.join(directory, "flight_chain.dir")) as f:
            cdir = f.read().strip()
    except OSError:
        return []
    if not os.path.isabs(cdir):
        cdir = os.path.join(os.path.dirname(HERE), cdir)
    try:
        with open(os.path.join(cdir, "chain_status.json")) as f:
            s = json.load(f)
    except (OSError, ValueError):
        return [f"G3 chain: {cdir} (no status yet)"]
    held = False
    try:
        import fcntl
        with open(os.path.join(directory, "flight_chain.lock")) as lk:
            try:
                fcntl.flock(lk, fcntl.LOCK_EX | fcntl.LOCK_NB)
                fcntl.flock(lk, fcntl.LOCK_UN)
            except OSError:
                held = True
    except (OSError, ImportError):
        pass
    state = s.get("state", "?")
    if state == "running" and not held:
        state = "DEAD (status says running, lock free)"
    for m in ("CHAIN_HALTED", "CHAIN_FINISHED"):
        if os.path.exists(os.path.join(cdir, m)):
            state += f"  [{m}]"
    first, last = s.get("idx_first", 0), s.get("idx_last", 0)
    total = last - first + 1
    done = s.get("done", 0)
    pct = 100 * done / total if total else 0
    bar_w = max(min(cols, WIDTH) - 60, 10)
    bar = "#" * round(bar_w * pct / 100) + "." * (bar_w - round(bar_w * pct / 100))
    out = [f"G3 chain {os.path.basename(cdir)}: {state}   idx {s.get('current_idx')} {s.get('phase', '')}   "
           f"speed {s.get('speed')}   ETA {s.get('eta', '?')}",
           f"  [{bar}] {done}/{total} ({pct:.0f} %)   failed {s.get('failed', 0)}   outcomes {s.get('outcomes', {})}",
           f"  scored {s.get('scored', 0)} (pending {s.get('score_pending', 0)}):   key 1 pass {s.get('key1_pass', 0)}"
           f"   key 2 pass {s.get('key2_pass', 0)}   mean cycle {s.get('mean_cycle_s', '?')} s   "
           f"updated {s.get('updated', '?')}"]
    try:
        with open(os.path.join(cdir, "progress.txt"), errors="replace") as f:
            prog = [l.rstrip() for l in f]
    except OSError:
        prog = []
    fails = [m.group(1) for l in prog for m in [re.search(r"idx=(\d+) score .*(?:FAIL|fail)", l)] if m]
    if fails:
        out.append("  scoring fails (idx): " + " ".join(dict.fromkeys(fails)))
    out += ["  " + one_line(l, cols - 4) for l in prog[-3:]]
    return out


def dashboard(directory, interval=2.0):
    color = sys.stdout.isatty()
    sup = os.path.join(directory, "supervisor.log")
    try:
        while True:
            cols, rows = shutil.get_terminal_size((WIDTH, 40))
            path = latest(directory)
            buf = io.StringIO()
            head = []
            if path:
                tr = Transcript(buf, subs=True, results=0)
                for e in events(path):
                    tr.feed(e)
                st = tr.stats
                end = st["result"] is not None
                state = f"ended: {st['result']}" if end else "RUNNING"
                try:
                    a = datetime.fromisoformat(st["start"].replace("Z", "+00:00"))
                    b = datetime.now(a.tzinfo) if not end else datetime.fromisoformat(st["end"].replace("Z", "+00:00"))
                    el = f"{round((b - a).total_seconds() / 60)} min"
                except (AttributeError, ValueError):
                    el = "?"
                cost = f"${st['cost']:.2f}" if st["cost"] is not None else "running"
                age = round(time.time() - os.path.getmtime(path))
                head += [f"{os.path.basename(path)}   {state}   elapsed {el}   cost {cost}   "
                         f"{st['tools']} tools, {st['agents']} agents   last write {age}s ago",
                         usage_line(path)]
            else:
                head.append(f"no run-*.jsonl in {directory} yet")
            try:
                with open(sup, errors="replace") as f:
                    sup_lines = [l.rstrip() for l in f.readlines()[-3:]]
            except OSError:
                sup_lines = []
            head += ["supervisor:"] + ["  " + one_line(l, cols - 4) for l in sup_lines]
            head += chain_lines(directory, cols)
            head.append("-" * min(cols, WIDTH))
            body = [l for l in buf.getvalue().splitlines() if l.strip()]
            for i, l in enumerate(body):    # the final report is long: keep its first 3 lines
                if l.startswith("SESSION END"):
                    body = body[:i + 4] + (["  …  (full text: logview.py --last)"] if len(body) > i + 4 else [])
                    break
            body = [one_line(l, cols - 1) if len(l) > cols - 1 else l for l in body]
            room = max(rows - len(head) - 2, 5)
            out = "\033[H\033[2J" if color else ""
            out += "\n".join(paint(l, color) for l in head[:-1]) + "\n" + head[-1] + "\n"
            out += "\n".join(paint(l, color) for l in body[-room:]) + "\n"
            print(out, end="", flush=True)
            time.sleep(interval)
    except KeyboardInterrupt:
        pass


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
    ap.add_argument("--color", choices=["auto", "always", "never"], default="auto",
                    help="ANSI colors for a transcript (auto: only on a terminal)")
    ap.add_argument("--export", metavar="OUTDIR")
    a = ap.parse_args()
    kw = dict(subs=a.subs, results=a.results, thinking=a.thinking)
    color = a.color == "always" or (a.color == "auto" and sys.stdout.isatty())
    if a.dashboard:
        dashboard(a.dir)
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

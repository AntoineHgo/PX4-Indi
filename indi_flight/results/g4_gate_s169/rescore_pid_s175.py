#!/usr/bin/env python3
"""S175: item 2 (rates) on PID reference logs, with and without the Q15 nav_state skip. Docker, repo root:
  indi_project/docker/run.sh -n g4rp -t 900 -- python3 indi_flight/results/g4_gate_s169/rescore_pid_s175.py"""
import json, subprocess
R = "indi_flight/results"
runs = ["a54_s169/pid_hover_harsh_s1", "a56_pid_s173/pid_hover_harsh_s2", "a56_pid_s173/pid_hover_harsh_s3"]
out = ["| PID run | item 2 p/q/r sustained, no skip | item 2 p/q/r sustained, Q15 skip | skipped windows p/q/r | chatter (Q14 rule) |", "|---|---|---|---|---|"]
for n in runs:
    e = [e for e in json.load(open(f"{R}/{n}/run.json"))["events"] if e["name"] == "hold"][0]
    end = e["t_us"] * 1e-6 + e["dur_s"]
    res = {}
    for tag, extra in (("noskip", []), ("skip", ["--skip-nav-change"])):
        subprocess.run(["python3", "indi_flight/bench/g3_checks.py", f"{R}/{n}/flight.ulg", "--t0", str(end - 10), "--t1", str(end), *extra,
                        "--json", f"{R}/{n}/g3_checks_s175_{tag}.json"], capture_output=True, text=True)
        res[tag] = json.load(open(f"{R}/{n}/g3_checks_s175_{tag}.json"))["item2_oscillation"]
    f = lambda o: "/".join("S" if o[k]["sustained"] else "-" for k in "pqr")
    out.append(f"| {n} | {f(res['noskip'])} | {f(res['skip'])} | {'/'.join(str(res['skip'][k]['skipped_windows']) for k in 'pqr')} | "
               f"{'CHATTER' if res['skip']['command_chatter']['sustained'] else 'no'} |")
print("\n".join(out)); open("indi_flight/results/g4_gate_s169/rescore_pid_s175.md", "w").write("\n".join(out) + "\n")

#!/usr/bin/env python3
"""(Q19 copy: runs g4/g3_checks_q19.py = key 1 with the nav_state skip on command chatter; json/md names changed, nothing else.)
S175 re-score of G4 (Q14 A chatter RMS clause, Q15 A nav_state skip). Run in docker from the repo root:
  indi_project/docker/run.sh -n g4rs -t 900 -- sh -c "sh indi_flight/bench/gate_g4.sh score indi_flight/results/g4_gate_s169 && python3 indi_flight/results/g4_gate_s169/rescore_s175.py"
Reads g4_table.md (R20 etc., windows) and runs g3_checks (key1, --skip-nav-change) on every run; writes rescore_key1_q19_runs.md
and <run>/g3_checks_q19.json. Extra args: a directory of PID reference run dirs -> item 2 only table."""
import json, os, subprocess, sys
O = "indi_flight/results/g4_gate_s169"
rows = [l.split("|")[1:-1] for l in open(f"{O}/g4_table.md").read().splitlines()[2:]]
out = ["| run | R20 % | C20 | R4 % | clip | chatter peak ratio (max) | line RMS at max ratio | line RMS max (ratio>20) | chatter | item 2 p/q/r | skipped windows | item 2 | item1 | item3 |", "|" + "---|" * 14]
for r in rows:
    c = [x.strip() for x in r]
    n = c[0]; w0, w1 = map(float, c[1].split("-"))
    ev = "hold" if n.startswith("hover") else "traj"
    e = [e for e in json.load(open(f"{O}/{n}/run.json"))["events"] if e["name"] == ev][0]
    end = e["t_us"] * 1e-6 + e["dur_s"]
    p = subprocess.run(["python3", "indi_flight/results/freeze10_s193/g4/g3_checks_q19.py", f"{O}/{n}/flight.ulg", "--t0", str(end - 10), "--t1", str(end),
                        "--skip-nav-change", "--json", f"{O}/{n}/g3_checks_q19.json"], capture_output=True, text=True)
    j = json.load(open(f"{O}/{n}/g3_checks_q19.json")); o = j["item2_oscillation"]
    ch = [m for m in o["command_chatter"]["motors"]]
    mr = max(ch, key=lambda m: m["max_ratio"])
    rmsfl = [m["max_rms_ratio_flagged"] for m in ch if m["max_rms_ratio_flagged"] is not None]
    pqr = "/".join("S" if o[k]["sustained"] else "-" for k in "pqr")
    sk = "/".join(str(o[k]["skipped_windows"]) for k in "pqr")
    out.append(f"| {n} | {c[3]} | {c[5]} | {c[4]} | {c[7]} | {mr['max_ratio']:.0f} | {mr['rms_at_max_ratio']:.2e} | "
               f"{(max(rmsfl) if rmsfl else 0):.2e} | {'CHATTER' if o['command_chatter']['sustained'] else 'no'} | {pqr} | {sk} | "
               f"{'PASS' if o['pass'] else 'FAIL'} | {'PASS' if j['item1_loc']['pass'] else 'FAIL'} | {'PASS' if j['item3_steady_state']['pass'] else 'FAIL'} |")
open(f"{O}/rescore_key1_q19_runs.md", "w").write("\n".join(out) + "\n")
print("\n".join(out))

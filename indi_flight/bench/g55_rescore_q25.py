#!/usr/bin/env python3
"""Q25 B re-score of tabled G5.5 o-row horizontal RMS (no re-fly). Reads key-1 values from <dir>.check.txt (JSON line),
key-2 values from key2_g55.txt, v_rms from each flight's own truth grid (g55_traj_limit). Prints markdown tables.
Usage: g55_rescore_q25.py   (repo root or anywhere)"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import g55_traj_limit as L  # noqa: E402
import scenarios  # noqa: E402

R = os.path.join(HERE, "..", "results")
F10 = os.path.join(R, "freeze10_s193")
V_LIM = 0.3


def key2_table(path):
    d, cur = {}, None
    for ln in open(path):
        m = re.match(r"(o\d_\w+_s\d) G55", ln)
        if m:
            cur = m.group(1)
        m = re.match(r"\s+(horizontal|vertical) RMS\s+([\d.]+)", ln)
        if m and cur:
            d.setdefault(cur, {})[m.group(1)] = float(m.group(2))
    return d


def vd(x, lim):
    return "PASS" if x <= lim else "FAIL"


def main():
    k2 = key2_table(os.path.join(F10, "g55", "key2_g55.txt"))
    print("## limit table (nominal grid, then per-flight grid range)")
    print("| row | v_rms nominal | H_lim nominal | v_rms flights (min-max) | H_lim flights |")
    print("|---|---|---|---|---|")
    rows = [k for k in scenarios.SCENARIOS if k[:2] in ("o1", "o2", "o3", "o4", "o5", "o6", "o7")]
    cells, nflight = [], {}
    for sc in rows:
        tr = scenarios.SCENARIOS[sc]["traj"]
        vn = L.v_rms(tr, L.nominal_grid(tr))
        vs = []
        for s in (1, 2, 3):
            d = os.path.join(F10, "g55", f"{sc}_s{s}")
            chk = json.loads(open(d + ".check.txt").read().splitlines()[0])
            v1, v2, n1, n2 = L.run_vrms(d)
            vs.append(v1)
            hl = L.h_lim(v1)
            c = k2[f"{sc}_s{s}"]
            cells.append((sc, s, chk["rms_h_m"], c["horizontal"], hl, v1, chk["rms_v_m"], c["vertical"], v1, v2))
        nflight[sc] = (vn, min(vs), max(vs), L.h_lim(min(vs)), L.h_lim(max(vs)))
        print(f"| {sc} | {vn:.4f} | {L.h_lim(vn):.4f} | {min(vs):.4f}-{max(vs):.4f} | {L.h_lim(min(vs)):.4f}-{L.h_lim(max(vs)):.4f} |")
    print("\n## INDI FREEZE-10 per row x seed")
    print("| row | seed | key1 H | key2 H | v_rms | H_lim | key1 | key2 | key1 margin | key2 margin | V key1 | V key2 | V key1 | V key2 |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for sc, s, h1, h2, hl, v, vv1, vv2, a, b in cells:
        print(f"| {sc} | {s} | {h1:.4f} | {h2:.4f} | {v:.3f} | {hl:.4f} | {vd(h1, hl)} | {vd(h2, hl)} | {hl - h1:+.4f} | {hl - h2:+.4f} | "
              f"{vv1:.4f} | {vv2:.4f} | {vd(vv1, V_LIM)} | {vd(vv2, V_LIM)} |")
    print("\n## PID references (G5.5 protocol, stock pid_default, same limit)")
    print("| flight | H (key1 scorer) | v_rms | H_lim | verdict | V | V verdict |")
    print("|---|---|---|---|---|---|---|")
    import subprocess
    pids = [f"freeze10_s193/g55_pid_ref/o2_circle_z_s{s}" for s in (1, 2, 3)] + ["g5_freeze_s157/o1_lemniscate_s1_pid",
            "g5_g55_s139/pid_ref/o1_lemniscate_s1"]
    for p in pids:
        d = os.path.join(R, p)
        out = subprocess.run([sys.executable, os.path.join(HERE, "g55_check.py"), d], capture_output=True, text=True).stdout
        j = json.loads(out.splitlines()[-1])
        v1 = L.run_vrms(d)[0]
        hl = L.h_lim(v1)
        print(f"| {p} | {j['rms_h_m']:.4f} | {v1:.3f} | {hl:.4f} | {vd(j['rms_h_m'], hl)} | {j['rms_v_m']:.4f} | {vd(j['rms_v_m'], V_LIM)} |")


if __name__ == "__main__":
    main()

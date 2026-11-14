#!/usr/bin/env python3
"""Find estimator glitches in recorded runs (infrastructure faults, D-v2-refly rule).

A glitch is |vz| above VZ_MAX or a height jump above JUMP_M within JUMP_S, inside the watchdog window of run.json
(takeoff completion to the land command). Such a run is re-flown for every controller of that (entry, seed).
Single process on purpose: never run heavy analysis beside a flying batch (it caused these glitches).

usage: glitch_scan.py RUNS_DIR   (layout RUNS_DIR/<entry>/<controller>/seed<N>/flight.ulg)
"""

import glob
import json
import os
import sys
import time

import numpy as np
from pyulog import ULog

VZ_MAX = 10.0  # m/s; no scenario commands more than ~3 m/s vertically
JUMP_M, JUMP_S = 5.0, 0.5  # height change no vehicle here can make in that time


def scan(path):
    run = json.load(open(os.path.join(os.path.dirname(path), "run.json")))
    t0, t1 = run["t_offboard_us"] * 1e-6 - 5.0, run["t_window_end_us"] * 1e-6 + 4.0
    p = ULog(path, ["vehicle_local_position"]).data_list[0].data
    t = p["timestamp"] * 1e-6
    m = (t >= t0) & (t <= t1) & np.isfinite(p["z"])
    t, h, vz = t[m], -p["z"][m].astype(float), p["vz"][m].astype(float)
    if len(t) < 2:
        return None
    k = np.searchsorted(t, t + JUMP_S)
    k = np.minimum(k, len(t) - 1)
    jump = np.abs(h[k] - h)
    bad = (np.abs(vz) > VZ_MAX) | (jump > JUMP_M)
    if not bad.any():
        return None
    i = int(np.argmax(bad))
    return t[i], float(np.abs(vz).max()), float(jump.max())


def main():
    root = sys.argv[1]
    rows = []
    for f in sorted(glob.glob(os.path.join(root, "*", "*", "seed*", "flight.ulg"))):
        try:
            r = scan(f)
        except (OSError, ValueError, KeyError, IndexError) as e:
            print("skip %s: %r" % (f, e), file=sys.stderr)
            continue
        if r:
            ent, ctl, seed = f.split(os.sep)[-4:-1]
            wall = time.strftime("%H:%M", time.localtime(os.path.getmtime(f)))
            rows.append((ent, seed, ctl, wall) + r)
    print("| entry | seed | controller | file time | t first (s) | max abs vz (m/s) | max jump (m) |")
    print("|---|---|---|---|---|---|---|")
    for r in rows:
        print("| %s | %s | %s | %s | %.1f | %.1f | %.1f |" % r)
    print("\nre-fly (all controllers): " + " ".join(sorted({"%s/%s" % (r[0], r[1]) for r in rows})))


if __name__ == "__main__":
    main()

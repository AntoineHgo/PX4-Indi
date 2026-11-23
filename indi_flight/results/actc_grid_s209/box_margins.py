#!/usr/bin/env python3
"""Linear margins at the corners of the proposed G3 ACT_TC box (no flight). python3 -I box_margins.py [fs ...]
Reuses cause_s199/margins_s200.py (cfg, loops) unchanged, method of q26_kscale.py. Pitch axis. Plant tau_r = tau_slow/mean/fast of a
motor with mean m x 0.033 and up/down asymmetry 1 or 3 (slow 1.5 m, fast 0.5 m). Worst over G1 error e {0.8,1.2} x telemetry frames {0,3}."""
import itertools, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "g3_refly_s199", "cause_s199"))
import margins_s200 as M
for a in sys.argv[1:] or ["800"]:
    fs = float(a)
    M.FS = fs
    M.W = 2 * np.pi * np.geomspace(0.05, 0.45 * fs, 600)
    print("fs", a)
    print("loop\tplant\tctrl\tm_x\tdelay\tr\tPM\tGM\tDM_ms\tPM_corner\tGM_corner")
    for m, (pl, f), dl, (ct, r) in itertools.product((0.5, 1, 3), (("mean", 1.0), ("slow", 1.5), ("fast", 0.5)), (0, 10),
                                                     (("box", 0.88), ("box", 1.0), ("box", 1.02), ("fixed", None))):
        tm = 0.033 * m
        tc = 0.033 if r is None else r * tm
        res = {}
        for e, fr in itertools.product((0.8, 1.2), (0, 3)):
            p = M.cfg("pitch", e, f * tm, dl, fr, tau_m=tc)
            for n, v in M.loops(p, ("rate", "rate+att")).items():
                res.setdefault(n, []).append(((e, fr), v))
        for n, lst in res.items():
            w = min(lst, key=lambda x: x[1]["pm"]); g = min(lst, key=lambda x: x[1]["gm"])
            print("\t".join(map(str, (n, pl, ct, m, dl, r, "%.1f" % w[1]["pm"], "%.1f" % g[1]["gm"], "%.1f" % (min(x[1]["dm"] for x in lst) * 1e3), w[0], g[0]))))

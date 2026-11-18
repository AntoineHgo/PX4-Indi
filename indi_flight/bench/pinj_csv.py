#!/usr/bin/env python3
"""Extract the outer-loop (acceleration) injection window of one NED axis from a ulog as CSV t,d,x,y, and optionally
estimate the margins with margins_est.py (same convention as m3a_csv.py).

t = indi_pos_status.timestamp [s], d = inject (MC_INDI_PINJ_*), x = a_c (u = c + d, what the INDI stage sees),
y = a_c_pre_inject (c, returned to the summation point), so L = -G_yd/G_xd (margins_est.py docstring).
Window = samples where d != 0 (the module zeroes d outside [t0, t0 + NP*Tp)).
Usage: pinj_csv.py <flight.ulg> <axis 0|1|2 = x|y|z NED> <out.csv> [--Tp S --fmin HZ --fmax HZ] [--margins]
"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import margins_est as me  # noqa: E402


def window(ulg, axis):
    from pyulog import ULog
    s = [d for d in ULog(ulg, ["indi_pos_status"]).data_list if d.name == "indi_pos_status"][0].data
    t = np.asarray(s["timestamp"], float) * 1e-6
    d = np.asarray(s[f"inject[{axis}]"], float)
    nz = np.flatnonzero(d != 0.0)
    if nz.size == 0:
        raise SystemExit("no injection on this axis")
    w = slice(nz[0], nz[-1] + 1)
    x = np.asarray(s[f"a_c[{axis}]"], float)
    y = np.asarray(s[f"a_c_pre_inject[{axis}]"], float)
    return np.column_stack([t[w], d[w], x[w], y[w]])


def estimate(a, Tp, fmin, fmax, discard=1):
    t, d, x, y = a.T
    fs = 1.0 / np.median(np.diff(t))
    res = me.frf_periodic(d, x, y, fs, Tp, me.log_bins(fmin, fmax, Tp), discard, t=t)
    return res, me.margins_from_frf(res), fs


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("ulg")
    ap.add_argument("axis", type=int, choices=(0, 1, 2))
    ap.add_argument("out")
    ap.add_argument("--Tp", type=float, default=None, help="multisine period [s], needed for --margins")
    ap.add_argument("--fmin", type=float, default=0.2, help="MC_INDI_PINJ_FLO")
    ap.add_argument("--fmax", type=float, default=8.0, help="MC_INDI_PINJ_FHI")
    ap.add_argument("--margins", action="store_true", help="print the margins_est result as JSON")
    a = ap.parse_args(argv)
    w = window(a.ulg, a.axis)
    np.savetxt(a.out, w, delimiter=",", header="t,d,x,y", comments="", fmt="%.9g")
    if a.margins:
        if not a.Tp:
            raise SystemExit("--margins needs --Tp")
        res, mg, fs = estimate(w, a.Tp, a.fmin, a.fmax)
        out = {"fs": fs, "margins": mg, "f": res["f"], "coh_x": res["g2_xd"], "coh_y": res["g2_yd"],
               "L_abs": np.abs(res["L"]), "accepted": res["accepted"]}
        print(json.dumps(out, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o)))


if __name__ == "__main__":
    main()

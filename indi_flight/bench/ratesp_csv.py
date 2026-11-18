#!/usr/bin/env python3
"""Attitude-loop break (MC_INDI_INJ_PT = 1) extractor: loop gain L(f) at the rate-setpoint injection point.

Reads `indi_rate_status` (time base `timestamp_sample`): y = rates_sp_pre_inject (attitude-controller output),
d = rates_sp_inject, x = rates_sp_applied = y + d (what the INDI law receives).  Loop gain y = -L x, so
L = -Y/X at the excited bins (margins_est.frf_periodic, same convention as pinj_csv.py).
Window = samples where d != 0 (the module zeroes d outside the injection window).

Usage: ratesp_csv.py <flight.ulg> <axis 0|1|2> <out.csv> --Tp 10 --fmin 0.2 --fmax 20 [--margins]
CSV per excited bin: f_hz, L_db, arg_L_deg (unwrapped over f), coh (min of the two coherences), L_spread (per-period
std of L / |L|), accepted.  --margins prints JSON: pm_deg, gm_db, f_c_hz, validity checks, full margins_est result.
"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import margins_est as me  # noqa: E402


def load(ulg, axis):
    from pyulog import ULog
    s = [d for d in ULog(ulg, ["indi_rate_status"]).data_list if d.name == "indi_rate_status"][0].data
    g = lambda n: np.asarray(s[n], float)  # noqa: E731
    t = np.asarray(s["timestamp_sample"], np.int64) * 1e-6
    return t, g(f"rates_sp_inject[{axis}]"), g(f"rates_sp_applied[{axis}]"), g(f"rates_sp_pre_inject[{axis}]")


def window(t, d, x, y):
    """Samples from the first to the last d != 0. Returns array columns t,d,x,y."""
    nz = np.flatnonzero(d != 0.0)
    if nz.size == 0:
        raise SystemExit("no injection on this axis")
    w = slice(nz[0], nz[-1] + 1)
    return np.column_stack([t[w], d[w], x[w], y[w]])


def estimate(a, Tp, fmin, fmax, discard=1):
    t, d, x, y = a.T
    fs = 1.0 / np.median(np.diff(t))
    res = me.frf_periodic(d, x, y, fs, Tp, me.log_bins(fmin, fmax, Tp), discard, t=t)
    if int(np.sum(res["accepted"])) < 2:
        nan = float("nan")
        return res, {"pm_deg": nan, "gm_db": nan, "crossings": [], "phase_crossings": [], "no_accepted_bins": True}, fs
    return res, me.margins_from_frf(res), fs


def validity(a, Tp):
    t, d, x, y = a.T
    dt = np.diff(t)
    return {"max_abs_x_minus_y_minus_d": float(np.max(np.abs(x - y - d))),
            "window_len_s": float(t[-1] - t[0]), "n_periods_complete": int(np.floor((t[-1] - t[0]) / Tp + 1e-6)),
            "n_samples": int(len(t)), "max_gap_s": float(dt.max()), "max_gap_periods": float(dt.max() / Tp),
            "median_dt_s": float(np.median(dt))}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("ulg")
    ap.add_argument("axis", type=int, choices=(0, 1, 2))
    ap.add_argument("out")
    ap.add_argument("--Tp", type=float, required=True, help="MC_INDI_INJ_TP [s]")
    ap.add_argument("--fmin", type=float, default=0.2)
    ap.add_argument("--fmax", type=float, default=20.0)
    ap.add_argument("--margins", action="store_true")
    a = ap.parse_args(argv)
    w = window(*load(a.ulg, a.axis))
    res, mg, fs = estimate(w, a.Tp, a.fmin, a.fmax)
    L = res["L"]
    spread = res["L_std"] / np.abs(L)
    coh = np.minimum(res["g2_xd"], res["g2_yd"])
    tab = np.column_stack([res["f"], 20 * np.log10(np.abs(L)), np.degrees(np.unwrap(np.angle(L))), coh, spread,
                           res["accepted"].astype(float)])
    np.savetxt(a.out, tab, delimiter=",", header="f_hz,L_db,arg_L_deg,coh,L_spread,accepted", comments="", fmt="%.9g")
    if a.margins:
        fc = [c["f_c"] for c in mg["crossings"]]
        out = {"pm_deg": mg["pm_deg"], "gm_db": mg["gm_db"], "f_c_hz": fc[0] if fc else float("nan"),
               "f_c_all_hz": fc, "validity": validity(w, a.Tp), "fs": fs, "margins": mg,
               "band_limited": mg.get("band_limited"), "n_accepted": int(np.sum(res["accepted"]))}
        print(json.dumps(out, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o)))


if __name__ == "__main__":
    main()

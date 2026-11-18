#!/usr/bin/env python3
"""Extract the outer-loop (acceleration) injection window of one NED axis from a ulog as CSV t,d,x,y, and optionally
estimate the margins with margins_est.py (same convention as m3a_csv.py).

t = indi_pos_status.timestamp [s], d = inject (MC_INDI_PINJ_*), x = a_c (u = c + d, what the INDI stage sees),
y = a_c_pre_inject (c, returned to the summation point), so L = -G_yd/G_xd (margins_est.py docstring).
Window = samples where d != 0 (the module zeroes d outside [t0, t0 + NP*Tp)).
Usage: pinj_csv.py <flight.ulg> <axis 0|1|2 = x|y|z NED> <out.csv> [--Tp S --fmin HZ --fmax HZ] [--margins] [--point input|output]
With --point output (MC_INDI_PINJ_PT = 1): u = t_c_applied = t_c + d (plant input of the acceleration loop), c = t_c.
"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import margins_est as me  # noqa: E402


def window(ulg, axis, point="input"):
    from pyulog import ULog
    s = [d for d in ULog(ulg, ["indi_pos_status"]).data_list if d.name == "indi_pos_status"][0].data
    t = np.asarray(s["timestamp"], float) * 1e-6
    d = np.asarray(s[f"inject[{axis}]"], float)
    nz = np.flatnonzero(d != 0.0)
    if nz.size == 0:
        raise SystemExit("no injection on this axis")
    w = slice(nz[0], nz[-1] + 1)
    if point == "output":  # acceleration-loop break (MC_INDI_PINJ_PT = 1): c = t_c, u = t_c_applied = t_c + d
        x = np.asarray(s[f"t_c_applied[{axis}]"], float)
        y = np.asarray(s[f"t_c[{axis}]"], float)
    else:
        x = np.asarray(s[f"a_c[{axis}]"], float)
        y = np.asarray(s[f"a_c_pre_inject[{axis}]"], float)
    return np.column_stack([t[w], d[w], x[w], y[w]])


def estimate(a, Tp, fmin, fmax, discard=1):
    t, d, x, y = a.T
    fs = 1.0 / np.median(np.diff(t))
    res = me.frf_periodic(d, x, y, fs, Tp, me.log_bins(fmin, fmax, Tp), discard, t=t)
    if int(np.sum(res["accepted"])) < 2:  # nothing to interpolate (all bins failed coherence): explicit, not an IndexError
        nan = float("nan")
        return res, {"pm_deg": nan, "dm_s": nan, "gm_db": nan, "crossings": [], "phase_crossings": [],
                     "band_limited": True, "top_db": nan, "no_accepted_bins": True}, fs
    return res, me.margins_from_frf(res), fs


def crossing_report(res, mg):
    """Explicit in-band status of the gain (|L| = 1) and phase (-180 deg) crossovers, for the --margins JSON.
    A missing crossover is a result (e.g. |L| < 1 over the whole band), not an error."""
    acc = np.asarray(res["accepted"], bool)
    f = np.asarray(res["f"], float)[acc]
    L = np.asarray(res["L"])[acc]
    if mg.get("no_accepted_bins") or f.size == 0:
        t = "no accepted bins (coherence below threshold everywhere): no crossover can be assessed"
        return {"gain_crossover": {"in_band": False, "text": t}, "phase_crossover": {"in_band": False, "text": t}}
    db = 20 * np.log10(np.abs(L))
    i = int(np.argmax(db))
    if mg["crossings"]:
        g = {"in_band": True, "f_c_hz": [c["f_c"] for c in mg["crossings"]], "text": "gain crossover in band"}
    else:
        g = {"in_band": False, "max_L_db": float(db[i]), "f_at_max_hz": float(f[i]),
             "text": "no 0 dB crossover in band (%.2f-%.2f Hz, accepted bins), max |L| = %.1f dB at %.2f Hz"
                     % (f[0], f[-1], db[i], f[i])}
    if mg["phase_crossings"]:
        p = {"in_band": True, "f_hz": [c["f"] for c in mg["phase_crossings"]], "text": "phase crossover in band"}
    else:
        ph = np.degrees(np.unwrap(np.angle(L)))
        j = int(np.argmin(ph))
        p = {"in_band": False, "min_arg_deg": float(ph[j]), "f_at_min_hz": float(f[j]),
             "text": "no -180 deg crossover in band, lowest unwrapped arg L = %.1f deg at %.2f Hz; |L| there %.1f dB"
                     % (ph[j], f[j], db[j])}
    return {"gain_crossover": g, "phase_crossover": p}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("ulg")
    ap.add_argument("axis", type=int, choices=(0, 1, 2))
    ap.add_argument("out")
    ap.add_argument("--Tp", type=float, default=None, help="multisine period [s], needed for --margins")
    ap.add_argument("--fmin", type=float, default=0.2, help="MC_INDI_PINJ_FLO")
    ap.add_argument("--fmax", type=float, default=8.0, help="MC_INDI_PINJ_FHI")
    ap.add_argument("--point", choices=("input", "output"), default="input",
                    help="input: x = a_c, y = a_c_pre_inject (PINJ_PT 0); output: x = t_c_applied, y = t_c (PINJ_PT 1)")
    ap.add_argument("--margins", action="store_true", help="print the margins_est result as JSON")
    a = ap.parse_args(argv)
    w = window(a.ulg, a.axis, a.point)
    np.savetxt(a.out, w, delimiter=",", header="t,d,x,y", comments="", fmt="%.9g")
    if a.margins:
        if not a.Tp:
            raise SystemExit("--margins needs --Tp")
        res, mg, fs = estimate(w, a.Tp, a.fmin, a.fmax)
        out = {"fs": fs, "margins": mg, "f": res["f"], "coh_x": res["g2_xd"], "coh_y": res["g2_yd"],
               "L_abs": np.abs(res["L"]), "accepted": res["accepted"], "report": crossing_report(res, mg)}
        print(json.dumps(out, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o)))


if __name__ == "__main__":
    main()

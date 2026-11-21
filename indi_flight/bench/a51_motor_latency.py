#!/usr/bin/env python3
"""A-51: command-to-rotor-speed latency in the sim, from one ulg (esc_status esc_rpm vs actuator_motors).
Usage: a51_motor_latency.py LOG.ulg [t0 t1]   (s since log start; default 60 80 = the M3a injection window of the freeze runs)
Fit per motor: rpm(t) = a + b * LP1_tau(cmd(t - d)) on a 0.1 ms grid, grid search d 0..30 ms and tau 15..60 ms (linear LS in a, b).
Reports (d, tau) for the free fit and d at tau fixed 33 ms (the airframe rotor time constant).  d includes the one-frame eRPM telemetry
reply (SIM_GZ_ERPM_LAT 0) and the sample-and-hold quantisation of the physics step; it is the lag the controller sees, not a pure ESC delay."""
import sys
import numpy as np
from pyulog import ULog

path = sys.argv[1]
t0 = float(sys.argv[2]) if len(sys.argv) > 2 else 60.0
t1 = float(sys.argv[3]) if len(sys.argv) > 3 else 80.0
u = ULog(path, ["esc_status", "actuator_motors"])
ts0 = u.start_timestamp
fb = u.initial_parameters.get("SIM_GZ_ESC_FB")
inst = max(d.multi_id for d in u.data_list if d.name == "esc_status")  # only instance logged in the freeze ulgs
esc = u.get_dataset("esc_status", inst).data
am = u.get_dataset("actuator_motors").data
ke = "timestamp_sample" if "timestamp_sample" in esc else "timestamp"
kc = "timestamp_sample" if "timestamp_sample" in am else "timestamp"
te = (esc[ke].astype(np.int64) - ts0) * 1e-6
tc = (am[kc].astype(np.int64) - ts0) * 1e-6
DT = 1e-4
g = np.arange(t0, t1, DT)
res = []
for i in range(4):
    rpm = np.abs(esc[f"esc[{i}].esc_rpm"]).astype(float)
    cmd = am[f"control[{i}]"].astype(float)
    # command is held between samples (zero-order hold); rpm sampled-and-held
    ci = np.searchsorted(tc, g, side="right") - 1
    ri = np.searchsorted(te, g, side="right") - 1
    c = cmd[np.clip(ci, 0, len(cmd) - 1)]
    r = rpm[np.clip(ri, 0, len(rpm) - 1)]
    best = {}
    for tau in np.arange(0.015, 0.0601, 0.001):
        a = np.exp(-DT / tau)
        # LP1 via recursive filter on a decimated 1 ms grid for speed would lose resolution; use scipy-free lfilter via cumulative form
        y = np.empty_like(c)
        acc = c[0]
        # vectorised first-order IIR with chunked loop is slow in python; use exact FFT-free approach: np.convolve with truncated kernel
        k = (1 - a) * a ** np.arange(int(8 * tau / DT))
        y = np.convolve(c, k, mode="full")[: len(c)]
        for d in np.arange(0.0, 0.0301, 0.0005):
            n = int(round(d / DT))
            yy = y[: len(y) - n] if n else y
            rr = r[n:]
            m = slice(int(0.5 / DT), None)  # drop filter start-up
            A = np.vstack([np.ones_like(yy[m]), yy[m]]).T
            sol, *_ = np.linalg.lstsq(A, rr[m], rcond=None)
            e = np.mean((A @ sol - rr[m]) ** 2)
            best[(round(tau, 4), round(d, 4))] = e
    (tau_b, d_b), _ = min(best.items(), key=lambda kv: kv[1])
    d33 = min(((k[1], v) for k, v in best.items() if abs(k[0] - 0.033) < 1e-6), key=lambda x: x[1])[0]
    res.append((i, tau_b, d_b, d33))
    print(f"motor {i}: free fit tau {tau_b*1e3:.0f} ms, delay {d_b*1e3:.1f} ms | tau fixed 33 ms: delay {d33*1e3:.1f} ms", flush=True)
print(f"mean delay free {np.mean([x[2] for x in res])*1e3:.2f} ms, tau33 {np.mean([x[3] for x in res])*1e3:.2f} ms; esc_fb {fb} inst {inst}")

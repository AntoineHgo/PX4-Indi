#!/usr/bin/env python3
"""S40 pre-test checks of an indi_m3a bench injection run (raw output, untracked).
Usage: checks.py <run_dir> <AMP> <DLY_s>   (run inside the px4 container, repo root as cwd)"""
import json
import os
import sys

import numpy as np
from pyulog import ULog

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "bench"))
import margins_est as me  # noqa: E402

run, amp, dly = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
TP, FMIN, FMAX, FS = 10.0, 1.0, 60.0, 800.0
NP = int(sys.argv[4]) if len(sys.argv) > 4 else 2

meta = json.load(open(os.path.join(run, "run.json")))
u = ULog(os.path.join(run, "flight.ulg"))


def get(name):
    ds = [d for d in u.data_list if d.name == name and d.multi_id == 0]
    return ds[0].data if ds else None


def vec(dct, prefix):
    return np.stack([np.asarray(dct[f"{prefix}[{i}]"], float) for i in range(3)], axis=1)


print(f"== {run}  exit_status={meta.get('exit_status')}  AMP={amp} DLY={dly}")
r = get("indi_rate_status")
if r is None:
    raise SystemExit("indi_rate_status MISSING")
ts_key = "timestamp_sample" if "timestamp_sample" in r else "timestamp"
print(f"time base: {ts_key}" + ("" if ts_key == "timestamp_sample" else "  WARNING: timestamp_sample absent, using timestamp"))
ts = np.asarray(r[ts_key], np.int64)
n = len(ts)
dt = np.diff(ts) * 1e-6
span = (ts[-1] - ts[0]) * 1e-6
print(f"[2] indi_rate_status n={n} median_rate={1 / np.median(dt):.2f} Hz mean_rate={(n - 1) / span:.2f} Hz "
      f"span={span:.3f} s dt==0:{int(np.sum(dt == 0))} gaps>1.5ms:{int(np.sum(dt > 1.5e-3))}")
amt = get("actuator_torque_measured")
if amt is None:
    print("[2] actuator_torque_measured: ABSENT")
else:
    tm = np.asarray(amt["timestamp"], np.int64)
    print(f"[2] actuator_torque_measured: present n={len(tm)} median_rate={1 / np.median(np.diff(tm) * 1e-6):.2f} Hz")

c = vec(r, "torque_sp_pre_inject")
d = vec(r, "inject")
uu = vec(r, "torque_sp")
fault = np.asarray(r["fault"]).astype(bool)
mtu = np.asarray(r["measured_torque_in_use"]).astype(bool) if "measured_torque_in_use" in r else None
nzax = [k for k in range(3) if np.any(d[:, k] != 0)]
idx = np.flatnonzero(np.any(d != 0, axis=1))
if idx.size == 0:
    raise SystemExit("no nonzero inject sample")
i0, i1 = int(idx[0]), int(idx[-1])
win = slice(i0, i1 + 1)
t0_us = int(ts[i0])
print(f"[3] injection axes (0=roll,1=pitch,2=yaw) nonzero: {nzax}; nonzero samples {idx.size}; "
      f"window idx {i0}..{i1}, t0={t0_us * 1e-6:.4f} s, end={ts[i1] * 1e-6:.4f} s, span={(ts[i1] - t0_us) * 1e-6:.4f} s")
print(f"[3] fault in window: {int(fault[win].sum())} of {i1 - i0 + 1}; fault whole run: {int(fault.sum())}")
if mtu is not None:
    print(f"[3] measured_torque_in_use in window: {int(mtu[win].sum())}; whole run: {int(mtu.sum())}")
ld = get("vehicle_land_detected")
if ld is None:
    print("[3] vehicle_land_detected MISSING")
    landed_held_win = None
else:
    lts = np.asarray(ld["timestamp"], np.int64)
    lnd = np.asarray(ld["landed"]).astype(bool)
    k = np.searchsorted(lts, ts, side="right") - 1  # sample-and-hold of the land detector state
    held = np.where(k >= 0, lnd[np.clip(k, 0, None)], True)
    landed_held_win = int(held[win].sum())
    print(f"[3] landed (held) in window: {landed_held_win} of {i1 - i0 + 1}; land-detector samples in window: "
          f"{int(np.sum((lts >= t0_us) & (lts <= ts[i1])))}; landed whole run (held): {int(held.sum())} of {n}")

# [4] u = c + d
err = np.abs(uu - (c + d))
print("[4] u=c+d max abs err per axis:", " ".join(f"{e:.3g}" for e in err.max(axis=0)),
      f"| injected axis {nzax[0]}: {err[:, nzax[0]].max():.3g}")
ldw = None

# [1] attitude over the window
att = get("vehicle_attitude")
if att is not None:
    qw, qx, qy, qz = (np.asarray(att[f"q[{i}]"], float) for i in range(4))
    roll = np.degrees(np.arctan2(2 * (qw * qx + qy * qz), 1 - 2 * (qx ** 2 + qy ** 2)))
    pitch = np.degrees(np.arcsin(np.clip(2 * (qw * qy - qz * qx), -1, 1)))
    at = np.asarray(att["timestamp"], np.int64)
    m = (at >= t0_us) & (at <= ts[i1])
    print(f"[1] attitude in window: n={int(m.sum())} max|roll|={np.abs(roll[m]).max():.2f} deg "
          f"max|pitch|={np.abs(pitch[m]).max():.2f} deg; whole run max|roll|={np.abs(roll).max():.2f} "
          f"max|pitch|={np.abs(pitch).max():.2f}")

# [6] arming / take-off / injection start
arm = get("actuator_armed")
t_arm = None
if arm is not None:
    am = np.asarray(arm["armed"]).astype(bool)
    if am.any():
        t_arm = int(np.asarray(arm["timestamp"], np.int64)[am][0])
t_air = None
if ld is not None and t_arm is not None:
    sel = (lts >= t_arm) & (~lnd)
    if sel.any():
        t_air = int(lts[sel][0])
lp = get("vehicle_local_position")
if t_arm is not None:
    print(f"[6] armed at {t_arm * 1e-6:.3f} s")
if t_air is not None:
    print(f"[6] first armed & not-landed (land detector) at {t_air * 1e-6:.3f} s; "
          f"injection start t0 at {t0_us * 1e-6:.3f} s; t0 - not-landed = {(t0_us - t_air) * 1e-6:.3f} s "
          f"(MC_INDI_INJ_DLY={dly} s); t0 - armed = {(t0_us - t_arm) * 1e-6:.3f} s")
if lp is not None:
    lpt = np.asarray(lp["timestamp"], np.int64)
    z = np.asarray(lp["z"], float)
    print(f"[6] height (-z) at t0 = {-np.interp(t0_us, lpt, z):.2f} m, at window end = {-np.interp(ts[i1], lpt, z):.2f} m")

# [5] generator check
bins = me.log_bins(FMIN, FMAX, TP, per_decade=10, n_axes=1, axis=0)
freqs = bins / TP
K = len(freqs)
amps = np.full(K, amp)


def expected(t):
    fr = np.sort(freqs)
    p = amps ** 2 / np.sum(amps ** 2)
    phi = np.array([-2 * np.pi * np.sum((kk - np.arange(kk)) * p[:kk]) for kk in range(K)])
    out = np.zeros_like(t, dtype=float)
    for f, a, ph in zip(fr, amps, phi):
        out += a * np.cos(2 * np.pi * f * t + ph)
    return out


tg, dref = me.multisine(freqs, amps, FS, TP, NP)
print(f"[5] generator: K={K} components, f {freqs[0]:.2f}..{freqs[-1]:.2f} Hz, self-check formula vs margins_est.multisine "
      f"max diff {np.max(np.abs(expected(tg) - dref)):.2e}")
dl = d[:, nzax[0]]
for label, tt0 in (("t0", t0_us), ("t0 - 1.25 ms", t0_us - 1250)):
    t = (ts - tt0) * 1e-6
    m = (t >= 0) & (t < NP * TP)
    e = expected(t[m])
    diff = np.abs(dl[m] - e)
    print(f"[5] {label}: samples in [0,{NP * TP}) s = {int(m.sum())}, max|logged d - expected| = {diff.max():.3e}, "
          f"samples with |d|>1e-6 in that range = {int(np.sum(np.abs(dl[m]) > 1e-6))}")
outside = (ts - t0_us) * 1e-6
mo = (outside < 0) | (outside >= NP * TP)
print(f"[5] max|d| outside [t0, t0+{NP * TP} s): {np.max(np.abs(dl[mo])) if mo.any() else 0:.3e}")
print(f"[5] samples with |d|>1e-6 in whole run (logged): {int(np.sum(np.abs(dl) > 1e-6))}")
print()

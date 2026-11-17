#!/usr/bin/env python3
"""G2-STEP PRIMARY metric (GATES.md "G2-STEP", measurement definition written S63).

  python3 bench/g2_step_metrics.py OUT.json FLIGHT_DIR [FLIGHT_DIR ...]

FLIGHT_DIR holds flight.ulg and run.json (scenario step_roll|step_pitch|step_yaw, t_window_start_us).
Only the FIRST step after t_window_start_us is measured (later step pairs are ignored).
All angles in degrees, times in us. Core functions take numpy arrays (no ULog needed).
"""
import json
import math
import os
import sys

import numpy as np

NOMINAL = {"roll": 15.0, "pitch": 15.0, "yaw": 45.0}  # deg, used only to detect the crossing
SETTLE_LIM_MS = {"roll": 450.0, "pitch": 450.0, "yaw": 1350.0}
OS_LIM_PCT = 5.0
PRE_US = 1_000_000        # median window before a crossing
MARGIN_US = 50_000        # window ends this long before the return step
END_US = 1_500_000        # last part of the window for the end estimator error
POST_US = 1_000_000       # span after t_on used for the median that gives the step size / final value


def wrap180(x):
    return (np.asarray(x, float) + 180.0) % 360.0 - 180.0


def euler_zyx_deg(q):
    """q (N,4) w-x-y-z -> roll, pitch, yaw in deg (yaw unwrapped)."""
    q = np.asarray(q, float)
    w, x, y, z = q[:, 0], q[:, 1], q[:, 2], q[:, 3]
    roll = np.arctan2(2 * (w * x + y * z), 1 - 2 * (x * x + y * y))
    pitch = np.arcsin(np.clip(2 * (w * y - z * x), -1, 1))
    yaw = np.unwrap(np.arctan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z)))
    return np.degrees(roll), np.degrees(pitch), np.degrees(yaw)


def _pre_median(t, x, i):
    j = np.searchsorted(t, t[i] - PRE_US, side="left")
    return np.median(x[j:i]) if i > j else math.nan


def find_crossing(t, x, thresh, t_from, t_min_sample=0):
    """Index of the first sample with t >= t_from whose value is >= thresh away from the median of the 1 s before it."""
    for i in range(max(np.searchsorted(t, t_from, side="left"), t_min_sample), len(t)):
        m = _pre_median(t, x, i)
        if not math.isnan(m) and abs(x[i] - m) >= thresh:
            return i
    return None


def find_steps(t_sp, sp, nominal, t_start_us):
    """-> dict(i_on, t_on, t_next|None, sp_pre, step) from the setpoint axis angle (deg, unwrapped)."""
    t_sp = np.asarray(t_sp, float)
    sp = np.asarray(sp, float)
    i_on = find_crossing(t_sp, sp, 0.5 * nominal, t_start_us)
    if i_on is None:
        raise ValueError("no setpoint step found after t_window_start")
    t_on = t_sp[i_on]
    sp_pre = _pre_median(t_sp, sp, i_on)
    post = sp[(t_sp >= t_on) & (t_sp < t_on + POST_US)]
    step = float(np.median(post) - sp_pre)
    # return step: searched from t_on + 1 s, where the 1 s median before a sample lies wholly in the hold level
    i_next = find_crossing(t_sp, sp, 0.5 * abs(step), t_on + POST_US)
    t_next = None if i_next is None else float(t_sp[i_next])
    return dict(t_on=float(t_on), t_next=t_next, sp_pre=float(sp_pre), step=step)


def _settle_ms(t, e, step, t_on, tol_frac=0.02):
    """e normalised so the final value is step (>0); time from t_on after which |e - step| stays <= tol. NaN if never."""
    bad = np.abs(e - step) > tol_frac * step
    if bad.size == 0 or bad[-1]:
        return math.nan
    idx = np.nonzero(bad)[0]
    k = 0 if idx.size == 0 else idx[-1] + 1
    return (t[k] - t_on) / 1e3


def _rise_ms(t, e, step):
    """10-90 % rise: linear-interpolated first crossings of 0.1 and 0.9 step."""
    def first(level):
        k = np.nonzero(e >= level)[0]
        if k.size == 0:
            return math.nan
        k = k[0]
        if k == 0:
            return t[0]
        return t[k - 1] + (level - e[k - 1]) / (e[k] - e[k - 1]) * (t[k] - t[k - 1])
    return (first(0.9 * step) - first(0.1 * step)) / 1e3


def _os_pct(e, step):
    return max(0.0, (float(np.max(e)) - step) / step * 100.0)


def step_metrics(t_sp, sp, t_est, est, t_tr, tr, nominal, t_start_us, settle_lim_ms, drop_margin=True):
    """Metrics for the first step after t_start_us. sp/est/tr: one axis in deg (yaw unwrapped); times in us."""
    t_sp, t_est, t_tr = (np.asarray(a, float) for a in (t_sp, t_est, t_tr))
    sp, est, tr = (np.asarray(a, float) for a in (sp, est, tr))
    s = find_steps(t_sp, sp, nominal, t_start_us)
    t_on, t_next, sp_pre, step_raw = s["t_on"], s["t_next"], s["sp_pre"], s["step"]
    sign = 1.0 if step_raw >= 0 else -1.0
    step = abs(step_raw)
    t_end = (t_next - (MARGIN_US if drop_margin else 0.0)) if t_next is not None else float(t_est[-1]) + 1.0
    # truth on estimate timestamps (unwrapped truth, interpolated); angles relative to the pre-step setpoint, step positive
    tr_i = np.interp(t_est, t_tr, tr)
    m = (t_est >= t_on) & (t_est < t_end)
    te = t_est[m]
    e_est = sign * wrap180(est[m] - sp_pre)
    e_tr = sign * wrap180(tr_i[m] - sp_pre)
    err = wrap180(est - tr_i)  # raw sign, est - truth
    pre = (t_est >= t_on - PRE_US) & (t_est < t_on)
    end = (t_est >= t_end - END_US) & (t_est < t_end)
    out = dict(
        step_deg=step_raw, t_on_us=int(t_on), t_next_us=None if t_next is None else int(t_next),
        window_ms=(t_end - t_on) / 1e3,
        est_rise_ms=_rise_ms(te, e_est, step), est_os_pct=_os_pct(e_est, step),
        est_settle_ms=_settle_ms(te, e_est, step, t_on),
        truth_os_pct=_os_pct(e_tr, step), truth_settle_ms=_settle_ms(te, e_tr, step, t_on),
        est_minus_truth_pre_deg=float(np.mean(err[pre])) if pre.any() else math.nan,
        est_minus_truth_end_deg=float(np.mean(err[end])) if end.any() else math.nan,
    )
    ok_settle = not math.isnan(out["est_settle_ms"]) and out["est_settle_ms"] <= settle_lim_ms
    out["pass"] = bool(out["est_os_pct"] <= OS_LIM_PCT and ok_settle and out["truth_os_pct"] <= OS_LIM_PCT)
    return out


def load_flight(path):
    from pyulog import ULog
    run = json.load(open(os.path.join(path, "run.json")))
    axis = run["scenario"].replace("step_", "")
    ul = ULog(os.path.join(path, "flight.ulg"),
              ["vehicle_attitude", "vehicle_attitude_setpoint", "vehicle_attitude_groundtruth"])

    def get(name, field):
        d = ul.get_dataset(name, 0).data
        return d["timestamp"], np.stack([d[f"{field}[{k}]"] for k in range(4)], 1)
    k = {"roll": 0, "pitch": 1, "yaw": 2}[axis]
    t_e, q_e = get("vehicle_attitude", "q")
    t_s, q_s = get("vehicle_attitude_setpoint", "q_d")
    t_g, q_g = get("vehicle_attitude_groundtruth", "q")
    return run, axis, (t_s, euler_zyx_deg(q_s)[k]), (t_e, euler_zyx_deg(q_e)[k]), (t_g, euler_zyx_deg(q_g)[k])


def measure_flight(path):
    run, axis, (ts, sp), (te, est), (tg, tr) = load_flight(path)
    r = step_metrics(ts, sp, te, est, tg, tr, NOMINAL[axis], run["t_window_start_us"], SETTLE_LIM_MS[axis])
    return dict(flight=path, axis=axis, **r)


def _clean(d):
    return {k: (None if isinstance(v, float) and math.isnan(v) else v) for k, v in d.items()}


COLS = ["flight", "axis", "step_deg", "window_ms", "est_rise_ms", "est_os_pct", "est_settle_ms", "truth_os_pct",
        "truth_settle_ms", "est_minus_truth_pre_deg", "est_minus_truth_end_deg", "pass"]


def table(rows):
    f = lambda v: "NaN" if v is None else (f"{v:.2f}" if isinstance(v, float) else str(v))
    lines = ["| " + " | ".join(COLS) + " |", "|" + "---|" * len(COLS)]
    lines += ["| " + " | ".join(f(r[c]) for c in COLS) + " |" for r in rows]
    return "\n".join(lines)


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    rows = [_clean(measure_flight(p)) for p in argv[2:]]
    json.dump(rows, open(argv[1], "w"), indent=1)
    print(table(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

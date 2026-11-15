#!/usr/bin/env python3
"""Identify outer-loop thrust constants G_T and k_cmd from hover ULog logs.

Per log, all topics are resampled onto esc_status timestamps (previous-value hold):
  mean_u = mean_i (omega_i / omega_max)^2, omega_i = esc[i].esc_rpm * 2*pi/60,
           omega_max = 1000 rad/s (CA_R_W_MAX); samples with any rpm <= 0 are skipped
  f      = |sensor_combined.accelerometer_m_s2| (body specific force), low-passed
           (scipy 2nd-order Butterworth at 5 Hz if importable, else 0.2 s moving average)
  T      = -vehicle_thrust_setpoint.xyz[2] (skipped if the topic is absent)
Fits through the origin:
  G_T   : f ~ G_T * mean_u
  k_cmd : mean_u ~ k_cmd * T
Hover window: run.json 'hold' event if present, intersected with not-landed,
|vz| < 0.3, |vx|, |vy| < 0.5 and t >= takeoff + 5 s.

Usage:
  python3 indi_project/bench/ident_gt.py --note indi_project/results/s8_ident_gt.md LOG [LOG ...]

Each log appends one line to the note; a summary block is appended at the end.
Identification only: no parameter is tuned here.
"""

import argparse
import json
import os

import numpy as np
from pyulog import ULog

try:
    from scipy.signal import butter, sosfiltfilt

    HAVE_SCIPY = True
except ImportError:
    HAVE_SCIPY = False

OMEGA_MAX = 1000.0  # rad/s, CA_R_W_MAX
LOWPASS_HZ = 5.0
LOWPASS_MA_S = 0.2  # moving-average fallback when scipy is missing
TAKEOFF_SKIP_S = 5.0
VZ_MAX = 0.3
VXY_MAX = 0.5
MIN_WINDOW_SAMPLES = 100


def field(ds, topic, key):
    if key not in ds.data:
        raise KeyError(f"{topic}: field '{key}' not in log")
    return np.asarray(ds.data[key], dtype=float)


def has_topic(ulog, name):
    return any(d.name == name for d in ulog.data_list)


def prev_idx(t_src, t_query):
    idx = np.searchsorted(t_src, t_query, side="right") - 1
    return np.clip(idx, 0, len(t_src) - 1)


def lowpass(x, fs):
    if HAVE_SCIPY:
        sos = butter(2, LOWPASS_HZ, btype="low", fs=fs, output="sos")
        return sosfiltfilt(sos, x), "butter2_5Hz_sosfiltfilt"
    n = max(1, int(round(LOWPASS_MA_S * fs)))
    return np.convolve(x, np.ones(n) / n, mode="same"), f"moving_average_{LOWPASS_MA_S}s"


def hold_window(path):
    """Return ((t0_us, t1_us) or None, description) from the sibling run.json."""
    rj = os.path.join(os.path.dirname(path), "run.json")
    if not os.path.isfile(rj):
        return None, "no run.json"
    with open(rj) as fh:
        meta = json.load(fh)
    for ev in meta.get("events", []):
        if ev.get("name") == "hold":
            t0 = float(ev["t_us"])
            t1 = t0 + 1e6 * float(ev["dur_s"])
            return (t0, t1), f"run.json hold {t0 * 1e-6:.1f}-{t1 * 1e-6:.1f}s"
    return None, "run.json has no hold event"


def fit_through_origin(x, y):
    k = float(np.dot(x, y) / np.dot(x, x))
    res = y - k * x
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1.0 - float(np.sum(res**2)) / ss_tot if ss_tot > 0 else float("nan")
    return k, r2, float(np.sqrt(np.mean(res**2)))


def analyze(path):
    ulog = ULog(path)
    need = ["esc_status", "sensor_combined", "vehicle_land_detected", "vehicle_local_position"]
    missing = [n for n in need if not has_topic(ulog, n)]
    if missing:
        raise RuntimeError(f"missing topics {missing}")

    esc = ulog.get_dataset("esc_status")
    t_e = field(esc, "esc_status", "timestamp")
    rpm = np.column_stack([field(esc, "esc_status", f"esc[{i}].esc_rpm") for i in range(4)])

    sc = ulog.get_dataset("sensor_combined")
    t_a = field(sc, "sensor_combined", "timestamp")
    acc = np.column_stack(
        [field(sc, "sensor_combined", f"accelerometer_m_s2[{i}]") for i in range(3)]
    )
    fs = 1e6 / float(np.median(np.diff(t_a)))
    f_lp, lp_name = lowpass(np.linalg.norm(acc, axis=1), fs)
    f_e = f_lp[prev_idx(t_a, t_e)]

    ld = ulog.get_dataset("vehicle_land_detected")
    t_l = field(ld, "vehicle_land_detected", "timestamp")
    landed = field(ld, "vehicle_land_detected", "landed") > 0.5
    landed_e = landed[prev_idx(t_l, t_e)]

    lp = ulog.get_dataset("vehicle_local_position")
    t_p = field(lp, "vehicle_local_position", "timestamp")
    vx_e = field(lp, "vehicle_local_position", "vx")[prev_idx(t_p, t_e)]
    vy_e = field(lp, "vehicle_local_position", "vy")[prev_idx(t_p, t_e)]
    vz_e = field(lp, "vehicle_local_position", "vz")[prev_idx(t_p, t_e)]

    flying = np.flatnonzero(~landed)
    if flying.size == 0:
        raise RuntimeError("vehicle never left the landed state")
    t_takeoff = float(t_l[flying[0]])

    T_e = None
    if has_topic(ulog, "vehicle_thrust_setpoint"):
        ts = ulog.get_dataset("vehicle_thrust_setpoint")
        t_t = field(ts, "vehicle_thrust_setpoint", "timestamp")
        T_src = -field(ts, "vehicle_thrust_setpoint", "xyz[2]")
        T_e = T_src[prev_idx(t_t, t_e)]

    omega = rpm * (2.0 * np.pi / 60.0)
    mean_u = np.mean((omega / OMEGA_MAX) ** 2, axis=1)
    rpm_ok = np.all(rpm > 0, axis=1)

    base = (
        rpm_ok
        & ~landed_e
        & (np.abs(vz_e) < VZ_MAX)
        & (np.abs(vx_e) < VXY_MAX)
        & (np.abs(vy_e) < VXY_MAX)
        & (t_e >= t_takeoff + TAKEOFF_SKIP_S * 1e6)
    )
    win, win_desc = hold_window(path)
    used = "filters only"
    mask = base
    if win is not None:
        m_win = base & (t_e >= win[0]) & (t_e <= win[1])
        if int(m_win.sum()) >= MIN_WINDOW_SAMPLES:
            mask = m_win
            used = win_desc
        else:
            used = f"{win_desc} (fewer than {MIN_WINDOW_SAMPLES} samples, filters only)"

    if int(mask.sum()) < MIN_WINDOW_SAMPLES:
        raise RuntimeError(f"only {int(mask.sum())} hover samples after filtering")

    x = mean_u[mask]
    f = f_e[mask]
    G, r2_g, rs_g = fit_through_origin(x, f)
    result = {
        "path": path,
        "ctrl": os.path.basename(os.path.dirname(os.path.dirname(path))),
        "seed": os.path.basename(os.path.dirname(path)),
        "n": int(mask.sum()),
        "G": G,
        "r2_G": r2_g,
        "rs_G": rs_g,
        "ratio": float(f.mean() / x.mean()),
        "G_umean": G * float(x.mean()),
        "mean_f": float(f.mean()),
        "k": None,
        "r2_k": float("nan"),
        "rs_k": float("nan"),
        "used": used,
        "lp": lp_name,
        "takeoff_s": t_takeoff * 1e-6,
    }
    if T_e is not None:
        k, r2_k, rs_k = fit_through_origin(T_e[mask], mean_u[mask])
        result.update(k=k, r2_k=r2_k, rs_k=rs_k)
    return result


def format_line(r):
    k_txt = "n/a (no vehicle_thrust_setpoint)"
    if r["k"] is not None:
        k_txt = f"{r['k']:.4f} (R2={r['r2_k']:.4f}, resid_std={r['rs_k']:.4f})"
    return (
        f"- `{r['path']}` [{r['ctrl']}/{r['seed']}]: n={r['n']}, G_T={r['G']:.3f} "
        f"(R2={r['r2_G']:.4f}, resid_std={r['rs_G']:.3f} m/s^2), "
        f"mean(f)/mean(mean_u)={r['ratio']:.3f}, G_T*mean(mean_u)={r['G_umean']:.3f} m/s^2, "
        f"k_cmd={k_txt}; takeoff={r['takeoff_s']:.2f}s; window: {r['used']}; filter: {r['lp']}"
    )


def summary_lines(results):
    lines = ["", "## Summary, median [min, max] across logs", ""]
    groups = {"all logs": results}
    for ctrl in sorted({r["ctrl"] for r in results}):
        groups[ctrl] = [r for r in results if r["ctrl"] == ctrl]
    for name, rs in groups.items():
        if not rs:
            continue
        G = np.array([r["G"] for r in rs])
        GU = np.array([r["G_umean"] for r in rs])
        ks = np.array([r["k"] for r in rs if r["k"] is not None])
        k_txt = "n/a"
        if ks.size:
            k_txt = f"{np.median(ks):.4f} [{ks.min():.4f}, {ks.max():.4f}] (n={ks.size})"
        lines.append(
            f"- {name} (n_logs={len(rs)}): G_T={np.median(G):.3f} "
            f"[{G.min():.3f}, {G.max():.3f}]; G_T*mean(mean_u)={np.median(GU):.3f} "
            f"[{GU.min():.3f}, {GU.max():.3f}] m/s^2; k_cmd={k_txt}"
        )
    return lines


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--note", required=True, help="markdown note to append result lines to")
    ap.add_argument("logs", nargs="+", help="flight.ulg files")
    args = ap.parse_args()

    results = []
    with open(args.note, "a") as note:
        for path in args.logs:
            try:
                r = analyze(path)
            except Exception as exc:  # unparseable or incomplete log: record and skip
                line = f"- `{path}`: SKIPPED ({type(exc).__name__}: {exc})"
            else:
                results.append(r)
                line = format_line(r)
            print(line)
            note.write(line + "\n")
            note.flush()
        for line in summary_lines(results):
            print(line)
            note.write(line + "\n")
    if not HAVE_SCIPY:
        print("note: scipy not importable, moving-average low-pass used")


if __name__ == "__main__":
    main()

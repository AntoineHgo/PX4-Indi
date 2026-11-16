#!/usr/bin/env python3
"""Independent timing and frame check of groundtruth topics in a PX4 ULog.

Checks, for the A-12 fix hover_s4 flight (default paths):
  - rate and gap statistics per groundtruth topic, split at the first
    vehicle_status sample with arming_state == 2 (armed);
  - strict monotonicity and duplicate timestamps;
  - EKF vehicle_local_position vs interpolated groundtruth position while armed;
  - time-base comparison against sensor_gyro.

Writes a markdown report and prints it. The default report is truth_check.md next to the
input ULog; it never defaults to a committed file (an earlier fixed default overwrote
results/a12_fix_s18/second_key.md).

Usage:
    python3 check_truth_s18.py [path/to/flight.ulg] [path/to/output.md]
"""
import os
import sys

import numpy as np
from pyulog import ULog

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)  # indi_flight/
DEFAULT_ULG = os.path.join(ROOT, "results", "a12_fix_s18", "hover_s4", "flight.ulg")

ARMED = 2           # vehicle_status.arming_state, ARMING_STATE_ARMED
GAP_US = 5000       # gap threshold, microseconds
ON_GROUND_M = 0.1   # altitude below which a sample counts as on the ground
GT_TOPICS = [
    "vehicle_local_position_groundtruth",
    "vehicle_attitude_groundtruth",
    "vehicle_angular_velocity_groundtruth",
]
TOPICS = ["vehicle_status", "vehicle_local_position", "sensor_gyro"] + GT_TOPICS


def load_topics(path):
    try:
        ulog = ULog(path, message_name_filter_list=TOPICS)
    except TypeError:
        ulog = ULog(path)
    found = {}
    for d in ulog.data_list:
        if d.name in TOPICS:
            found.setdefault(d.name, []).append(d)
    return found


def pick(found, name):
    """Return (data, n_instances, multi_id) for instance 0 of a topic, or None."""
    if name not in found:
        return None
    insts = found[name]
    inst = next((d for d in insts if d.multi_id == 0), insts[0])
    return inst.data, len(insts), inst.multi_id


def f(x, nd=3):
    if x is None or not np.isfinite(x):
        return "n/a"
    return f"{x:.{nd}f}"


def row(*cells):
    return "| " + " | ".join(str(c) for c in cells) + " |"


def phase_rate(t):
    n = t.size
    if n < 2:
        return n, None, None
    dt = np.diff(t)
    med_dt = np.median(dt)
    mean = (n - 1) / ((t[-1] - t[0]) * 1e-6)
    med = 1e6 / med_dt if med_dt > 0 else None
    return n, mean, med


def analyse_topic(name, data, n_inst, mid, t_arm, armed_at, alt_t, alt_z, add, flags):
    t = np.asarray(data["timestamp"]).astype(np.int64)
    d = np.diff(t)
    t_end = t[1:]
    n_dup = int(np.sum(d == 0))
    n_back = int(np.sum(d < 0))
    strict = n_dup == 0 and n_back == 0

    add(f"### {name}")
    add("")
    add(f"Instance multi_id={mid} ({n_inst} instance(s) in log). Samples: {t.size}. "
        f"First t={t[0]/1e6:.6f} s, last t={t[-1]/1e6:.6f} s, "
        f"duration {(t[-1]-t[0])/1e6:.3f} s.")
    add(f"Strictly increasing: {'yes' if strict else 'NO'}; "
        f"duplicate timestamps: {n_dup}; backward steps: {n_back}.")
    add("")

    pre_gap = t_end < t_arm
    add("| phase | samples | mean rate (Hz) | median rate (Hz) | max gap (ms) "
        "| time of max gap, log s (rel. arm s) | gaps > 5 ms |")
    add("|---|---|---|---|---|---|---|")
    for label, tp, gm in (("before arm", t[t < t_arm], pre_gap),
                          ("after arm", t[t >= t_arm], ~pre_gap)):
        n, mean, med = phase_rate(tp)
        g = d[gm]
        if g.size:
            i = int(np.argmax(g))
            tmax = int(t_end[gm][i])
            mx_ms = g[i] / 1e3
            tstr = f"{tmax/1e6:.3f} ({(tmax - t_arm)/1e6:+.3f})"
        else:
            mx_ms, tstr = None, "n/a"
        n5 = int(np.sum(g > GAP_US))
        add(row(label, n, f(mean, 2), f(med, 2), f(mx_ms, 3), tstr, n5))
    add("")
    add("Rates use samples inside each phase; gaps are attributed to the sample that ends them.")
    add("")

    # Nominal-period view: a fixed 5 ms threshold flags every sample of a 100 Hz topic,
    # so also report the dt distribution and gaps relative to the median period.
    med_dt = float(np.median(d)) if d.size else float("nan")
    vals, cnts = np.unique(d, return_counts=True)
    top = np.argsort(cnts)[::-1][:6]
    hist = ", ".join(f"{vals[k]/1e3:.3f} ms x{cnts[k]}" for k in top)
    add(f"Median dt: {med_dt/1e3:.3f} ms. dt histogram (top 6 values): {hist}.")
    thr = 1.5 * med_dt
    big_thr = np.flatnonzero(d > thr)
    if big_thr.size:
        ta = armed_at(t[big_thr + 1])
        add(f"Gaps > 1.5 x median dt ({thr/1e3:.3f} ms): {big_thr.size} "
            f"(armed at end: {int(ta.sum())}, disarmed at end: {int((~ta).sum())}; "
            f"max {d[big_thr].max()/1e3:.3f} ms at log t={t[big_thr[np.argmax(d[big_thr])]+1]/1e6:.3f} s).")
    else:
        add(f"Gaps > 1.5 x median dt ({thr/1e3:.3f} ms): 0.")
    add("")

    big = np.flatnonzero(d > GAP_US)
    if big.size == 0:
        add("No gaps > 5 ms.")
        add("")
        flags.append(f"{name}: no gaps > 5 ms")
        return
    te = t[big + 1]
    armed = armed_at(te)
    if alt_t is not None:
        alt = -np.interp(te, alt_t, alt_z)
    else:
        alt = np.full(te.size, np.nan)
    n_pre = int(np.sum(te < t_arm))
    n_armed = int(np.sum(armed))
    n_disarmed_post = int(np.sum((~armed) & (te >= t_arm)))
    n_armed_ground = int(np.sum(armed & (alt < ON_GROUND_M)))
    n_armed_air = int(np.sum(armed & (alt >= ON_GROUND_M)))
    max_alt_armed = float(np.nanmax(alt[armed])) if n_armed else None

    add(f"Gaps > 5 ms: {big.size} total. Ending before arm: {n_pre}. "
        f"Ending while armed: {n_armed} (on ground, alt < {ON_GROUND_M} m: {n_armed_ground}; "
        f"airborne: {n_armed_air}; max alt during armed gaps: {f(max_alt_armed, 3)} m). "
        f"Ending after arm while disarmed: {n_disarmed_post}.")
    add("")
    add("| gap start, log s | gap end, log s | gap (ms) | armed at end | alt at end (m) |")
    add("|---|---|---|---|---|")
    for k in range(min(big.size, 25)):
        add(row(f"{t[big[k]]/1e6:.3f}", f"{te[k]/1e6:.3f}", f(d[big[k]]/1e3, 3),
                "yes" if armed[k] else "no", f(alt[k], 3)))
    if big.size > 25:
        add(f"| ... {big.size - 25} more rows omitted | | | | |")
    add("")
    flags.append(f"{name}: {big.size} gaps > 5 ms; {n_armed} while armed "
                 f"({n_armed_air} airborne)")


def main():
    ulg_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_ULG
    out_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(ulg_path)), "truth_check.md")
    found = load_topics(ulg_path)

    md = []
    add = md.append
    flags = []

    add("# Second-key check: groundtruth timing and frame (A-12 fix, hover_s4)")
    add("")
    add(f"Log: `{ulg_path}`")
    add("")
    missing = [t for t in TOPICS if t not in found]
    add(f"Topics missing from log: {', '.join(missing) if missing else 'none'}")
    add("")

    st = pick(found, "vehicle_status")
    if st is None:
        raise SystemExit("vehicle_status missing, cannot split on arming")
    sd = st[0]
    vs_t = np.asarray(sd["timestamp"]).astype(np.int64)
    vs_arm = np.asarray(sd["arming_state"]).astype(np.int64)
    armed_rows = np.flatnonzero(vs_arm == ARMED)
    if armed_rows.size == 0:
        raise SystemExit("no vehicle_status sample with arming_state == 2")
    t_arm = int(vs_t[armed_rows[0]])
    not_armed_after = (vs_arm != ARMED) & (vs_t > t_arm)
    n_disarm_after = int(np.sum(not_armed_after))
    disarm_desc = ", ".join(
        f"log t={x/1e6:.3f} s (arming_state {int(s)})"
        for x, s in zip(vs_t[not_armed_after], vs_arm[not_armed_after]))
    add(f"First armed vehicle_status sample (arming_state == {ARMED}): "
        f"log t = {t_arm/1e6:.6f} s. vehicle_status samples: {vs_t.size}; "
        f"samples not armed after first arm: {n_disarm_after}"
        f"{' (' + disarm_desc + ')' if n_disarm_after else ''}.")
    add("")
    flags.append(f"arm at log t={t_arm/1e6:.3f} s; disarmed samples after arm: {n_disarm_after}")

    def armed_at(t):
        t = np.asarray(t, dtype=np.int64)
        i = np.searchsorted(vs_t, t, side="right") - 1
        state = vs_arm[np.clip(i, 0, None)]
        return (i >= 0) & (state == ARMED)

    gp = pick(found, "vehicle_local_position_groundtruth")
    if gp is not None:
        gpd = gp[0]
        gp_t_raw = np.asarray(gpd["timestamp"]).astype(np.int64)
        alt_t = gp_t_raw
        alt_z = np.asarray(gpd["z"]).astype(np.float64)
    else:
        alt_t, alt_z = None, None

    add("## 1-3. Rate, gaps, monotonicity per groundtruth topic")
    add("")
    for name in GT_TOPICS:
        got = pick(found, name)
        if got is None:
            add(f"### {name}")
            add("")
            add("Topic not present in log.")
            add("")
            continue
        data, n_inst, mid = got
        analyse_topic(name, data, n_inst, mid, t_arm, armed_at, alt_t, alt_z, add, flags)

    # Q4: EKF vs groundtruth position while armed
    add("## 4. Frame sanity: vehicle_local_position (EKF) vs groundtruth position, armed only")
    add("")
    vlp = pick(found, "vehicle_local_position")
    if vlp is None or gp is None:
        add("Cannot compare: vehicle_local_position or groundtruth position missing.")
        add("")
    else:
        vd = vlp[0]
        vt = np.asarray(vd["timestamp"]).astype(np.int64)
        gt_t, gidx = np.unique(gp_t_raw, return_index=True)
        mask = (vt >= t_arm) & armed_at(vt) & (vt >= gt_t[0]) & (vt <= gt_t[-1])
        n_cmp = int(mask.sum())
        add(f"Comparison samples (armed, inside groundtruth span): {n_cmp}. "
            f"Groundtruth interpolated (linear) onto EKF timestamps. Residual = EKF - truth.")
        add("")
        add("| axis | mean abs diff (m) | max abs diff (m) | mean residual (m) | rms (m) |")
        add("|---|---|---|---|---|")
        for ax in ("x", "y", "z"):
            v = np.asarray(vd[ax])[mask].astype(np.float64)
            g_full = np.asarray(gpd[ax])[gidx].astype(np.float64)
            g = np.interp(vt[mask], gt_t, g_full)
            ok = np.isfinite(v) & np.isfinite(g)
            res = v[ok] - g[ok]
            mabs = float(np.mean(np.abs(res))) if res.size else None
            xabs = float(np.max(np.abs(res))) if res.size else None
            bias = float(np.mean(res)) if res.size else None
            rms = float(np.sqrt(np.mean(res ** 2))) if res.size else None
            add(row(ax, f(mabs, 4), f(xabs, 4), f(bias, 4), f(rms, 4)))
            if ax == "z":
                res_z_max = xabs
        add("")
        zt = np.asarray(gpd["z"])[gidx].astype(np.float64)
        zt_armed = np.interp(vt[mask], gt_t, zt)
        vz = np.asarray(vd["z"])[mask].astype(np.float64)
        alt_truth = -zt_armed
        add("| quantity | mean (m) | max (m) | min (m) |")
        add("|---|---|---|---|")
        add(row("groundtruth z, NED (m)", f(np.mean(zt_armed), 3), f(np.max(zt_armed), 3),
                f(np.min(zt_armed), 3)))
        add(row("EKF z, NED (m)", f(np.nanmean(vz), 3), f(np.nanmax(vz), 3), f(np.nanmin(vz), 3)))
        add(row("groundtruth altitude = -z (m)", f(np.mean(alt_truth), 3),
                f(np.max(alt_truth), 3), f(np.min(alt_truth), 3)))
        add("")
        add(f"Groundtruth z at first armed sample: {f(zt_armed[0], 3)} m (NED). "
            f"Groundtruth z at last armed sample: {f(zt_armed[-1], 3)} m (NED).")
        add("")
        flags.append(f"EKF-truth max abs z residual while armed: {f(res_z_max, 4)} m")

    # Q5: time base vs sensor_gyro
    add("## 5. Time base: groundtruth vs sensor_gyro")
    add("")
    gy = pick(found, "sensor_gyro")
    if gy is None:
        add("sensor_gyro not present in log.")
        add("")
    else:
        gyd, n_inst, mid = gy
        gt_stamp = np.asarray(gyd["timestamp"]).astype(np.int64)
        n, mean, med = phase_rate(gt_stamp)
        add(f"sensor_gyro multi_id={mid} ({n_inst} instance(s)): samples {n}, "
            f"first {gt_stamp[0]/1e6:.6f} s, last {gt_stamp[-1]/1e6:.6f} s, "
            f"mean rate {f(mean, 1)} Hz, median rate {f(med, 1)} Hz, "
            f"strictly increasing: {'yes' if np.all(np.diff(gt_stamp) > 0) else 'NO'}.")
        add("")
        add("| topic | first (s) | last (s) | first - gyro first (s) | last - gyro last (s) "
            "| share of samples inside gyro span |")
        add("|---|---|---|---|---|---|")
        for name in GT_TOPICS:
            got = pick(found, name)
            if got is None:
                continue
            tt = np.asarray(got[0]["timestamp"]).astype(np.int64)
            inside = np.mean((tt >= gt_stamp[0]) & (tt <= gt_stamp[-1]))
            add(row(name, f"{tt[0]/1e6:.6f}", f"{tt[-1]/1e6:.6f}",
                    f"{(tt[0]-gt_stamp[0])/1e6:+.6f}", f"{(tt[-1]-gt_stamp[-1])/1e6:+.6f}",
                    f"{inside:.3f}"))
        add("")
        flags.append(f"sensor_gyro first t={gt_stamp[0]/1e6:.3f} s, last t={gt_stamp[-1]/1e6:.3f} s")

    add("## Flags")
    add("")
    for fl in flags:
        add(f"- {fl}")
    add("")

    text = "\n".join(md)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(text)
    print(text)
    print(f"\nWritten: {out_path}")


if __name__ == "__main__":
    main()

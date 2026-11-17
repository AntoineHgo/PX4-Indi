"""A-28 (S63): time course of estimator-minus-truth around an attitude step.

Usage: python3 a28_offset_course.py OUT.md FLIGHT_DIR [FLIGHT_DIR ...]
For each flight: est-truth (step axis) mean in bins relative to t_on (setpoint 50 % crossing),
and truth error against the setpoint (truth - setpoint), to tell a constant estimator bias from a
transient one. Reuses the T127 helpers (independent of the primary metric script).
"""
import json, os, sys
import numpy as np
from pyulog import ULog
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from t127_step_metrics_key import topic, quat_stack, euler_deg, unwrap_deg, first, AMP

BINS_S = [(-1.0, 0.0), (0.0, 0.1), (0.1, 0.2), (0.2, 0.3), (0.3, 0.45), (0.45, 0.6), (0.6, 1.0), (1.0, 1.5), (1.5, 3.0)]


def course(folder):
    run = json.load(open(os.path.join(folder, "run.json")))
    axis = run["scenario"].split("_")[1]
    amp = AMP[axis]
    t0 = int(run["t_window_start_us"])
    u = ULog(os.path.join(folder, "flight.ulg"))
    att, sp, gt = (topic(u, n) for n in ("vehicle_attitude", "vehicle_attitude_setpoint", "vehicle_attitude_groundtruth"))
    t_a = att["timestamp"].astype(np.int64); est = euler_deg(quat_stack(att, "q"))[axis]
    t_s = sp["timestamp"].astype(np.int64); setp = euler_deg(quat_stack(sp, "q_d"))[axis]
    t_g = gt["timestamp"].astype(np.int64); tru = euler_deg(quat_stack(gt, "q"))[axis]
    if axis == "yaw":
        est, setp, tru = unwrap_deg(est), unwrap_deg(setp), unwrap_deg(tru)
    # step direction sign so that amp > 0 in the T127 convention
    i_on = first((t_s >= t0) & (np.abs(setp - np.median(setp[(t_s >= t0) & (t_s < t0 + 1_000_000)])) >= 0.5 * abs(amp)))
    t_on = int(t_s[i_on])
    tru_i = np.interp(t_a, t_g, tru)
    sp_i = np.interp(t_a, t_s, setp)  # setpoint is piecewise constant, interp only near the edge
    d = est - tru_i
    e = tru_i - sp_i
    ee = est - sp_i
    out = []
    for a, b in BINS_S:
        m = (t_a >= t_on + a * 1e6) & (t_a < t_on + b * 1e6)
        out.append((a, b, d[m].mean(), e[m].mean(), np.abs(e[m]).max(), np.abs(ee[m]).max()))
    return os.path.basename(os.path.dirname(os.path.normpath(folder))) + "/" + os.path.basename(os.path.normpath(folder)), axis, amp, out


def main():
    out_path = sys.argv[1]
    lines = ["# A-28 est-truth time course (S63, bench/a28_offset_course.py)", "",
             "Bins in s from t_on (setpoint 50 % crossing). d = est - truth mean; e = truth - setpoint mean; |e|max, |est-sp|max.", ""]
    for f in sys.argv[2:]:
        name, axis, amp, rows = course(f)
        lines += [f"## {name} ({axis}, amp {amp} deg, 2 % band {0.02*abs(amp):.2f} deg)", "",
                  "| bin [s] | d mean | e mean | abs(e) max | abs(est-sp) max |", "|---|---|---|---|---|"]
        for a, b, dm, em, emax, eemax in rows:
            lines.append(f"| {a:+.2f}..{b:+.2f} | {dm:+.3f} | {em:+.3f} | {emax:.3f} | {eemax:.3f} |")
        lines.append("")
    open(out_path, "w").write("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""A-19 check: truth-minus-EKF attitude offsets vs setpoint, EKF heading innovation and mag innovation.

Usage:
  a19_check.py LOG.ulg [LOG.ulg ...] --out OUT.json [--metrics-check LOG.ulg ...]

Per log: arm time = first vehicle_status sample with arming_state == 2.
  (a) pre-arm window  [arm - 5 s, arm]
  (b) analysis window [arm + 15 s, arm + 35 s]
Truth quaternion (sim_ground_truth q[0..3], Hamilton w-x-y-z) is interpolated onto vehicle_attitude times
(sign-aligned nlerp, bench/metrics.py interp_quat). The setpoint q_d is interpolated onto the same times.
Euler angles: bench/metrics.py quat_to_euler (ZYX yaw-pitch-roll). Heading innovation: estimator_innovations.heading;
mag field innovation: estimator_aid_src_mag.innovation[0..2]. The yaw offset is interpolated onto the innovation
timestamps for the correlations.
--metrics-check LOG: attitude-metric gap check (window b): bench/metrics.py att_track against per-sample quantities,
including a rotation angle from the relative quaternion (atan2 form, no arccos near 1).
"""
import argparse
import json
import math
import os
import sys

import numpy as np

sys.dont_write_bytecode = True  # do not write __pycache__ into bench/
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "bench"))
import metrics as M  # noqa: E402
from pyulog import ULog  # noqa: E402

S = 1e6  # us per s
PRE = (-5.0, 0.0)
ANA = (15.0, 35.0)


def topic(u, name):
    for d in u.data_list:
        if d.name == name and d.multi_id == 0:
            return {k: np.asarray(v) for k, v in d.data.items()}
    return None


def arm_time(vs):
    if vs is None or "arming_state" not in vs:
        return None
    idx = np.nonzero(vs["arming_state"] == 2)[0]
    return float(vs["timestamp"][idx[0]]) if idx.size else None


def stats_deg(x):
    x = np.degrees(np.asarray(x, float))
    x = x[np.isfinite(x)]
    if x.size == 0:
        return None
    return {"mean_deg": round(float(x.mean()), 4), "std_deg": round(float(x.std()), 4), "n": int(x.size)}


def circ_mean_deg(a):
    a = np.asarray(a, float)
    if a.size == 0:
        return None
    return round(math.degrees(math.atan2(float(np.mean(np.sin(a))), float(np.mean(np.cos(a))))), 4)


def analyse(path):
    u = ULog(path)
    gt, ek = topic(u, "sim_ground_truth"), topic(u, "vehicle_attitude")
    sp, inn = topic(u, "vehicle_attitude_setpoint"), topic(u, "estimator_innovations")
    mag = topic(u, "estimator_aid_src_mag")
    arm = arm_time(topic(u, "vehicle_status"))
    res = {"log": path, "arm_s": None if arm is None else round(arm / S, 6)}
    if gt is None or ek is None or arm is None:
        res["error"] = "missing sim_ground_truth, vehicle_attitude or armed sample"
        return res
    t = ek["timestamp"].astype(float)
    qe = M.qcols(ek, "q").astype(float)
    tg = gt["timestamp"].astype(float)
    qt = np.full_like(qe, np.nan)
    qs = np.full_like(qe, np.nan)
    ins = (t >= tg[0]) & (t <= tg[-1])
    with np.errstate(all="ignore"):
        qt[ins] = M.interp_quat(tg, M.qcols(gt, "q").astype(float), t[ins])
        if sp is not None:
            ts = sp["timestamp"].astype(float)
            ins_s = (t >= ts[0]) & (t <= ts[-1])
            qs[ins_s] = M.interp_quat(ts, M.qcols(sp, "q_d").astype(float), t[ins_s])
        rt, pt, yt = M.quat_to_euler(qt)
        re, pe, ye = M.quat_to_euler(qe)
        _, _, ys = M.quat_to_euler(qs)
    d_roll, d_pitch, d_yaw = rt - re, pt - pe, M.wrap(yt - ye)
    d_sp_yaw = M.wrap(ys - ye)

    res["windows"] = {}
    for name, (a0, a1) in (("a_prearm", PRE), ("b_analysis", ANA)):
        m = (t >= arm + a0 * S) & (t <= arm + a1 * S)
        res["windows"][name] = {
            "n_ekf": int(m.sum()),
            "yaw_truth_minus_ekf": stats_deg(d_yaw[m]),
            "roll_truth_minus_ekf": stats_deg(d_roll[m]),
            "pitch_truth_minus_ekf": stats_deg(d_pitch[m]),
            "yaw_setpoint_minus_ekf": stats_deg(d_sp_yaw[m]),
        }

    # absolute yaw before arm (circular mean): does the truth yaw or the EKF yaw differ between runs?
    ma = (t >= arm + PRE[0] * S) & (t <= arm + PRE[1] * S)
    res["yaw_abs_prearm"] = {
        "truth_deg": circ_mean_deg(yt[ma & np.isfinite(yt)]),
        "ekf_deg": circ_mean_deg(ye[ma]),
        "setpoint_deg": circ_mean_deg(ys[ma & np.isfinite(ys)]),
    }

    corr = {"n": 0}
    mb = (t >= arm + ANA[0] * S) & (t <= arm + ANA[1] * S) & np.isfinite(d_yaw)
    if mb.sum() > 2:
        tb, yb = t[mb], d_yaw[mb]
        if inn is not None and "heading" in inn:
            ti, hi = inn["timestamp"].astype(float), inn["heading"].astype(float)
            mi = ((ti >= tb[0]) & (ti <= tb[-1]) & np.isfinite(hi)
                  & (ti >= arm + ANA[0] * S) & (ti <= arm + ANA[1] * S))
            h, o = hi[mi], np.interp(ti[mi], tb, yb)
            corr = {"n": int(mi.sum()), "innov_heading_deg": stats_deg(h),
                    "innov_nonzero_frac": round(float(np.mean(h != 0)), 4) if h.size else None}
            if h.size > 2 and h.std() > 0 and o.std() > 0:
                corr["pearson_r"] = round(float(np.corrcoef(h, o)[0, 1]), 4)
                corr["slope_yaw_offset_per_innov"] = round(float(np.polyfit(h, o, 1)[0]), 4)
        if mag is not None and "fused" in mag:
            tm = mag["timestamp"].astype(float)
            mm = (tm >= arm + ANA[0] * S) & (tm <= arm + ANA[1] * S)
            corr["mag_aid_n_b"] = int(mm.sum())
            corr["mag_fused_frac_b"] = round(float(np.mean(mag["fused"][mm])), 4) if mm.any() else None
        if mag is not None and "innovation[0]" in mag:
            tm = mag["timestamp"].astype(float)
            mm = (tm >= tb[0]) & (tm <= tb[-1]) & (tm >= arm + ANA[0] * S) & (tm <= arm + ANA[1] * S)
            o = np.interp(tm[mm], tb, yb)
            mg = {"n": int(mm.sum())}
            for i in range(3):
                c = mag[f"innovation[{i}]"][mm].astype(float)
                mg[f"innov{i}_mean"] = round(float(c.mean()), 6) if c.size else None
                mg[f"innov{i}_std"] = round(float(c.std()), 6) if c.size else None
                if c.size > 2 and c.std() > 0 and o.std() > 0:
                    mg[f"innov{i}_pearson_r_yaw_offset"] = round(float(np.corrcoef(c, o)[0, 1]), 4)
            corr["mag_field_innov_b"] = mg
    res["heading_corr_b"] = corr
    return res


def reported(path):
    """Numeric attitude keys already in the run's metrics.json (for comparison only)."""
    p = os.path.join(os.path.dirname(path), "metrics.json")
    if not os.path.exists(p):
        return None
    with open(p) as f:
        js = json.load(f)
    found = {}

    def walk(o, pre):
        if isinstance(o, dict):
            for k, v in o.items():
                walk(v, f"{pre}.{k}" if pre else k)
        elif isinstance(o, (int, float)) and "att" in pre.lower() and ("rotation" in pre or "_rms_deg" in pre):
            found[pre] = o
    walk(js, "")
    return found


def qmul(p, q):
    p0, pv, q0, qv = p[:, :1], p[:, 1:], q[:, :1], q[:, 1:]
    r0 = p0 * q0 - np.sum(pv * qv, axis=1, keepdims=True)
    rv = p0 * qv + q0 * pv + np.cross(pv, qv)
    return np.hstack([r0, rv])


def metric_gap(path):
    """Attitude-metric gap on window b: bench/metrics.py att_track against per-sample quantities."""
    u = ULog(path)
    ek, sp = topic(u, "vehicle_attitude"), topic(u, "vehicle_attitude_setpoint")
    arm = arm_time(topic(u, "vehicle_status"))
    w0, w1 = arm + ANA[0] * S, arm + ANA[1] * S
    t = ek["timestamp"].astype(float)
    qe = M.qcols(ek, "q").astype(float)
    at = M.att_track(t, qe, sp, w0, w1)
    m = (t >= w0) & (t <= w1)
    qs = np.column_stack([M.zoh(sp["timestamp"], sp[f"q_d[{i}]"], t[m]) for i in range(4)])
    ok = np.isfinite(qs).all(axis=1)
    qm, qk = qe[m][ok], qs[ok].astype(float)
    dot = np.sum(qm * qk, axis=1)
    theta = 2 * np.arccos(np.clip(np.abs(dot), 0, 1))  # metrics.py rotation angle, rad
    qrel = qmul(qk * np.array([1.0, -1, -1, -1]), qm)  # conj(q_d) * q_m
    qrel = np.where(qrel[:, :1] < 0, -qrel, qrel)
    theta_s = 2 * np.arctan2(np.linalg.norm(qrel[:, 1:], axis=1), qrel[:, 0])  # stable form, rad
    eu, esp = M.quat_to_euler(qm), M.quat_to_euler(qk)
    E = np.column_stack([eu[0] - esp[0], eu[1] - esp[1], M.wrap(eu[2] - esp[2])])  # per-axis Euler error, rad
    en = np.linalg.norm(E, axis=1)
    axis_rms = np.sqrt(np.mean(E ** 2, axis=0))
    rss = float(np.sqrt(np.sum(axis_rms ** 2)))
    rot = float(np.sqrt(np.mean(theta ** 2)))
    rots = float(np.sqrt(np.mean(theta_s ** 2)))
    d = math.degrees
    return {
        "log": path,
        "n": int(ok.sum()),
        "att_track_rotation_angle_rms_deg": round(at["rotation_angle_rms_deg"], 4),
        "att_track_axis_rms_deg": {ax: round(at[ax + "_rms_deg"], 4) for ax in ("roll", "pitch", "yaw")},
        "sqrt_sum_sq_axis_rms_deg": round(d(rss), 4),
        "euler_vector_norm_rms_deg": round(d(float(np.sqrt(np.mean(en ** 2)))), 4),
        "rotation_angle_arccos_rms_deg": round(d(rot), 4),
        "rotation_angle_stable_rms_deg": round(d(rots), 4),
        "ratio_arccos_over_sqrt_sum": round(rot / rss, 4),
        "ratio_stable_over_sqrt_sum": round(rots / rss, 4),
        "arccos_clipped_frac": round(float(np.mean(np.abs(dot) >= 1.0)), 4),
        "mean_theta_arccos_deg": round(d(float(np.mean(theta))), 4),
        "mean_theta_stable_deg": round(d(float(np.mean(theta_s))), 4),
        "mean_euler_norm_deg": round(d(float(np.mean(en))), 4),
        "rms_theta_stable_minus_euler_norm_deg": round(d(float(np.sqrt(np.mean((theta_s - en) ** 2)))), 4),
        "metrics_json_att_keys": reported(path),
    }


def agg(xs):
    xs = [x for x in xs if x is not None]
    if not xs:
        return None
    return {"mean": round(float(np.mean(xs)), 4), "std": round(float(np.std(xs)), 4),
            "min": round(float(min(xs)), 4), "max": round(float(max(xs)), 4), "n": len(xs)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("logs", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--metrics-check", nargs="*", default=[])
    a = ap.parse_args()

    runs = [analyse(p) for p in a.logs]
    for r in runs:
        r["group"] = os.path.basename(os.path.dirname(os.path.dirname(r["log"])))
        r["run"] = os.path.basename(os.path.dirname(r["log"]))
    ok_runs = [r for r in runs if "error" not in r]

    summary = {}
    for g in sorted({r["group"] for r in ok_runs}):
        rs = [r for r in ok_runs if r["group"] == g]

        def col(win, key, sub="mean_deg", rs=rs):
            return [r["windows"][win][key][sub] if r["windows"][win][key] else None for r in rs]
        summary[g] = {
            "runs": [r["run"] for r in rs],
            "yaw_truth_minus_ekf_prearm_mean_deg": agg(col("a_prearm", "yaw_truth_minus_ekf")),
            "yaw_truth_minus_ekf_analysis_mean_deg": agg(col("b_analysis", "yaw_truth_minus_ekf")),
            "yaw_truth_minus_ekf_analysis_std_deg": agg(col("b_analysis", "yaw_truth_minus_ekf", "std_deg")),
            "yaw_setpoint_minus_ekf_analysis_mean_deg": agg(col("b_analysis", "yaw_setpoint_minus_ekf")),
            "roll_truth_minus_ekf_analysis_mean_deg": agg(col("b_analysis", "roll_truth_minus_ekf")),
            "pitch_truth_minus_ekf_analysis_mean_deg": agg(col("b_analysis", "pitch_truth_minus_ekf")),
            "heading_innov_pearson_r": agg([r["heading_corr_b"].get("pearson_r") for r in rs]),
            "per_run_abs_yaw_prearm_truth_deg": [r["yaw_abs_prearm"]["truth_deg"] for r in rs],
            "per_run_abs_yaw_prearm_ekf_deg": [r["yaw_abs_prearm"]["ekf_deg"] for r in rs],
        }

    checks = [metric_gap(p) for p in a.metrics_check]

    with open(a.out, "w") as f:
        json.dump({"runs": runs, "summary_by_group": summary, "metric_gap_checks": checks}, f, indent=2)

    for r in runs:
        if "error" in r:
            print(r["log"], "ERROR", r["error"])
            continue
        wa, wb = r["windows"]["a_prearm"], r["windows"]["b_analysis"]
        c = r["heading_corr_b"]
        print(f"{r['group']}/{r['run']} arm={r['arm_s']}s absYaw_prearm={r['yaw_abs_prearm']} "
              f"yawTE_a={wa['yaw_truth_minus_ekf']} yawTE_b={wb['yaw_truth_minus_ekf']} "
              f"yawSP-E_b={wb['yaw_setpoint_minus_ekf']} rollTE_b={wb['roll_truth_minus_ekf']} "
              f"pitchTE_b={wb['pitch_truth_minus_ekf']} "
              f"headInnov_b={c.get('innov_heading_deg')} r={c.get('pearson_r')} "
              f"magInnov_b={c.get('mag_field_innov_b')}")
    print("SUMMARY")
    for g, s in summary.items():
        print(g, json.dumps({k: v for k, v in s.items() if k != "runs"}))
    for c in checks:
        print("METRIC_GAP", json.dumps(c))


if __name__ == "__main__":
    main()

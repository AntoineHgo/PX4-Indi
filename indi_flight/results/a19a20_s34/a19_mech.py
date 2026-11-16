#!/usr/bin/env python3
"""A-19 (S33) per-run EKF2 yaw-error mechanism analysis, from ULog files only.

Usage: a19_mech.py [RUN ...]   (default: the 15 speed4 runs hover/step_roll/traj_lemniscate r1..r5)
Writes a19_mech.json and a19_table.md next to this script. Read-only on the logs.

Conventions
  err      = truth yaw minus EKF yaw (deg, wrapped), from sim_ground_truth q and vehicle_attitude q
  magerr   = EKF yaw minus truth yaw, from the bearing of vehicle_magnetometer rotated by the EKF
             attitude minus the same bearing rotated by the truth attitude (so magerr ~ -err)
  Yaw from quaternion: ZYX, atan2(2(wz+xy), 1-2(y^2+z^2)).
  EKF estimator_states layout (checked against the norm of states[16:19] in the run): quat 0-3,
  vel 4-6, pos 7-9, delta-angle bias 10-12, delta-vel bias 13-15, mag earth field NED (gauss) 16-18,
  mag body bias (gauss) 19-21, wind 22-23.
  Times are seconds relative to the first vehicle_status sample with arming_state == 2 (arm).
  Window b = [arm+15, arm+35] s (same as a19_check.py).
"""
import json
import math
import os
import re
import sys

import numpy as np

sys.dont_write_bytecode = True
from pyulog import ULog  # noqa: E402

S = 1e6
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE  # S34 copy: runs next to the script
WORLD = os.path.normpath(os.path.join(HERE, "..", "..", "sim", "worlds", "default.sdf"))
RUNS = ["hover_r1", "hover_r2", "step_roll_r1"]
CS = ["cs_yaw_align", "cs_mag_hdg", "cs_mag_3d", "cs_mag_dec", "cs_gnss_yaw", "cs_mag_aligned_in_flight", "cs_in_air"]
PARAMS = ["EKF2_MAG_DECL", "EKF2_DECL_TYPE", "EKF2_MAG_TYPE", "EKF2_GPS_CTRL", "EKF2_MAG_CHECK",
          "EKF2_MAG_NOISE", "EKF2_MAG_E_NOISE", "EKF2_MAG_B_NOISE", "EKF2_GPS_YAW_RST", "EKF2_HGT_REF",
          "SENS_MAG_AUTOCAL", "SENS_MAG_MODE", "SENS_MAG_RATE", "CAL_MAG0_ROT", "CAL_MAG0_XOFF",
          "CAL_MAG0_YOFF", "CAL_MAG0_ZOFF", "SIM_GZ_EN_MAG", "SYS_HAS_MAG"]
NAN = float("nan")


def topic(u, name):
    for d in u.data_list:
        if d.name == name and d.multi_id == 0:
            return {k: np.asarray(v) for k, v in d.data.items()}
    return None


def vec(d, base, n):
    return np.stack([d[f"{base}[{i}]"].astype(float) for i in range(n)], axis=1)


def first_true(t, v):
    idx = np.nonzero(np.asarray(v).astype(bool))[0]
    return float(t[idx[0]]) if idx.size else None


def nearest(t_src, t_q):
    i = np.clip(np.searchsorted(t_src, t_q), 1, len(t_src) - 1)
    left, right = t_src[i - 1], t_src[i]
    return np.where(np.abs(t_q - left) <= np.abs(right - t_q), i - 1, i)


def quat_rot(q):
    """Body->NED rotation matrices from Hamilton quaternions (w, x, y, z), shape (N, 3, 3)."""
    w, x, y, z = q.T
    return np.stack([
        np.stack([1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)], 1),
        np.stack([2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)], 1),
        np.stack([2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)], 1)], 1)


def yaw_of(q):
    w, x, y, z = q.T
    return np.arctan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))


def wrap(a):
    return (a + np.pi) % (2 * np.pi) - np.pi


def circ_deg(a):
    a = np.asarray(a, float)
    return math.degrees(math.atan2(np.mean(np.sin(a)), np.mean(np.cos(a)))) if a.size else NAN


def wm(t, x, lo, hi):
    m = (t >= lo) & (t <= hi) & np.isfinite(x)
    return float(np.mean(x[m])) if m.any() else NAN


def ws(t, x, lo, hi):
    m = (t >= lo) & (t <= hi) & np.isfinite(x)
    return float(np.std(x[m])) if m.any() else NAN


def gz_field():
    txt = open(WORLD, encoding="utf-8-sig").read()
    mf = [float(v) for v in re.search(r"<magnetic_field>([^<]+)</magnetic_field>", txt).group(1).split()]
    lat = float(re.search(r"<latitude_deg>([^<]+)<", txt).group(1))
    lon = float(re.search(r"<longitude_deg>([^<]+)<", txt).group(1))
    e, n, u_ = mf  # gz world frame is ENU
    return {"B_enu_T": mf, "lat_deg": lat, "lon_deg": lon,
            "decl_deg": math.degrees(math.atan2(e, n)),
            "incl_deg": math.degrees(math.atan2(-u_, math.hypot(e, n))),
            "H_T": math.hypot(e, n), "Z_down_T": -u_}


def analyse(run):
    u = ULog(os.path.join(ROOT, run, "flight.ulg"))
    gt, ek = topic(u, "sim_ground_truth"), topic(u, "vehicle_attitude")
    esf, es = topic(u, "estimator_status_flags"), topic(u, "estimator_states")
    mg, sb = topic(u, "vehicle_magnetometer"), topic(u, "estimator_sensor_bias")
    vs = topic(u, "vehicle_status")
    arm = first_true(vs["timestamp"].astype(float), vs["arming_state"] == 2)
    out = {"run": run, "arm_s": round(arm / S, 3)}

    # ---- parameters
    ip = u.initial_parameters
    out["params"] = {k: (float(ip[k]) if k in ip else None) for k in PARAMS}

    # ---- truth vs EKF yaw
    tg = gt["timestamp"].astype(float)
    qg = vec(gt, "q", 4)
    te = ek["timestamp"].astype(float)
    qe = vec(ek, "q", 4)
    ta = (te - arm) / S
    tgr = (tg - arm) / S
    yt_all = yaw_of(qg)
    out["truth_yaw_deg_winb"] = round(circ_deg(yt_all[(tgr >= 15) & (tgr <= 35)]), 4)
    err = np.degrees(wrap(yt_all[nearest(tg, te)] - yaw_of(qe)))

    # ---- estimator flag transitions
    tf = (esf["timestamp"].astype(float) - arm) / S
    flags = {}
    for c in CS:
        v = np.asarray(esf[c]).astype(bool) if c in esf else np.zeros(tf.size, bool)
        ch = np.nonzero(np.diff(v.astype(int)))[0]
        f = first_true(tf, v)
        flags[c] = {"first_true_s": None if f is None else round(f, 2),
                    "transitions": [[round(float(tf[i + 1]), 2), int(v[i + 1])] for i in ch][:8]}
    out["flags"] = flags
    t_al = flags["cs_yaw_align"]["first_true_s"]
    gnss_on = None
    if flags["cs_gnss_yaw"]["first_true_s"] is not None:
        gnss_on = flags["cs_gnss_yaw"]["first_true_s"]

    E = {"t_align_s": t_al, "gnss_yaw_on_s": gnss_on}
    E["err_align_pm0.2"] = wm(ta, err, t_al - 0.2, t_al + 0.2) if t_al is not None else NAN
    E["err_align_plus1s"] = wm(ta, err, t_al, t_al + 1.0) if t_al is not None else NAN
    E["err_arm_pm0.5"] = wm(ta, err, -0.5, 0.5)
    E["err_prearm_m5_0"] = wm(ta, err, -5.0, 0.0)
    E["err_winb"] = wm(ta, err, 15.0, 35.0)
    E["err_winb_std"] = ws(ta, err, 15.0, 35.0)
    if gnss_on is not None:
        E["err_gnss_before_2s"] = wm(ta, err, gnss_on - 2.0, gnss_on - 0.1)
        E["err_gnss_after_2s"] = wm(ta, err, gnss_on + 0.1, gnss_on + 2.0)
        E["err_gnss_after_winb"] = wm(ta, err, 15.0, 35.0)

    # ---- magnetometer: field bearing under truth and EKF attitude
    tmA = mg["timestamp"].astype(float)
    tm = (tmA - arm) / S
    m = vec(mg, "magnetometer_ga", 3)
    dt = np.einsum("nij,nj->ni", quat_rot(qg[nearest(tg, tmA)]), m)
    de = np.einsum("nij,nj->ni", quat_rot(qe[nearest(te, tmA)]), m)
    bt = np.arctan2(dt[:, 1], dt[:, 0])
    be = np.arctan2(de[:, 1], de[:, 0])
    magerr = np.degrees(wrap(be - bt))
    pre = (tm >= -5.0) & (tm <= 0.0)
    dur = max(tm[-1] - tm[0], 1e-9)
    body_std = m[pre].std(0) if pre.sum() > 2 else np.full(3, NAN)
    diff_std = np.std(np.diff(m[pre], axis=0), axis=0) / math.sqrt(2) if pre.sum() > 3 else np.full(3, NAN)
    E["mag_n"] = int(m.shape[0])
    E["mag_rate_hz"] = round(m.shape[0] / dur, 2)
    E["mag_body_mean_pre_ga"] = [round(float(v), 5) for v in m[pre].mean(0)] if pre.any() else None
    E["mag_noise_std_pre_ga"] = [round(float(v), 5) for v in body_std]
    E["mag_noise_whitediff_pre_ga"] = [round(float(v), 5) for v in diff_std]
    E["truth_field_bearing_pre_deg"] = round(circ_deg(bt[pre]), 3) if pre.any() else NAN
    E["truth_field_H_pre_ga"] = round(float(np.mean(np.hypot(dt[pre, 0], dt[pre, 1]))), 4) if pre.any() else NAN
    E["truth_field_D_pre_ga"] = round(float(np.mean(dt[pre, 2])), 4) if pre.any() else NAN
    E["magerr_align_pm1"] = wm(tm, magerr, t_al - 1.0, t_al + 1.0) if t_al is not None else NAN
    E["magerr_winb"] = wm(tm, magerr, 15.0, 35.0)
    E["magerr_winb_std"] = ws(tm, magerr, 15.0, 35.0)
    al = (tm >= t_al) & (tm <= t_al + 1.0) if t_al is not None else np.zeros(tm.size, bool)
    E["mag_body_mean_align_ga"] = [round(float(v), 5) for v in m[al].mean(0)] if al.any() else None
    E["decl_sensor_align_deg"] = round(circ_deg(bt[al]), 3) if al.any() else NAN
    t3 = flags["cs_mag_3d"]["first_true_s"]
    E["err_pre3d_m3_m0.5"] = wm(ta, err, t3 - 3.0, t3 - 0.5) if t3 is not None else NAN
    E["err_post3d_p0.5_p3"] = wm(ta, err, t3 + 0.5, t3 + 3.0) if t3 is not None else NAN

    # ---- EKF states: earth field, body mag bias
    ts = (es["timestamp"].astype(float) - arm) / S
    st = vec(es, "states", 25)
    decl_ekf = np.degrees(np.arctan2(st[:, 17], st[:, 16]))
    mI, mB = st[:, 16:19], st[:, 19:22]
    E["magI_norm_winb"] = wm(ts, np.linalg.norm(mI, axis=1), 15.0, 35.0)
    E["magI_D_winb"] = wm(ts, mI[:, 2], 15.0, 35.0)
    E["decl_ekf_align"] = wm(ts, decl_ekf, t_al - 0.5, t_al + 0.5) if t_al is not None else NAN
    E["decl_ekf_winb"] = wm(ts, decl_ekf, 15.0, 35.0)
    E["decl_ekf_winb_std"] = ws(ts, decl_ekf, 15.0, 35.0)
    E["decl_mismatch_winb"] = E["decl_ekf_winb"] - E["truth_field_bearing_pre_deg"]
    E["magB_align"] = [wm(ts, mB[:, i], t_al - 0.5, t_al + 0.5) if t_al is not None else NAN for i in range(3)]
    E["magB_winb"] = [wm(ts, mB[:, i], 15.0, 35.0) for i in range(3)]
    # time-resolved test: yaw error (truth minus EKF) at EKF-state times vs EKF mag body-x bias, 0..35 s
    e_s = err[nearest(te, es["timestamp"].astype(float))]
    ok = (ts >= 0) & (ts <= 35) & np.isfinite(e_s)
    if ok.sum() > 10 and np.std(mB[ok, 0]) > 0:
        E["ts_r_err_magBx_0_35"] = round(float(np.corrcoef(mB[ok, 0], e_s[ok])[0, 1]), 4)
        E["ts_slope_deg_per_G"] = round(float(np.polyfit(mB[ok, 0], e_s[ok], 1)[0]), 1)
    dev = np.nonzero(ok & (np.abs(mB[:, 0]) > 1e-3))[0]
    E["magBx_first_abs_gt_1mG_s"] = round(float(ts[dev[0]]), 2) if dev.size else None
    E["ts_err_at_t_s"] = {str(t): round(float(e_s[np.argmin(np.abs(ts - t))]), 3) for t in (0, 5, 10, 15, 20, 25, 30, 35)}
    E["ts_magBx_at_t_G"] = {str(t): round(float(mB[np.argmin(np.abs(ts - t)), 0]), 5) for t in (0, 5, 10, 15, 20, 25, 30, 35)}

    # ---- sensor bias estimator (gyro z bias rad/s, mag bias gauss)
    if sb is not None:
        tb = (sb["timestamp"].astype(float) - arm) / S
        gb, mbs = vec(sb, "gyro_bias", 3), vec(sb, "mag_bias", 3)
        E["gyro_z_bias_align"] = wm(tb, gb[:, 2], t_al - 0.5, t_al + 0.5) if t_al is not None else NAN
        E["gyro_z_bias_winb"] = wm(tb, gb[:, 2], 15.0, 35.0)
        E["sb_magbias_align"] = [wm(tb, mbs[:, i], t_al - 0.5, t_al + 0.5) if t_al is not None else NAN for i in range(3)]
        E["sb_magbias_winb"] = [wm(tb, mbs[:, i], 15.0, 35.0) for i in range(3)]
    out["E"] = E
    return out


def corr_block(rows, gz):
    y_name = "err_winb"
    preds = {
        "decl_ekf_winb": lambda e: e["decl_ekf_winb"],
        "decl_mismatch_winb": lambda e: e["decl_mismatch_winb"],
        "magB_x_winb": lambda e: e["magB_winb"][0],
        "magB_y_winb": lambda e: e["magB_winb"][1],
        "magB_z_winb": lambda e: e["magB_winb"][2],
        "gyro_z_bias_winb": lambda e: e.get("gyro_z_bias_winb", NAN),
        "sb_magbias_x_winb": lambda e: e.get("sb_magbias_winb", [NAN] * 3)[0],
        "sb_magbias_y_winb": lambda e: e.get("sb_magbias_winb", [NAN] * 3)[1],
        "sb_magbias_z_winb": lambda e: e.get("sb_magbias_winb", [NAN] * 3)[2],
        "magI_norm_winb": lambda e: e["magI_norm_winb"],
        "magI_D_winb": lambda e: e["magI_D_winb"],
        "magerr_pre_align": lambda e: e["magerr_align_pm1"],
        "err_align_plus1s": lambda e: e["err_align_plus1s"],
        "err_arm": lambda e: e["err_arm_pm0.5"],
    }
    y = np.array([r["E"][y_name] for r in rows], float)
    lines = [f"Correlation across runs (n={len(rows)}) with {y_name} (truth-minus-EKF, deg)", "",
             "| quantity | r | slope (deg per unit) | n finite |", "|---|---|---|---|"]
    res = {}
    for k, f in preds.items():
        x = np.array([f(r["E"]) for r in rows], float)
        ok = np.isfinite(x) & np.isfinite(y)
        if ok.sum() > 2 and x[ok].std() > 0 and y[ok].std() > 0:
            rr = float(np.corrcoef(x[ok], y[ok])[0, 1])
            sl = float(np.polyfit(x[ok], y[ok], 1)[0])
            res[k] = {"r": round(rr, 3), "slope": round(sl, 4), "n": int(ok.sum())}
            lines.append(f"| {k} | {rr:+.3f} | {sl:+.4f} | {int(ok.sum())} |")
        else:
            res[k] = None
            lines.append(f"| {k} | n/a | n/a | {int(ok.sum())} |")
    xb = np.array([r["E"]["magB_winb"][0] for r in rows], float)
    if np.isfinite(xb).all() and xb.std() > 0:
        slope, icpt = np.polyfit(xb, y, 1)
        res["fit_err_winb_on_magB_x"] = {"slope_deg_per_G": round(float(slope), 2),
                                         "intercept_deg": round(float(icpt), 3),
                                         "pred_slope_-1/H_deg_per_G": round(-math.degrees(1.0 / 0.2166), 1)}
        lines += ["", f"Fit err_winb = a + b*magB_x: b = {slope:.1f} deg/G, a = {icpt:+.3f} deg "
                      f"(-1/H with H = 0.2166 G predicts b = {-math.degrees(1 / 0.2166):.1f} deg/G)"]
    lines += ["", "Within-group correlations (n=5 per group; indicative only)", "",
              "| group | y | x | r | slope |", "|---|---|---|---|---|"]
    pairs = [("err_winb", "magB_x_winb", lambda e: e["magB_winb"][0]),
             ("err_winb", "decl_sensor_pre_deg", lambda e: e["truth_field_bearing_pre_deg"]),
             ("err_align_plus1s", "decl_sensor_align_deg", lambda e: e["decl_sensor_align_deg"]),
             ("err_winb", "gyro_z_bias_winb", lambda e: e.get("gyro_z_bias_winb", NAN))]
    for g in ("hover", "step_roll", "traj_lemniscate"):
        sub = [r for r in rows if r["run"].startswith(g + "/")]
        for yk, xk, f in pairs:
            yy = np.array([r["E"][yk] for r in sub], float)
            xx = np.array([f(r["E"]) for r in sub], float)
            ok = np.isfinite(xx) & np.isfinite(yy)
            if ok.sum() > 2 and xx[ok].std() > 0 and yy[ok].std() > 0:
                lines.append(f"| {g} | {yk} | {xk} | {np.corrcoef(xx[ok], yy[ok])[0, 1]:+.3f} | "
                             f"{np.polyfit(xx[ok], yy[ok], 1)[0]:+.4g} |")
            else:
                lines.append(f"| {g} | {yk} | {xk} | n/a | n/a |")
    return res, lines


def main(runs):
    gz = gz_field()
    rows = [analyse(r) for r in runs]
    corr, cl = corr_block(rows, gz)
    head = ["| run | arm s | align s | mag_hdg s | mag_3d s | gnss_yaw s | err align+1s | err arm | err winb (std) | "
            "decl EKF winb | decl truth pre | magB x,y,z winb | sb magbias x,y,z winb | gyro z bias winb | magerr winb |",
            "|" + "---|" * 15]
    tl = []
    for r in rows:
        e, f = r["E"], r["flags"]

        def ft(c):
            return "-" if f[c]["first_true_s"] is None else f"{f[c]['first_true_s']:.2f}"

        def fl(v, p=2):
            return "nan" if v is None or not np.isfinite(v) else f"{v:+.{p}f}"

        mb = " ".join(fl(v, 4) for v in e["magB_winb"])
        sbm = " ".join(fl(v, 4) for v in e.get("sb_magbias_winb", [NAN] * 3))
        tl.append(f"| {r['run']} | {r['arm_s']:.2f} | {ft('cs_yaw_align')} | {ft('cs_mag_hdg')} | {ft('cs_mag_3d')} | "
                  f"{ft('cs_gnss_yaw')} | {fl(e['err_align_plus1s'])} | {fl(e['err_arm_pm0.5'])} | "
                  f"{fl(e['err_winb'])} ({fl(e['err_winb_std'], 3)}) | {fl(e['decl_ekf_winb'])} | "
                  f"{fl(e['truth_field_bearing_pre_deg'])} | {mb} | {sbm} | {fl(e.get('gyro_z_bias_winb'), 5)} | "
                  f"{fl(e['magerr_winb'])} |")
    gz_line = (f"gz world field (default.sdf, ENU): decl {gz['decl_deg']:.2f} deg, incl {gz['incl_deg']:.2f} deg, "
               f"H {gz['H_T'] * 1e6:.2f} uT, Z {gz['Z_down_T'] * 1e6:.2f} uT (down), lat {gz['lat_deg']:.4f} "
               f"lon {gz['lon_deg']:.4f}")
    md = ["# A-19 S34 pretest per-run table (generated by a19_mech.py)", "", gz_line, ""] + head + tl + [""] + cl
    here = HERE
    with open(os.path.join(here, "a19_table.md"), "w") as fh:
        fh.write("\n".join(md) + "\n")
    with open(os.path.join(here, "a19_mech.json"), "w") as fh:
        json.dump({"gz": gz, "rows": rows, "corr": corr}, fh, indent=1, default=float)
    print("\n".join(md))


if __name__ == "__main__":
    main(sys.argv[1:] or RUNS)

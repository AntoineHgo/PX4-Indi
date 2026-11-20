#!/usr/bin/env python3
"""Stage-by-stage delay of the INDI position chain on one SITL ULog (analysis only).
Delay = phase of the least-squares fit of sin/cos(k*phi(t)) (k=1,2) + dc, over the cruise window of the analytic
trajectory (phi(t) from metrics.traj_phase), relative to the analytic reference. usage: lag_chain.py run_dir"""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import metrics
G = 9.80665

def basis(phi, ks=(1, 2)):
    cols = [np.ones_like(phi)]
    for k in ks:
        cols += [np.sin(k * phi), np.cos(k * phi)]
    return np.column_stack(cols)

def coefs(t, y, phi, ks=(1, 2)):
    ok = np.isfinite(y)
    c = np.linalg.lstsq(basis(phi[ok], ks), y[ok], rcond=None)[0]
    return {k: complex(c[2 + 2 * (i)], c[1 + 2 * i]) for i, k in enumerate(ks)}  # cos + i sin ... see delay()

def delay(sig, ref, k, w):
    """(delay s, signed amplitude ratio). a sin(kphi)+b cos(kphi) = Im((b... use z=b+ia: z = A e^{i(kphi+th)}.
    Delayed copy: th_sig - th_ref = -k w tau; z=b+ia has th=-k w tau.. sign fixed empirically by the selftest. Sign flip (inverting channel) folded into the ratio."""
    z = sig[k] / ref[k]
    r, dth = abs(z), np.angle(z)
    if abs(dth) > np.pi / 2:
        r, dth = -r, np.angle(-z)
    return dth / (k * w), r

def window(tt, traj, t0):
    tr = traj["ramp_s"]
    t_rel = (tt - t0) * 1e-6
    return (t_rel >= tr) & (t_rel <= 2 * np.pi * traj["laps"] / traj["w"])

def phi_of(traj, t_us, t0):
    return np.array([metrics.traj_phase(traj, (t - t0) * 1e-6) for t in t_us])

def ref_pva(traj, t_us, t0):
    out = [[], [], []]
    for t in (t_us - t0) * 1e-6:
        p, v, a = metrics.traj_pva(traj, t)
        out[0].append(p[:2]); out[1].append(v[:2]); out[2].append(a[:2])
    return [np.array(o) for o in out]

def ref_jerk(traj, t_us, t0, h=1e-2):
    ap = ref_pva(traj, t_us + h * 1e6, t0)[2]; am = ref_pva(traj, t_us - h * 1e6, t0)[2]
    return (ap - am) / (2 * h)

def zb_acc(q):
    w, x, y, z = q[:, 0], q[:, 1], q[:, 2], q[:, 3]
    zb = np.column_stack([2 * (x * z + w * y), 2 * (y * z - w * x), 1 - 2 * (x * x + y * y)])
    return -G * zb[:, :2] / zb[:, 2:3]  # earth NED x,y accel for a thrust-balanced-gravity vehicle

def topic(u, name):
    return next(d.data for d in u.data_list if d.name == name)

def stage_rows(u, run):
    traj, t0 = run["trajectory"], run["trajectory"]["t0_us"]
    w = traj["w"]
    rows = []
    def run_one(name, t_us, ax_sig, ref_fn, rate_label=None):
        """ax_sig (N,2) in earth x,y; ref_fn(t_us)->(N,2). Window to cruise."""
        m = window(t_us, traj, t0)
        tt = t_us[m]; phi = phi_of(traj, tt, t0); ref = ref_fn(tt)
        hz = 1e6 / np.median(np.diff(t_us))
        for ai, an, k in ((0, "x(large)", 1), (1, "y(small)", 2)):
            cs = coefs(tt, ax_sig[m, ai], phi); cr = coefs(tt, ref[:, ai], phi)
            d, r = delay(cs, cr, k, w)
            rows.append((name, an, 1e3 * d, r, hz))
    return traj, t0, w, run_one, rows

def main(run_dir):
    run = json.load(open(os.path.join(run_dir, "run.json")))
    u = metrics.ULog(os.path.join(run_dir, "flight.ulg")) if hasattr(metrics, "ULog") else None
    if u is None:
        from pyulog import ULog
        u = ULog(os.path.join(run_dir, "flight.ulg"))
    traj, t0, w, run_one, rows = stage_rows(u, run)
    acc_ref = lambda t: ref_pva(traj, t, t0)[2]
    pos_ref = lambda t: ref_pva(traj, t, t0)[0]
    jerk_ref = lambda t: ref_jerk(traj, t, t0)
    ts = topic(u, "trajectory_setpoint"); T = ts["timestamp"].astype(float)
    run_one("1 traj_sp.accel", T, np.column_stack([ts["acceleration[0]"], ts["acceleration[1]"]]), acc_ref)
    run_one("0 traj_sp.pos (vs analytic)", T, np.column_stack([ts["position[0]"], ts["position[1]"]]), pos_ref)
    lp = topic(u, "vehicle_local_position_setpoint"); T = lp["timestamp"].astype(float)
    run_one("2a local_pos_sp.accel", T, np.column_stack([lp["acceleration[0]"], lp["acceleration[1]"]]), acc_ref)
    ps = topic(u, "indi_pos_status"); T = ps["timestamp"].astype(float)
    run_one("2b indi a_c", T, np.column_stack([ps["a_c[0]"], ps["a_c[1]"]]), acc_ref)
    asp = topic(u, "vehicle_attitude_setpoint"); T = asp["timestamp"].astype(float)
    a3 = zb_acc(np.column_stack([asp["q_d[%d]" % i] for i in range(4)]))
    run_one("3 att_sp implied", T, a3, acc_ref)
    at = topic(u, "vehicle_attitude"); T = at["timestamp"].astype(float)
    run_one("4 att est implied", T, zb_acc(np.column_stack([at["q[%d]" % i] for i in range(4)])), acc_ref)
    ag = topic(u, "vehicle_attitude_groundtruth"); T = ag["timestamp"].astype(float)
    run_one("4t att truth implied", T, zb_acc(np.column_stack([ag["q[%d]" % i] for i in range(4)])), acc_ref)
    for nm in ("a_f", "t_f", "t_c", "t_c_applied"):
        run_one("2c indi " + nm + " (xy, raw)", ps["timestamp"].astype(float), np.column_stack([ps[nm + "[0]"], ps[nm + "[1]"]]), acc_ref)
    gt = topic(u, "sim_ground_truth")
    # drag correction: truth accel = c * tilt_accel(truth att) - k v (fit over the window), then applied to stages 3/4
    Tg = gt["timestamp"].astype(float); mg = window(Tg, traj, t0)
    agt = np.column_stack([np.gradient(gt["vx"], Tg * 1e-6), np.gradient(gt["vy"], Tg * 1e-6)])
    vg = np.column_stack([gt["vx"], gt["vy"]])
    Ta = ag["timestamp"].astype(float)
    tilt_g = zb_acc(np.column_stack([ag["q[%d]" % i] for i in range(4)]))
    tilt_gi = np.column_stack([np.interp(Tg, Ta, tilt_g[:, i]) for i in range(2)])
    A = np.column_stack([tilt_gi[mg].ravel(), vg[mg].ravel()])
    c, kd = np.linalg.lstsq(A, agt[mg].ravel(), rcond=None)[0]
    res = agt[mg].ravel() - A @ np.array([c, kd])
    print("drag fit: a_truth = %.3f * tilt_acc + (%.3f) * v ; resid rms %.3f of %.3f m/s2" % (c, kd, res.std(), agt[mg].std()))
    def corr(T, tilt):
        v = np.column_stack([np.interp(T, Tg, vg[:, i]) for i in range(2)])
        return c * tilt + kd * v
    run_one("3d att_sp implied -drag(v_truth)", asp["timestamp"].astype(float), corr(asp["timestamp"].astype(float), a3), acc_ref)
    run_one("4d att est implied -drag(v_truth)", at["timestamp"].astype(float), corr(at["timestamp"].astype(float), zb_acc(np.column_stack([at["q[%d]" % i] for i in range(4)]))), acc_ref)
    run_one("4td att truth implied -drag", Ta, corr(Ta, tilt_g), acc_ref)
    for lab, tk in (("timestamp", "timestamp"), ("timestamp_sample", "timestamp_sample")):
        T = gt[tk].astype(float)
        run_one("5p truth pos [%s]" % lab, T, np.column_stack([gt["x"], gt["y"]]), pos_ref)
        if tk == "timestamp":
            ax_ = np.column_stack([np.gradient(gt["vx"], T * 1e-6), np.gradient(gt["vy"], T * 1e-6)])
            run_one("5 truth accel d(v)/dt", T, ax_, acc_ref)
    # 6: omega_ff (body roll, pitch) vs analytic jerk and vs d(3)/dt; channel -> earth axis chosen by fit amplitude
    of = topic(u, "indi_rate_feedforward"); T = of["timestamp"].astype(float)
    om = np.column_stack([of["omega_ff[0]"], of["omega_ff[1]"]])
    m = window(T, traj, t0); phi = phi_of(traj, T[m], t0); jr = ref_jerk(traj, T[m], t0)
    d3 = np.gradient(zb_acc(np.column_stack([np.interp(T, asp["timestamp"], asp["q_d[%d]" % i]) for i in range(4)])), T * 1e-6, axis=0)
    out6 = []
    for ci, cn in ((0, "roll"), (1, "pitch")):
        best = None
        for ai, k in ((0, 1), (1, 2)):
            cs = coefs(T[m], om[m, ci], phi); cr = coefs(T[m], jr[:, ai], phi)
            d, r = delay(cs, cr, k, w)
            if best is None or abs(cs[k]) > best[0]:
                best = (abs(cs[k]), ai, k, d, r)
        _, ai, k, d, r = best
        cd = coefs(T[m], d3[m, ai], phi); cr = coefs(T[m], jr[:, ai], phi)
        d3d, r3 = delay(cd, cr, k, w)
        rows.append(("6 omega_ff.%s vs jerk(%s)" % (cn, "xy"[ai]), "xy"[ai] + "@%dw" % k, 1e3 * d, r, 1e6 / np.median(np.diff(T))))
        rows.append(("6b d(att_sp acc)/dt vs jerk", "xy"[ai] + "@%dw" % k, 1e3 * d3d, r3, 1e6 / np.median(np.diff(T))))
    for r in rows:
        print("%-32s %-9s %8.1f ms  ratio %6.3f  %6.1f Hz" % r)
    return rows

def selftest():
    run = json.load(open("results/g5_g55_s141_a18/o1_lemniscate_s1/run.json"))
    traj, t0 = run["trajectory"], run["trajectory"]["t0_us"]
    from pyulog import ULog
    u = ULog("results/g5_g55_s141_a18/o1_lemniscate_s1/flight.ulg")
    for name in ("trajectory_setpoint", "vehicle_attitude", "indi_rate_feedforward", "sim_ground_truth"):
        T = topic(u, name)["timestamp"].astype(float)
        m = window(T, traj, t0); tt = T[m]; phi = phi_of(traj, tt, t0)
        res = []
        for tau, amp in ((0.100, 0.7),):
            sh = tt - tau * 1e6
            sig = amp * ref_pva(traj, sh, t0)[2]
            ref = ref_pva(traj, tt, t0)[2]
            for ai, k in ((0, 1), (1, 2)):
                d, r = delay(coefs(tt, sig[:, ai], phi), coefs(tt, ref[:, ai], phi), k, traj["w"])
                res.append("%s: %.2f ms r %.3f" % ("xy"[ai], 1e3 * d, r))
        print("selftest", name, "%.0f Hz" % (1e6 / np.median(np.diff(T))), "tau 100 ms amp 0.7 ->", "; ".join(res))

if __name__ == "__main__":
    if sys.argv[1] == "selftest":
        selftest()
    else:
        main(sys.argv[1])

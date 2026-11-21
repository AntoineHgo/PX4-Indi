#!/usr/bin/env python3
"""G5.11 estimator reset transients (GATES.md "G5.11 exact test (S160"). Usage: g511_check.py [--out DIR] RUN_DIR...
S175 amendment (Q8 b, Q12 B + D): ekf_xy is judged on the ground-truth HORIZONTAL excursion <= 0.5 m and no sustained oscillation
(tilt jump reported only); ekf_yaw keeps the 1 deg tilt limit with tilt jump = event value minus the 95th percentile of the same
tilt metric at no-event instants of the same flight (excess), plus the unchanged excursion (3-D) and oscillation tests; the z reset
part is not tested (owner decision Q8(b)). The pre-S175 verdict is kept as column "legacy".
Truth only (sim_ground_truth pose + body rates, 800 Hz); setpoint tilt from vehicle_attitude_setpoint.
Metric functions take arrays (times in s); ulog loading is separate."""
import json, math, os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import osc_detector

TILT_LIM_DEG, EXC_LIM_M = 1.0, 0.5
EVENTS = (("ekf_yaw", "vehicle_attitude", "quat_reset_counter"), ("ekf_xy", "vehicle_local_position", "xy_reset_counter"))


def body_z(q):
    q = np.asarray(q, float)
    w, x, y, z = q.T
    return np.stack([2 * (x * z + w * y), 2 * (y * z - w * x), 1 - 2 * (x * x + y * y)], 1)


def yaw_of(q):
    w, x, y, z = np.asarray(q, float).T
    return np.arctan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))


def wrap(a):
    return (np.asarray(a) + np.pi) % (2 * np.pi) - np.pi


def tilt_jump_deg(t, zb, ta):
    """max angle (deg) over [ta, ta+1] between body z (Nx3) and its normalised mean over [ta-1, ta)."""
    t = np.asarray(t, float)
    pre = (t >= ta - 1) & (t < ta)
    post = (t >= ta) & (t <= ta + 1)
    m = np.mean(zb[pre], 0)
    m /= np.linalg.norm(m)
    zn = zb[post] / np.linalg.norm(zb[post], axis=1, keepdims=True)
    return float(np.degrees(np.arccos(np.clip(zn @ m, -1, 1))).max())


def excursion_m(t, pos, ta):
    """max 3-D distance over [ta, ta+5] of pos (Nx3) from its mean over [ta-1, ta)."""
    t = np.asarray(t, float)
    m = np.mean(pos[(t >= ta - 1) & (t < ta)], 0)
    post = (t >= ta) & (t <= ta + 5)
    return float(np.linalg.norm(pos[post] - m, axis=1).max())


def excursion_h_m(t, pos, ta):
    """max HORIZONTAL (x, y) distance over [ta, ta+5] of pos (Nx3) from its mean over [ta-1, ta) (S175 xy criterion)."""
    t = np.asarray(t, float)
    m = np.mean(pos[(t >= ta - 1) & (t < ta)][:, :2], 0)
    post = (t >= ta) & (t <= ta + 5)
    return float(np.linalg.norm(pos[post][:, :2] - m, axis=1).max())


def noevent_tilt_jumps(tsp, zb, nav_t, nav, navv, ev_times, step=0.25, excl_pre=1.0, excl_post=9.0):
    """Tilt-jump metric (same function as the event value) at no-event instants of one flight: instants on a `step` grid with
    >= 1 s of setpoint data on both sides, nav_state == navv over [t-1, t+1], and no event (times ev_times, s) with
    t in [t_ev - excl_pre - 1, t_ev + excl_post + 1]. Returns (instants, values)."""
    tsp = np.asarray(tsp, float)
    out_t, out_v = [], []
    for tt in np.arange(tsp[0] + 1.0, tsp[-1] - 1.0, step):
        if any(te - excl_pre - 1.0 <= tt <= te + excl_post + 1.0 for te in ev_times):
            continue
        w = (nav_t >= tt - 1.0) & (nav_t <= tt + 1.0)
        base = np.asarray(nav)[nav_t <= tt - 1.0]
        if not w.any() or len(base) == 0 or np.any(np.asarray(nav)[w] != navv) or base[-1] != navv:
            continue
        out_t.append(tt)
        out_v.append(tilt_jump_deg(tsp, zb, tt))
    return np.array(out_t), np.array(out_v)


def noevent_p95(v):
    return float(np.percentile(v, 95)) if len(v) else float("nan")


def yaw_change_deg(t, yaw, ta):
    """truth yaw at ta+1 s minus mean pre-yaw over [ta-1, ta) (wrapped), deg; and max |change| over [ta, ta+1]."""
    t = np.asarray(t, float)
    ref = yaw[(t >= ta - 1) & (t < ta)][0]
    d = wrap(yaw - ref)
    pre = d[(t >= ta - 1) & (t < ta)].mean()
    post = (t >= ta) & (t <= ta + 1)
    dd = np.degrees(d[post] - pre)
    return float(dd[-1]), float(dd[np.argmax(np.abs(dd))])


def sp_yaw_step_deg(t, yaw_sp, ta):
    t = np.asarray(t, float)
    m = (t >= ta) & (t <= ta + 1)
    i = np.where(m)[0]
    i = np.r_[i[0] - 1, i] if i[0] > 0 else i
    return float(np.degrees(np.abs(wrap(np.diff(yaw_sp[i])))).max())


def osc_sustained(t, pqr_dps, ta):
    m = (t >= ta) & (t <= ta + 8)
    w, s = osc_detector.detect(t[m], pqr_dps[m, 0], pqr_dps[m, 1], pqr_dps[m, 2])
    return s, w


def verdict(valid, tilt, exc, osc):
    if not valid:
        return "INVALID"
    return "PASS" if (tilt <= TILT_LIM_DEG and exc <= EXC_LIM_M and not osc) else "FAIL"


def verdict_s175(kind, valid, tilt_excess, exc_h, exc_3d, osc):
    """S175: xy = horizontal excursion + no oscillation; yaw = tilt excess (event - p95 no-event) <= 1 deg, 3-D excursion, no osc."""
    if not valid:
        return "INVALID"
    if kind == "ekf_xy":
        return "PASS" if (exc_h <= EXC_LIM_M and not osc) else "FAIL"
    return "PASS" if (tilt_excess <= TILT_LIM_DEG and exc_3d <= EXC_LIM_M and not osc) else "FAIL"


def validity(ta, cnt_t, cnt, nav_t, nav, events, name):
    """cnt/nav arrays in s. Returns (valid, why list, nav value)."""
    why = []
    w = (cnt_t >= ta - 1) & (cnt_t <= ta + 8)
    c = np.asarray(cnt)[w]
    inc = int(np.count_nonzero(np.diff(c) != 0))
    if inc != 1:
        why.append(f"counter increments {inc} times in window")
    nv = np.asarray(nav)[(nav_t >= ta - 1) & (nav_t <= ta + 8)]
    base = np.asarray(nav)[nav_t <= ta]
    navv = int(base[-1]) if len(base) else None
    if len(nv) == 0 or np.any(nv != navv):
        why.append("nav_state not constant")
    for e in events:
        if e["name"] != name and ta - 1 <= e["t_applied_us"] / 1e6 <= ta + 8:
            why.append(f"other event {e['name']} in window")
    return not why, why, navv


def load(run):
    from pyulog import ULog
    ul = ULog(os.path.join(run, "flight.ulg"))
    d = {}
    for x in ul.data_list:
        if x.multi_id == 0 and x.name in ("sim_ground_truth", "vehicle_attitude", "vehicle_local_position",
                                           "vehicle_attitude_setpoint", "vehicle_status"):
            d[x.name] = x.data
    return d


def check_run(run, out_dir=None):
    d = load(run)
    meta = json.load(open(os.path.join(run, "run.json")))
    evs = meta["g5_events"]
    g = d["sim_ground_truth"]
    t = g["timestamp"] / 1e6
    pos = np.stack([g["x"], g["y"], g["z"]], 1)
    pqr = np.degrees(np.stack([g[f"angular_velocity[{i}]"] for i in range(3)], 1))
    yaw = yaw_of(np.stack([g[f"q[{i}]"] for i in range(4)], 1))
    sp = d["vehicle_attitude_setpoint"]
    tsp = sp["timestamp"] / 1e6
    qd = np.stack([sp[f"q_d[{i}]"] for i in range(4)], 1)
    zb, yawsp = body_z(qd), yaw_of(qd)
    vs = d["vehicle_status"]
    out = []
    for name, topic, field in EVENTS:
        r = dict(run=run, event=name)
        tt, cnt = d[topic]["timestamp"] / 1e6, d[topic][field]
        i = np.where(np.diff(cnt.astype(np.int64)) != 0)[0]
        e = next(e for e in evs if e["name"] == name)
        i = [k for k in i if tt[k + 1] >= e["t_cmd_us"] / 1e6 - 0.1]
        if not i:
            r.update(verdict="INVALID", why=["no counter increment"])
            out.append(r); continue
        ta = float(tt[i[0] + 1])
        ok, why, navv = validity(ta, tt, cnt, vs["timestamp"] / 1e6, vs["nav_state"], evs, name)
        tilt = tilt_jump_deg(tsp, zb, ta)
        exc = excursion_m(t, pos, ta)
        exc_h = excursion_h_m(t, pos, ta)
        _, nev = noevent_tilt_jumps(tsp, zb, vs["timestamp"] / 1e6, vs["nav_state"], navv, [e["t_applied_us"] / 1e6 for e in evs])
        p95 = noevent_p95(nev)
        excess = tilt - p95
        osc, wins = osc_sustained(t, pqr, ta)
        ychg, ymax = yaw_change_deg(t, yaw, ta)
        r.update(t_a=ta, valid=ok, why=why, nav_state=navv, tilt_jump_deg=tilt, truth_excursion_m=exc, osc_sustained=bool(osc),
                 osc_windows=[dict(t0=w["t0"], flagged=w["flagged"], f_hz=w["f_hz"], ratio=w["ratio"], rms_dps=w["rms_dps"]) for w in wins],
                 truth_yaw_change_deg=ychg, truth_yaw_max_dev_deg=ymax, sp_yaw_step_deg=sp_yaw_step_deg(tsp, yawsp, ta),
                 truth_excursion_h_m=exc_h, noevent_n=int(len(nev)), noevent_p95_deg=p95, noevent_max_deg=float(nev.max()) if len(nev) else float("nan"),
                 tilt_excess_deg=excess, legacy=verdict(ok, tilt, exc, osc),
                 verdict=verdict_s175(name, ok, excess, exc_h, exc, osc) if len(nev) else "INVALID")
        if not len(nev):
            r["why"] = r["why"] + ["no no-event instants for the tilt p95"]
        out.append(r)
    od = out_dir or run
    os.makedirs(od, exist_ok=True)
    json.dump(out, open(os.path.join(od, (os.path.basename(run) + "." if out_dir else "") + "g511_check.json"), "w"), indent=1)
    return out


def line(r):
    if "t_a" not in r:
        return f"{r['verdict']:8s} {r['run']} {r['event']}: {r['why']}"
    return (f"{r['verdict']:8s} {r['run']} {r['event']}: t_a {r['t_a']:.3f} s, nav {r['nav_state']}, valid {r['valid']} {r['why']}, "
            f"tilt jump {r['tilt_jump_deg']:.2f} deg, no-event p95 {r['noevent_p95_deg']:.2f} / max {r['noevent_max_deg']:.2f} deg (n {r['noevent_n']}), "
            f"excess {r['tilt_excess_deg']:.2f} deg (yaw <=1), excursion 3-D {r['truth_excursion_m']:.3f} m / horizontal {r['truth_excursion_h_m']:.3f} m (<=0.5), legacy {r['legacy']}, "
            f"osc sustained {r['osc_sustained']}, truth yaw change {r['truth_yaw_change_deg']:.2f} deg, sp yaw step {r['sp_yaw_step_deg']:.2f} deg")


if __name__ == "__main__":
    a = sys.argv[1:]
    od = None
    if "--out" in a:
        i = a.index("--out")
        od = a[i + 1]
        a = a[:i] + a[i + 2:]
    for run in a:
        for r in check_run(run.rstrip("/"), od):
            print(line(r))

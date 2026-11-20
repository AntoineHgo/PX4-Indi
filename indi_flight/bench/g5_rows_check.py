#!/usr/bin/env python3
"""G5.8 / G5.9 gate-row scorer from an existing g5_events flight (host side, pyulog, no firmware).

  python3 indi_flight/bench/g5_rows_check.py <flight_dir> [...]   (flight_dir has flight.ulg, run.json)
Writes <flight_dir>/g5_rows.json and g5_rows.txt; one PASS / FAIL / NOT-COMPUTED line per sub-check.

G5.8 (hover case only; "3 m/s: not flown"), per loss rc_loss / link_loss / offboard_loss:
  timeout reference (firmware time, GATES S144 note), parameters read at the event time from the ulog
  (initial params + changed_parameters, so runtime param sets are respected):
    rc: rise of failsafe_flags.manual_control_signal_lost - COM_RC_LOSS_T (failsafe_flags is published on change and every 500 ms: logged sample = firmware publish instant)
    link: last telemetry_status (any instance) with heartbeat_type_gcs=1 before the failsafe entry + COM_DL_LOSS_T
    offboard: last offboard_control_mode sample before the failsafe entry + COM_OF_LOSS_T
  entry = first vehicle_status.nav_state change after the event; if the vehicle was already in the configured
  mode (hold while in AUTO hold), nav_state cannot change, so entry = first vehicle_status.failsafe rise (else NOT-COMPUTED).
  limit: entry - timeout <= 1 s. Configured action: nav_state expected from NAV_RCL_ACT / NAV_DLL_ACT / COM_OBL_RC_ACT.
  excursion = max 3-D distance of vehicle_local_position_groundtruth (else vehicle_local_position) from its value
  at onset (event applied time) until entry + 5 s; limit <= 1 m. max tilt from vehicle_attitude over the same window
  is reported only; the G5.3/G5.4 sub-check is NOT computed.
G5.9: (a) motors all 0 after kill: reference = first manual_control_switches.kill_switch change (else
  actuator_armed.kill rise, published on change + 500 ms); delay = first actuator_motors sample at/after reference that is 0 on all
  channels and stays 0 until disarm; PASS if delay <= one command period (run.json physics_step_s, 1.25 ms).
  (b) INDI states zero at re-arm: first indi_pos_status / indi_rate_status sample at/after the re-arm time, fields
  listed zero/non-zero; the state set is POS_STATES / RATE_STATES; sample later than MAX_FIRST_S -> NOT-COMPUTED
  (a missing sample is not a zero). (c) first-second motor command change: windows of 0.1 s from re-arm, per motor the
  mean in each window; value = max over motors and windows 1..9 of |mean_k - mean_0|, in units of full scale (1.0);
  <= 0.05. (d) take-off after re-arm: |mean(indi_pos_status.thrust, 0.1 s after) - mean(0.1 s before)| at the
  takeoff_status rampup(4)->flight(5) edge after re-arm <= 10 % of MPC_THR_HOVER, and truth altitude dip
  (z_up at edge minus min over 1 s after) <= 0.3 m.
"""
import json, math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from g5_events import load_ulog, first_rise  # noqa: E402  (reuse, not duplicated)

NAV = {"hold": 4, "return": 5, "land": 18}
ACT_NAME = {1: "hold", 2: "return", 3: "land"}      # NAV_RCL_ACT / NAV_DLL_ACT
OBL_NAME = {3: "return", 4: "land", 5: "hold"}      # COM_OBL_RC_ACT
# STATES = fields carrying memory from the previous flight, not re-derived from current measurements (see
# results/g5_events_s145/fix.md); they must be at their reset value (0) in the first sample after arming.
# Measurements (a_f, t_f, angular_accel_filtered, mean_u ...), setpoints and outputs are reported only.
POS_STATES = ["blend", "hold_cycles"]
# torque_increment is algebraic (G1^-1 (nu - a_f) of the current cycle, indi_rate_control.cpp step 8); its only memory,
# the yaw back-calculation term _yaw_inc_prev, is zeroed by the law while landed and is not logged: reported only.
RATE_STATES = ["torque_filtered[0]", "torque_filtered[1]", "torque_filtered[2]",
               "rate_sp_dot[0]", "rate_sp_dot[1]", "rate_sp_dot[2]"]
POS_MEAS = ["a_f[0]", "a_f[1]", "a_f[2]", "t_f[0]", "t_f[1]", "t_f[2]", "mean_u"]
RATE_MEAS = ["angular_accel_filtered[0]", "angular_accel_filtered[1]", "angular_accel_filtered[2]",
             "torque_increment[0]", "torque_increment[1]", "torque_increment[2]"]
MAX_FIRST_S = 0.2
ZERO_EPS = 0.002  # disarmed idle command in the sim is about 0.001
LOSS_WIN_S = 5.0


def param_at(params, changes, name, t_us, default=None):
    """value of `name` at t_us: initial value overridden by the last change with timestamp <= t_us."""
    v = params.get(name, default)
    for ts, n, val in changes:
        if n == name and ts <= t_us:
            v = val
    return v


def res(name, status, text, **num):
    return {"name": name, "status": status, "text": text, **num}


def _a(d, k):
    return np.asarray(d[k], dtype=float)


def entry_time(L, t_from, win_s=10.0, link=False):
    """(t_entry_us, how, nav_after): earliest of the candidates inside [t_from, t_from + win_s]:
    nav_state change; vehicle_status.gcs_connection_lost rise (link only: the failsafe flag can already be latched by an
    earlier loss, so it cannot rise again); vehicle_status.failsafe rise (needed when the vehicle is already in the
    configured mode, e.g. hold failsafe while in AUTO hold, where nav_state cannot change)."""
    vs = L["vehicle_status"]
    t, n = _a(vs, "timestamp"), _a(vs, "nav_state")
    t1 = t_from + win_s * 1e6
    cand = []
    for i in range(1, len(t)):
        if t_from <= t[i] <= t1 and n[i] != n[i - 1]:
            cand.append((int(t[i]), f"nav_state {int(n[i-1])}->{int(n[i])}", int(n[i]))); break
    for key, lab in (("gcs_connection_lost", "vehicle_status.gcs_connection_lost rise"),
                     ("failsafe", "vehicle_status.failsafe rise (nav_state unchanged)")):
        if key in vs and (key != "gcs_connection_lost" or link):
            r = first_rise(t, _a(vs, key), t_from)
            if r is not None and r <= t1:
                cand.append((r, lab, int(n[min(int(np.searchsorted(t, r)), len(n) - 1)])))
    if not cand:
        return None, "no nav_state change, gcs_connection_lost or failsafe rise", None
    return min(cand)


def tilt_deg(att, t0, t1):
    t = _a(att, "timestamp")
    m = (t >= t0) & (t <= t1)
    if not m.any():
        return None
    q = np.stack([_a(att, f"q[{i}]")[m] for i in range(4)], 1)
    cz = 1 - 2 * (q[:, 1] ** 2 + q[:, 2] ** 2)
    return float(np.degrees(np.arccos(np.clip(cz, -1, 1))).max())


def excursion(pos, t0, t1):
    t = _a(pos, "timestamp")
    m = (t >= t0) & (t <= t1)
    if not m.any() or t[0] > t0:
        return None
    i0 = int(np.searchsorted(t, t0))
    p = np.stack([_a(pos, k) for k in ("x", "y", "z")], 1)
    return float(np.linalg.norm(p[m] - p[min(i0, len(p) - 1)], axis=1).max())


def g58(L, ev, params, changes):
    out = []
    evd = {e["name"]: e for e in ev}
    pos = L.get("gt") or L.get("vehicle_local_position")
    src = "vehicle_local_position_groundtruth" if L.get("gt") else "vehicle_local_position (NO ground truth)"
    for name in ("rc_loss", "link_loss", "offboard_loss"):
        row = "G5.8 " + name
        if name not in evd:
            out.append(res(row, "NOT-COMPUTED", "event not in run.json")); continue
        tap = evd[name]["t_applied_us"]
        P = lambda k, d=None: param_at(params, changes, k, tap, d)
        if name == "rc_loss":
            act, tmo, nm = P("NAV_RCL_ACT"), P("COM_RC_LOSS_T"), ACT_NAME.get(P("NAV_RCL_ACT"))
            ff = L["failsafe_flags"]
            r = first_rise(_a(ff, "timestamp"), _a(ff, "manual_control_signal_lost"), tap)
            if r is None:
                out.append(res(row, "NOT-COMPUTED", "no manual_control_signal_lost rise")); continue
            timeout, ref, onset = r - tmo * 1e6, f"flag rise {r/1e6:.3f} s (publication instant, on change) - {tmo} s", tap
        else:
            if name == "link_loss":
                act, tmo, nm = P("NAV_DLL_ACT"), P("COM_DL_LOSS_T"), ACT_NAME.get(P("NAV_DLL_ACT"))
            else:
                act, tmo, nm = P("COM_OBL_RC_ACT"), P("COM_OF_LOSS_T"), OBL_NAME.get(P("COM_OBL_RC_ACT"))
            t_e, _, _ = entry_time(L, tap, link=(name == "link_loss"))
            if t_e is None:
                out.append(res(row, "NOT-COMPUTED", "no failsafe entry found")); continue
            if name == "link_loss":
                ts = L["tel_gcs_ts"]
                ts = ts[(ts >= tap - 3e6) & (ts < t_e)]  # hb stopped at the event; entry bounds the search
                lab = "last telemetry_status gcs heartbeat"
            else:
                ts = _a(L["offboard_control_mode"], "timestamp")
                ts = ts[(ts >= evd.get("offboard_mode", evd[name])["t_applied_us"]) & (ts < t_e)]
                lab = "last offboard_control_mode"
            if len(ts) == 0:
                out.append(res(row, "NOT-COMPUTED", f"no {lab} sample")); continue
            onset = int(ts.max()); timeout = onset + tmo * 1e6
            ref = f"{lab} {onset/1e6:.3f} s + {tmo} s"
        t_e, how, nav_after = entry_time(L, tap, link=(name == "link_loss"))
        if t_e is None:
            out.append(res(row, "NOT-COMPUTED", how)); continue
        dt = (t_e - timeout) / 1e6
        want = NAV.get(nm)
        act_ok = None if want is None else (nav_after == want)
        exc = excursion(pos, onset, t_e + LOSS_WIN_S * 1e6)
        tl = tilt_deg(L["vehicle_attitude"], onset, t_e + LOSS_WIN_S * 1e6) if "vehicle_attitude" in L else None
        ok = dt <= 1.0 and exc is not None and exc <= 1.0 and act_ok is not False
        txt = (f"timeout ref {ref}; entry {t_e/1e6:.3f} s via {how}; entry-timeout {dt*1000:.0f} ms (<= 1000); configured "
               f"action {nm} (nav {want}), entered nav {nav_after}: {act_ok}; excursion {None if exc is None else round(exc,3)} m "
               f"(<= 1, {src}); max tilt {None if tl is None else round(tl,1)} deg (report only); hover case only, "
               f"3 m/s: not flown; G5.3/G5.4 sub-check not computed")
        out.append(res(row, "NOT-COMPUTED" if exc is None else ("PASS" if ok else "FAIL"), txt,
                       entry_minus_timeout_s=dt, excursion_m=exc, max_tilt_deg=tl, nav_after=nav_after))
    return out


def all_zero_after(t, M, t_ref):
    """first index >= t_ref from which every channel stays 0 (NaN counts as 0) to the end of the array; None if never."""
    z = np.all(np.nan_to_num(M) == 0.0, axis=1)
    bad = np.where(~z)[0]
    i0 = int(np.searchsorted(t, t_ref))
    start = max(i0, (bad.max() + 1) if len(bad) and bad.max() >= i0 else i0)
    return start if start < len(t) and z[start:].all() else None


def motors_mat(am):
    return np.stack([_a(am, f"control[{i}]") for i in range(12) if f"control[{i}]" in am], 1)


def g59a(L, ev, step_us):
    evd = {e["name"]: e for e in ev}
    if "kill" not in evd:
        return [res("G5.9a kill", "NOT-COMPUTED", "no kill event")]
    tk = evd["kill"]["t_applied_us"]
    ref, rtxt, resol = None, "", None
    sw = L.get("manual_control_switches")
    if sw is not None:
        t, k = _a(sw, "timestamp"), _a(sw, "kill_switch")
        idx = [i for i in range(1, len(t)) if t[i] >= tk - 1e6 and k[i] != k[i - 1]]
        if idx:
            ref, rtxt = int(t[idx[0]]), "manual_control_switches.kill_switch change"
            resol = float(np.median(np.diff(t)) / 1e3) if len(t) > 1 else None
            rtxt += f" (published on change plus a {resol:.0f} ms heartbeat, logged at every publication)"
    if ref is None:
        aa = L["actuator_armed"]
        ref = first_rise(_a(aa, "timestamp"), _a(aa, "kill"), tk - 1e6)
        rtxt = "actuator_armed.kill rise (published on change, logged at every publication)"
        if ref is None:
            return [res("G5.9a kill", "NOT-COMPUTED", "no firmware-side kill record")]
    vs = L["vehicle_status"]
    tv, ar = _a(vs, "timestamp"), _a(vs, "arming_state")
    dis = [tv[i] for i in range(len(tv)) if tv[i] > ref and ar[i] != 2]
    am = L["actuator_motors"]
    t, M = _a(am, "timestamp"), motors_mat(am)
    t_end = dis[0] if dis else t[-1]
    seg = (t >= ref) & (t <= t_end)
    per = step_us / 1e3
    # actuator_motors = controller command; stock output stage zeroes the outputs on kill, not this topic
    ts, Ms = t[seg], np.abs(np.nan_to_num(M[seg])) > ZERO_EPS
    nzmax = float(np.abs(np.nan_to_num(M[seg])).max()) if seg.any() else float("nan")
    last_nz = float(ts[Ms.any(1)].max()) if Ms.any() else None
    i = all_zero_after(ts, np.where(Ms, 1.0, 0.0), ref)
    out = []
    # actuator_motors is the controller command: informational only (the output stage zeroes actuator_outputs, not this topic)
    if i is None:
        out.append(res("G5.9a kill command (info)", "INFO",
                       f"actuator_motors (controller command) NOT 0 after kill: up to {nzmax:.3f} until disarm "
                       f"{(t_end-ref)/1e6:.2f} s after the switch; reference {rtxt} at {ref/1e6:.4f} s"))
    else:
        out.append(res("G5.9a kill command (info)", "INFO",
                       f"actuator_motors 0 at {(ts[i]-ref)/1e3:.2f} ms after switch; reference {rtxt}"))
    ao = L.get("actuator_outputs")
    if ao is None or "output[0]" not in ao:
        return out + [res("G5.9a kill motors", "NOT-COMPUTED", "actuator_outputs not logged")]
    to = _a(ao, "timestamp")
    # outputs 0..3 by numeric index (a lexicographic sort put output[10..12] before output[2]); window ends at disarm,
    # since the flight re-arms and takes off again after the kill
    O = np.nan_to_num(np.stack([_a(ao, f"output[{i}]") for i in range(4)], 1))
    sp = float(np.median(np.diff(to)) / 1e3)
    wo = to <= t_end
    to, O = to[wo], O[wo]
    k = all_zero_after(to, O, ref)  # first sample from which all 4 outputs stay 0 until disarm
    rres = "reference = first publication carrying the change (on-change topic)"
    if k is None:
        return out + [res("G5.9a kill motors", "FAIL", f"actuator_outputs (full rate, spacing {sp:.2f} ms) not 0 until the end after kill; "
                          f"{rtxt} at {ref/1e6:.4f} s; {rres}", delay_ms=None, period_ms=per, ref_us=ref)]
    # attribution (info): commander latency switch -> actuator_armed.kill, output-stage latency kill -> outputs 0
    aa = L.get("actuator_armed")
    tkr = first_rise(_a(aa, "timestamp"), _a(aa, "kill"), ref - 1e6) if aa is not None and "kill" in aa else None
    if tkr is not None:
        out.append(res("G5.9a kill chain (info)", "INFO",
                       f"actuator_armed.kill rise {(tkr-ref)/1e3:.2f} ms after the switch; outputs 0 "
                       f"{(to[k]-tkr)/1e3:.2f} ms after the kill flag", armed_kill_ms=(tkr - ref) / 1e3,
                       out_after_flag_ms=(to[k] - tkr) / 1e3))
    hi = (to[k] - ref) / 1e3
    lo = (to[k - 1] - ref) / 1e3 if k > 0 and to[k - 1] >= ref else 0.0  # last non-zero sample (or the reference)
    st = "PASS" if hi <= per else ("FAIL" if lo > per else "NOT-COMPUTED")
    return out + [res("G5.9a kill motors", st,
                      f"actuator_outputs all 0 at {hi:.2f} ms after the switch (last non-zero {lo:.2f} ms), command period {per:.2f} ms, "
                      f"output sample spacing {sp:.2f} ms; {rtxt} at {ref/1e6:.4f} s; {rres}",
                      delay_ms=hi, last_nonzero_ms=lo, period_ms=per, ref_us=ref)]


def arm_time(L, ev):
    evd = {e["name"]: e for e in ev}
    if "rearm" in evd:
        return evd["rearm"]["t_applied_us"], "run.json rearm applied"
    return None, ""


def g59b(L, t_arm):
    lines, bad, stat, miss = [], [], "PASS", []
    for topic, states, meas in (("indi_pos_status", POS_STATES, POS_MEAS), ("indi_rate_status", RATE_STATES, RATE_MEAS)):
        d = L.get(topic)
        if d is None:
            miss.append(topic); continue
        t = _a(d, "timestamp")
        i = int(np.searchsorted(t, t_arm))
        if i >= len(t) or (t[i] - t_arm) / 1e6 > MAX_FIRST_S:
            miss.append(f"{topic} first sample {(t[i]-t_arm)/1e6 if i < len(t) else float('nan'):.3f} s after arm")
            continue
        nz = [f"{k}={d[k][i]:.3g}" for k in states if k in d and d[k][i] != 0]
        zr = [k for k in states if k in d and d[k][i] == 0]
        allnz = [k for k in d if k != "timestamp" and d[k][i] != 0]
        ms = ", ".join(f"{k}={d[k][i]:.3g}" for k in meas if k in d)
        lines.append(f"{topic} +{(t[i]-t_arm)/1e3:.1f} ms: states non-zero {nz or 'none'} (of {len(states)}); measurements (reported only) {ms}")
        bad += [x.split('=')[0] for x in nz]
    if miss and not lines:
        return res("G5.9b rearm states", "NOT-COMPUTED", "; ".join(miss))
    if bad:
        stat = "FAIL"
    elif miss:
        stat = "NOT-COMPUTED"
    return res("G5.9b rearm states", stat, " | ".join(lines + (["not computed: " + "; ".join(miss)] if miss else [])), nonzero=bad)


def g59c(L, t_arm, win=0.1, n=10):
    am = L["actuator_motors"]
    t, M = _a(am, "timestamp"), np.nan_to_num(motors_mat(am))
    if t[-1] < t_arm + n * win * 1e6:
        return res("G5.9c first second", "NOT-COMPUTED", "log ends before re-arm + 1 s")
    means = []
    for k in range(n):
        m = (t >= t_arm + k * win * 1e6) & (t < t_arm + (k + 1) * win * 1e6)
        if not m.any():
            return res("G5.9c first second", "NOT-COMPUTED", f"no motor samples in window {k}")
        means.append(M[m].mean(0))
    means = np.array(means)
    dev = float(np.abs(means[1:] - means[0]).max())
    return res("G5.9c first second", "PASS" if dev <= 0.05 else "FAIL",
               f"max |0.1 s window mean - first window| over motors and windows = {dev*100:.2f} % of full scale (<= 5); "
               f"first-window means {np.round(means[0],3).tolist()}", dev_pct=dev * 100)


def g59d(L, t_arm, thr_hover):
    ts = L["takeoff_status"]
    t, s = _a(ts, "timestamp"), _a(ts, "takeoff_state")
    edge = next((int(t[i]) for i in range(1, len(t)) if t[i] >= t_arm and s[i - 1] == 4 and s[i] == 5), None)
    if edge is None:
        return res("G5.9d takeoff", "NOT-COMPUTED", "no rampup->flight edge after re-arm")
    d = L.get("indi_pos_status")
    gt = L.get("gt") or L.get("vehicle_local_position")
    tp, th = _a(d, "timestamp"), _a(d, "thrust")
    b, a = (tp >= edge - 1e5) & (tp < edge), (tp >= edge) & (tp < edge + 1e5)
    if b.sum() < 3 or a.sum() < 3:
        return res("G5.9d takeoff", "NOT-COMPUTED", f"too few indi_pos_status samples around edge (before {b.sum()}, after {a.sum()})")
    step = abs(th[a].mean() - th[b].mean())
    tg, zg = _a(gt, "timestamp"), -_a(gt, "z")
    w = (tg >= edge) & (tg <= edge + 1e6)
    if not w.any():
        return res("G5.9d takeoff", "NOT-COMPUTED", "no truth samples after edge")
    dip = float(max(0.0, zg[w][0] - zg[w].min()))
    ok = step <= 0.1 * thr_hover and dip <= 0.3
    return res("G5.9d takeoff", "PASS" if ok else "FAIL",
               f"edge {edge/1e6:.3f} s: |thrust step| {step:.4f} = {step/thr_hover*100:.1f} % of hover {thr_hover:.3f} (<= 10); "
               f"truth altitude dip {dip:.3f} m (<= 0.3)", thrust_step=step, dip_m=dip)


def analyse(L, ev, params, changes, step_us=1250):
    out = g58(L, ev, params, changes)
    out += g59a(L, ev, step_us)
    t_arm, _ = arm_time(L, ev)
    if t_arm is None:
        out += [res(n, "NOT-COMPUTED", "no rearm event") for n in ("G5.9b rearm states", "G5.9c first second", "G5.9d takeoff")]
    else:
        thr = param_at(params, changes, "MPC_THR_HOVER", t_arm, 0.5)
        out += [g59b(L, t_arm), g59c(L, t_arm), g59d(L, t_arm, thr)]
    return out


def load(d):
    from pyulog import ULog
    meta = json.load(open(os.path.join(d, "run.json")))
    L, _ = load_ulog(os.path.join(d, "flight.ulg"))
    ul = ULog(os.path.join(d, "flight.ulg"))
    want = {"indi_pos_status", "indi_rate_status", "takeoff_status", "manual_control_switches", "offboard_control_mode",
            "vehicle_local_position_groundtruth", "actuator_outputs"}
    gcs = []
    for x in ul.data_list:
        dd = {k: np.asarray(v) for k, v in x.data.items()}
        if x.name in want and x.multi_id == 0:
            L["gt" if x.name.endswith("groundtruth") else x.name] = dd
        if x.name == "telemetry_status":
            gcs.append(dd["timestamp"][dd["heartbeat_type_gcs"] > 0])
    L["tel_gcs_ts"] = np.sort(np.concatenate(gcs)) if gcs else np.array([])
    L["actuator_motors"] = {k: np.asarray(v) for k, v in L["actuator_motors"].items()}
    changes = [(c[0], c[1], c[2]) for c in ul.changed_parameters]
    return L, meta, dict(ul.initial_parameters), changes


def main(dirs):
    for d in dirs:
        L, meta, params, changes = load(d)
        rows = analyse(L, meta.get("g5_events", []), params, changes, int(round(meta.get("physics_step_s", 0.00125) * 1e6)))
        lines = [f"{r['status']:13s} {r['name']}: {r['text']}" for r in rows]
        print(f"== {d}")
        print("\n".join(lines))
        json.dump(rows, open(os.path.join(d, "g5_rows.json"), "w"), indent=1, default=float)
        open(os.path.join(d, "g5_rows.txt"), "w").write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main(sys.argv[1:])

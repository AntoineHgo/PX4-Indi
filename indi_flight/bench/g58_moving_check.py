#!/usr/bin/env python3
"""G5.8 at 3 m/s (GATES row G5.8, Q8 add.3 (i)/(ii)), key 1.  Host side, pyulog.

  python3 indi_flight/bench/g58_moving_check.py RUN_DIR [--out FILE]      (RUN_DIR has flight.ulg, run.json)

Per event rc_loss / link_loss / offboard_loss:
  timeout reference  firmware time, GATES S144 note, as g5_rows_check.g58 (code copied, parameters read at the event time):
                     rc = rise of failsafe_flags.manual_control_signal_lost - COM_RC_LOSS_T; link = last telemetry_status
                     with heartbeat_type_gcs=1 + COM_DL_LOSS_T; offboard = last offboard_control_mode sample + COM_OF_LOSS_T.
  entry              first vehicle_status.nav_state change at/after the event (the nav state entered is that new state); if
                     none, first vehicle_status.failsafe rise (nav_state unchanged). The g5_rows_check entry_time() instead
                     returns the earliest of nav change / gcs_connection_lost rise, and reads the nav state AT the flag rise,
                     i.e. still 14 for link loss: the nav change follows the flag by one commander cycle (see G58_KEY1.md).
                     The flag time is reported too. Limit: entry - reference <= 1 s.
  commanded setpoint trajectory_setpoint position x, y (the setpoint the position controller receives).  Samples whose
                     position is NaN (velocity-only offboard setpoints, before the failsafe action publishes a position) are
                     EXCLUDED from the deviation (no position is commanded, so no position deviation exists); their fraction
                     in the window is reported.  Informational only: for them a reference is built by integrating the
                     velocity setpoint from the last valid setpoint position (or, if none, from the truth at the first NaN
                     sample); it does not enter the verdict.
  ground truth       vehicle_local_position_groundtruth x, y (NED, origin at spawn) + OFFSET, where OFFSET = median(estimator
                     local position - truth) over the hover [T0-8 s, T0-0.5 s] before the event schedule (the setpoints are in
                     the estimator local frame, which differs from truth by the EKF start error, a few cm).
  window             failsafe entry until the next nav_state change, the next kill event, or 15 s, whichever is first.
  excursion          max over window of |truth_aligned(t) - setpoint_xy(t)| at the setpoint sample times (valid positions).
  speed at onset     truth horizontal speed at the event applied time (about 3 m/s).
  verdict            PASS iff entry - reference <= 1 s and excursion <= 1 m (and some valid setpoint sample in the window).
"""
import json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from g5_events import first_rise  # noqa: E402
from g5_rows_check import load, param_at, entry_time, ACT_NAME, OBL_NAME, NAV  # noqa: E402

WIN_MAX_S = 15.0
ALIGN_PRE_S = (8.0, 0.5)
ENTRY_LIMIT_S = 1.0
EXC_LIMIT_M = 1.0
NAV_NAME = {2: "posctl", 3: "auto_mission", 4: "hold", 5: "return", 14: "offboard", 18: "land"}


def _a(d, k):
    return np.asarray(d[k], dtype=float)


def frame_offset(est_t, est_xy, truth_t, truth_xy, t_from, t_to):
    """median(estimator - truth) per axis over [t_from, t_to] (us); estimator samples, truth interpolated."""
    m = (est_t >= t_from) & (est_t <= t_to)
    if m.sum() < 5:
        return None
    tx = np.interp(est_t[m], truth_t, truth_xy[:, 0])
    ty = np.interp(est_t[m], truth_t, truth_xy[:, 1])
    return np.array([np.median(est_xy[m, 0] - tx), np.median(est_xy[m, 1] - ty)])


def find_entry(vs_t, vs_nav, vs_failsafe, t_from, t_to):
    """(t_entry, nav_entered, how): first nav_state change in (t_from, t_to]; else first failsafe rise."""
    for i in range(1, len(vs_t)):
        if t_from <= vs_t[i] <= t_to and vs_nav[i] != vs_nav[i - 1]:
            return int(vs_t[i]), int(vs_nav[i]), f"nav_state {int(vs_nav[i-1])}->{int(vs_nav[i])}"
    if vs_failsafe is not None:
        r = first_rise(vs_t, vs_failsafe, t_from)
        if r is not None and r <= t_to:
            return r, int(vs_nav[min(int(np.searchsorted(vs_t, r)), len(vs_nav) - 1)]), "failsafe rise (nav_state unchanged)"
    return None, None, "no nav_state change or failsafe rise"


def window_end(vs_t, vs_nav, t_entry, kill_t=None, max_s=WIN_MAX_S):
    """end of the window (us) and why: next nav_state change, kill event, or max_s."""
    end, why = t_entry + max_s * 1e6, f"{max_s:g} s"
    for i in range(1, len(vs_t)):
        if vs_t[i] > t_entry and vs_nav[i] != vs_nav[i - 1]:
            if vs_t[i] < end:
                end, why = int(vs_t[i]), f"nav_state change to {int(vs_nav[i])}"
            break
    if kill_t is not None and t_entry < kill_t < end:
        end, why = int(kill_t), "kill event"
    return end, why


def deviation(truth_t, truth_xy, sp_t, sp_pos, sp_vel, offset, t0, t1):
    """Horizontal deviation truth+offset vs trajectory_setpoint over [t0, t1] (us).
    Returns dict: n, n_nan, nan_frac, max_dev (valid-position samples), t_max, max_dev_vint (velocity-integrated reference
    over NaN segments, info only; None when no NaN)."""
    m = (sp_t >= t0) & (sp_t <= t1)
    t, p, v = sp_t[m], sp_pos[m], sp_vel[m]
    n = int(m.sum())
    if n == 0:
        return {"n": 0, "n_nan": 0, "nan_frac": None, "max_dev": None, "t_max": None, "max_dev_vint": None}
    tr = np.stack([np.interp(t, truth_t, truth_xy[:, 0]), np.interp(t, truth_t, truth_xy[:, 1])], 1) + offset
    nan = ~np.isfinite(p).all(1)
    out = {"n": n, "n_nan": int(nan.sum()), "nan_frac": float(nan.mean()), "max_dev": None, "t_max": None,
           "max_dev_vint": None}
    if (~nan).any():
        d = np.linalg.norm(tr[~nan] - p[~nan], axis=1)
        i = int(np.argmax(d))
        out["max_dev"], out["t_max"] = float(d[i]), int(t[~nan][i])
    if nan.any():  # info: velocity-only samples, position reference integrated from the last valid / first truth
        ref = np.empty_like(p)
        last, lt, lv = None, None, np.zeros(2)
        for i in range(n):
            if not nan[i]:
                last, lt, ref[i] = p[i].copy(), t[i], p[i]
                continue
            if last is None:
                last, lt = tr[i].copy(), t[i]
            v_i = np.nan_to_num(v[i])
            last = last + v_i * (t[i] - lt) * 1e-6
            lt = t[i]
            ref[i] = last
        out["max_dev_vint"] = float(np.linalg.norm(tr - ref, axis=1).max())
    return out


def verdict(dt_s, exc, nav_entered, want_nav):
    ok = dt_s is not None and dt_s <= ENTRY_LIMIT_S and exc is not None and exc <= EXC_LIMIT_M
    if exc is None or dt_s is None:
        return "NOT-COMPUTED"
    return "PASS" if ok else "FAIL"


def timeout_ref(L, name, evd, params, changes):
    """(timeout_us, text, nm, want_nav) copied from g5_rows_check.g58 (same definitions)."""
    tap = evd[name]["t_applied_us"]
    P = lambda k, d=None: param_at(params, changes, k, tap, d)
    if name == "rc_loss":
        tmo, nm = P("COM_RC_LOSS_T"), ACT_NAME.get(P("NAV_RCL_ACT"))
        ff = L["failsafe_flags"]
        r = first_rise(_a(ff, "timestamp"), _a(ff, "manual_control_signal_lost"), tap)
        if r is None:
            return None, "no manual_control_signal_lost rise", nm, NAV.get(nm)
        return r - tmo * 1e6, f"flag rise {r/1e6:.3f} s - {tmo} s", nm, NAV.get(nm)
    if name == "link_loss":
        tmo, nm = P("COM_DL_LOSS_T"), ACT_NAME.get(P("NAV_DLL_ACT"))
    else:
        tmo, nm = P("COM_OF_LOSS_T"), OBL_NAME.get(P("COM_OBL_RC_ACT"))
    t_e, _, _ = entry_time(L, tap, link=(name == "link_loss"))
    if t_e is None:
        return None, "no failsafe entry found", nm, NAV.get(nm)
    if name == "link_loss":
        ts = L["tel_gcs_ts"]
        ts = ts[(ts >= tap - 3e6) & (ts < t_e)]
        lab = "last telemetry_status gcs heartbeat"
    else:
        ts = _a(L["offboard_control_mode"], "timestamp")
        ts = ts[(ts >= evd.get("offboard_mode", evd[name])["t_applied_us"]) & (ts < t_e)]
        lab = "last offboard_control_mode"
    if len(ts) == 0:
        return None, f"no {lab} sample", nm, NAV.get(nm)
    onset = int(ts.max())
    return onset + tmo * 1e6, f"{lab} {onset/1e6:.3f} s + {tmo} s", nm, NAV.get(nm)


def analyse(d):
    from pyulog import ULog
    L, meta, params, changes = load(d)
    ul = ULog(os.path.join(d, "flight.ulg"))
    U = {x.name: x.data for x in ul.data_list if x.multi_id == 0}
    ts_ = U["trajectory_setpoint"]
    sp_t = _a(ts_, "timestamp")
    sp_pos = np.stack([_a(ts_, "position[0]"), _a(ts_, "position[1]")], 1)
    sp_vel = np.stack([_a(ts_, "velocity[0]"), _a(ts_, "velocity[1]")], 1)
    g = U["vehicle_local_position_groundtruth"]
    g_t, g_xy = _a(g, "timestamp"), np.stack([_a(g, "x"), _a(g, "y")], 1)
    g_v = np.stack([_a(g, "vx"), _a(g, "vy")], 1)
    lp = U["vehicle_local_position"]
    T0 = meta["g5_T0_us"]
    off = frame_offset(_a(lp, "timestamp"), np.stack([_a(lp, "x"), _a(lp, "y")], 1), g_t, g_xy,
                       T0 - ALIGN_PRE_S[0] * 1e6, T0 - ALIGN_PRE_S[1] * 1e6)
    if off is None:
        off = np.zeros(2)
    vs = L["vehicle_status"]
    vs_t, vs_nav = _a(vs, "timestamp"), _a(vs, "nav_state")
    vs_fs = _a(vs, "failsafe") if "failsafe" in vs else None
    ev = meta["g5_events"]
    evd = {e["name"]: e for e in ev}
    kill_t = evd["kill"]["t_applied_us"] if "kill" in evd else None
    rows = []
    for name in ("rc_loss", "link_loss", "offboard_loss"):
        r = {"event": name}
        if name not in evd:
            r.update(status="NOT-COMPUTED", text="event not in run.json"); rows.append(r); continue
        tap = evd[name]["t_applied_us"]
        tref, rtxt, nm, want = timeout_ref(L, name, evd, params, changes)
        t_e, nav, how = find_entry(vs_t, vs_nav, vs_fs, tap, tap + 12e6)
        if tref is None or t_e is None:
            r.update(status="NOT-COMPUTED", text=rtxt if tref is None else how); rows.append(r); continue
        flag_t, _, flag_how = entry_time(L, tap, link=(name == "link_loss"))
        dt = (t_e - tref) / 1e6
        t_end, why = window_end(vs_t, vs_nav, t_e, kill_t)
        dev = deviation(g_t, g_xy, sp_t, sp_pos, sp_vel, off, t_e, t_end)
        i = int(np.searchsorted(g_t, tap))
        spd = float(np.hypot(*g_v[min(i, len(g_t) - 1)]))
        exc = dev["max_dev"]
        st = verdict(dt, exc, nav, want)
        r.update(status=st, ref_s=tref / 1e6, ref_text=rtxt, entry_s=t_e / 1e6, entry_how=how, nav=nav,
                 configured=nm, configured_nav=want, entry_minus_ref_s=dt, flag_s=None if flag_t is None else flag_t / 1e6,
                 flag_how=flag_how, win_s=(t_end - t_e) / 1e6, win_end=why, speed_onset=spd, offset=[float(x) for x in off],
                 **{k: dev[k] for k in ("n", "n_nan", "nan_frac", "max_dev", "max_dev_vint")},
                 t_max_s=None if dev["t_max"] is None else dev["t_max"] / 1e6)
        rows.append(r)
    return rows


def fmt(r):
    if "entry_s" not in r:
        return f"NOT-COMPUTED {r['event']}: {r.get('text')}"
    nm = NAV_NAME.get(r["nav"], r["nav"])
    act = "configured action entered" if r["nav"] == r["configured_nav"] else f"configured {r['configured']} (nav {r['configured_nav']}) NOT entered"
    ex = "n/a" if r["max_dev"] is None else f"{r['max_dev']:.3f}"
    vi = "" if r["max_dev_vint"] is None else f"; velocity-integrated ref over NaN samples (info) {r['max_dev_vint']:.3f} m"
    return (f"{r['status']} {r['event']}: ref {r['ref_s']:.3f} s ({r['ref_text']}); entry {r['entry_s']:.3f} s via {r['entry_how']} "
            f"-> nav {r['nav']} ({nm}), {act}; entry-ref {r['entry_minus_ref_s']*1000:.0f} ms (<= 1000); gcs/failsafe flag at "
            f"{r['flag_s'] if r['flag_s'] is None else round(r['flag_s'], 3)} s; window {r['win_s']:.2f} s (end: {r['win_end']}); "
            f"setpoint samples {r['n']}, NaN position {r['n_nan']} ({100*r['nan_frac']:.1f} %); excursion {ex} m (<= 1)"
            f"{vi}; speed at onset {r['speed_onset']:.2f} m/s; frame offset est-truth [{r['offset'][0]:.3f}, {r['offset'][1]:.3f}] m")


def main(a):
    out = None
    if "--out" in a:
        i = a.index("--out"); out = a[i + 1]; a = a[:i] + a[i + 2:]
    d = a[0]
    rows = analyse(d)
    lines = [f"== {d}"] + [fmt(r) for r in rows]
    print("\n".join(lines))
    if out:
        open(out, "w").write("\n".join(lines) + "\n")
        json.dump(rows, open(os.path.splitext(out)[0] + ".json", "w"), indent=1, default=float)
    return rows


if __name__ == "__main__":
    main(sys.argv[1:])

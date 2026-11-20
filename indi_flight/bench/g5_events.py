#!/usr/bin/env python3
"""G5 event injector + G1.5 verdicts, firmware-free (S142).

Fly (inside docker, same args as run_scenario.py, scenario is forced):
  python3 indi_flight/bench/g5_events.py --controller indi --model quad5in --seed 1 --speed 4 --sim v2 \
     --gps-dly 110 --gnss-delay 110 --params <params> --out <dir>
Check (host, pyulog):  python3 indi_flight/bench/g5_events.py --check <dir>

Events (sim time relative to the hold start T0, in one AUTO-hold flight at 3 m):
  ekf_yaw (MAV_CMD_EXTERNAL_ATTITUDE_ESTIMATE = 620, +5 deg), ekf_xy (MAV_CMD_EXTERNAL_POSITION_ESTIMATE 1 m),
  rc_loss (stop RC_CHANNELS_OVERRIDE), link_loss (stop GCS HEARTBEAT), offboard_loss (stop setpoints),
  kill (RC kill switch ch7) -> disarm -> unkill -> re-arm -> take-off -> land.
NOT INJECTABLE without firmware: maybe_landed, ekf z reset (see README).
"""
import json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

ALT = 3.0
STEP_US = 1250  # physics step 1.25 ms (run.json physics_step_s)
TIMES = dict(yaw=3.0, xy=12.0, rc=21.0, rc_len=3.5, hb=33.0, hb_len=7.0, ob_pre=48.0, ob=51.0, ob_stop=55.0,
             ob_hold=61.0, kill=70.0)
MOVING = False  # --moving: the three losses at 3 m/s (offboard velocity setpoint) instead of hover (S146)
MV = dict(vel=3.0, leg=18.0, ob_pre=2.0, loss=9.0, t0=3.0)  # leg k starts at t0 + k*leg (rel. T0); loss at start+loss
FS_PARAMS = {"COM_RC_IN_MODE": 0, "COM_RCL_EXCEPT": 0, "COM_DLL_EXCEPT": 0, "NAV_RCL_ACT": 1, "NAV_DLL_ACT": 1,
             "COM_OBL_RC_ACT": 5, "COM_RC_OVERRIDE": 0, "COM_RC_LOSS_T": 0.5, "COM_DL_LOSS_T": 3, "RC_MAP_ROLL": 1, "RC_MAP_PITCH": 2,
             "RC_MAP_THROTTLE": 3, "RC_MAP_YAW": 4, "RC_MAP_KILL_SW": 7, "RC_CHAN_CNT": 8, "MIS_TAKEOFF_ALT": ALT}


# ---------------------------------------------------------------- flight (runs inside the sim container)
def g5_flight(sim, a, sc, meta):
    import run_scenario as rs
    evs = meta["g5_events"] = []
    ph = meta["auto_phases"] = []
    sim.mode_log, sim.mode_log_last = [], None
    st = {"rc": True, "hb": True, "ob": False, "kill": False, "rc_t": -9.0, "hb_t": -9.0, "pend": []}

    def mark(n):
        ph.append({"name": n, "t_us": int(sim.t * 1e6)})

    def ev(name, t_cmd, **kw):
        # commanded time = the schedule time of the event being dispatched (key2 S146 B1: --moving reused hover times)
        t_cmd = st.get("t_cmd", t_cmd)
        evs.append({"name": name, "t_cmd_us": int(round(t_cmd * 1e6)), "t_applied_us": int(sim.t * 1e6), **kw})

    def tick():
        t = sim.t
        if st["rc"] and t - st["rc_t"] >= 0.0199:
            ch = [1500, 1500, 1000, 1500, 1500, 1500, 2000 if st["kill"] else 1000, 1500]
            sim.log_send("rc_override", f"kill={int(st['kill'])}")
            sim.mav.mav.rc_channels_override_send(sim.sysid, 1, *ch, *([65535] * 10))
            st["rc_t"] = t
        if st["hb"] and t - st["hb_t"] >= 1.0:
            sim.mav.mav.heartbeat_send(6, 8, 0, 0, 4)  # MAV_TYPE_GCS
            st["hb_t"] = t
        if st["ob"] and sim.pos:
            if "vel" in st:
                sim.send_vel(st["vel"], st["hold_yaw"])
            else:
                sim.send_pos(sim.pos, sim.yaw) if "hold_ned" not in st else sim.send_pos(st["hold_ned"], st["hold_yaw"])
        while st["pend"] and t >= st["pend"][0][0]:
            st["t_cmd"], fn = st["pend"].pop(0)
            fn()
            del st["t_cmd"]  # events sent outside the schedule (unkill, rearm, takeoff2) keep their own time

    def at(t_rel, fn):
        st["pend"].append((T0 + t_rel, fn))
        st["pend"].sort(key=lambda x: x[0])

    for k, v in FS_PARAMS.items():
        try:
            sim.set_param(k, v)
            meta["params_applied"][k] = v
        except rs.RunError as e:  # a renamed or absent param must not end the flight; listed in run.json
            meta.setdefault("params_missing", []).append(k)
            print("param skipped:", k, str(e)[:80], file=sys.stderr)
    sim.run(1.0, sp=tick, what="g5_settle")
    mark("armed")
    if sim.gpos is None:
        sim.run(3.0, sp=tick, what="wait_gpos")
    sim.sp_period = 0.0  # tick on every ATTITUDE
    sim.cmd(511, 30, 1250, wait_ack=False)  # ATTITUDE at 800 Hz = one physics step, to shrink the tick-limited applied time
    for msg_id, hz in ((33, 50), (245, 2)):
        sim.cmd(511, msg_id, 1e6 / hz, wait_ack=False)
    alt_amsl = sim.gpos_alt + ALT
    if not sim.cmd(22, float("nan"), 0, 0, float("nan"), float("nan"), float("nan"), alt_amsl):
        raise rs.RunError("takeoff rejected")
    mark("takeoff_cmd")
    sim.run(None, until=lambda: sim.pos and sim.pos[2] <= -(ALT - 0.3), sp=tick, wall_timeout=120 + 120 / a.speed,
            what="g5_climb")
    mark("takeoff_done")
    T0 = sim.t + 5.0
    meta["g5_T0_us"] = int(T0 * 1e6)

    def f_yaw():
        sim.cmd(620, 0, 0, math.degrees(sim.yaw) + 5.0, 0, 0, 0, 1.0, wait_ack=False)
        ev("ekf_yaw", T0 + TIMES["yaw"], cmd_deg=5.0)

    def f_xy():
        lat, lon = sim.gpos[0] * 1e-7, sim.gpos[1] * 1e-7
        n, e = 0.6, 0.8
        nlat = lat + math.degrees(n / 6371000.0)
        nlon = lon + math.degrees(e / (6371000.0 * math.cos(math.radians(lat))))
        sim.mav.mav.command_int_send(sim.sysid, 1, 0, 43003, 0, 0, 0, 0, 0.5, 0, int(round(nlat * 1e7)),
                                     int(round(nlon * 1e7)), float(sim.gpos_alt))
        ev("ekf_xy", T0 + TIMES["xy"], cmd_m=1.0, cmd_ne=[n, e])

    def f_rc_off():
        st["rc"] = False
        ev("rc_loss", T0 + TIMES["rc"], last_msg_us=int(st["rc_t"] * 1e6))

    def f_rc_on():
        st["rc"] = True
        ev("rc_resume", T0 + TIMES["rc"] + TIMES["rc_len"])

    def f_hb_off():
        st["hb"] = False
        ev("link_loss", T0 + TIMES["hb"], last_msg_us=int(st["hb_t"] * 1e6))

    def f_hb_on():
        st["hb"] = True
        st["hb_t"] = -9.0
        ev("link_resume", T0 + TIMES["hb"] + TIMES["hb_len"])

    def f_ob_pre():
        st["hold_ned"], st["hold_yaw"] = sim.pos, sim.yaw
        st["ob"] = True
        ev("offboard_stream_on", T0 + TIMES["ob_pre"])

    def f_ob_mode():
        sim.cmd(176, 1, 6, wait_ack=False)
        ev("offboard_mode", T0 + TIMES["ob"])

    def f_ob_stop():
        st["ob"] = False
        st.pop("vel", None)  # key2 S146 M1: no stale velocity setpoint if the stream is ever restarted
        ev("offboard_loss", T0 + TIMES["ob_stop"])

    def f_ob_hold():
        sim.cmd(176, 1, 4, 3, wait_ack=False)
        ev("hold_mode", T0 + TIMES["ob_hold"])

    def f_kill():
        st["kill"] = True
        ev("kill", T0 + TIMES["kill"])

    def mv_leg(k, loss_fn, name):
        s0 = MV["t0"] + k * MV["leg"]
        sgn = 1.0 if k % 2 == 0 else -1.0  # out and back along north

        def on():
            st["hold_yaw"], st["vel"], st["ob"] = sim.yaw, (sgn * MV["vel"], 0.0, 0.0), True
            ev("offboard_stream_on", T0 + s0)

        at(s0, on)
        at(s0 + MV["ob_pre"], f_ob_mode)
        at(s0 + MV["loss"], loss_fn)
        return s0 + MV["loss"]

    if MOVING:
        mv_leg(0, f_rc_off, "rc")
        at(MV["t0"] + MV["loss"] + TIMES["rc_len"], f_rc_on)
        mv_leg(1, f_hb_off, "hb")
        at(MV["t0"] + MV["leg"] + MV["loss"] + TIMES["hb_len"], f_hb_on)
        t3 = mv_leg(2, f_ob_stop, "ob")
        at(t3 + 6.0, f_ob_hold)
        at(t3 + 12.0, f_kill)
    else:
        at(TIMES["yaw"], f_yaw)
        at(TIMES["xy"], f_xy)
        at(TIMES["rc"], f_rc_off)
        at(TIMES["rc"] + TIMES["rc_len"], f_rc_on)
        at(TIMES["hb"], f_hb_off)
        at(TIMES["hb"] + TIMES["hb_len"], f_hb_on)
        at(TIMES["ob_pre"], f_ob_pre)
        at(TIMES["ob"], f_ob_mode)
        at(TIMES["ob_stop"], f_ob_stop)
        at(TIMES["ob_hold"], f_ob_hold)
        at(TIMES["kill"], f_kill)
    sim.run(None, until=lambda: not st["pend"], sp=tick, wall_timeout=120 + 150 / a.speed, what="g5_events")
    mark("kill_sent")
    sim.run(None, until=lambda: not sim.armed, sp=tick, wall_timeout=120 + 60 / a.speed, what="g5_disarm")
    mark("disarmed")
    sim.run(2.0, sp=tick, what="g5_ground")
    st["kill"] = False
    ev("unkill", sim.t)
    sim.run(2.0, sp=tick, what="g5_unkill")
    for i in range(20):
        if sim.cmd(400, 1):
            break
        meta["rearm_rejected"] = meta.get("rearm_rejected", 0) + 1
        sim.run(1.0, sp=tick, what="rearm_retry")
    else:
        raise rs.RunError("re-arm rejected 20 times")
    ev("rearm", sim.t)
    sim.run(None, until=lambda: sim.armed, sp=tick, wall_timeout=30, what="rearmed")
    sim.run(1.0, sp=tick, what="g5_rearm_settle")
    if not sim.cmd(22, float("nan"), 0, 0, float("nan"), float("nan"), float("nan"), sim.gpos_alt + ALT):
        raise rs.RunError("second takeoff rejected")
    ev("takeoff2", sim.t)
    sim.run(None, until=lambda: sim.pos and sim.pos[2] <= -(ALT - 0.3), sp=tick, wall_timeout=120 + 120 / a.speed,
            what="g5_climb2")
    mark("takeoff2_done")
    sim.run(4.0, sp=tick, what="g5_hover2")
    sim.cmd(21, 0, 0, 0, float("nan"), float("nan"), float("nan"), 0)
    sim.run(None, until=lambda: not sim.armed, sp=tick, wall_timeout=120 + 120 / a.speed, what="g5_land")
    sim.run(2.0, what="post_disarm")
    meta["mode_log"] = sim.mode_log


# ---------------------------------------------------------------- verdicts (pure, host side)
def first_rise(t, x, t_from_us, thr=0.5):
    """first t >= t_from_us where x crosses above thr after being <= thr (or None)."""
    prev = None
    for ti, xi in zip(t, x):
        if ti >= t_from_us and xi > thr and (prev is None or prev <= thr):
            return int(ti)
        prev = xi
    return None


def first_counter_step(t, cnt, t_from_us):
    """(t, index) of the first sample at/after t_from_us whose counter differs from the previous sample."""
    for i in range(1, len(t)):
        if t[i] >= t_from_us and cnt[i] != cnt[i - 1]:
            return int(t[i]), i
    return None, None


def cmd_applied(log, e, cid):
    """firmware receipt time: first vehicle_command row with this command id at/after the runner send time (fallback: runner time)."""
    vc = log.get("vehicle_command", {})
    for t, c in zip(vc.get("timestamp", []), vc.get("command", [])):
        if c == cid and t >= e["t_cmd_us"]:
            return int(t)
    return e["t_applied_us"]


def mk_verdict(name, t_cmd_us, t_app_us, t_eff_us, mag=None, mag_exp=None, tol=0.02, step_us=STEP_US, note=""):
    """one G1.5 line: effect visible, magnitude within tol (relative), applied time within one physics step."""
    why = []
    dt_app = t_app_us - t_cmd_us
    if t_eff_us is None:
        why.append("effect not visible in log")
    if abs(dt_app) > step_us:
        why.append(f"applied-commanded {dt_app / 1e3:.2f} ms > {step_us / 1e3:.2f} ms step")
    if mag is not None and mag_exp:
        err = abs(mag - mag_exp) / abs(mag_exp)
        if err > tol:
            why.append(f"magnitude {mag:.4g} vs {mag_exp:.4g} ({100 * err:.1f} % > {100 * tol:.0f} %)")
    ms = "" if mag is None else f" mag={mag:.4g}" + ("" if not mag_exp else f"/{mag_exp:.4g}")
    eff = "" if t_eff_us is None else f" effect_after_applied={(t_eff_us - t_app_us) / 1e3:.1f}ms"
    return f"G1.5 {name}: {'FAIL' if why else 'PASS'} applied_dt={dt_app / 1e3:.2f}ms{ms}{eff}" \
           + (f" [{'; '.join(why)}]" if why else "") + (f" ({note})" if note else "")


def yaw_of(w, x, y, z):
    return math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))


def analyse(log, events, step_us=STEP_US):
    """log: {topic: {field: list}}; events: list of event dicts. Returns list of verdict lines."""
    byname = {e["name"]: e for e in events}
    out = []
    lp = log.get("vehicle_local_position", {})
    fs = log.get("failsafe_flags", {})
    aa = log.get("actuator_armed", {})
    ao = log.get("actuator_outputs", {})
    out.append("G1.5 maybe_landed: NOT INJECTABLE firmware-free (land detector needs min thrust + ground_contact + commanded descent)")
    out.append("G1.5 ekf_z (0.5 m): NOT INJECTABLE firmware-free (external position hard reset is horizontal only)")
    e = byname.get("ekf_yaw")
    va = log.get("vehicle_attitude", {})
    if e is None or not va:
        out.append("G1.5 ekf_yaw: FAIL not flown or vehicle_attitude missing")
    else:  # largest one-sample yaw step after the firmware received the command; effect time = quat_reset_counter step
        ta = cmd_applied(log, e, 620)
        yaw = [yaw_of(va["q[0]"][i], va["q[1]"][i], va["q[2]"][i], va["q[3]"][i]) for i in range(len(va["timestamp"]))]
        best, tb = 0.0, None
        for i in range(1, len(yaw)):
            if ta - 20000 <= va["timestamp"][i] <= ta + 300000:
                d = math.degrees(math.atan2(math.sin(yaw[i] - yaw[i - 1]), math.cos(yaw[i] - yaw[i - 1])))
                if abs(d) > abs(best):
                    best, tb = d, int(va["timestamp"][i])
        if "quat_reset_counter" in va:
            tb, _ = first_counter_step(va["timestamp"], va["quat_reset_counter"], ta - 100000)
        out.append(mk_verdict("ekf_yaw", e["t_cmd_us"], ta, tb if abs(best) > 1.0 else None, abs(best), 5.0,
                              step_us=step_us, note="applied=vehicle_command 620, effect=quat_reset_counter step"))
    for nm, cnt, dkeys, key, exp in (("ekf_xy", "xy_reset_counter", ["delta_xy[0]", "delta_xy[1]"], "cmd_m", 1.0),):
        e = byname.get(nm)
        if e is None or not lp:
            out.append(f"G1.5 {nm}: FAIL not flown or topic missing")
            continue
        ta = cmd_applied(log, e, 43003)
        t_eff, i = first_counter_step(lp["timestamp"], lp[cnt], ta - 100000)
        mag = None
        if i is not None:
            mag = math.hypot(*[lp[k][i] for k in dkeys])
        out.append(mk_verdict(nm, e["t_cmd_us"], ta, t_eff, mag, exp, step_us=step_us))
    for nm, flag, tout in (("rc_loss", "manual_control_signal_lost", 0.5), ("link_loss", "gcs_connection_lost", 3.0),
                           ("offboard_loss", "offboard_control_signal_lost", 1.0)):
        e = byname.get(nm)
        if e is None or not fs or flag not in fs:
            out.append(f"G1.5 {nm}: FAIL not flown or {flag} not logged")
            continue
        t_eff = first_rise(fs["timestamp"], fs[flag], e["t_cmd_us"] - 100000)  # applied = failsafe flag rise
        line = mk_verdict(nm, e["t_cmd_us"], t_eff if t_eff is not None else e["t_applied_us"], t_eff,
                          note="applied=failsafe flag rise; failsafe onset below")
        if t_eff is not None:
            onset = (t_eff - e.get("last_msg_us", e["t_applied_us"])) / 1e6
            line += f" | onset (not G1.5): flag {onset:.2f}s after last msg, timeout {tout}s"
        out.append(line)
    e = byname.get("kill")
    if e is None or not aa:
        out.append("G1.5 kill: FAIL not flown or actuator_armed missing")
    else:
        t_k = first_rise(aa["timestamp"], aa["kill"], e["t_cmd_us"] - 100000)
        t_z = None
        if t_k is not None and ao:
            n = len(ao["timestamp"])
            for j in range(n):
                if ao["timestamp"][j] >= t_k and all(ao.get(f"output[{m}]", [1] * n)[j] <= 0 for m in range(4)):
                    t_z = int(ao["timestamp"][j])
                    break
        line = mk_verdict("kill", e["t_cmd_us"], t_k if t_k is not None else e["t_applied_us"], t_k, note="applied=kill flag")
        line += f" | motors 0 {'never' if t_z is None else f'{(t_z - t_k) / 1e3:.2f}ms after flag'} (G5.9)"
        if t_z is None:
            line = line.replace(": PASS", ": FAIL")
        out.append(line)
    return out


def load_ulog(path):
    from pyulog import ULog
    ul = ULog(path)
    log, rates = {}, []
    dur = (ul.last_timestamp - ul.start_timestamp) / 1e6
    for d in ul.data_list:
        if d.name in ("vehicle_local_position", "vehicle_attitude", "failsafe_flags", "actuator_armed", "actuator_outputs",
                      "actuator_motors", "vehicle_land_detected", "vehicle_status", "vehicle_command") and d.multi_id == 0:
            log[d.name] = {k: list(v) for k, v in d.data.items()}
            rates.append(f"{d.name}: {len(d.data['timestamp'])} samples, {len(d.data['timestamp']) / dur:.0f} Hz")
    return log, rates


def check(out_dir):
    meta = json.load(open(os.path.join(out_dir, "run.json")))
    log, rates = load_ulog(os.path.join(out_dir, "flight.ulg"))
    lines = ["logged rates: " + "; ".join(rates)] + analyse(log, meta.get("g5_events", []))
    ld = log.get("vehicle_land_detected")
    if ld:
        t0, t1 = meta.get("g5_T0_us", 0), min((e["t_applied_us"] for e in meta["g5_events"] if e["name"] == "kill"), default=0)
        ml = [m for t, m in zip(ld["timestamp"], ld["maybe_landed"]) if t0 <= t <= t1]
        lines.append(f"maybe_landed during hold (T0..kill): any true = {any(ml)} ({len(ml)} samples)")
    open(os.path.join(out_dir, "verdicts.txt"), "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


def main():
    if "--check" in sys.argv:
        return check(sys.argv[sys.argv.index("--check") + 1])
    global MOVING
    MOVING = "--moving" in sys.argv
    if MOVING:
        sys.argv.remove("--moving")
    import run_scenario as rs
    # S145 fix: event topics at every publication (interval 0) via the runner's logger_topics.txt, this flight only.
    # The runner writes "<entry> 0 0" per entry; telemetry_status is multi (mavlink instances 0..3): the newline
    # entries add instances 1..3 and the last line is completed by the runner into instance 0.
    rs.LOG_TOPICS += ["failsafe_flags", "actuator_outputs", "actuator_armed", "manual_control_switches",
                      "telemetry_status 0 1\ntelemetry_status 0 2\ntelemetry_status 0 3\ntelemetry_status"]
    rs.SCENARIOS["g5_events"] = {"mode": "auto", "auto": {}}
    rs.run_auto = g5_flight
    sys.argv += ["--scenario", "g5_events"]
    return rs.main()


if __name__ == "__main__":
    sys.exit(main())

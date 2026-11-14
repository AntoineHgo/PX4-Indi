#!/usr/bin/env python3
"""Disturbance injector for the SITL benchmark (T6 gust_x, T7 payload_add, H2 gust_diag, H3 com_shift). Runs INSIDE the px4-indi-sim container,
next to the runner, in the same network namespace as gz.

The ApplyLinkWrench system is loaded at runtime (world service /world/<w>/entity/system/add), no world/model file
is edited. A one-step wrench (topic /world/<w>/wrench; the persistent topic ACCUMULATES per message) is published on the x500 base_link as a function of gz SIM time, at every clock
message, so the profile does not depend on the speed factor. The profile starts at an onset that the runner writes to
a trigger file (JSON {"onset_px4_s": float}); onset is expressed in PX4/ULog time and converted with CLOCK_OFFSET_S.

  disturbance.py --profile gust_x|payload_add|gust_diag|com_shift --out DIR [--world default] [--model x500_0] [--stop-after S]

Writes DIR/disturbance.csv (sim_time_s, px4_time_s, fx, fy, fz, tx, ty, tz; world frame, applied at the CoM) and
DIR/disturbance.log. Ends on SIGTERM (clears the wrench) or when the profile ended + --stop-after.
"""
import argparse
import json
import math
import os
import signal
import sys
import time

# ---------------- constants (assumptions, see plan/disturbance_spec.md) ----------------
RHO = 1.225                 # kg/m^3
CD_A = 0.06                 # m^2, drag coefficient * frontal area of the x500 frame (assumption)
C_DRAG = 0.5 * RHO * CD_A   # F = C_DRAG * v * |v|
COP_Z = 0.05                # m, centre of pressure above the CoM (body z up)
WIND_RAMP_TO = 3.0          # m/s
WIND_RAMP_T = 2.0           # s
WIND_HOLD1_T = 10.0         # s
GUST_AMP = 6.0              # m/s, added on top of the base wind (peak total 9 m/s)
GUST_T = 1.0                # s, 1-cosine
WIND_HOLD2_T = 15.0         # s
GUST_DURATION = WIND_RAMP_T + WIND_HOLD1_T + GUST_T + WIND_HOLD2_T  # 28 s
X500_MASS_KG = 2.0 + 4 * 0.016076923076923075  # base_link + 4 rotor links (x500_base/model.sdf)
GRAVITY = 9.8               # gz world gravity (default.sdf)
PAYLOAD_FRAC = 0.25
PAYLOAD_DURATION = 30.0     # s, held until the end of the scenario window
# H2 gust_diag: same shape as gust_x, base wind and gust in different xy directions. Directions are where the air
# moves to, angle from world +x towards +y (deg), the convention of gust_x (+x = 0 deg).
DIAG_BASE_SPEED, DIAG_BASE_DIR = 4.0, 45.0
DIAG_GUST_AMP, DIAG_GUST_DIR, DIAG_GUST_T = 8.0, 120.0, 0.6
DIAG_DURATION = WIND_RAMP_T + WIND_HOLD1_T + DIAG_GUST_T + WIND_HOLD2_T  # 27.6 s
# H3 com_shift: payload_add with a smaller mass whose weight acts 5 cm off the CoM along +y. The offset is kept fixed
# in the world frame (level-hover approximation: the vehicle holds its spawn yaw and stays near level).
SHIFT_FRAC = 0.15
SHIFT_Y = 0.05              # m
# gz sim time minus PX4 (ULog / MAVLink time_boot_ms) time. Measured, see bench/RUNNER_NOTES.md.
CLOCK_OFFSET_S = 0.0


def wind_speed(t):
    """Wind speed (m/s, +x) at profile time t (s)."""
    if t < 0:
        return 0.0
    if t < WIND_RAMP_T:
        return WIND_RAMP_TO * t / WIND_RAMP_T
    t -= WIND_RAMP_T
    if t < WIND_HOLD1_T:
        return WIND_RAMP_TO
    t -= WIND_HOLD1_T
    if t < GUST_T:
        return WIND_RAMP_TO + GUST_AMP * 0.5 * (1.0 - math.cos(2.0 * math.pi * t / GUST_T))
    return WIND_RAMP_TO  # hold (profile end handled by the caller)


def gust_x(t):
    """Wrench (fx, fy, fz, tx, ty, tz) at the CoM, world frame, for profile time t."""
    v = wind_speed(t)
    f = (C_DRAG * v * abs(v), 0.0, 0.0)
    r = (0.0, 0.0, COP_Z)
    tq = (r[1] * f[2] - r[2] * f[1], r[2] * f[0] - r[0] * f[2], r[0] * f[1] - r[1] * f[0])
    return (*f, *tq)


def payload_add(t):
    fz = -PAYLOAD_FRAC * X500_MASS_KG * GRAVITY if t >= 0 else 0.0
    return (0.0, 0.0, fz, 0.0, 0.0, 0.0)


def wind_diag(t):
    """Wind vector (vx, vy) in m/s at profile time t for gust_diag."""
    if t < 0:
        return 0.0, 0.0
    base = DIAG_BASE_SPEED * min(t / WIND_RAMP_T, 1.0)
    t_g = t - WIND_RAMP_T - WIND_HOLD1_T
    gust = DIAG_GUST_AMP * 0.5 * (1.0 - math.cos(2.0 * math.pi * t_g / DIAG_GUST_T)) if 0 <= t_g < DIAG_GUST_T else 0.0
    b, g = math.radians(DIAG_BASE_DIR), math.radians(DIAG_GUST_DIR)
    return base * math.cos(b) + gust * math.cos(g), base * math.sin(b) + gust * math.sin(g)


def gust_diag(t):
    vx, vy = wind_diag(t)
    v = math.hypot(vx, vy)
    f = (C_DRAG * vx * v, C_DRAG * vy * v, 0.0)
    r = (0.0, 0.0, COP_Z)
    tq = (r[1] * f[2] - r[2] * f[1], r[2] * f[0] - r[0] * f[2], r[0] * f[1] - r[1] * f[0])
    return (*f, *tq)


def com_shift(t):
    fz = -SHIFT_FRAC * X500_MASS_KG * GRAVITY if t >= 0 else 0.0
    return (0.0, 0.0, fz, SHIFT_Y * fz, 0.0, 0.0)  # torque = (0, SHIFT_Y, 0) x (0, 0, fz)


PROFILES = {"gust_x": (gust_x, GUST_DURATION), "payload_add": (payload_add, PAYLOAD_DURATION),
            "gust_diag": (gust_diag, DIAG_DURATION), "com_shift": (com_shift, PAYLOAD_DURATION)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", required=True, choices=sorted(PROFILES))
    ap.add_argument("--out", required=True)
    ap.add_argument("--world", default="default")
    ap.add_argument("--model", default="x500_0")
    ap.add_argument("--link", default="base_link")
    ap.add_argument("--stop-after", type=float, default=30.0, help="exit this many sim s after the profile ended")
    ap.add_argument("--wall-timeout", type=float, default=900.0)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    trigger = os.path.join(a.out, "disturbance_trigger.json")

    from gz.msgs10.boolean_pb2 import Boolean
    from gz.msgs10.clock_pb2 import Clock
    from gz.msgs10.entity_pb2 import Entity
    from gz.msgs10.entity_factory_pb2 import EntityFactory  # noqa: F401  (ensures msgs are importable)
    from gz.msgs10.entity_wrench_pb2 import EntityWrench
    from gz.msgs10.stringmsg_pb2 import StringMsg  # noqa: F401
    from gz.transport13 import Node

    log = open(os.path.join(a.out, "disturbance.log"), "w", buffering=1)

    def say(*m):
        print(time.strftime("%H:%M:%S"), *m, file=log)

    node = Node()
    fn, dur = PROFILES[a.profile]
    w = f"/world/{a.world}"

    # ---- load the system at runtime ----
    # The python binding cannot build gz.msgs.Plugin ("No message class registered"), so the one-off service call
    # goes through the gz CLI. The ApplyLinkWrench topics are then driven from python.
    import subprocess
    req = ('entity {id: 1} plugins {filename: "gz-sim-apply-link-wrench-system" '
           'name: "gz::sim::systems::ApplyLinkWrench"}')
    ok = False
    for attempt in range(20):
        r = subprocess.run(["gz", "service", "-s", f"{w}/entity/system/add", "--reqtype", "gz.msgs.EntityPlugin_V",
                            "--reptype", "gz.msgs.Boolean", "--timeout", "3000", "--req", req],
                           capture_output=True, text=True)
        say(f"system add attempt {attempt}: rc={r.returncode} out={r.stdout.strip()!r}")
        if "true" in r.stdout:
            ok = True
            break
        time.sleep(1)
    if not ok:
        say("FAILED to add ApplyLinkWrench system")
        return 2
    time.sleep(1.0)

    pub = node.advertise(f"{w}/wrench", EntityWrench)  # one-step wrench, re-sent at every clock tick
    pub_clear = node.advertise(f"{w}/wrench/clear", Entity)
    time.sleep(1.0)

    def entity():
        e = Entity()
        e.name = f"{a.model}::{a.link}"
        e.type = Entity.LINK
        return e

    csv = open(os.path.join(a.out, "disturbance.csv"), "w", buffering=1)
    csv.write("sim_time_s,px4_time_s,fx,fy,fz,tx,ty,tz\n")
    state = {"onset": None, "t": None, "ended": False, "last_pub": None, "n": 0, "stop": False, "t_end_sim": None}
    wall0 = time.time()

    def apply(wr):
        m = EntityWrench()
        m.entity.CopyFrom(entity())
        m.wrench.force.x, m.wrench.force.y, m.wrench.force.z = wr[0:3]
        m.wrench.torque.x, m.wrench.torque.y, m.wrench.torque.z = wr[3:6]
        pub.publish(m)

    def on_clock(msg):
        t = msg.sim.sec + msg.sim.nsec * 1e-9
        state["t"] = t
        if state["onset"] is None:
            if os.path.exists(trigger):
                try:
                    state["onset"] = json.load(open(trigger))["onset_px4_s"] + CLOCK_OFFSET_S
                    say(f"trigger: onset gz sim time {state['onset']:.3f} (now {t:.3f})")
                except (ValueError, KeyError):
                    pass
            return
        tp = t - state["onset"]
        if tp < 0 or state["ended"]:
            return
        if tp >= dur:
            wr = (0.0,) * 6
            state["ended"], state["t_end_sim"] = True, t
            pub_clear.publish(entity())
            say(f"profile ended at sim {t:.3f}, wrench cleared")
        else:
            wr = fn(tp)
            apply(wr)
        state["n"] += 1
        csv.write(f"{t:.4f},{t - CLOCK_OFFSET_S:.4f}," + ",".join(f"{x:.5f}" for x in wr) + "\n")

    if not node.subscribe(Clock, f"{w}/clock", on_clock):
        say("subscribe to clock failed")
        return 3
    say(f"profile {a.profile}, duration {dur} s; waiting for trigger {trigger}")
    signal.signal(signal.SIGTERM, lambda *_: state.update(stop=True))
    signal.signal(signal.SIGINT, lambda *_: state.update(stop=True))
    while not state["stop"] and time.time() - wall0 < a.wall_timeout:
        if state["t_end_sim"] is not None and state["t"] - state["t_end_sim"] > a.stop_after:
            break
        time.sleep(0.2)
    pub_clear.publish(entity())
    say(f"exit, {state['n']} wrench updates")
    csv.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Disturbance injector for the SITL benchmark (T6 gust_x, T7 payload_add, H2 gust_diag, H3 com_shift). Runs INSIDE the px4-indi-sim container,
next to the runner, in the same network namespace as gz.

The ApplyLinkWrench system is normally already loaded by the gz server config (src/modules/simulation/gz_bridge/server.config, named by
$GZ_SIM_SERVER_CONFIG_PATH / $PX4_GZ_SERVER_CONFIG); then the runtime add is SKIPPED (a second instance applied every wrench twice, A-31).
Otherwise it is added at runtime (world service /world/<w>/entity/system/add; --add-system auto|yes|no). No world/model file is edited. A one-step wrench (topic /world/<w>/wrench; the persistent topic ACCUMULATES per message) is published on the x500 base_link as a function of gz SIM time, at every clock
message, so the profile does not depend on the speed factor. The profile starts at an onset that the runner writes to
a trigger file (JSON {"onset_px4_s": float}); onset is expressed in PX4/ULog time and converted with CLOCK_OFFSET_S.

  disturbance.py --profile gust_x|payload_add|gust_diag|com_shift|torque_steps --out DIR [--world default] [--model x500_0]
                 [--airframe x500|quad5in] [--sdf PATH] [--stop-after S]

Sizing (N1 C2): every profile is sized from the FLOWN airframe (mass = sum of link masses of its base SDF, base_link
inertia, frame drag CdA), not from x500 constants. --airframe defaults from --model (x500_0 -> x500, quad5in_0 -> quad5in);
--sdf overrides the SDF file. x500 numbers are unchanged from before (default --model x500_0). See
indi_flight/design/t132_disturbance_c2_s65.md.

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
# Per-airframe drag/geometry. cda = drag coefficient * frontal area (m^2), cop_z = centre of pressure above the CoM (m).
# x500: assumption of the original spec (unchanged). quad5in: UNVERIFIED assumption, the x500 values scaled by the frame
# size ratio (5-inch ~0.22 m motor diagonal vs x500 ~0.51 m): CdA ~ L^2 -> 0.06*0.43^2 = 0.011 -> 0.012 m^2 (consistent
# with the 0.01-0.02 m^2 usually quoted for a 5-inch freestyle quad with battery), cop_z ~ L -> 0.02 m. No measured source.
AIRFRAMES = {
    "x500": {"sdf": ("..", "..", "Tools", "simulation", "gz", "models", "x500_base", "model.sdf"), "cda": 0.06, "cop_z": 0.05,
             # fallback if the SDF is not readable (container mount): values of the SDF at T132 time
             "fallback": (2.0 + 4 * 0.016076923076923075, (0.02166666666666667, 0.02166666666666667, 0.04000000000000001))},
    "quad5in": {"sdf": ("..", "sim", "models", "quad5in_base", "model.sdf"), "cda": 0.012, "cop_z": 0.02,
                "fallback": (0.566 + 4 * 0.011, (1.022e-3, 1.122e-3, 1.944e-3))},
}
WIND_RAMP_TO = 3.0          # m/s
WIND_RAMP_T = 2.0           # s
WIND_HOLD1_T = 10.0         # s
GUST_AMP = 6.0              # m/s, added on top of the base wind (peak total 9 m/s)
GUST_T = 1.0                # s, 1-cosine
WIND_HOLD2_T = 15.0         # s
GUST_DURATION = WIND_RAMP_T + WIND_HOLD1_T + GUST_T + WIND_HOLD2_T  # 28 s
X500_MASS_KG = 2.0 + 4 * 0.016076923076923075  # base_link + 4 rotor links (x500_base/model.sdf); reference only
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


class Airframe:
    """Mass (sum of link masses), base_link inertia diagonal, CdA and CoP height of the flown vehicle."""

    def __init__(self, name, mass, inertia, cda, cop_z, source):
        self.name, self.mass, self.inertia, self.cda, self.cop_z, self.source = name, mass, inertia, cda, cop_z, source
        self.c_drag = 0.5 * RHO * cda   # F = c_drag * v * |v|


def parse_sdf(path):
    """(total mass of all links, base_link (ixx, iyy, izz)) from a model SDF."""
    import xml.etree.ElementTree as ET
    root = ET.parse(path).getroot()
    mass, inertia = 0.0, None
    for link in root.iter("link"):
        m = link.find("inertial/mass")
        if m is not None:
            mass += float(m.text)
        i = link.find("inertial/inertia")
        if link.get("name") == "base_link" and i is not None:
            inertia = tuple(float(i.find(k).text) for k in ("ixx", "iyy", "izz"))
    return mass, inertia


def load_airframe(name, sdf=None):
    spec = AIRFRAMES[name]
    path = sdf or os.path.join(os.path.dirname(os.path.abspath(__file__)), *spec["sdf"])
    try:
        mass, inertia = parse_sdf(path)
        src = path
        if inertia is None or mass <= 0:
            raise ValueError("no base_link inertial in SDF")
    except (OSError, ValueError, TypeError, AttributeError, SyntaxError):  # ParseError is a SyntaxError
        mass, inertia = spec["fallback"]
        src = "fallback constants (SDF not readable: %s)" % path
    return Airframe(name, mass, inertia, spec["cda"], spec["cop_z"], src)


def airframe_from_model(model):
    return "quad5in" if model.startswith("quad5in") else "x500"


# gz sim time minus PX4 (ULog / MAVLink time_boot_ms) time. Measured, see bench/RUNNER_NOTES.md.
CLOCK_OFFSET_S = 0.0


def wind_speed(t, steady=WIND_RAMP_TO, amp=GUST_AMP):
    """Wind speed (m/s, along the profile direction) at profile time t (s). Defaults = the original gust_x numbers."""
    if t < 0:
        return 0.0
    if t < WIND_RAMP_T:
        return steady * t / WIND_RAMP_T
    t -= WIND_RAMP_T
    if t < WIND_HOLD1_T:
        return steady
    t -= WIND_HOLD1_T
    if t < GUST_T:
        return steady + amp * 0.5 * (1.0 - math.cos(2.0 * math.pi * t / GUST_T))
    return steady  # hold (profile end handled by the caller)


def gust_x(t, af, steady=WIND_RAMP_TO, amp=GUST_AMP, dir_deg=0.0, vel=None):
    """Wrench (fx, fy, fz, tx, ty, tz) at the CoM, world frame, for profile time t. steady / amp (gust added on the steady
    wind) in m/s; dir_deg = where the air moves to, from world +x towards +y (gust_diag convention). Defaults: +x, 3 m/s,
    +6 m/s.
    vel = vehicle ground-truth world velocity (vx, vy, vz) m/s, same frame as the wind: the force is then the drag of the
    AIR-RELATIVE velocity, F = c_drag * (w - v) * |w - v| (vector form). The gz models (quad5in, x500) have no body drag
    (only the per-rotor rotorDragCoefficient), so the whole drag is injected here, not only the wind part. vel=None is the
    legacy pure force c_drag * w * |w| (v taken as 0; bit-identical to the old code)."""
    w = wind_speed(t, steady, amp)
    if vel is None:
        d = af.c_drag * w * abs(w)
        f = (d, 0.0, 0.0) if dir_deg == 0.0 else (d * math.cos(math.radians(dir_deg)), d * math.sin(math.radians(dir_deg)), 0.0)
    else:
        rel = (w * math.cos(math.radians(dir_deg)) - vel[0], w * math.sin(math.radians(dir_deg)) - vel[1], -vel[2])
        n = math.sqrt(rel[0] ** 2 + rel[1] ** 2 + rel[2] ** 2)
        f = (af.c_drag * rel[0] * n, af.c_drag * rel[1] * n, af.c_drag * rel[2] * n)
    r = (0.0, 0.0, af.cop_z)
    tq = (r[1] * f[2] - r[2] * f[1], r[2] * f[0] - r[0] * f[2], r[0] * f[1] - r[1] * f[0])
    return (*f, *tq)


def wind_profile_args(steady, peak, dir_deg):
    """CLI --wind-steady/--wind-peak/--wind-dir (any may be None) -> (steady, gust amp ABOVE steady, dir_deg).
    peak is the TOTAL wind in the gust, so amp = peak - steady. Raises ValueError unless 0 <= steady <= peak."""
    st = WIND_RAMP_TO if steady is None else steady
    pk = st + GUST_AMP if peak is None else peak
    if st < 0 or pk < st:
        raise ValueError("need 0 <= --wind-steady <= --wind-peak")
    return st, pk - st, (dir_deg or 0.0)


class PoseVelocity:
    """Finite-difference world velocity of a pose stream, deterministic in the sample times (sim time, s). update() returns
    None until two samples at least min_dt apart exist; the velocity is then held between differences."""

    def __init__(self, min_dt=0.004):
        self.min_dt, self.last, self.vel = min_dt, None, None

    def update(self, t, pos):
        if self.last is None:
            self.last = (t, tuple(pos))
        elif t - self.last[0] >= self.min_dt:
            dt = t - self.last[0]
            self.vel = tuple((pos[i] - self.last[1][i]) / dt for i in range(3))
            self.last = (t, tuple(pos))
        return self.vel


def payload_add(t, af):
    fz = -PAYLOAD_FRAC * af.mass * GRAVITY if t >= 0 else 0.0
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


def gust_diag(t, af):
    vx, vy = wind_diag(t)
    v = math.hypot(vx, vy)
    f = (af.c_drag * vx * v, af.c_drag * vy * v, 0.0)
    r = (0.0, 0.0, af.cop_z)
    tq = (r[1] * f[2] - r[2] * f[1], r[2] * f[0] - r[0] * f[2], r[0] * f[1] - r[1] * f[0])
    return (*f, *tq)


def com_shift(t, af):
    fz = -SHIFT_FRAC * af.mass * GRAVITY if t >= 0 else 0.0
    return (0.0, 0.0, fz, SHIFT_Y * fz, 0.0, 0.0)  # torque = (0, SHIFT_Y, 0) x (0, 0, fz)


# torque_steps: pure body-torque steps at near-level hover (world ~ body axes at spawn yaw). TQ_STEPS are the quad5in
# values (~4-5 % of the INDI G1 authority: roll 1757*1.4e-3 = 2.5 N m, yaw 205*2.7e-3 = 0.55 N m per unit command), i.e. the
# reference. For another airframe the torque scales with base_link inertia (same angular-acceleration step):
# tq = TQ_STEPS * I_axis / TQ_REF_INERTIA (quad5in -> factor 1, numbers unchanged).
TQ_REF_INERTIA = (1.022e-3, 1.122e-3, 1.944e-3)
TQ_STEPS = [(0.0, 2.0, (0.10, 0.0, 0.0)), (4.0, 6.0, (0.0, 0.10, 0.0)), (8.0, 10.0, (0.0, 0.0, 0.03))]
TQ_DURATION = 12.0


def torque_steps(t, af):
    for t0, t1, tq in TQ_STEPS:
        if t0 <= t < t1:
            return (0.0, 0.0, 0.0, *(q * i / r for q, i, r in zip(tq, af.inertia, TQ_REF_INERTIA)))
    return (0.0,) * 6


PROFILES = {"torque_steps": (torque_steps, TQ_DURATION), "gust_x": (gust_x, GUST_DURATION), "payload_add": (payload_add, PAYLOAD_DURATION),
            "gust_diag": (gust_diag, DIAG_DURATION), "com_shift": (com_shift, PAYLOAD_DURATION)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", required=True, choices=sorted(PROFILES))
    ap.add_argument("--out", required=True)
    ap.add_argument("--world", default="default")
    ap.add_argument("--model", default="x500_0")
    ap.add_argument("--airframe", choices=sorted(AIRFRAMES), default=None, help="default: derived from --model")
    ap.add_argument("--sdf", default=None, help="base model SDF to size the profiles from (default: the airframe SDF)")
    ap.add_argument("--link", default="base_link")
    ap.add_argument("--stop-after", type=float, default=30.0, help="exit this many sim s after the profile ended")
    ap.add_argument("--add-system", choices=("auto", "yes", "no"), default="auto",
                    help="auto: add ApplyLinkWrench at runtime only if the gz server config lacks it (A-31)")
    ap.add_argument("--wall-timeout", type=float, default=900.0)
    ap.add_argument("--wind-steady", type=float, default=None, help="gust_x only: steady wind m/s (default 3)")
    ap.add_argument("--wind-peak", type=float, default=None, help="gust_x only: peak TOTAL wind m/s in the gust (default 9)")
    ap.add_argument("--wind-dir", type=float, default=None,
                    help="gust_x only: deg from world +x towards +y, where the air moves to (default 0)")
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
    wind_given = any(x is not None for x in (a.wind_steady, a.wind_peak, a.wind_dir))
    if wind_given and a.profile != "gust_x":
        print("--wind-* only for --profile gust_x", file=sys.stderr)
        return 2
    if wind_given:
        try:
            st, am, dd = wind_profile_args(a.wind_steady, a.wind_peak, a.wind_dir)
        except ValueError as e:
            print(e, file=sys.stderr)
            return 2
        fn = lambda t, af_, vel=None, st=st, am=am, dd=dd: gust_x(t, af_, st, am, dd, vel)  # noqa: E731
    af = load_airframe(a.airframe or airframe_from_model(a.model), a.sdf)
    w = f"/world/{a.world}"

    # ---- load the system at runtime ----
    # The python binding cannot build gz.msgs.Plugin ("No message class registered"), so the one-off service call
    # goes through the gz CLI. The ApplyLinkWrench topics are then driven from python.
    import subprocess
    loaded_by = None
    for env in ("GZ_SIM_SERVER_CONFIG_PATH", "PX4_GZ_SERVER_CONFIG"):
        cfg = os.environ.get(env)
        if cfg and os.path.isfile(cfg):
            try:
                if "apply-link-wrench" in open(cfg).read():
                    loaded_by = cfg
                    break
            except OSError:
                pass
    do_add = a.add_system == "yes" or (a.add_system == "auto" and loaded_by is None)
    say(f"add-system={a.add_system}: config check -> {loaded_by!r}; runtime add {'YES' if do_add else 'NO'}")
    if not do_add and loaded_by:
        say(f"ApplyLinkWrench already loaded by {loaded_by}, not added")
    if do_add:
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
    state = {"onset": None, "t": None, "ended": False, "last_pub": None, "n": 0, "stop": False, "t_end_sim": None, "vel_none": 0}
    wall0 = time.time()

    def apply(wr):
        m = EntityWrench()
        m.entity.CopyFrom(entity())
        m.wrench.force.x, m.wrench.force.y, m.wrench.force.z = wr[0:3]
        m.wrench.torque.x, m.wrench.torque.y, m.wrench.torque.z = wr[3:6]
        pub.publish(m)

    pv = PoseVelocity()

    def on_pose(msg):  # /world/<w>/pose/info: pose of every entity, stamped with sim time
        for p in msg.pose:
            if p.name == a.model:
                pv.update(msg.header.stamp.sec + msg.header.stamp.nsec * 1e-9, (p.position.x, p.position.y, p.position.z))
                return

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
            if a.profile == "gust_x":  # air-relative drag: feed the vehicle ground-truth velocity (None until 2 pose samples)
                wr = fn(tp, af, pv.vel)
                state["vel_none"] += pv.vel is None
            else:
                wr = fn(tp, af)
            apply(wr)
        state["n"] += 1
        csv.write(f"{t:.4f},{t - CLOCK_OFFSET_S:.4f}," + ",".join(f"{x:.5f}" for x in wr) + "\n")

    from gz.msgs10.pose_v_pb2 import Pose_V
    if not node.subscribe(Pose_V, f"{w}/pose/info", on_pose):
        say("subscribe to pose/info failed")
        return 3
    if not node.subscribe(Clock, f"{w}/clock", on_clock):
        say("subscribe to clock failed")
        return 3
    say(f"airframe {af.name}: mass {af.mass:.4f} kg, inertia {af.inertia}, CdA {af.cda}, cop_z {af.cop_z}, source {af.source}")
    say(f"profile {a.profile}, duration {dur} s; waiting for trigger {trigger}")
    signal.signal(signal.SIGTERM, lambda *_: state.update(stop=True))
    signal.signal(signal.SIGINT, lambda *_: state.update(stop=True))
    while not state["stop"] and time.time() - wall0 < a.wall_timeout:
        if state["t_end_sim"] is not None and state["t"] - state["t_end_sim"] > a.stop_after:
            break
        time.sleep(0.2)
    pub_clear.publish(entity())
    say(f"exit, {state['n']} wrench updates, {state['vel_none']} gust_x updates without a velocity (legacy force)")
    csv.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

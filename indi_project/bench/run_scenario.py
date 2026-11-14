#!/usr/bin/env python3
"""Run ONE benchmark scenario in PX4 SITL (gz_x500, headless). Runs INSIDE the px4-indi-sim container.

  indi_project/docker/run.sh -n NAME -t SECONDS -- python3 indi_project/bench/run_scenario.py \
      --scenario step_roll --controller pid_default --seed 1 --speed 1 --out DIR [--params FILE]

Uses pymavlink (mavsdk in the image is the v4 native binding, different API). Setpoint timing is driven by PX4
sim time (time_boot_ms in MAVLink messages) so the speed factor does not matter for the scenario timing.
Always ends: every wait has a wall-clock timeout, cleanup runs in `finally`.
"""
import argparse
import glob
import json
import math
import os
import re
import shutil
import signal
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scenarios import SCENARIOS  # noqa: E402
from model_variant import build_variant  # noqa: E402

REPO = os.environ.get("PX4_INDI_REPO", os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
BUILD = os.path.join(REPO, "build/px4_sitl_default")

# Same for every controller under test: no GCS, no RC in this harness. Plus full-rate logging profile.
BASE_PARAMS = {
    "NAV_DLL_ACT": 0, "COM_RC_IN_MODE": 4, "COM_RCL_EXCEPT": 4,
    "SDLOG_PROFILE": 17, "MIS_TAKEOFF_ALT": 5.0,
}
TAKEOFF_ALT = 5.0
ALT_KP, ALT_KD = 0.04, 0.10  # thrust per m / per m/s of altitude error in attitude/rate scenarios
SETPOINT_PERIOD = 0.02  # sim seconds between offboard setpoints


class RunError(Exception):
    pass


class Sim:
    def __init__(self, a):
        self.a = a
        self.out = os.path.abspath(a.out)
        self.rootfs = os.path.join(self.out, "rootfs")
        self.procs = []
        self.env = None
        self.px4log = os.path.join(self.out, "px4.log")
        # latest MAVLink state
        self.t = 0.0
        self.pos = None  # (x, y, z) NED
        self.vz = 0.0
        self.yaw = 0.0
        self.armed = False
        self.main_mode = None
        self.landed_state = None
        self.mav = None
        self.sysid = a.instance + 1

    # ---------- processes ----------
    def load_env(self):
        out = subprocess.run(["bash", "-c", f"source {BUILD}/gz_env.sh; env -0"], capture_output=True, check=True).stdout
        env = dict(kv.split("=", 1) for kv in out.decode().split("\0") if "=" in kv)
        env.update(HEADLESS="1", PX4_SIM_MODEL="gz_x500", PX4_SIM_SPEED_FACTOR=str(self.a.speed))
        self.env = env

    def apply_model_variant(self, spec):
        """Per-run model copy with scaled values; PX4 spawns $PX4_GZ_MODELS/x500, x500_base resolves via the path."""
        vdir, rec = build_variant(spec, self.out, self.env["PX4_GZ_MODELS"])
        self.env["PX4_GZ_MODELS"] = vdir
        self.env["GZ_SIM_RESOURCE_PATH"] = vdir + ":" + self.env.get("GZ_SIM_RESOURCE_PATH", "")
        return rec

    def spawn(self, argv, logname):
        f = open(os.path.join(self.out, logname), "w")
        p = subprocess.Popen(argv, env=self.env, stdout=f, stderr=subprocess.STDOUT, start_new_session=True,
                             cwd=self.out)
        self.procs.append(p)
        return p

    def wait_log(self, pattern, timeout, path=None):
        path = path or self.px4log
        t0 = time.time()
        while time.time() - t0 < timeout:
            try:
                if pattern in open(path, errors="replace").read():
                    return True
            except FileNotFoundError:
                pass
            if self.px4.poll() is not None:
                raise RunError(f"px4 exited early (rc={self.px4.returncode}) while waiting for '{pattern}'")
            time.sleep(0.5)
        raise RunError(f"timeout ({timeout}s wall) waiting for '{pattern}' in {path}")

    def start_gz(self):
        world = os.path.join(self.env["PX4_GZ_WORLDS"], "default.sdf")
        self.gz = self.spawn(["gz", "sim", "--verbose=1", "-r", "-s", "--seed", str(self.a.seed), world], "gz.log")
        t0 = time.time()
        while time.time() - t0 < 120:
            r = subprocess.run(["gz", "topic", "-l"], capture_output=True, text=True, env=self.env, timeout=20)
            if "/world/default/clock" in r.stdout:
                return
            if self.gz.poll() is not None:
                raise RunError("gz sim exited early")
            time.sleep(1)
        raise RunError("timeout waiting for gz world")

    def start_px4(self):
        os.makedirs(self.rootfs, exist_ok=True)
        self.px4 = self.spawn([f"{BUILD}/bin/px4", "-i", str(self.a.instance), "-d", "-w", self.rootfs,
                               f"{BUILD}/etc"], "px4.log")
        self.wait_log("Startup script returned successfully", 180)
        try:  # evidence of the model gz actually loaded (inertia, link poses); informational only
            r = subprocess.run(["gz", "model", "-m", "x500_0"], capture_output=True, text=True, env=self.env,
                               timeout=30)
            open(os.path.join(self.out, "gz_model_info.txt"), "w").write(r.stdout + r.stderr)
        except Exception as e:  # noqa: BLE001
            open(os.path.join(self.out, "gz_model_info.txt"), "w").write(f"failed: {e}\n")

    def cli(self, tool, *args, timeout=30):
        r = subprocess.run([f"{BUILD}/bin/{tool}", "--instance", str(self.a.instance), *args], capture_output=True,
                           text=True, timeout=timeout, env=self.env)
        return r.stdout + r.stderr

    def set_param(self, name, value):
        out = self.cli("px4-param", "set", name, str(value))
        if "error" in out.lower() or "not found" in out.lower():
            raise RunError(f"param set {name} {value} failed: {out.strip()}")

    def get_param(self, name):
        out = self.cli("px4-param", "show", "-q", name)
        m = re.search(r"(-?\d+)\s*$", out.strip())
        if not m:
            raise RunError(f"param show {name} failed: {out.strip()}")
        return int(m.group(1))

    def cleanup(self):
        try:
            if getattr(self, "px4", None) and self.px4.poll() is None:
                try:
                    self.cli("px4-shutdown", timeout=15)
                except Exception:
                    pass
                try:
                    self.px4.wait(timeout=15)
                except Exception:
                    pass
        finally:
            for p in reversed(self.procs):
                if p.poll() is None:
                    try:
                        os.killpg(p.pid, signal.SIGTERM)
                    except ProcessLookupError:
                        pass
            deadline = time.time() + 10
            for p in self.procs:
                while p.poll() is None and time.time() < deadline:
                    time.sleep(0.2)
                if p.poll() is None:
                    try:
                        os.killpg(p.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass

    # ---------- MAVLink ----------
    def connect(self):
        from pymavlink import mavutil
        self.mavutil = mavutil
        self.mav = mavutil.mavlink_connection(f"udpin:0.0.0.0:{14540 + self.a.instance}", source_system=255)
        if self.mav.wait_heartbeat(timeout=60) is None:
            raise RunError("no MAVLink heartbeat in 60 s")
        for msg_id, hz in ((30, 100), (32, 50), (245, 2)):  # ATTITUDE, LOCAL_POSITION_NED, EXTENDED_SYS_STATE
            self.cmd(511, msg_id, 1e6 / hz, wait_ack=False)

    def cmd(self, command, p1=0, p2=0, p3=0, p4=0, p5=0, p6=0, p7=0, wait_ack=True, timeout=15):
        self.mav.mav.command_long_send(self.sysid, 1, command, 0, p1, p2, p3, p4, p5, p6, p7)
        if not wait_ack:
            return True
        t0 = time.time()
        while time.time() - t0 < timeout:
            m = self.mav.recv_match(type=["COMMAND_ACK"], blocking=True, timeout=1)
            if m is not None and m.command == command:
                return m.result == 0
        raise RunError(f"no COMMAND_ACK for {command}")

    def pump(self, timeout=2.0):
        """Read one message batch, update state. Returns True if an ATTITUDE (sim-time tick) was seen."""
        m = self.mav.recv_match(blocking=True, timeout=timeout)
        if m is None:
            return False
        ty = m.get_type()
        if ty == "ATTITUDE":
            self.t = m.time_boot_ms * 1e-3
            self.yaw = m.yaw
            return True
        if ty == "LOCAL_POSITION_NED":
            self.pos = (m.x, m.y, m.z)
            self.vz = m.vz
        elif ty == "HEARTBEAT" and m.get_srcSystem() == self.sysid and m.type != 6:
            self.armed = bool(m.base_mode & 128)
            self.main_mode = (m.custom_mode >> 16) & 0xFF
        elif ty == "EXTENDED_SYS_STATE":
            self.landed_state = m.landed_state
        return False

    def run(self, sim_dur, sp=None, until=None, wall_timeout=None, what=""):
        """Advance sim time by sim_dur (or until cond), sending setpoint sp() every SETPOINT_PERIOD sim s."""
        wall_timeout = wall_timeout or (60 + 3 * (sim_dur or 60) / max(self.a.speed, 0.1) + 30)
        w0 = time.time()
        t_start = self.t
        next_sp = self.t
        while True:
            if until is not None and until():
                return True
            if sim_dur is not None and self.t - t_start >= sim_dur:
                return True
            if time.time() - w0 > wall_timeout:
                raise RunError(f"wall timeout ({wall_timeout:.0f}s) in phase '{what}' (sim t={self.t:.2f})")
            if self.pump() and sp is not None and self.t >= next_sp:
                sp()
                next_sp = self.t + SETPOINT_PERIOD

    def send_pos(self, pos, yaw):
        self.mav.mav.set_position_target_local_ned_send(
            int(self.t * 1e3), self.sysid, 1, 1, 0b100111111000 | 0b000000000000, pos[0], pos[1], pos[2],
            0, 0, 0, 0, 0, 0, yaw, 0)

    @staticmethod
    def quat(roll, pitch, yaw):
        cr, sr = math.cos(roll / 2), math.sin(roll / 2)
        cp, sp_ = math.cos(pitch / 2), math.sin(pitch / 2)
        cy, sy = math.cos(yaw / 2), math.sin(yaw / 2)
        return [cr * cp * cy + sr * sp_ * sy, sr * cp * cy - cr * sp_ * sy,
                cr * sp_ * cy + sr * cp * sy, cr * cp * sy - sr * sp_ * cy]

    def send_att(self, roll, pitch, yaw, thrust):
        self.mav.mav.set_attitude_target_send(int(self.t * 1e3), self.sysid, 1, 0b00000111,
                                              self.quat(roll, pitch, yaw), 0, 0, 0, thrust)

    def send_rate(self, p, q, r, thrust):
        self.mav.mav.set_attitude_target_send(int(self.t * 1e3), self.sysid, 1, 0b10000000,
                                              [1, 0, 0, 0], p, q, r, thrust)


def hover_thrust(sim):
    out = sim.cli("px4-listener", "hover_thrust_estimate", "-n", "1")
    for line in out.splitlines():
        if "hover_thrust:" in line and "uncertainty" not in line:
            try:
                return float(line.split(":")[1])
            except ValueError:
                pass
    return None


def git_info():
    def g(*a):
        return subprocess.run(["git", "-C", REPO, *a], capture_output=True, text=True).stdout.strip()
    return {"commit": g("rev-parse", "HEAD"), "dirty": bool(g("status", "--porcelain", "--untracked-files=no"))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", required=True, choices=sorted(SCENARIOS))
    ap.add_argument("--controller", required=True)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--params", default=None, help="file with lines 'NAME VALUE' applied before arming")
    ap.add_argument("--out", required=True)
    ap.add_argument("--instance", type=int, default=0)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    sc = SCENARIOS[a.scenario]
    meta = {"scenario": a.scenario, "controller": a.controller, "seed": a.seed, "speed": a.speed,
            "instance": a.instance, "params_file": a.params, "params_applied": {}, "git": git_info(),
            "noise_seed": {"gz_sim_seed": a.seed, "px4_baro_srand": 1234}, "events": [], "phase_log": [],
            "exit_status": "running", "error": None}
    overlay = {}
    if a.params:
        for line in open(a.params):
            line = line.split("#")[0].strip()
            if line:
                k, v = line.split(None, 1)
                overlay[k] = v.strip()
    sim = Sim(a)
    t_wall0 = time.time()
    ok = False
    try:
        sim.load_env()
        if sc.get("model_variant"):
            meta["model_variant"] = sim.apply_model_variant(sc["model_variant"])
        sim.start_gz()
        sim.start_px4()
        if sc.get("disturbance"):  # idle injector: loads the wrench system, waits for the onset trigger
            sim.spawn(["python3", os.path.join(os.path.dirname(os.path.abspath(__file__)), "disturbance.py"),
                       "--profile", sc["disturbance"], "--out", a.out], "disturbance.stdout")
        for k, v in {**BASE_PARAMS, **overlay}.items():
            sim.set_param(k, v)
            meta["params_applied"][k] = v
        # logger reads SDLOG_PROFILE only at start: restart it so the full-rate profile takes effect
        sim.cli("px4-logger", "stop")
        time.sleep(1)
        sim.cli("px4-logger", "start", "-b", "20", "-t")
        sim.wait_log("Ready for takeoff", 180)
        sim.connect()
        sim.run(1.0, what="warmup")
        for attempt in range(40):  # "Ready for takeoff" can be transient right after boot: retry
            if sim.cmd(400, 1):
                break
            sim.run(1.0, what="arm_retry")
        else:
            raise RunError("arm rejected 40 times")
        meta["arm_attempts"] = attempt + 1
        sim.run(None, until=lambda: sim.armed, wall_timeout=20, what="armed")
        meta["t_arm_us"] = int(sim.t * 1e6)
        if not sim.cmd(22, float("nan"), 0, 0, float("nan"), float("nan"), float("nan"), float("nan")):
            raise RunError("takeoff rejected")
        sim.run(None, until=lambda: sim.pos and sim.pos[2] <= -(TAKEOFF_ALT - 0.3), wall_timeout=120 + 60 / a.speed,
                what="climb")
        sim.run(5.0, what="hover_before_offboard")
        hold_pos, hold_yaw = sim.pos, sim.yaw
        meta["hold_pos_ned"], meta["hold_yaw_rad"] = hold_pos, hold_yaw
        ht = hover_thrust(sim)
        meta["hover_thrust_estimate"] = ht
        thr0 = ht if ht and 0.1 < ht < 0.9 else 0.5
        def thr_cmd(tilt):
            """Collective thrust: hover estimate / tilt + PD on altitude error (identical for every controller)."""
            e = sim.pos[2] - hold_pos[2]  # NED z: positive = too low
            return max(0.1, min(0.95, thr0 / tilt + ALT_KP * e + ALT_KD * sim.vz))

        # offboard: stream setpoints, then switch mode
        pos_sp = lambda: sim.send_pos(hold_pos, hold_yaw)  # noqa: E731
        sim.run(1.0, sp=pos_sp, what="pre_offboard_stream")
        sim.cmd(176, 1, 6)
        sim.run(None, sp=pos_sp, until=lambda: sim.main_mode == 6, wall_timeout=30, what="offboard_engage")
        meta["t_offboard_us"] = int(sim.t * 1e6)
        sim.run(3.0, sp=pos_sp, what="offboard_settle")

        # ---- scenario ----
        axis, mode = sc["axis"], sc["mode"]
        meta["t_window_start_us"] = int(sim.t * 1e6)
        if sc.get("disturbance"):
            # onset = start of the segment named "dist" (PX4 time); the injector (started earlier, idle) reads it
            onset = sim.t + sum(d for n, d, _ in sc["segments"][:[n for n, _, _ in sc["segments"]].index("dist")])
            meta["disturbance"] = {"profile": sc["disturbance"], "onset_px4_s": onset, "onset_us": int(onset * 1e6),
                                   "csv": "disturbance.csv"}
            json.dump({"onset_px4_s": onset}, open(os.path.join(a.out, "disturbance_trigger.json"), "w"))
        fault = sc.get("motor_fault")
        if fault:  # plant change: read nominal MIN/MAX of the motor's gz channel now (param index = motor + 1)
            ch = fault["motor"] + 1
            nom = {k: sim.get_param(f"SIM_GZ_EC_{k}{ch}") for k in ("MIN", "MAX")}
            meta["motor_fault"] = {"motor": fault["motor"], "thrust_scale": fault["thrust_scale"], "nominal": nom,
                                   "segment": fault["segment"]}
        prev = 0.0
        for name, dur, val in sc["segments"]:
            if fault and name == fault["segment"]:
                k_om = math.sqrt(fault["thrust_scale"])
                new = {k: int(round(v * k_om)) for k, v in nom.items()}
                t_req = sim.t
                for k, v in new.items():
                    sim.set_param(f"SIM_GZ_EC_{k}{ch}", v)
                meta["motor_fault"].update({"event_us": int(t_req * 1e6), "event_done_us": int(sim.t * 1e6), "applied": new,
                                            "omega_ratio": k_om})
            ev = {"name": name, "t_us": int(sim.t * 1e6), "dur_s": dur, "mode": mode, "axis": axis,
                  "value": val, "prev": prev, "step": name != "settle" and mode != "position"}
            meta["events"].append(ev)
            r = val if axis in ("roll", "rollpitch") else 0.0
            p = val if axis in ("pitch", "rollpitch") else 0.0
            y = val if axis == "yaw" else 0.0
            if mode == "position":
                sp = pos_sp
            elif mode == "attitude":
                rr, pp = math.radians(r), math.radians(p)
                tilt = max(0.3, math.cos(rr) * math.cos(pp))
                sp = (lambda rr=rr, pp=pp, yy=hold_yaw + math.radians(y), tilt=tilt:
                      sim.send_att(rr, pp, yy, thr_cmd(tilt)))
            else:
                sp = (lambda r=math.radians(r), p=math.radians(p), y=math.radians(y): sim.send_rate(r, p, y, thr_cmd(1.0)))
            sim.run(dur, sp=sp, what=f"scenario:{name}")
            prev = val
        meta["t_window_end_us"] = int(sim.t * 1e6)
        sim.run(4.0, sp=pos_sp, what="recover")  # outside the metrics window

        # ---- land ----
        sim.cmd(21, 0, 0, 0, float("nan"), float("nan"), float("nan"), 0)
        sim.run(None, until=lambda: not sim.armed, wall_timeout=120 + 120 / a.speed, what="land")
        sim.run(2.0, what="post_disarm")
        ok = True
    except Exception as e:  # noqa: BLE001
        meta["error"] = f"{type(e).__name__}: {e}"
        print("RUN FAILED:", meta["error"], file=sys.stderr)
    finally:
        try:
            sim.cleanup()
        except Exception as e:  # noqa: BLE001
            meta["error"] = (meta["error"] or "") + f" | cleanup: {e}"
        ulogs = sorted(glob.glob(os.path.join(sim.rootfs, "**", "*.ulg"), recursive=True), key=os.path.getmtime)
        if ulogs:
            shutil.copy(ulogs[-1], os.path.join(a.out, "flight.ulg"))
            meta["ulog"] = "flight.ulg"
        else:
            ok = False
            meta["error"] = (meta["error"] or "") + " | no ulog"
        meta["wall_time_s"] = round(time.time() - t_wall0, 1)
        meta["exit_status"] = "ok" if ok else "failed"
        json.dump(meta, open(os.path.join(a.out, "run.json"), "w"), indent=1)
        # keep the out dir small: drop the per-run rootfs (params/dataman/log copies)
        shutil.rmtree(sim.rootfs, ignore_errors=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

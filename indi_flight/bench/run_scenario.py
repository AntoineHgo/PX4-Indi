#!/usr/bin/env python3
"""Run ONE benchmark scenario in PX4 SITL (gz_x500, headless). Runs INSIDE the px4-indi-sim container.

  indi_project/docker/run.sh -n NAME -t SECONDS -- python3 indi_flight/bench/run_scenario.py \
      --scenario step_roll --controller pid_default --seed 1 --speed 1 --out DIR [--params FILE]

Uses pymavlink (mavsdk in the image is the v4 native binding, different API). Setpoint timing is driven by PX4
sim time (time_boot_ms in MAVLink messages) so the speed factor does not matter for the scenario timing.
Always ends: every wait has a wall-clock timeout, cleanup runs in `finally`.
"""
import argparse
import copy
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
import provenance  # noqa: E402
import scenario_overrides  # noqa: E402
import stick_profile  # noqa: E402
import stick_pilot  # noqa: E402

REPO = os.environ.get("PX4_INDI_REPO", os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
# ported to indi_flight/bench: inputs (scenarios, model_variant, disturbance, params) live next to this file, outputs
# default under indi_flight/results/. REPO stays the PX4 repo root (build dir, docker launcher indi_project/docker).
RESULTS_DIR = os.path.join(REPO, "indi_flight", "results")
MODELS_DIR = os.path.join(REPO, "indi_flight", "sim", "models")  # quad5in reference airframe (F-3)
# D-SIM-STEP (s15): ONE world for every run, physics step 1.25 ms (800 Hz); the stock world (4 ms) is not used. The repo is
# mounted at its own path in the container (indi_project/docker/run.sh), so the host path is valid there, like MODELS_DIR.
WORLDS_DIR = os.path.join(REPO, "indi_flight", "sim", "worlds")
# gz IMU rate of each reference model; --imu-rate changes the sensor only, never the physics step
MODEL_IMU_RATE = {"quad5in": 800, "x500": 250}
RATES_HZ = (800, 400, 267)  # selectable controller rates (G2): IMU_GYRO_RATEMAX; PX4 decimates by round(800/RATEMAX) = 1, 2, 3
# Fixed across rates so only the rate varies: PX4 defaults, set explicitly so a changed default cannot leak in
IMU_GYRO_CUTOFF_HZ, IMU_DGYRO_CUTOFF_HZ = 40, 20
# PX4_INDI_BUILD: fly another build directory of the same tree (e.g. a branch build while a batch uses the default).
BUILD = os.environ.get("PX4_INDI_BUILD", os.path.join(REPO, "build/px4_sitl_default"))



HERE_PARAMS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "params")


def read_params(path):
    """'NAME VALUE' lines, '#' comments, as a dict of strings (order kept)."""
    out = {}
    for line in open(path):
        line = line.split("#")[0].strip()
        if line:
            k, v = line.split(None, 1)
            out[k] = v.strip()
    return out


def o11_build():
    """True for builds with the separate mc_indi_rate_control module (O-11): INDI is selected by MC_INDI_EN at boot,
    not by MC_RATE_CTL_TYPE, and the rotor speed scale is MC_INDI_W_MAX instead of CA_R_W_MAX."""
    try:
        return "MC_INDI_EN" in open(os.path.join(BUILD, "parameters.xml")).read()
    except OSError:
        return False


# Same for every controller under test: no GCS, no RC in this harness. Plus full-rate logging profile.
BASE_PARAMS = {
    "NAV_DLL_ACT": 0, "COM_RC_IN_MODE": 4, "COM_RCL_EXCEPT": 4,
    "SDLOG_PROFILE": 17, "MIS_TAKEOFF_ALT": 5.0,
}
# Logged at every update (interval 0). PX4 adds these to the SDLOG_PROFILE set and overrides the interval of any
# topic the profile already logs; read from <rootfs>/fs/etc/logging/logger_topics.txt (see start_px4).
LOG_TOPICS = [
    "trajectory_setpoint", "vehicle_attitude_setpoint", "vehicle_rates_setpoint", "vehicle_angular_velocity",
    "vehicle_acceleration", "vehicle_attitude", "vehicle_local_position", "vehicle_local_position_setpoint",
    "vehicle_local_position_groundtruth", "actuator_motors", "esc_status", "vehicle_thrust_setpoint",
    "vehicle_torque_setpoint", "sensor_combined", "vehicle_status", "vehicle_control_mode", "vehicle_land_detected",
    "parameter_update", "hover_thrust_estimate", "control_allocator_status", "indi_pos_status",
    "vehicle_imu_status", "sensor_gyro",  # D-SIM-STEP pre-test evidence: gyro rate (sensor_gyro ~ IMU rate, 800 Hz)
    "vehicle_attitude_groundtruth", "vehicle_angular_velocity_groundtruth",  # A-12 s18: were 100 Hz (profile rate)
    "sim_ground_truth",  # A-15 s21: sim-only truth, uORB queue 16, one sample per sim step
    "indi_rate_status", "actuator_torque_measured",  # D-G2-INJ s39: c, d, u per cycle and the measured rotor torque
    "takeoff_status",  # S131 AUTO smoke: rampup -> flight edge of the navigator take-off
    "sim_schedule_applied",  # D-SCHED s24: row applied by sim_scenario_player (queue 8), only published with --sched
]
TAKEOFF_ALT = 5.0
GA_ALT_M, GA_CLIMB_MPS = 3.0, 1.0  # --ground-arm: climb target (estimate) and stick climb rate
# S81 --stick-mode: PX4 custom main modes of the HEARTBEAT (px4_custom_mode.h) and the run's stick parameters
STICK_MAIN_MODE = {"altctl": 2, "posctl": 3, "acro": 5, "stabilized": 7}
# S139: (main, sub) of MAV_CMD_DO_SET_MODE for the per-segment modes; hold = AUTO_LOITER (main 4, sub 3)
SEG_MODE_CUSTOM = {"altctl": (2, 0), "posctl": (3, 0), "stabilized": (7, 0), "hold": (4, 3)}
STICK_PARAMS = {"MPC_VEL_MANUAL": stick_profile.MPC_VEL_MANUAL, "COM_RC_IN_MODE": 1, "COM_RCL_EXCEPT": 7, "MPC_Z_VEL_MAX_UP": stick_profile.VZ_MAX_UP,
                "MPC_Z_VEL_MAX_DN": stick_profile.VZ_MAX_UP, "MAN_DEADZONE": 0,
                "MPC_THR_CURVE": 0, "MPC_MANTHR_MIN": stick_profile.MANTHR_MIN,
                "MPC_THR_MAX": stick_profile.THR_MAX}  # 1 = MAVLink only; no deadzone; stick expo 0.6 is hard-coded and inverted in stick_profile (it gave gain 0.3)
ALT_KP, ALT_KD = 0.04, 0.10  # thrust per m / per m/s of altitude error in attitude/rate scenarios
SETPOINT_PERIOD = 0.02  # sim seconds between offboard setpoints
# G1.6 determinism (s12): arm and offboard happen at FIXED sim times, so same-seed runs fly the same time slice.
# s11 pre-study: the arm happened at sim 15.4-17.6 s (wall time spent in param sets, logger restart, wait_log,
# arm retries), arm->offboard took 15-16 s. T_ARM_S sits >2 s after the latest observed ready time. T_OFFBOARD_S
# leaves room for the climb (~8-9 s observed) + 5 s hover (HOVER_MIN_S) + 1 s pre-stream (PRESTREAM_S) with margin.
# s12 pre-test: at sim 20-25 s the arming check fails ("height estimate not stable"), and the climb took > 8.8 s
# (it missed the 34 s deadline after a 25.2 s arm). Arm at 30 s, give the climb 16 s.
T_ARM_S = 30.0
T_OFFBOARD_S = T_ARM_S + 22.0  # 52 s
HOVER_MIN_S = 5.0  # hover between end of climb and hold capture (as before)
PRESTREAM_S = 1.0  # position-setpoint stream before the offboard switch (as before)
T_HOLD_S = T_OFFBOARD_S - PRESTREAM_S  # hold_pos/hold_yaw captured here (fixed sim time)
# T53 (--sched-anchor): rows after the anchor, times in us RELATIVE to the observed offboard transition (nav_state 14)
SCHED_ANCHOR_ROWS = ["3000000 sp_hold", "6000000 sp_hold"]
# D-SCHED (--sched): the hold setpoint is captured in flight by the schedule row `sp_hold` (T53), not hard-coded.
SCHED_SETTLE_S = 3.0  # T55: scenario rows start this long after the offboard anchor (the runner's offboard_settle, metrics.OFFBOARD_SETTLE_S)
SCHED_FILE = "sim_schedule.txt"  # in the PX4 working dir (the run's rootfs); rcS starts sim_scenario_player when present
LATE_TOL_S = 0.1  # an arm later than T_ARM_S + this is flagged as arm_late_s in run.json
# O-12 watchdog (D-watchdog), active from takeoff completion to the landing command
WD_TILT_DEG, WD_TILT_HOLD_S = 60.0, 0.5  # MPC_TILTMAX_AIR 45 deg; largest commanded tilt ~52 deg (H4)
WD_MIN_HEIGHT_M = 0.3  # ground contact while airborne
WD_BELOW_M, WD_BELOW_HOLD_S = 3.0, 1.0  # height deficit below the hold altitude; worst recorded excursions < 1 m
WD_NO_TICK_S = 10.0  # wall seconds without ATTITUDE while PX4 is alive (host suspend, stall)


def world_step_s():
    """max_step_size [s] read from the world file the run uses (recorded in run.json; gz log must agree)."""
    m = re.search(r"<max_step_size>([^<]+)</max_step_size>",
                  open(os.path.join(WORLDS_DIR, "default.sdf"), encoding="utf-8").read())
    return float(m.group(1)) if m else None


class RunError(Exception):
    pass


class WatchdogTrip(RunError):
    def __init__(self, reason, t_sim_s, value):
        super().__init__(f"watchdog: {reason} (sim t={t_sim_s:.2f}, value={value:.3g})")
        self.info = {"reason": reason, "t_sim_s": round(t_sim_s, 3), "value": value}


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
        self.roll = 0.0
        self.pitch = 0.0
        self.armed = False
        self.main_mode = None
        self.sub_mode = None
        self.landed_state = None
        self.mav = None
        self.sysid = a.instance + 1
        # watchdog state; armed by wd_start() once the vehicle is airborne
        self.wd_on = False
        self.wd_href = None
        self.wd_tilt_t0 = None
        self.wd_below_t0 = None
        self.wd_last_tick = time.time()
        # sends log (G1): one row per setpoint send / param set / sag step, buffered, written in cleanup()
        self.wall0 = time.time()
        self.sends = []
        self.sends_pending = []  # blocking rows still waiting for their sim_time_after (next ATTITUDE)
        self.sp_period = SETPOINT_PERIOD  # sim s between sp() calls
        self.sp_grid = False  # --stick-mode: sp() on a fixed sim-time grid (see run), offboard paths unchanged
        self.sticks = []  # S81 --stick-mode: applied MANUAL_CONTROL samples (sim time, raw fields), written to sticks.csv

    # ---------- sends log ----------
    SENDS_COLS = ("kind", "intended_sim_time_us", "sim_time_before_us", "sim_time_after_us", "wall_time_s",
                  "wall_after_s", "payload")

    def log_send(self, kind, payload, intended_us=None, blocking=False):
        tus = int(self.t * 1e6)  # latest ATTITUDE time_boot_ms seen = sim time that triggered this send
        row = [kind, tus if intended_us is None else intended_us, tus, "", round(time.time() - self.wall0, 4), "",
               payload]
        self.sends.append(row)
        if blocking:
            self.sends_pending.append(row)
        return row

    def write_sends(self):
        import csv
        with open(os.path.join(self.out, "sends.csv"), "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(self.SENDS_COLS)
            w.writerows(self.sends)

    # ---------- processes ----------
    def load_env(self):
        out = subprocess.run(["bash", "-c", f"source {BUILD}/gz_env.sh; env -0"], capture_output=True, check=True).stdout
        env = dict(kv.split("=", 1) for kv in out.decode().split("\0") if "=" in kv)
        env.update(HEADLESS="1", PX4_SIM_MODEL=f"gz_{self.a.model}", PX4_SIM_SPEED_FACTOR=str(self.a.speed))
        env["PX4_GZ_WORLDS"] = WORLDS_DIR  # px4-rc.gzsim reads max_step_size from $PX4_GZ_WORLDS/$PX4_GZ_WORLD.sdf
        if self.a.model != "x500":
            env["PX4_GZ_MODELS"] = MODELS_DIR
            env["GZ_SIM_RESOURCE_PATH"] = MODELS_DIR + ":" + env.get("GZ_SIM_RESOURCE_PATH", "")
        self.env = env

    def apply_model_variant(self, spec):
        """Per-run model copy with scaled values; PX4 spawns $PX4_GZ_MODELS/x500, x500_base resolves via the path."""
        vdir, rec = build_variant(spec, self.out, self.env["PX4_GZ_MODELS"], model=self.a.model)
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
        world = os.path.join(self.env["PX4_GZ_WORLDS"], "default.sdf")  # fixed 1.25 ms world, same for every run
        run_flag = [] if self.a.paused_start else ["-r"]  # --paused-start: gz waits paused until unpause_gz()
        self.gz = self.spawn(["gz", "sim", "--verbose=1", *run_flag, "-s", "--seed", str(self.a.seed), world],
                             "gz.log")
        t0 = time.time()
        while time.time() - t0 < 120:
            r = subprocess.run(["gz", "topic", "-l"], capture_output=True, text=True, env=self.env, timeout=20)
            if "/world/default/clock" in r.stdout:
                return
            if self.gz.poll() is not None:
                raise RunError("gz sim exited early")
            time.sleep(1)
        raise RunError("timeout waiting for gz world")

    def gz_clock(self):
        r = subprocess.run(["gz", "topic", "-e", "-t", "/world/default/clock", "-n", "1"], capture_output=True,
                           text=True, env=self.env, timeout=20)
        return " ".join((r.stdout + r.stderr).split())

    def unpause_gz(self):
        clock_before = self.gz_clock()  # evidence that sim time was frozen until the unpause
        r = subprocess.run(["gz", "service", "-s", "/world/default/control", "--reqtype", "gz.msgs.WorldControl",
                            "--reptype", "gz.msgs.Boolean", "--timeout", "5000", "--req", "pause: false"],
                           capture_output=True, text=True, env=self.env, timeout=30)
        open(os.path.join(self.out, "unpause.txt"), "w").write(
            f"wall={time.time() - self.wall0:.3f} rc={r.returncode}\nclock_before: {clock_before}\n"
            f"{r.stdout}{r.stderr}clock_after: {self.gz_clock()}\n")
        if r.returncode != 0 or "true" not in r.stdout:
            raise RunError(f"gz unpause failed: {r.stdout} {r.stderr}")

    def start_px4(self):
        os.makedirs(self.rootfs, exist_ok=True)
        topics_dir = os.path.join(self.rootfs, "fs", "etc", "logging")  # SITL storage root is ./fs
        os.makedirs(topics_dir, exist_ok=True)
        if self.a.sched:  # D-SCHED: arm, offboard switch and setpoint stream played inside PX4 in simulation time
            rows = [f"{int(T_ARM_S * 1e6)} arm",
                    f"{int((T_OFFBOARD_S - PRESTREAM_S) * 1e6)} sp_hold",  # T53: x y z heading captured in flight
                    f"{int(T_OFFBOARD_S * 1e6)} mode_offboard"]
            sc = SCENARIOS[self.a.scenario]
            if sc["mode"] == "position":
                if self.a.sched_anchor:  # T53: later rows are offsets from the observed offboard transition
                    rows += [f"{int(T_OFFBOARD_S * 1e6)} anchor nav_state=14"] + SCHED_ANCHOR_ROWS
            else:  # T55: attitude / trajectory rows, offsets from the offboard transition (anchor) or from T_OFFBOARD_S
                if self.a.sched_anchor:
                    rows += [f"{int(T_OFFBOARD_S * 1e6)} anchor nav_state=14"]
                    base = 0
                else:
                    base = int(T_OFFBOARD_S * 1e6)
                rows += [f"{base + off} {text}" for off, text in sched_scenario_rows(sc)]
            text = "# t_sim_us kind fields (written by run_scenario.py --sched)\n" + "\n".join(rows) + "\n"
            open(os.path.join(self.rootfs, SCHED_FILE), "w").write(text)
            open(os.path.join(self.out, "sched.txt"), "w").write(text)
        with open(os.path.join(topics_dir, "logger_topics.txt"), "w") as f:
            f.writelines(f"{t} 0 0\n" for t in LOG_TOPICS)  # instance 0 only: multi-instance adds exhaust the 255 slots
        self.px4 = self.spawn([f"{BUILD}/bin/px4", "-i", str(self.a.instance), "-d", "-w", self.rootfs,
                               f"{BUILD}/etc"], "px4.log")
        if self.a.paused_start:  # A-17 s25: gz was started paused; unpause once the wait pattern is in px4.log
            self.wait_log(self.a.unpause_after, 180)
            self.unpause_gz()
        self.wait_log("Startup script returned successfully", 180)
        try:  # evidence of the model gz actually loaded (inertia, link poses); informational only
            r = subprocess.run(["gz", "model", "-m", f"{self.a.model}_0"], capture_output=True, text=True, env=self.env,
                               timeout=30)
            open(os.path.join(self.out, "gz_model_info.txt"), "w").write(r.stdout + r.stderr)
        except Exception as e:  # noqa: BLE001
            open(os.path.join(self.out, "gz_model_info.txt"), "w").write(f"failed: {e}\n")

    def cli(self, tool, *args, timeout=30):
        r = subprocess.run([f"{BUILD}/bin/{tool}", "--instance", str(self.a.instance), *args], capture_output=True,
                           text=True, timeout=timeout, env=self.env)
        return r.stdout + r.stderr

    def set_param(self, name, value, kind="param", intended_us=None, extra=""):
        row = self.log_send(kind, f"{name}={value}{extra}", intended_us, blocking=True)
        try:
            out = self.cli("px4-param", "set", name, str(value))
        finally:
            row[5] = round(time.time() - self.wall0, 4)  # wall time at return; sim_time_after_us filled by pump()
        if "error" in out.lower() or "not found" in out.lower():
            raise RunError(f"param set {name} {value} failed: {out.strip()}")

    def get_param_float(self, name):
        out = self.cli("px4-param", "show", "-q", name)
        m = re.search(r"(-?\d+(?:\.\d*)?(?:[eE][-+]?\d+)?)\s*$", out.strip())
        if not m:
            raise RunError(f"param show {name} failed: {out.strip()}")
        return float(m.group(1))

    def get_param(self, name):
        out = self.cli("px4-param", "show", "-q", name)
        m = re.search(r"(-?\d+)\s*$", out.strip())
        if not m:
            raise RunError(f"param show {name} failed: {out.strip()}")
        return int(m.group(1))

    def cleanup(self):
        try:
            self.write_sends()
        except Exception as e:  # noqa: BLE001
            print("sends.csv not written:", e, file=sys.stderr)
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
            if self.sends_pending:  # first sim tick after a blocking call returned: upper bound of its sim duration
                for r in self.sends_pending:
                    r[3] = int(self.t * 1e6)
                self.sends_pending.clear()
            self.yaw = m.yaw
            self.roll, self.pitch = m.roll, m.pitch
            self.wd_last_tick = time.time()
            if self.wd_on:
                self.wd_check(m)
            return True
        if ty == "LOCAL_POSITION_NED":
            self.pos = (m.x, m.y, m.z)
            self.vz = m.vz
        elif ty == "HEARTBEAT" and m.get_srcSystem() == self.sysid and m.type != 6:
            self.armed = bool(m.base_mode & 128)
            self.main_mode = (m.custom_mode >> 16) & 0xFF
            self.sub_mode = (m.custom_mode >> 24) & 0xFF
            key = (self.main_mode, self.sub_mode, self.armed)
            if key != self.mode_log_last:  # S131: every (main, sub, armed) change with its sim time, for AUTO phases
                self.mode_log_last = key
                self.mode_log.append([round(self.t, 3), *key])
        elif ty == "GLOBAL_POSITION_INT":
            self.gpos = (m.lat, m.lon)
            self.gpos_alt = m.alt * 1e-3  # AMSL m
        elif ty == "MISSION_ITEM_REACHED":
            self.reached = m.seq
        elif ty == "EXTENDED_SYS_STATE":
            self.landed_state = m.landed_state
        return False

    mode_log, mode_log_last, gpos, gpos_alt, reached = [], None, None, 0.0, -1  # S131 (mode_log is reset per Sim in run_auto)

    def wd_start(self):
        self.wd_on = self.a.watchdog == "on"
        self.wd_href = -self.pos[2]

    def wd_check(self, m):
        vals = (m.roll, m.pitch, m.yaw, m.rollspeed, m.pitchspeed, m.yawspeed)
        if not all(math.isfinite(v) for v in vals):
            raise WatchdogTrip("non-finite attitude or rate", self.t, float("nan"))
        tilt = math.degrees(max(abs(m.roll), abs(m.pitch)))
        if tilt > WD_TILT_DEG:
            self.wd_tilt_t0 = self.t if self.wd_tilt_t0 is None else self.wd_tilt_t0
            if self.t - self.wd_tilt_t0 >= WD_TILT_HOLD_S:
                raise WatchdogTrip(f"tilt > {WD_TILT_DEG:.0f} deg for {WD_TILT_HOLD_S} s", self.t, tilt)
        else:
            self.wd_tilt_t0 = None
        if self.pos is None:
            return
        h = -self.pos[2]
        if h < WD_MIN_HEIGHT_M:
            raise WatchdogTrip(f"height < {WD_MIN_HEIGHT_M} m", self.t, h)
        if self.wd_href - h > WD_BELOW_M:
            self.wd_below_t0 = self.t if self.wd_below_t0 is None else self.wd_below_t0
            if self.t - self.wd_below_t0 >= WD_BELOW_HOLD_S:
                raise WatchdogTrip(f"> {WD_BELOW_M} m below hold altitude for {WD_BELOW_HOLD_S} s", self.t,
                                   self.wd_href - h)
        else:
            self.wd_below_t0 = None

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
            if (self.wd_on and time.time() - self.wd_last_tick > WD_NO_TICK_S and getattr(self, "px4", None)
                    and self.px4.poll() is None):
                raise WatchdogTrip(f"no ATTITUDE for {WD_NO_TICK_S:.0f} s wall in phase '{what}'", self.t,
                                   time.time() - self.wd_last_tick)
            if self.pump() and sp is not None and self.t >= next_sp:
                sp()
                # S82 stick mode: fixed sim-time grid (t + period landed on every 3rd ~15 ms ATTITUDE tick = 33 Hz)
                next_sp = max(next_sp + self.sp_period, self.t) if self.sp_grid else self.t + self.sp_period

    def send_pos(self, pos, yaw):
        self.log_send("send_pos", f"x={pos[0]:.5g};y={pos[1]:.5g};z={pos[2]:.5g};yaw={yaw:.5g}")
        self.mav.mav.set_position_target_local_ned_send(
            int(self.t * 1e3), self.sysid, 1, 1, 0b100111111000 | 0b000000000000, pos[0], pos[1], pos[2],
            0, 0, 0, 0, 0, 0, yaw, 0)

    def send_pva(self, pos, vel, acc, yaw):
        """Position + velocity + acceleration feedforward (type mask ignores only yaw rate)."""
        self.log_send("send_pva", f"x={pos[0]:.5g};y={pos[1]:.5g};z={pos[2]:.5g};vx={vel[0]:.5g};vy={vel[1]:.5g};"
                      f"vz={vel[2]:.5g};ax={acc[0]:.5g};ay={acc[1]:.5g};az={acc[2]:.5g};yaw={yaw:.5g}")
        self.mav.mav.set_position_target_local_ned_send(
            int(self.t * 1e3), self.sysid, 1, 1, 0b100000000000, pos[0], pos[1], pos[2],
            vel[0], vel[1], vel[2], acc[0], acc[1], acc[2], yaw, 0)

    def send_vel(self, vel, yaw):
        """S133 T7: velocity-only setpoint (position and acceleration ignored, yaw used, yaw rate ignored)."""
        self.log_send("send_vel", f"vx={vel[0]:.5g};vy={vel[1]:.5g};vz={vel[2]:.5g};yaw={yaw:.5g}")
        self.mav.mav.set_position_target_local_ned_send(
            int(self.t * 1e3), self.sysid, 1, 1, 0b100111000111, 0, 0, 0,
            vel[0], vel[1], vel[2], 0, 0, 0, yaw, 0)

    @staticmethod
    def quat(roll, pitch, yaw):
        cr, sr = math.cos(roll / 2), math.sin(roll / 2)
        cp, sp_ = math.cos(pitch / 2), math.sin(pitch / 2)
        cy, sy = math.cos(yaw / 2), math.sin(yaw / 2)
        return [cr * cp * cy + sr * sp_ * sy, sr * cp * cy - cr * sp_ * sy,
                cr * sp_ * cy + sr * cp * sy, cr * cp * sy - sr * sp_ * cy]

    def send_att(self, roll, pitch, yaw, thrust):
        self.log_send("send_att", f"roll={roll:.5g};pitch={pitch:.5g};yaw={yaw:.5g};thrust={thrust:.5g}")
        self.mav.mav.set_attitude_target_send(int(self.t * 1e3), self.sysid, 1, 0b00000111,
                                              self.quat(roll, pitch, yaw), 0, 0, 0, thrust)

    def send_stick(self, smp):
        """S81: one MANUAL_CONTROL sample (x pitch, y roll, z throttle 0..1000, r yaw), logged as applied (sim time)."""
        self.sticks.append((int(self.t * 1e6), smp["x"], smp["y"], smp["z"], smp["r"], smp["throttle"], smp["vz_up_demand"])
                           + ((smp["pilot_thr"], smp["pilot_roll"], smp["pilot_pitch"]) if "pilot_thr" in smp else ()))
        self.mav.mav.manual_control_send(self.sysid, smp["x"], smp["y"], smp["z"], smp["r"], 0)

    def write_sticks(self):
        with open(os.path.join(self.out, "sticks.csv"), "w") as f:
            f.write("t_sim_us,x,y,z,r,throttle_applied,vz_up_demand_mps"
                    + (",pilot_thr,pilot_roll_stick,pilot_pitch_stick" if any(len(r) > 7 for r in self.sticks) else "") + "\n")
            for r in self.sticks:
                r = tuple(r) + ("",) * (10 - len(r)) if any(len(q) > 7 for q in self.sticks) else r  # neutral rows: no pilot columns
                f.write(",".join(f"{v:.6g}" if isinstance(v, float) else str(v) for v in r) + "\n")

    def send_rate(self, p, q, r, thrust):
        self.log_send("send_rate", f"p={p:.5g};q={q:.5g};r={r:.5g};thrust={thrust:.5g}")
        self.mav.mav.set_attitude_target_send(int(self.t * 1e3), self.sysid, 1, 0b10000000,
                                              [1, 0, 0, 0], p, q, r, thrust)


def fault_apply(cum_scale, ents, nom_all):
    """Multiply each entry's thrust_scale into cum_scale (per motor, in place); return the SIM_GZ_EC MIN/MAX values to
    set per motor: nominal * sqrt(cumulative scale) (thrust ~ omega^2), rounded to int."""
    for f in ents:
        for fm in (f.get("motors") or [f["motor"]]):
            if f.get("reset"):  # G5.10: the saturation window ends, available thrust back to nominal
                cum_scale[fm] = 1.0
            cum_scale[fm] *= f["thrust_scale"]
    return {fm: {k: int(round(v * math.sqrt(cum_scale[fm]))) for k, v in nom_all[fm].items()} for fm in nom_all}


def erpm_loss_split(dur, t_on, t_len, motor):
    """Timed eRPM loss inside one segment of length dur: [(label, duration_s, motor_bitmask or None)] for pre (t_on),
    loss (t_len, bit 1 << motor) and post (the rest of the segment)."""
    return [("pre", t_on, None), ("loss", t_len, 1 << motor), ("post", dur - t_on - t_len, None)]


def traj_phase(traj, t):
    """Phase of a closed trajectory: phase rate ramps 0 -> w (smoothstep, ramp_s), cruises, ramps back to 0, and the
    total phase is laps * 2 pi, so the path starts and ends at the hold position with zero velocity."""
    w, tr = traj["w"], traj["ramp_s"]
    tc = 2 * math.pi * traj["laps"] / w - tr
    if t <= 0:
        return 0.0
    if t < tr:
        u = t / tr
        return w * tr * (u ** 3 - u ** 4 / 2)
    if t < tr + tc:
        return w * tr / 2 + w * (t - tr)
    if t < 2 * tr + tc:
        u = (2 * tr + tc - t) / tr
        return 2 * math.pi * traj["laps"] - w * tr * (u ** 3 - u ** 4 / 2)
    return 2 * math.pi * traj["laps"]


def traj_pos(traj, phi):
    """NED offset from the hold position at phase phi (zero at phi = 0)."""
    if traj["shape"] == "lemniscate":  # Gerono lemniscate, size_x x size_y
        return [traj["ax"] * math.sin(phi), traj["ay"] * math.sin(2 * phi), 0.0]
    if traj["shape"] == "circle":  # circle of radius r through the start point, plus a vertical sine (NED z: up = -)
        r = traj["r"]
        return [r * (math.cos(phi) - 1.0), r * math.sin(phi), -traj["z_amp"] * math.sin(phi)]
    if traj["shape"] == "zmulti":  # vertical multisine, harmonics k of the phase with amplitudes a (m)
        return [0.0, 0.0, -sum(a * math.sin(k * phi) for k, a in zip(traj["harm"], traj["amps"]))]
    raise ValueError(traj["shape"])


def traj_pva(traj, t, h=1e-3):
    """Position, velocity and acceleration setpoints (velocity/acceleration by central differences of the path)."""
    p0, pm, pp = (traj_pos(traj, traj_phase(traj, tt)) for tt in (t, t - h, t + h))
    vel = [(pp[i] - pm[i]) / (2 * h) for i in range(3)]
    acc = [(pp[i] - 2 * p0[i] + pm[i]) / (h * h) for i in range(3)]
    return p0, vel, acc


def sched_scenario_rows(sc):
    """T55: (offset_us from the offboard transition, row text) of an attitude or trajectory scenario for sim_scenario_player.
    Same segments, same values and the same functions as the MAVLink path: attitude rows hold roll / pitch / yaw offset
    (rad) with thrust `auto` (thr_cmd inside the player); trajectory rows are traj_pva() sampled every SETPOINT_PERIOD
    (dx dy dz vx vy vz ax ay az, offsets from the sp_hold position, yaw = sp_hold heading); `sp_back` (the hold
    position, like the runner's pos_sp) ends the scenario."""
    mode, axis = sc["mode"], sc["axis"]
    rows, t = [], SCHED_SETTLE_S
    for name, dur, val in sc["segments"]:
        if mode == "attitude":
            r = val if axis in ("roll", "rollpitch") else 0.0
            p = val if axis in ("pitch", "rollpitch") else 0.0
            y = val if axis == "yaw" else 0.0
            rows.append((int(round(t * 1e6)), f"att {math.radians(r):.9g} {math.radians(p):.9g} {math.radians(y):.9g} auto"))
        elif mode == "trajectory" and name == "traj":
            for k in range(int(math.ceil(dur / SETPOINT_PERIOD - 1e-9))):  # sim.run(): sp() while t - t_seg0 < dur
                p, v, acc = traj_pva(sc["traj"], k * SETPOINT_PERIOD)
                rows.append((int(round((t + k * SETPOINT_PERIOD) * 1e6)),
                             "pva " + " ".join(f"{x:.9g}" for x in (*p, *v, *acc))))
        elif mode not in ("attitude", "trajectory"):
            raise SystemExit(f"--sched: scenario mode {mode} is not supported")
        t += dur
        if mode == "trajectory" and name == "traj":
            rows.append((int(round(t * 1e6)), "sp_back"))
    if mode == "attitude":
        rows.append((int(round(t * 1e6)), "sp_back"))
    return rows


def sched_anchor_s(sim):
    """T55: instant (sim s) of the offboard anchor the player logged: anchor_us of the last sim_schedule_applied sample.
    The scenario rows are offsets from it, so the segment times in run.json (read by metrics.py) must be based on it, not on
    the runner's own observation of the mode change (HEARTBEAT, up to 1 s late)."""
    out = sim.cli("px4-listener", "sim_schedule_applied", "-n", "1")
    for line in out.splitlines():
        if "anchor_us:" in line:
            v = int(line.split(":")[1])
            if v > 0:
                return v * 1e-6
    raise RunError("sim_schedule_applied has no anchor_us (anchor row not applied)")


def hover_thrust(sim):
    """Last hover_thrust_estimate: (hover_thrust or None, valid flag)."""
    out = sim.cli("px4-listener", "hover_thrust_estimate", "-n", "1")
    ht, valid = None, False
    for line in out.splitlines():
        key, _, val = line.strip().partition(":")
        if key == "hover_thrust":
            try:
                ht = float(val)
            except ValueError:
                pass
        elif key == "valid":
            valid = val.strip().lower() in ("true", "1")
    return ht, valid


def hover_thrust_used(ht, valid, thr_hover_param):
    """Hover thrust mc_att_control centres the stabilized throttle curve on (mc_att_control_main.cpp:237-247):
    a valid finite HTE value clamped to [0.05, 0.9]; otherwise MPC_THR_HOVER as is (PX4 does not clamp the param)."""
    if valid and ht is not None and math.isfinite(ht):
        return min(0.9, max(0.05, ht))
    return thr_hover_param


def hover_meta(ht, valid, thr_hover_param):
    """run.json hover fields for every run (K115 M1/M2): raw HTE, valid flag, param, value used and its source."""
    used = hover_thrust_used(ht, valid, thr_hover_param)
    src = "hte" if (valid and ht is not None and math.isfinite(ht)) else "mpc_thr_hover"
    return {"hover_thrust_estimate": ht, "hover_thrust_valid": valid, "mpc_thr_hover": thr_hover_param,
            "hover_thr_used": used, "hover_thr_source": src}


def run_metrics(out_dir):
    """Run bench/metrics.py on <out_dir>/flight.ulg -> <out_dir>/metrics.json. Never raises; returns a status string."""
    try:
        r = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "metrics.py"),
                            os.path.join(out_dir, "flight.ulg"), "--run-json", os.path.join(out_dir, "run.json"),
                            "--out", os.path.join(out_dir, "metrics.json")],
                           capture_output=True, text=True, timeout=300)
        if r.returncode == 0:
            return "ok"
        tail = (r.stderr or r.stdout).strip().splitlines()[-1:] or [""]
        print("METRICS FAILED:", r.stderr, file=sys.stderr)
        return f"failed rc={r.returncode}: {tail[0][:200]}"
    except Exception as e:  # noqa: BLE001
        return f"failed: {type(e).__name__}: {e}"


def git_info():
    def g(*a):
        return subprocess.run(["git", "-C", REPO, *a], capture_output=True, text=True).stdout.strip()
    return {"commit": g("rev-parse", "HEAD"), "dirty": bool(g("status", "--porcelain", "--untracked-files=no"))}


def make_pilot_sp(sim, a, thr0, meta, sc_steps=False):
    """S118 / F118 --stick-pilot: (neutral_sp, stick_sp(t_seg0, st)); ONE Pilot for the whole stick-mode period (design/i118_stick_pilot.md).

    Active from the first sample sent after the manual mode is observed (neutral samples included); before that the plain sample
    is sent. Reference altitude = altitude at activation + integral of vz_up_demand (0 on neutral rows), kept in the Pilot.
    Measurements are the latest estimator values (LOCAL_POSITION_NED, ATTITUDE) in sim time.
    """
    pilot = stick_pilot.Pilot(a.stick_mode, thr0)
    meta["stick"]["pilot"] = pilot.params()

    def send(smp):
        if sim.main_mode != STICK_MAIN_MODE[a.stick_mode]:
            sim.send_stick(smp)
            return
        base = stick_profile.stick_to_thrust(smp["throttle"], a.stick_mode, thr0)
        c = pilot.track(sim.t, -sim.pos[2], -sim.vz, sim.roll, sim.pitch, smp["vz_up_demand"], base)
        if pilot.active:
            z = stick_profile.stick_to_raw(stick_profile.thrust_to_stick(base + c.thr, a.stick_mode, thr0))
            if steps:  # S136 G5.1: the pilot holds altitude with the throttle only; x / y / r stay the step table
                smp = dict(smp, z=z, throttle=stick_profile.raw_to_stick(z))
            else:
                smp = dict(smp, z=z, throttle=stick_profile.raw_to_stick(z), x=int(round(c.pitch_stick * 1000)),
                           y=int(round(c.roll_stick * 1000)))
        smp.update(pilot_thr=c.thr, pilot_roll=c.roll_stick, pilot_pitch=c.pitch_stick)
        sim.send_stick(smp)

    def neutral():
        send(stick_profile.neutral_sample(a.stick_mode, thr0))

    steps = bool(sc_steps)

    def stick(t_seg0, st):
        return lambda: send(stick_profile.stick_sample(lambda x: traj_pva(st, x), sim.t - t_seg0, a.stick_mode, hover_thr=thr0,
                                                       steps=steps))
    return neutral, stick


def mission_upload(sim, wps, alt_m):
    """MAVLink mission protocol (mission_count, then one MISSION_ITEM_INT per request). wps: (north_m, east_m) of home."""
    if sim.gpos is None:
        sim.run(3.0, what="wait_gpos")
    if sim.gpos is None:
        raise RunError("no GLOBAL_POSITION_INT: cannot place the mission")
    lat0, lon0 = sim.gpos[0] * 1e-7, sim.gpos[1] * 1e-7
    items = [(int((lat0 + n / 111320.0) * 1e7), int((lon0 + e / (111320.0 * math.cos(math.radians(lat0)))) * 1e7))
             for n, e in wps]
    sim.mav.mav.mission_count_send(sim.sysid, 1, len(items), 0)
    t0 = time.time()
    while time.time() - t0 < 30:
        m = sim.mav.recv_match(type=["MISSION_REQUEST_INT", "MISSION_REQUEST", "MISSION_ACK"], blocking=True, timeout=1)
        if m is None:
            continue
        if m.get_type() == "MISSION_ACK":
            if m.type != 0:
                raise RunError(f"mission rejected, MISSION_ACK type {m.type}")
            return {"home_lat": lat0, "home_lon": lon0, "n": len(items)}
        la, lo = items[m.seq]
        sim.mav.mav.mission_item_int_send(sim.sysid, 1, m.seq, 6, 16, 1 if m.seq == 0 else 0, 1, 0.0, 0.0, 0.0,
                                          float("nan"), la, lo, float(alt_m))
    raise RunError("mission upload timeout")


def run_ground_arm(sim, a, meta):
    """S153 --ground-arm: arm on the ground in altctl / posctl with the throttle stick low (no take-off command), hold it low
    3 s, centre it 5 s, climb at about +1 m/s to GA_ALT_M (estimate), centre 5 s, then the normal land. Phase starts -> meta."""
    sim.sp_grid = True
    mode = a.stick_mode
    low = dict(x=0, y=0, z=0, r=0, throttle=-1.0, vz_up_demand=0.0)
    cz = stick_profile.stick_to_raw(stick_profile.inv_expo(GA_CLIMB_MPS / stick_profile.VZ_MAX_UP))
    climb = dict(x=0, y=0, z=cz, r=0, throttle=stick_profile.raw_to_stick(cz), vz_up_demand=GA_CLIMB_MPS)
    cur = [low]
    sp = lambda: sim.send_stick(cur[0])  # noqa: E731
    ph = meta["ground_arm"] = {"phases_us": {}, "climb_stick_raw_z": cz, "target_alt_m": GA_ALT_M}
    mark = lambda n: ph["phases_us"].__setitem__(n, int(sim.t * 1e6))  # noqa: E731
    meta["stick"] = {"mode": mode, "main_mode": STICK_MAIN_MODE[mode], "params": STICK_PARAMS}
    sim.run(1.0, sp=sp, what="ga_prestream")
    sim.cmd(176, 1, STICK_MAIN_MODE[mode], 0)
    sim.run(None, sp=sp, until=lambda: sim.main_mode == STICK_MAIN_MODE[mode], wall_timeout=30, what="ga_mode")
    mark("mode_set")
    mark("arm_cmd")
    for attempt in range(10):
        if sim.cmd(400, 1):
            break
        meta["arm_rejected_t_s"] = meta.get("arm_rejected_t_s", []) + [sim.t]
        sim.run(1.0, sp=sp, what="ga_arm_retry")
    else:
        raise RunError("ground arm rejected 10 times")
    sim.run(None, sp=sp, until=lambda: sim.armed, wall_timeout=30, what="ga_armed")
    meta["t_arm_us"] = int(sim.t * 1e6)
    mark("low")
    sim.run(3.0, sp=sp, what="ga_low")
    cur[0] = stick_profile.neutral_sample(mode)
    mark("centre")
    sim.run(5.0, sp=sp, what="ga_centre")
    cur[0] = climb
    mark("climb")
    sim.run(None, sp=sp, until=lambda: sim.pos and sim.pos[2] <= -GA_ALT_M, wall_timeout=120 + 60 / a.speed, what="ga_climb")
    cur[0] = stick_profile.neutral_sample(mode)
    mark("hold")
    sim.run(5.0, sp=sp, what="ga_hold")
    mark("land_cmd")
    meta["t_land_cmd_us"] = int(sim.t * 1e6)
    sim.cmd(21, 0, 0, 0, float("nan"), float("nan"), float("nan"), 0)
    sim.run(None, sp=sp, until=lambda: not sim.armed, wall_timeout=120 + 120 / a.speed, what="land")
    mark("disarmed")
    sim.run(2.0, what="post_disarm")


def run_auto(sim, a, sc, meta):
    """S131: navigator-driven AUTO flight after arm: takeoff -> hold (loiter) [-> mission] -> RTL | land -> disarm.
    Phase sim times go to meta['auto_phases'] (same time base as the ULog) and the heartbeat mode changes to meta['mode_log']."""
    sim.mode_log, sim.mode_log_last = [], None
    try:
        _run_auto(sim, a, sc, meta)
    finally:
        meta["mode_log"] = sim.mode_log  # [t_s, main, sub, armed], also when the flight failed


def _run_auto(sim, a, sc, meta):
    cfg = sc["auto"]
    ph = meta["auto_phases"] = []

    def mark(name):
        ph.append({"name": name, "t_us": int(sim.t * 1e6), "main": sim.main_mode, "sub": sim.sub_mode})

    for k, v in cfg["params"].items():
        sim.set_param(k, v)
        meta["params_applied"][k] = v
    sim.run(1.0, what="auto_settle")
    mark("armed")
    alt = cfg["takeoff_alt"]
    if sim.gpos is None:
        sim.run(3.0, what="wait_gpos")
    # explicit AMSL altitude (home altitude on the ground + takeoff_alt): the MIS_TAKEOFF_ALT set above did not reach the
    # navigator in the first S131 try ("Using default takeoff altitude: 5.0 m" for a 10 m scenario)
    alt_amsl = (sim.gpos_alt + alt) if sim.gpos is not None else float("nan")
    meta["takeoff_alt_amsl_m"] = alt_amsl
    if not sim.cmd(22, float("nan"), 0, 0, float("nan"), float("nan"), float("nan"), alt_amsl):
        raise RunError("takeoff rejected")
    mark("takeoff_cmd")
    sim.run(None, until=lambda: sim.pos and sim.pos[2] <= -(alt - 0.3), wall_timeout=120 + 120 / a.speed, what="auto_climb")
    mark("takeoff_done")
    sim.wd_start()  # watchdog only once airborne (its height floor would trip on the ground)
    sim.run(cfg["hold_s"], what="auto_hold")
    mark("hold_end")
    if cfg.get("mission"):
        wps = cfg["mission"]
        meta["mission"] = {**mission_upload(sim, wps, alt), "wps_ne_m": wps, "alt_m": alt}
        mark("mission_uploaded")
        for tries in range(5):  # the navigator validates the new mission asynchronously: "Mission start denied! No valid mission"
            sim.run(2.0, what="auto_mission_valid")
            if sim.cmd(300, 0, len(wps) - 1):  # MAV_CMD_MISSION_START (first item 0, last item n-1)
                break
        else:
            raise RunError("MISSION_START rejected 5 times")
        meta["mission_start_tries"] = tries + 1
        sim.reached = -1
        mark("mission_start")
        sim.run(None, until=lambda: sim.reached >= len(wps) - 1, wall_timeout=60 + cfg["mission_max_s"] / a.speed,
                what="auto_mission")
        mark("mission_end")
        sim.run(cfg["post_mission_s"], what="auto_post_mission")
    sim.wd_on = False
    if cfg["end"] == "rtl":
        ok = sim.cmd(20)  # NAV_RETURN_TO_LAUNCH
    else:
        ok = sim.cmd(21, 0, 0, 0, float("nan"), float("nan"), float("nan"), 0)  # NAV_LAND == `commander land`
    mark(cfg["end"] + "_cmd")
    if not ok:
        raise RunError(f"{cfg['end']} rejected")
    sim.run(None, until=lambda: not sim.armed, wall_timeout=120 + 240 / a.speed, what="auto_end")
    mark("disarmed")
    sim.run(2.0, what="post_disarm")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", required=True, choices=sorted(SCENARIOS))
    ap.add_argument("--controller", required=True)
    ap.add_argument("--model-variant", default=None, metavar="K=V,...",
                    help="plant variant scale factors merged over the scenario's model_variant, e.g. mass=1.3,tau=2,tau_up=1.5,"
                         "ixx=0.7 (keys: bench/model_variant.py); applied to --model quad5in or x500, recorded in run.json")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--model", default="quad5in", help="gz model: quad5in (reference airframe) or x500 (archive)")
    ap.add_argument("--params", default=None, help="file with lines 'NAME VALUE' applied before arming")
    ap.add_argument("--out", default=None, help="run dir; default indi_flight/results/<scenario>_<controller>_s<seed>")
    ap.add_argument("--instance", type=int, default=0)
    ap.add_argument("--sim", choices=("v1", "v2", "v2true"), default="v1",
                    help="v1: stock gz_x500 (esc_rpm echoes the command); v2: stage-2 sim, rotor speed through the "
                         "eRPM telemetry model; v2true: stage-2 sim, exact rotor speed in esc_rpm")
    ap.add_argument("--imu-rate", type=int, default=None,
                    help="gz IMU sensor rate in Hz; default = the model's own (quad5in 800, x500 250). Does NOT change "
                         "the physics step (fixed 1.25 ms world, D-SIM-STEP)")
    ap.add_argument("--rate-hz", type=int, choices=RATES_HZ, default=800,
                    help="controller rate = IMU_GYRO_RATEMAX (800: stock PX4 multicopter default, rc.mc_defaults; 400; "
                         "267 = 800/3, the 'reported 250 Hz' point). Sets vehicle_angular_velocity rate")
    ap.add_argument("--vib-acc", type=float, default=0.0, help="v2: IMU vibration accel amplitude per rotor [m/s^2]")
    ap.add_argument("--vib-gyr", type=float, default=0.0, help="v2: IMU vibration gyro amplitude per rotor [rad/s]")
    ap.add_argument("--scenario-overrides", default=None, metavar="FILE.json",
                    help="JSON object whose top-level keys replace (shallow merge) the same keys of the selected scenario: "
                         "thrust_sag, motor_fault, erpm_loss, wind {steady, peak, dir_deg}, disturbance, dist_segment; unknown keys and "
                         "unknown segment names are rejected (bench/scenario_overrides.py); the overrides are recorded in run.json")
    ap.add_argument("--erpm-drop", type=float, default=0.0, help="v2: probability of a dropped eRPM frame")
    ap.add_argument("--sim-seed", type=int, default=0,
                    help="v2: SIM_GZ_SEED, seed of eRPM dropout and extra IMU noise streams (0 = fixed default streams)")
    ap.add_argument("--imu-noise-scale", type=float, default=1.0,
                    help="v2: SIM_GZ_IMU_NSC, total IMU noise stddev multiplier vs the SDF noise (1..10)")
    ap.add_argument("--dly-act", type=int, default=0, choices=range(0, 11), metavar="0..10",
                    help="SIM_GZ_DLY_ACT [ms], motor command delay PX4 -> gz (quantised to the mixer period)")
    ap.add_argument("--dly-imu", type=int, default=0, choices=range(0, 11), metavar="0..10",
                    help="SIM_GZ_DLY_IMU [ms], IMU delay gz -> PX4 (quantised to the IMU period)")
    ap.add_argument("--gps-dly", type=int, default=0, choices=range(0, 251), metavar="0..250",
                    help="SIM_GZ_GPS_DLY [ms], GNSS delivery delay gz -> PX4 (no sample time reported, as the undelayed path; matched compensation is --gnss-delay equal to it)")
    ap.add_argument("--gnss-delay", type=int, default=None,
                    help="SENS_GNSS0_DELAY [ms]; the gz GNSS has no latency but stamps no sample time, so the stock "
                         "110 ms makes the EKF lead the truth by 110 ms (D-s8-gnss-delay); unset keeps the stock value")
    ap.add_argument("--watchdog", choices=("on", "off"), default="on",
                    help="O-12 run watchdog; 'off' is for diagnosis only, never in a batch")
    # default since S22: A-14 (take-off EKF height offset) seen 3/6 without -f, 0/9 with it (results/a14_s21)
    ap.add_argument("--log-from-start", action=argparse.BooleanOptionalAction, default=True,
                    help="logger starts with -f so the log covers the time before arm (--no-log-from-start: from arm)")
    ap.add_argument("--sched-anchor", action="store_true",
                    help="T53: with --sched, append an anchor on offboard (nav_state 14); the rows after it are offsets from it: two sp_hold rows 3 s and 6 s after it (hover) or the scenario rows starting 3 s after it (T55)")
    ap.add_argument("--stick-mode", choices=sorted(STICK_MAIN_MODE), default=None,
                    help="S81: fly a mode='stick' scenario in this manual mode: MANUAL_CONTROL streamed at 50 Hz sim time "
                         "(COM_RC_IN_MODE 1), mode switched by MAV_CMD_DO_SET_MODE after the hover, schedule anchored on "
                         "the observed main mode; sticks.csv in the run dir. Not combinable with --sched")
    ap.add_argument("--ground-arm", action="store_true",
                    help="S153: with --stick-mode altctl|posctl: arm on the ground in that mode (throttle low), no take-off command; "
                         "low 3 s, centre 5 s, climb stick to 3 m, centre 5 s, land (phase times in run.json ground_arm)")
    ap.add_argument("--stick-pilot", action="store_true",
                    help="S118: simulated pilot on the stick scenario in stabilized / acro (altitude PI on thrust, acro levelling); "
                         "corrections logged in sticks.csv, gains in meta.json. Default off")
    ap.add_argument("--sched", action="store_true",
                    help="D-SCHED: arm, offboard switch and the setpoint stream are played by PX4 (sim_scenario_player, "
                         "schedule file in sim time) instead of being sent over MAVLink; position, attitude and trajectory scenarios (T55)")
    ap.add_argument("--paused-start", action="store_true",
                    help="A-17: start gz paused (no -r) and unpause it after --unpause-after appears in px4.log, so "
                         "Commander starts at a fixed sim time (loop phase independent of wall-clock races)")
    ap.add_argument("--unpause-after", default="Startup script returned successfully",
                    help="px4.log pattern after which --paused-start unpauses gz")
    ap.add_argument("--log-poll", default="actuator_motors", help="topic the logger wakes on (logger -p)")
    ap.add_argument("--probe-ff-drag", type=float, default=0.0,
                    help="PROBE ONLY (D-A18-SOURCE): add D*v_ref to the sent acceleration x,y [1/s]; recorded in run.json")
    ap.add_argument("--gate", action="store_true",
                    help="gate-bearing run (G1.7): refuse on a dirty tree or a binary not built from HEAD")
    a = ap.parse_args()
    if a.imu_rate is None:
        a.imu_rate = MODEL_IMU_RATE.get(a.model, 800)
    if a.out is None:
        a.out = os.path.join(RESULTS_DIR, f"{a.scenario}_{a.controller}_s{a.seed}")
    # absolute: child processes (disturbance.py) run with cwd=a.out, so a relative path would resolve under itself
    # and the injector would never see its trigger file (no wrench applied, no error)
    a.out = os.path.abspath(a.out)
    os.makedirs(a.out, exist_ok=True)

    sc = SCENARIOS[a.scenario]
    sc_base = sc
    ov = None
    if a.scenario_overrides:
        try:
            ov = json.load(open(a.scenario_overrides))
            sc = scenario_overrides.merge(sc_base, ov)
        except (OSError, ValueError) as e:  # json.JSONDecodeError is a ValueError
            raise SystemExit(f"--scenario-overrides {a.scenario_overrides}: {e}")
    if a.ground_arm and (a.stick_mode not in ("altctl", "posctl") or a.stick_pilot):
        raise SystemExit("--ground-arm goes with --stick-mode altctl|posctl")
    if a.stick_pilot and not a.stick_mode:
        raise SystemExit("--stick-pilot goes with --stick-mode")
    if (a.stick_mode is not None) != (sc["mode"] == "stick") or (a.stick_mode and a.sched):
        raise SystemExit("--stick-mode goes with a mode='stick' scenario and not with --sched")
    if a.sched and (sc["mode"] not in ("position", "attitude", "trajectory")
                    or any(k in sc_base for k in ("disturbance", "motor_fault", "erpm_loss", "thrust_sag"))):
        raise SystemExit("--sched supports position, attitude and trajectory scenarios without runner-side hooks "
                         "(disturbance, motor_fault, erpm_loss, thrust_sag need the runner's segment times)")
    meta = {"scenario": a.scenario, "controller": a.controller, "seed": a.seed, "speed": a.speed, "sim": a.sim,
            "instance": a.instance, "params_file": a.params, "params_applied": {}, "git": git_info(),
            "noise_seed": {"gz_sim_seed": a.seed, "px4_baro_srand": 1234}, "events": [], "phase_log": [],
            "exit_status": "running", "error": None,
            "physics_step_s": world_step_s(), "world": os.path.join(WORLDS_DIR, "default.sdf"),
            "imu_rate": a.imu_rate, "rate_hz": a.rate_hz,
            "imu_filter_hz": {"IMU_GYRO_CUTOFF": IMU_GYRO_CUTOFF_HZ, "IMU_DGYRO_CUTOFF": IMU_DGYRO_CUTOFF_HZ}}
    meta["probe_ff_drag"] = a.probe_ff_drag  # probe-only (D-A18-SOURCE), 0 = off
    if ov is not None:
        meta["scenario_overrides"] = {"file": os.path.abspath(a.scenario_overrides), "overrides": ov, "merged_keys": sorted(ov),
                                      "merged_hooks": {k: sc[k] for k in ("disturbance", "dist_segment", "wind", "thrust_sag",
                                                                           "motor_fault", "erpm_loss") if k in sc}}
    af_params = os.path.join(HERE_PARAMS, f"{a.model}_indi_g1.params")  # derived airframe INDI parameters (S46/S47)
    af_params = af_params if os.path.exists(af_params) else None
    prov_files = [os.path.join(WORLDS_DIR, "default.sdf"), a.params, af_params]
    prov_files += sorted(glob.glob(os.path.join(MODELS_DIR, a.model, "*")))
    meta["provenance"] = provenance.collect(REPO, BUILD, prov_files)
    meta["gate_bearing"] = a.gate
    if a.gate and provenance.refusal(meta["provenance"]):
        raise SystemExit("G1.7 refuses this gate-bearing run: " + provenance.refusal(meta["provenance"]))
    overlay = read_params(a.params) if a.params else {}
    if overlay.get("MC_INDI_EN", "0").strip() == "1" and overlay.get("MC_RATE_CTL_TYPE", "0").strip() != "1":
        overlay["MC_RATE_CTL_TYPE"] = "1"  # S131: MC_INDI_EN 1 in a params file is an alias of MC_RATE_CTL_TYPE 1
        meta["alias_MC_INDI_EN"] = True
    if a.controller == "indi" and overlay.get("MC_RATE_CTL_TYPE", "0").strip() != "1":
        # S121: without it the INDI module is not started and the run silently flies the stock rate loop
        raise SystemExit("--controller indi needs MC_RATE_CTL_TYPE 1 in the params file (starts mc_indi_rate_control)")
    if af_params and overlay.get("MC_RATE_CTL_TYPE", "0").strip() == "1":
        # every INDI run of an airframe with a derived file flies its G1/G2 under the run's own file, which wins on clash
        base = read_params(af_params)
        meta["airframe_params_file"] = af_params
        meta["airframe_params_used"] = {k: v for k, v in base.items() if k not in overlay}
        overlay = {**base, **overlay}
    clash = {"IMU_GYRO_RATEMAX", "IMU_GYRO_CUTOFF", "IMU_DGYRO_CUTOFF"} & set(overlay)
    if clash:  # the rate and its filters are set by --rate-hz only, so a params file cannot change them unseen
        raise SystemExit(f"params file sets {sorted(clash)}: use --rate-hz (filter cutoffs are fixed)")
    sim = Sim(a)
    t_wall0 = time.time()
    ok = False
    try:
        sim.load_env()
        if o11_build():  # INDI is a module started at boot (O-11): same params files fly old and new binaries
            if overlay.pop("MC_RATE_CTL_TYPE", "0").strip() == "1":
                sim.env["PX4_PARAM_MC_INDI_EN"] = "1"
                meta["boot_params"] = {"MC_INDI_EN": 1}
            overlay.setdefault("MC_INDI_ID_OK", "1")  # S128: bench keeps full K gains (firmware default 0 halves them)
            if "CA_R_W_MAX" in overlay:
                overlay["MC_INDI_W_MAX"] = overlay.pop("CA_R_W_MAX")
            if overlay.pop("MC_INDI_POS_EN", "0").strip() == "1":  # stage 8: outer-loop INDI module, started at boot
                sim.env["PX4_PARAM_MC_INDI_POS_EN"] = "1"
                meta.setdefault("boot_params", {})["MC_INDI_POS_EN"] = 1
        variant = dict(sc.get("model_variant") or {})
        if a.model_variant:
            for kv in a.model_variant.split(","):
                k, sep, v = kv.partition("=")
                try:
                    x = float(v)
                except ValueError:
                    x = float("nan")
                if not sep or not math.isfinite(x) or x <= 0.0:
                    raise SystemExit(f"--model-variant: bad item '{kv}' (want KEY=positive finite scale)")
                variant[k.strip()] = x
        # S102 delay lines (gz_bridge, reboot_required, read at gz_bridge init; 0 = bypassed)
        sim.env["PX4_PARAM_SIM_GZ_DLY_ACT"] = str(a.dly_act)
        sim.env["PX4_PARAM_SIM_GZ_DLY_IMU"] = str(a.dly_imu)
        meta["dly_act_ms"] = a.dly_act
        meta["dly_imu_ms"] = a.dly_imu
        sim.env["PX4_PARAM_SIM_GZ_GPS_DLY"] = str(a.gps_dly)
        meta["gps_dly_ms"] = a.gps_dly
        if a.sim != "v1":  # read once when gz_bridge starts
            if a.model == "x500":  # quad5in/model.sdf already carries the per-step JointStatePublisher
                variant["rpm"] = True
            sim.env["PX4_PARAM_SIM_GZ_ESC_FB"] = "2" if a.sim == "v2" else "1"
            sim.env["PX4_PARAM_SIM_GZ_ERPM_DRP"] = str(a.erpm_drop)
            meta["erpm_drop"] = a.erpm_drop
            sim.env["PX4_PARAM_SIM_GZ_SEED"] = str(a.sim_seed)
            sim.env["PX4_PARAM_SIM_GZ_IMU_NSC"] = str(a.imu_noise_scale)
            meta["sim_seed"] = a.sim_seed
            meta["imu_noise_scale"] = a.imu_noise_scale
            if a.vib_acc > 0 or a.vib_gyr > 0:  # needs the rotor joint speeds of SIM_GZ_ESC_FB >= 1
                sim.env["PX4_PARAM_SIM_GZ_VIB_ACC"] = str(a.vib_acc)
                sim.env["PX4_PARAM_SIM_GZ_VIB_GYR"] = str(a.vib_gyr)
                meta["vib"] = {"acc": a.vib_acc, "gyr": a.vib_gyr}
        if a.gnss_delay is not None:
            sim.env["PX4_PARAM_SENS_GNSS0_DELAY"] = str(a.gnss_delay)
            meta["gnss_delay"] = a.gnss_delay
        for k, v in (sc.get("sim_params") or {}).items():  # scenario plant settings, override the CLI ones
            sim.env[f"PX4_PARAM_{k}"] = str(v)
            meta.setdefault("sim_params", {})[k] = v
        # controller rate: read at boot, so rc.mc_defaults (400 -> 800 set-default) sees the value; cutoffs pinned
        sim.env["PX4_PARAM_IMU_GYRO_RATEMAX"] = str(a.rate_hz)
        sim.env["PX4_PARAM_IMU_GYRO_CUTOFF"] = str(IMU_GYRO_CUTOFF_HZ)
        sim.env["PX4_PARAM_IMU_DGYRO_CUTOFF"] = str(IMU_DGYRO_CUTOFF_HZ)
        if a.imu_rate != MODEL_IMU_RATE.get(a.model, 800):  # sensor rate only; the model copy carries it
            variant["imu_rate"] = a.imu_rate
        if variant:
            meta["model_variant"] = sim.apply_model_variant(variant)
        sim.start_gz()
        sim.start_px4()
        if sc.get("disturbance"):  # idle injector: loads the wrench system, waits for the onset trigger
            sim.spawn(["python3", os.path.join(os.path.dirname(os.path.abspath(__file__)), "disturbance.py"),
                       "--profile", sc["disturbance"], "--out", a.out, "--model", f"{a.model}_0"]
                      + scenario_overrides.wind_flags(sc), "disturbance.stdout")
        for k, v in {**BASE_PARAMS, **(STICK_PARAMS if a.stick_mode else {}), **overlay}.items():
            sim.set_param(k, v)
            meta["params_applied"][k] = v
        # logger reads SDLOG_PROFILE only at start: restart it so the full-rate profile takes effect
        sim.cli("px4-logger", "stop")
        time.sleep(1)
        # -p actuator_motors (last publication of a control cycle): every controller-rate topic is logged in full; the
        # default 3.5 ms timer logged 800 Hz topics at ~285 Hz, -p sensor_gyro lost 10-20 % downstream at speed 1 and 4
        # (S16 pre-test, results/pretest_simstep_s16). -b 200 KiB: 20 KiB gave 44 write dropouts at 800 Hz.
        logger_args = ["px4-logger", "start", "-b", "200", "-t", "-p", a.log_poll]
        meta["log_poll"] = a.log_poll
        if a.log_from_start:
            logger_args.append("-f")
            meta["log_from_start"] = True
        sim.cli(*logger_args)
        sim.wait_log("Ready for takeoff", 180)
        sim.connect()
        sim.run(1.0, what="warmup")  # first ATTITUDE tick makes sim.t valid (it is 0.0 before connect/pump)
        meta["t_arm_target_s"], meta["t_offboard_target_s"] = T_ARM_S, T_OFFBOARD_S
        meta["t_before_arm_wait_s"] = sim.t
        sim.run(None, until=lambda: sim.t >= T_ARM_S, wall_timeout=120 + 2 * T_ARM_S / a.speed, what="wait_t_arm")
        t_arm_sent = sim.t
        attempt = 0
        if a.ground_arm:  # S153: arms inside run_ground_arm (mode first, sticks low), so skip the plain arm below
            run_ground_arm(sim, a, meta)
            ok = True
            return 0
        if a.sched:  # the schedule row arms the vehicle at T_ARM_S sim time; no retry
            meta["sched"] = True
        else:
            for attempt in range(40):  # "Ready for takeoff" can be transient right after boot: retry
                if sim.cmd(400, 1):
                    break
                meta["arm_rejected_t_s"] = meta.get("arm_rejected_t_s", []) + [sim.t]
                sim.run(1.0, what="arm_retry")
            else:
                raise RunError("arm rejected 40 times")
        meta["arm_attempts"] = attempt + 1
        meta["t_arm_sent_s"] = t_arm_sent
        if sim.t - T_ARM_S > LATE_TOL_S:  # visible in run.json: this run flies a shifted time slice
            meta["arm_late_s"] = round(sim.t - T_ARM_S, 3)
        sim.run(None, until=lambda: sim.armed, wall_timeout=30, what="armed")
        meta["t_arm_us"] = int(sim.t * 1e6)
        if sc["mode"] == "auto":  # S131: navigator-driven flight, no offboard / stick phase
            run_auto(sim, a, sc, meta)
            ok = True
            return 0
        if not sim.cmd(22, float("nan"), 0, 0, float("nan"), float("nan"), float("nan"), float("nan")):
            raise RunError("takeoff rejected")
        sim.run(None, until=lambda: (sim.pos and sim.pos[2] <= -(TAKEOFF_ALT - 0.3)) or sim.t > T_HOLD_S - HOVER_MIN_S,
                wall_timeout=120 + 60 / a.speed, what="climb")
        meta["t_climb_done_s"] = sim.t
        if not (sim.pos and sim.pos[2] <= -(TAKEOFF_ALT - 0.3)) or sim.t > T_HOLD_S - HOVER_MIN_S:
            raise RunError(f"climb not finished by t={T_HOLD_S - HOVER_MIN_S:.1f} s (sim t={sim.t:.2f}); "
                           f"T_OFFBOARD_S={T_OFFBOARD_S} would slip")
        sim.wd_start()
        sim.run(None, until=lambda: sim.t >= T_HOLD_S, wall_timeout=120 + 2 * (T_HOLD_S - sim.t) / a.speed,
                what="hover_before_offboard")
        hold_pos, hold_yaw = sim.pos, sim.yaw
        meta["t_hold_s"] = sim.t
        meta["hold_pos_ned"], meta["hold_yaw_rad"] = hold_pos, hold_yaw
        ht, ht_valid = hover_thrust(sim)
        thr_hover_param = sim.get_param_float("MPC_THR_HOVER")
        meta.update(hover_meta(ht, ht_valid, thr_hover_param))
        thr0 = meta["hover_thr_used"]
        def thr_cmd(tilt):
            """Collective thrust: hover estimate / tilt + PD on altitude error (identical for every controller)."""
            e = sim.pos[2] - hold_pos[2]  # NED z: positive = too low
            return max(0.1, min(0.95, thr0 / tilt + ALT_KP * e + ALT_KD * sim.vz))

        # offboard: stream setpoints, then switch mode
        pos_sp = None if a.sched else (lambda: sim.send_pos(hold_pos, hold_yaw))  # noqa: E731
        if a.stick_mode:  # S82: 50 Hz mean on a fixed sim-time grid (ATTITUDE ticks are ~15 ms apart)
            sim.sp_grid = True
            # S81: neutral sticks instead of the position stream (no offboard in this run)
            pos_sp = lambda: sim.send_stick(stick_profile.neutral_sample(a.stick_mode, thr0))  # noqa: E731
            meta["stick"] = {"mode": a.stick_mode, "main_mode": STICK_MAIN_MODE[a.stick_mode], "params": STICK_PARAMS,
                             "hover_thr_used": thr0}
            if a.stick_pilot:  # F118: the pilot starts at the first neutral sample after the mode is observed
                pos_sp, pilot_stick_sp = make_pilot_sp(sim, a, thr0, meta, sc_steps=sc.get("steps"))
        sim.run(None, sp=pos_sp, until=lambda: sim.t >= T_OFFBOARD_S, wall_timeout=60 + 2 * PRESTREAM_S / a.speed,
                what="pre_offboard_stream")
        meta["t_offboard_sent_s"] = sim.t
        if sim.t - T_OFFBOARD_S > LATE_TOL_S:
            meta["offboard_late_s"] = round(sim.t - T_OFFBOARD_S, 3)
        # stage 8: INDI POS replaces offboard and is reported as AUTO (4) / EXTERNALn (sub mode >= 11)
        indip = meta.get("boot_params", {}).get("MC_INDI_POS_EN") == 1
        if a.stick_mode:  # MAV_CMD_DO_SET_MODE, base mode custom, PX4 main mode, no sub mode
            sim.cmd(176, 1, STICK_MAIN_MODE[a.stick_mode], 0)
        elif not a.sched:  # with --sched the mode_offboard row of the schedule file switches the mode
            sim.cmd(176, 1, 6)
        sim.run(None, sp=pos_sp, until=lambda: (sim.main_mode == STICK_MAIN_MODE[a.stick_mode]) if a.stick_mode else (sim.main_mode == 6 or (indip and sim.main_mode == 4 and (sim.sub_mode or 0) >= 11)),
                wall_timeout=30, what="offboard_engage")
        meta["t_offboard_us"] = int(sim.t * 1e6)
        meta["offboard_custom_mode"] = [sim.main_mode, sim.sub_mode]
        sim.run(3.0, sp=pos_sp, what="offboard_settle")
        sched_t0 = None  # T55: scenario start of the player (anchor + SCHED_SETTLE_S); None = the runner's own sim.t
        if a.sched and a.sched_anchor and sc["mode"] != "position":
            sched_t0 = sched_anchor_s(sim) + SCHED_SETTLE_S
            meta["sched_t0_us"] = int(sched_t0 * 1e6)
        seg_elapsed = 0.0

        def seg_now():
            return sched_t0 + seg_elapsed if sched_t0 is not None else sim.t

        # ---- scenario ----
        axis, mode = sc["axis"], sc["mode"]
        meta["t_window_start_us"] = int(seg_now() * 1e6)
        if sc.get("disturbance"):
            # onset = start of the segment named by `dist_segment` (default "dist", PX4 time); the injector (started
            # earlier, idle) reads it
            dist_seg = sc.get("dist_segment", "dist")
            onset = sim.t + sum(d for n, d, _ in sc["segments"][:[n for n, _, _ in sc["segments"]].index(dist_seg)])
            meta["disturbance"] = {"profile": sc["disturbance"], "onset_px4_s": onset, "onset_us": int(onset * 1e6),
                                   "csv": "disturbance.csv", **({"wind": sc["wind"]} if sc.get("wind") else {})}
            json.dump({"onset_px4_s": onset}, open(os.path.join(a.out, "disturbance_trigger.json"), "w"))
        faults = scenario_overrides.fault_entries(sc)  # one dict or a list (weak motor + saturation); scales multiply per motor
        fault = bool(faults)
        if faults:  # plant change: read nominal MIN/MAX of each affected motor's gz channel now (param index = motor + 1)
            # `motor` (one index, T8/H4) or `motors` (list, V' W3): every listed motor gets the entry's thrust scale
            f_ms = [f.get("motors") or [f["motor"]] for f in faults]
            fmotors = sorted({m for ms in f_ms for m in ms})
            nom_all = {fm: {k: sim.get_param(f"SIM_GZ_EC_{k}{fm + 1}") for k in ("MIN", "MAX")} for fm in fmotors}
            cum_scale = {fm: 1.0 for fm in fmotors}  # product of the thrust scales applied so far, per motor
            meta["motor_fault"] = {"motor": fmotors[0], "thrust_scale": faults[0]["thrust_scale"],
                                   "nominal": nom_all[fmotors[0]], "segment": faults[0]["segment"]}
            if len(fmotors) > 1:
                meta["motor_fault"].update({"motors": list(fmotors), "nominal_all": {str(m): v for m, v in nom_all.items()}})
            if len(faults) > 1:
                meta["motor_fault"]["entries"] = copy.deepcopy(faults)
        loss = sc.get("erpm_loss")  # dict(motor, start, end): total eRPM loss from segment start to segment end
        if loss:
            meta["erpm_loss"] = dict(loss)
        sag = sc.get("thrust_sag")  # dict(scale): available thrust ramps linearly 1 -> scale over the window
        if sag:
            sag_t0, sag_dur = sim.t, sum(d for _, d, _ in sc["segments"])
            sag_state = {"next": sim.t, "steps": []}
            meta["thrust_sag"] = {**sag, "t0_us": int(sag_t0 * 1e6), "dur_s": sag_dur, "steps": sag_state["steps"]}

            def sag_tick():  # 0.5 s staircase; one param set per step (PX4 CLI, blocks a few ms of wall time)
                if sim.t >= sag_state["next"]:
                    frac = min(1.0, (sim.t - sag_t0) / sag_dur)
                    v = round(1.0 - frac * (1.0 - sag["scale"]), 4)
                    sim.set_param("SIM_GZ_THR_SC", v, kind="sag", extra=f";frac={frac:.4f};sched_us={int(sag_state['next'] * 1e6)}")
                    sag_state["steps"].append((int(sim.t * 1e6), v))
                    sag_state["next"] += 0.5
        prev = 0.0
        segs = sc["segments"]
        if sc.get("pos_steps") and a.stick_mode == "altctl":  # G5.2: the x step is posctl only
            segs = [x for x in segs if x[0] not in ("xstep", "xhold")]
        for name, dur, val in segs:
            if loss and "end" in loss and name in (loss["start"], loss["end"]):
                on = name == loss["start"]
                sim.set_param("SIM_GZ_ERPM_LOSS", (1 << loss["motor"]) if on else 0)
                meta["erpm_loss"]["on_us" if on else "off_us"] = int(sim.t * 1e6)
            ents = [f for f in faults if f["segment"] == name]
            if ents:
                new_all = fault_apply(cum_scale, ents, nom_all)
                k_om = math.sqrt(cum_scale[fmotors[0]])
                t_req = sim.t
                uniform = set(fmotors) == {0, 1, 2, 3} and len({cum_scale[m] for m in fmotors}) == 1
                if uniform:  # S148 A-48: one atomic param (8 per-motor sets took ~110 ms, asymmetric torque at the edge)
                    sim.set_param("SIM_GZ_THR_SC", cum_scale[fmotors[0]], kind="motor_fault")
                    meta["motor_fault"]["via"] = "SIM_GZ_THR_SC"
                else:
                    for fm in fmotors:
                        for k, v in new_all[fm].items():
                            sim.set_param(f"SIM_GZ_EC_{k}{fm + 1}", v)
                meta["motor_fault"].update({"event_us": int(t_req * 1e6), "event_done_us": int(sim.t * 1e6),
                                            "applied": new_all[fmotors[0]], "omega_ratio": k_om})
                if len(fmotors) > 1:
                    meta["motor_fault"]["applied_all"] = {str(m): v for m, v in new_all.items()}
            segm = (sc.get("seg_modes") or {}).get(name) if a.stick_mode else None
            if segm:  # S139 G5.7 / G5.3: per-segment mode switch (MAV_CMD_DO_SET_MODE), logged with sim time
                mm, ms = SEG_MODE_CUSTOM[segm]
                t_req = sim.t
                ack = sim.cmd(176, 1, mm, ms)
                meta.setdefault("mode_switches", []).append({"segment": name, "mode": segm, "main": mm, "sub": ms,
                                                             "t_cmd_us": int(t_req * 1e6), "t_done_us": int(sim.t * 1e6), "ack": bool(ack)})
            ev = {"name": name, "t_us": int(seg_now() * 1e6), "dur_s": dur, "mode": mode, "axis": axis,
                  "value": val, "prev": prev, "step": name != "settle" and mode not in ("position", "trajectory", "stick", "velocity")}
            meta["events"].append(ev)
            r = val if axis in ("roll", "rollpitch") else 0.0
            p = val if axis in ("pitch", "rollpitch") else 0.0
            y = val if axis == "yaw" else 0.0
            if mode == "trajectory" and name == "traj":
                traj = sc["traj"]
                t_seg0 = seg_now()
                meta["trajectory"] = {**traj, "t0_us": int(t_seg0 * 1e6), "dur_s": dur}

                def sp(t_seg0=t_seg0, traj=traj):
                    p, v, acc = traj_pva(traj, sim.t - t_seg0)
                    acc = [acc[0] + a.probe_ff_drag * v[0], acc[1] + a.probe_ff_drag * v[1], acc[2]]  # probe-only (D-A18-SOURCE)
                    sim.send_pva([hold_pos[i] + p[i] for i in range(3)], v, acc, hold_yaw)
            elif mode == "velocity":  # S133 T7: vx = val [m/s] for the whole segment, vy = vz = 0, no position setpoint
                sp = (lambda vx=val: sim.send_vel([vx, 0.0, 0.0], hold_yaw))
            elif mode == "position" and name in (sc.get("seg_pos") or {}):  # G5.10: NED offset from the hold position
                sp = (lambda o=sc["seg_pos"][name]: sim.send_pos([hold_pos[i] + o[i] for i in range(3)], hold_yaw))
            elif mode in ("position", "trajectory"):
                sp = pos_sp
            elif mode == "stick" and sc.get("seg_sticks"):  # S139: sticks by segment name (stick_profile.seg_sample)
                sp = (lambda n=name: sim.send_stick(stick_profile.seg_sample(sc["seg_sticks"][n], thr0)))
            elif mode == "stick" and sc.get("pos_steps"):  # S138 G5.2: sticks by segment name; x step ends at 3 m of travel
                sp = (lambda n=name: sim.send_stick(stick_profile.pos_step_sample(n)))
                if name == "xstep":
                    p0 = sim.pos
                    meta["pos_steps"] = {"x_start_est_ned": list(p0), "t_xstep_us": int(sim.t * 1e6)}
                    xuntil = lambda: math.hypot(sim.pos[0] - p0[0], sim.pos[1] - p0[1]) >= stick_profile.POS_X_TRAVEL_M  # noqa: E731
            elif mode == "stick":  # S81: the stick sample of the profile at the segment time, neutral outside "stick"
                if name == "stick":
                    t_seg0, st = sim.t, sc["traj"]
                    meta["stick"].update({"t0_us": int(t_seg0 * 1e6), "dur_s": dur, "traj": st})
                    if a.stick_pilot:
                        sp = pilot_stick_sp(t_seg0, st)
                    else:
                        if sc.get("steps"):  # S136 G5.1: roll / pitch / yaw stick steps, throttle at hover
                            sp = (lambda t_seg0=t_seg0: sim.send_stick(stick_profile.stick_sample(
                                lambda tt: ([0, 0, 0], [0, 0, 0], [0, 0, 0]), sim.t - t_seg0, a.stick_mode, hover_thr=thr0, steps=True)))
                        else:
                            sp = (lambda t_seg0=t_seg0, st=st: sim.send_stick(stick_profile.stick_sample(
                                lambda tt: traj_pva(st, tt), sim.t - t_seg0, a.stick_mode, hover_thr=thr0)))
                else:
                    sp = pos_sp
            elif mode == "attitude":
                rr, pp = math.radians(r), math.radians(p)
                tilt = max(0.3, math.cos(rr) * math.cos(pp))
                sp = (lambda rr=rr, pp=pp, yy=hold_yaw + math.radians(y), tilt=tilt:
                      sim.send_att(rr, pp, yy, thr_cmd(tilt)))
            else:
                sp = (lambda r=math.radians(r), p=math.radians(p), y=math.radians(y): sim.send_rate(r, p, y, thr_cmd(1.0)))
            if a.sched:  # T55: the player publishes the setpoints (att / pva rows of sched.txt), the runner only waits
                sp = None
            if sag:
                sp = (lambda sp0=sp: (sag_tick(), sp0() if sp0 else None))
            if loss and "duration_s" in loss and name == loss["start"]:
                # timed eRPM loss (sim time): on at segment start + offset, off `duration_s` later, the rest of the segment as is
                for what, d, bit in erpm_loss_split(dur, loss["start_offset_s"], loss["duration_s"], loss["motor"]):
                    if bit is not None:
                        sim.set_param("SIM_GZ_ERPM_LOSS", bit)
                        meta["erpm_loss"]["on_us"] = int(sim.t * 1e6)
                    if d > 0:
                        sim.run(d, sp=sp, what=f"scenario:{name}:{what}")
                    if what == "loss":
                        sim.set_param("SIM_GZ_ERPM_LOSS", 0)
                        meta["erpm_loss"]["off_us"] = int(sim.t * 1e6)
            else:
                sim.run(dur, sp=sp, until=xuntil if (sc.get("pos_steps") and name == "xstep") else None, what=f"scenario:{name}")
                if sc.get("pos_steps") and name == "xstep":
                    meta["pos_steps"]["x_dur_s"] = sim.t - meta["pos_steps"]["t_xstep_us"] * 1e-6
                    dur = sim.t - meta["pos_steps"]["t_xstep_us"] * 1e-6
            prev = val
            seg_elapsed += dur
        meta["t_window_end_us"] = int(seg_now() * 1e6)
        if sag:
            sim.set_param("SIM_GZ_THR_SC", 1.0)
        if loss and loss.get("end", 1) is None:
            sim.set_param("SIM_GZ_ERPM_LOSS", 0)
        sim.run(4.0, sp=pos_sp, what="recover")  # outside the metrics window

        # ---- land ----
        sim.wd_on = False
        meta["t_land_cmd_us"] = int(sim.t * 1e6)  # sim time (= ULog absolute timestamp) of the NAV_LAND; NOT ulog-start relative
        sim.cmd(21, 0, 0, 0, float("nan"), float("nan"), float("nan"), 0)
        sim.run(None, sp=pos_sp if a.stick_mode else None, until=lambda: not sim.armed,
                wall_timeout=120 + 120 / a.speed, what="land")
        sim.run(2.0, what="post_disarm")
        ok = True
    except Exception as e:  # noqa: BLE001
        meta["error"] = f"{type(e).__name__}: {e}"
        meta["traceback"] = __import__("traceback").format_exc()[-1500:]
        if isinstance(e, WatchdogTrip):
            meta["watchdog"] = e.info
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
        if sim.sticks:
            sim.write_sticks()
            meta["sticks_csv"] = "sticks.csv"
        dsum = os.path.join(a.out, "disturbance_summary.json")  # gust_x injector: vel-None ticks (F-3), absent for other profiles
        if os.path.exists(dsum) and isinstance(meta.get("disturbance"), dict):
            try:
                meta["disturbance"]["injector"] = json.load(open(dsum))
            except ValueError as e:
                meta["disturbance"]["injector"] = {"error": f"unreadable disturbance_summary.json: {e}"}
        meta["wall_time_s"] = round(time.time() - t_wall0, 1)
        meta["exit_status"] = "ok" if ok else "failed"
        json.dump(meta, open(os.path.join(a.out, "run.json"), "w"), indent=1)
        if os.path.exists(os.path.join(a.out, "flight.ulg")):  # metrics read run.json (window): it is written above
            meta["metrics_status"] = run_metrics(a.out)
            json.dump(meta, open(os.path.join(a.out, "run.json"), "w"), indent=1)
        else:
            meta["metrics_status"] = "skipped: no flight.ulg"
            json.dump(meta, open(os.path.join(a.out, "run.json"), "w"), indent=1)
        # keep the out dir small: drop the per-run rootfs (params/dataman/log copies)
        shutil.rmtree(sim.rootfs, ignore_errors=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

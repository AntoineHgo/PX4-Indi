"""Scenario table for the SITL benchmark runner (v0).

All durations are SIM seconds. Every scenario starts after the vehicle hovers at ~5 m in offboard mode.

mode:   "position"  -> hold the position/yaw captured at offboard start
        "attitude"  -> roll/pitch/yaw attitude setpoints (deg, yaw relative to initial yaw), thrust = hover
        "rate"      -> body-rate setpoints (deg/s), thrust = hover
axis:   which channel the segment values drive (roll | pitch | yaw | rollpitch = roll and pitch together)
segments: (name, duration_s, value). `settle` segments are not step events (value 0, lead-in);
          every other segment starts a step from the previous value to `value`.
"""
import math

STEP_DEG = 15.0
DIAG_STEP_DEG = 20.0
YAW_STEP_DEG = 45.0
RATE_STEP_DPS = 120.0

LEMNISCATE = dict(shape="lemniscate", ax=4.0, ay=2.0, w=5.0 / math.sqrt(32.0), laps=2, ramp_s=3.0)
CIRCLE_FAST = dict(shape="circle", r=4.0, z_amp=1.0, w=7.0 / 4.0, laps=3, ramp_s=3.0)


def _traj_dur(traj):
    return 2 * math.pi * traj["laps"] / traj["w"] + traj["ramp_s"]


def _attitude_steps(axis, amp, dur):
    return [
        ("settle", 2.0, 0.0),
        ("up", dur, +amp),
        ("zero1", dur, 0.0),
        ("down", dur, -amp),
        ("zero2", dur, 0.0),
    ]


def _rate_pulses(n=3):
    seq = [("settle", 2.0, 0.0)]
    for i in range(n):
        seq += [(f"pulse{i}_up", 0.25, +RATE_STEP_DPS), (f"pulse{i}_gap1", 2.0, 0.0),
                (f"pulse{i}_down", 0.25, -RATE_STEP_DPS), (f"pulse{i}_gap2", 2.0, 0.0)]
    return seq


SCENARIOS = {
    "hover": dict(mode="position", axis=None, segments=[("hold", 30.0, 0.0)]),
    "step_roll": dict(mode="attitude", axis="roll", segments=_attitude_steps("roll", STEP_DEG, 3.0)),
    # T9: plant mismatch, Ixx and Iyy x1.3 in the sim (controllers unchanged), T2 attitude step pattern.
    # model_variant: scale factors, see bench/model_variant.py (reused by held-out H5).
    "mismatch_inertia": dict(mode="attitude", axis="roll", segments=_attitude_steps("roll", STEP_DEG, 3.0),
                             model_variant=dict(ixx=1.3, iyy=1.3)),
    "step_pitch": dict(mode="attitude", axis="pitch", segments=_attitude_steps("pitch", STEP_DEG, 3.0)),
    "step_yaw": dict(mode="attitude", axis="yaw", segments=_attitude_steps("yaw", YAW_STEP_DEG, 4.0)),
    # Held-out H6: simultaneous roll and pitch steps.
    "step_diag": dict(mode="attitude", axis="rollpitch", segments=_attitude_steps("rollpitch", DIAG_STEP_DEG, 3.0)),
    "rate_step_roll": dict(mode="rate", axis="roll", segments=_rate_pulses(3)),
    # Held-out H5: combined plant mismatch (inertia x0.8 on all three axes, mass x1.15, motor time constants x2),
    # flown as two runs: the T2 attitude step pattern and the T4 rate pulses (D-h5).
    "mismatch_combined_att": dict(mode="attitude", axis="roll", segments=_attitude_steps("roll", STEP_DEG, 3.0),
                                  model_variant=dict(ixx=0.8, iyy=0.8, izz=0.8, mass=1.15, tau=2.0)),
    # Diagnostics for H5 (not part of the benchmark, never used for tuning): each H5 plant change on its own.
    "diag_h5_tau": dict(mode="attitude", axis="roll", segments=_attitude_steps("roll", STEP_DEG, 3.0),
                        model_variant=dict(tau=2.0)),
    "diag_h5_inertia": dict(mode="attitude", axis="roll", segments=_attitude_steps("roll", STEP_DEG, 3.0),
                            model_variant=dict(ixx=0.8, iyy=0.8, izz=0.8, mass=1.15)),
    "mismatch_combined_rate": dict(mode="rate", axis="roll", segments=_rate_pulses(3),
                                   model_variant=dict(ixx=0.8, iyy=0.8, izz=0.8, mass=1.15, tau=2.0)),
    # Trajectories (mode "trajectory"): the segment named "traj" flies a closed path from the hold position with
    # position, velocity and acceleration feedforward (bench/run_scenario.py traj_pva); other segments hold position.
    # T5: Gerono lemniscate 8 m x 4 m, peak speed 5 m/s (w = 5 / sqrt(32)), 2 laps.
    "traj_lemniscate": dict(mode="trajectory", axis=None, traj=LEMNISCATE,
                            segments=[("settle", 3.0, 0.0), ("traj", _traj_dur(LEMNISCATE), 0.0), ("hold", 3.0, 0.0)]),
    # Held-out H1: circle radius 4 m at 7 m/s (w = 1.75 rad/s) with a +-1 m vertical sine (2 m peak to peak), 3 laps.
    "traj_circle_fast": dict(mode="trajectory", axis=None, traj=CIRCLE_FAST,
                             segments=[("settle", 3.0, 0.0), ("traj", _traj_dur(CIRCLE_FAST), 0.0), ("hold", 3.0, 0.0)]),
    # Held-out H4: motor 2 thrust x0.6 from the start of the T5 lemniscate.
    "motor_loss_2": dict(mode="trajectory", axis=None, traj=LEMNISCATE,
                         motor_fault=dict(segment="traj", motor=2, thrust_scale=0.6),
                         segments=[("settle", 3.0, 0.0), ("traj", _traj_dur(LEMNISCATE), 0.0), ("hold", 3.0, 0.0)]),
    # Disturbance scenarios (bench/disturbance.py). Position mode; the segment named "dist" starts the disturbance
    # profile (profile time 0 = start of that segment). The key `disturbance` selects the injector profile.
    # gust_x: profile 28 s = 2 ramp + 10 hold + 1 gust + 15 hold at 3 m/s. payload_add: step held 30 s.
    "gust_x": dict(mode="position", axis=None, disturbance="gust_x",
                   segments=[("settle", 10.0, 0.0), ("dist", 28.0, 0.0)]),
    "payload_add": dict(mode="position", axis=None, disturbance="payload_add",
                        segments=[("settle", 10.0, 0.0), ("dist", 30.0, 0.0)]),
    # Held-out H2/H3, same structure as T6/T7 (profiles in bench/disturbance.py).
    "gust_diag": dict(mode="position", axis=None, disturbance="gust_diag",
                      segments=[("settle", 10.0, 0.0), ("dist", 27.6, 0.0)]),
    "com_shift": dict(mode="position", axis=None, disturbance="com_shift",
                      segments=[("settle", 10.0, 0.0), ("dist", 30.0, 0.0)]),
    # Plant fault (T8): attitude mode (level hold + yaw step). At the start of the segment named "loss" the runner sets
    # SIM_GZ_EC_MIN1/MAX1 (motor 0) to sqrt(scale) x their start value; omega = MIN + (MAX-MIN)*c and gz thrust ~ omega^2, so
    # thrust of motor 0 is `scale` x nominal at every command. Same plant change for every controller.
    # segments: 5 s settle, 10 s hold with the weak motor, 45 deg yaw step 4 s, back to 0 for 4 s.
    "motor_loss_0": dict(mode="attitude", axis="yaw", motor_fault=dict(segment="loss", motor=0, thrust_scale=0.7),
                         segments=[("settle", 5.0, 0.0), ("loss", 10.0, 0.0), ("up", 4.0, +YAW_STEP_DEG),
                                   ("zero", 4.0, 0.0)]),
}

"""Scenario table for the SITL benchmark runner (v0).

All durations are SIM seconds. Every scenario starts after the vehicle hovers at ~5 m in offboard mode.

mode:   "position"  -> hold the position/yaw captured at offboard start
        "attitude"  -> roll/pitch/yaw attitude setpoints (deg, yaw relative to initial yaw), thrust = hover
        "rate"      -> body-rate setpoints (deg/s), thrust = hover
axis:   which channel the segment values drive (roll | pitch | yaw | rollpitch = roll and pitch together)
segments: (name, duration_s, value). `settle` segments are not step events (value 0, lead-in);
          every other segment starts a step from the previous value to `value`.
"""

STEP_DEG = 15.0
DIAG_STEP_DEG = 20.0
YAW_STEP_DEG = 45.0
RATE_STEP_DPS = 120.0


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
    "step_pitch": dict(mode="attitude", axis="pitch", segments=_attitude_steps("pitch", STEP_DEG, 3.0)),
    "step_yaw": dict(mode="attitude", axis="yaw", segments=_attitude_steps("yaw", YAW_STEP_DEG, 4.0)),
    # Held-out H6: simultaneous roll and pitch steps.
    "step_diag": dict(mode="attitude", axis="rollpitch", segments=_attitude_steps("rollpitch", DIAG_STEP_DEG, 3.0)),
    "rate_step_roll": dict(mode="rate", axis="roll", segments=_rate_pulses(3)),
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

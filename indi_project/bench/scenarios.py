"""Scenario table for the SITL benchmark runner (v0).

All durations are SIM seconds. Every scenario starts after the vehicle hovers at ~5 m in offboard mode.

mode:   "position"  -> hold the position/yaw captured at offboard start
        "attitude"  -> roll/pitch/yaw attitude setpoints (deg, yaw relative to initial yaw), thrust = hover
        "rate"      -> body-rate setpoints (deg/s), thrust = hover
axis:   which channel the segment values drive (roll | pitch | yaw)
segments: (name, duration_s, value). `settle` segments are not step events (value 0, lead-in);
          every other segment starts a step from the previous value to `value`.
"""

STEP_DEG = 15.0
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
    "rate_step_roll": dict(mode="rate", axis="roll", segments=_rate_pulses(3)),
}

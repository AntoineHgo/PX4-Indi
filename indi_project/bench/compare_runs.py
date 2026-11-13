#!/usr/bin/env python3
"""Print a markdown table comparing metrics.json of several run dirs side by side.
usage: compare_runs.py LABEL=DIR [LABEL=DIR ...]"""
import json
import sys

ROWS = [("rate rms roll [rad/s]", "rate_tracking.roll_rms_rad_s"), ("rate rms pitch [rad/s]", "rate_tracking.pitch_rms_rad_s"),
        ("rate rms yaw [rad/s]", "rate_tracking.yaw_rms_rad_s"), ("att rotation rms [deg]", "attitude_tracking.rotation_angle_rms_deg"),
        ("att roll rms [deg]", "attitude_tracking.roll_rms_deg"), ("step delay10 mean [s]", "step_summary.delay_10pct_s_mean"),
        ("step rise 10-90 mean [s]", "step_summary.rise_10_90_s_mean"), ("step overshoot mean [%]", "step_summary.overshoot_pct_mean"),
        ("step settle 5% mean [s]", "step_summary.settle_5pct_s_mean"), ("pos rms 3d [m]", "position.rms_3d_m"),
        ("pos rms horiz [m]", "position.rms_horizontal_m"), ("pos rms vert [m]", "position.rms_vertical_m"),
        ("pos max dev 3d [m]", "position.max_dev_3d_m"), ("motor rate rms [1/s]", "effort.motor_rate_rms_per_s"),
        ("motor spread mean|u-mean| ", "effort.motor_spread_mean_abs"), ("motor mean", "effort.motor_mean"),
        ("saturation frac (motors)", "effort.saturation_frac_motors"), ("allocator sat frac", "allocator.frac_any_actuator_saturation"),
        ("window duration [s]", "window.duration_s")]


def get(d, path):
    for p in path.split("."):
        d = d.get(p) if isinstance(d, dict) else None
    return d


runs = [a.split("=", 1) for a in sys.argv[1:]]
data = [json.load(open(f"{d}/metrics.json")) for _, d in runs]
print("| metric | " + " | ".join(l for l, _ in runs) + " |")
print("|---|" + "---|" * len(runs))
for name, path in ROWS:
    vals = [get(m, path) for m in data]
    if all(v is None for v in vals):
        continue
    print(f"| {name} | " + " | ".join("-" if v is None else f"{v:.4g}" for v in vals) + " |")

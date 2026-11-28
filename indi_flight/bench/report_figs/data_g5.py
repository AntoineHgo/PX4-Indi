"""G5 worst-case transient per row against its limit.

Values are the ones printed in report/03_validation.md section 3.5 (worst case over 3 seeds, INDI) and the limits
printed there; tests/test_figs.py checks that every number below occurs in that chapter. Source files:
results/freeze10_s193/G5_SCORES.md, G5_VERDICT_AUDIT.md, G5_5_RESCORE_Q25.md, g5_gaps_s198/moving/G58_KEY1.md.
"""
# label, worst value, limit, unit, PID reference value or None
ROWS = [
    ("Acro steps, rate error", 1.94, 10.0, "deg/s", None),
    ("Stabilized release, tilt", 0.12, 3.0, "deg", None),
    ("Position hold in wind, 3-D RMS", 0.062, 0.3, "m", None),
    ("Mission, waypoint error", 0.970, 1.0, "m", None),
    ("Return to launch, height error", 0.062, 1.0, "m", None),
    ("Offboard trajectory o2, H RMS", 0.5027, 0.5685, "m", None),
    ("Mode switch, attitude jump", 3.98, 5.0, "deg", None),
    ("Link loss at 3 m/s, excursion", 0.25, 1.0, "m", 0.514),
    ("Re-arm, take-off handover step", 4.7, 10.0, "% of hover", None),
    ("Stabilized full scale, attitude error", 0.24, 5.0, "deg", None),
    ("EKF yaw reset, excursion", 0.040, 0.5, "m", None),
    ("EKF position reset, excursion", 0.248, 0.5, "m", None),
]

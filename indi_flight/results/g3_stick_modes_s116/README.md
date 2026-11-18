# S116 A116: stick_zsine_o6 flyability in ALTCTL and POSCTL (INDI, quad5in, 800 Hz)

Pre-test, 3 flights, commands in fly.sh (ladder s116 nominal command with --stick-mode changed). Agent haiku A116,
README written by the orchestrator from the agent report.

| row | mode | rc | exit_status | main_mode | horiz RMS | vert RMS / max |
|---|---|---|---|---|---|---|
| m1 altctl | altctl | 0 | ok | 2 | 0.12 m | 1.03 / ~2.2 m |
| m2 posctl | posctl | 0 | ok | 3 | 0.03 m | 1.04 / ~2.2 m |
| m3 posctl_sag07 | posctl + thrust_sag 0.7 from 55.49 s for 24 s (applied record in run.json) | 0 | ok | 3 | 0.03 m | 0.66 / 1.58 m |

All three FLY (no abort). Interpretation limits:
- In ALTCTL/POSCTL the z-sine throttle stick is a climb-rate command, so vertical deviation from the hold altitude is
  commanded motion, not tracking error. metrics.py also warned that it found no offboard/INDI nav_state span, so its
  window is not the stick window. The vertical numbers (including the lower m3 value under sag, which is consistent
  with a sag-limited climb) are NOT a tracking metric. Before these modes enter a campaign, the metric needs a stick
  reference (integrated commanded climb rate / held position) and a stick-mode window.
- Reached mode rests on run.json main_mode (px4.log does not print mode switches).

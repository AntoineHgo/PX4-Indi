# G3 single-factor check S113: does mass x1.3 alone cause the pre-stick altitude loss? (stick_zsine_o6, stabilized)

Result: NO. Nominal mass (control) and PID lose altitude identically at the same instant. The cause is the scenario's
stabilized-mode thrust hand-off, not mass and not the INDI controller. Not a controller finding.

## Commands (fly.sh in this directory, one draw-independent run_scenario.py call each; base params quad5in_indi_g1.params as given)
indi_project/docker/run.sh -n g3s_NAME -t 900 -- python3 indi_flight/bench/run_scenario.py --scenario stick_zsine_o6 --controller CTRL \
  --model quad5in --sim v2 --rate-hz 800 --seed 768592122 --sim-seed 680969658 --out RUN --params indi_flight/bench/params/quad5in_indi_g1.params \
  --stick-mode stabilized [--model-variant mass=1.3]
Same flags as g3_run.py emits (mode stabilized taken from the seed14/run_018 dry-run); no wind, motor fault, eRPM loss, telemetry latency, vibration,
loop delay, GNSS delay, inertia/tau variants, no G1 multiplier. mass enters only as --model-variant mass=1.3 (plant), no controller-side change.
A: indi, mass 1.3 | C: indi, mass 1.0 | B: pid_default, mass 1.0 (PID run uses the same INDI params file; MC_INDI_* is unused by PID, not checked).
Analysis: an.py / an2.py (pyulog, ground truth vehicle_local_position_groundtruth, vehicle_thrust_setpoint, vehicle_status).

## Results (sim time == ulog time within 0.01 s; log time axis starts at 0)
| run | exit | gt alt 50 s | 52 s | 53 s | 54 s | 55.5 s | thrust sp before -> after 52.0 s | watchdog |
|---|---|---|---|---|---|---|---|---|
| A indi m1.3 | failed | 5.00 | 5.00 | ~3.3 (4.34 at 52.7, 1.51 at 53.5) | not reached | not reached | 0.178 -> 0.115 | height<0.3 m at 53.67 s |
| C indi m1.0 | failed | 4.96 | 4.96 | ~3.0 (4.15 at 52.8, 1.45 at 53.6) | not reached | not reached | 0.137 -> 0.095 | 53.79 s |
| B pid m1.0 | failed | 4.95 | 4.96 | ~3.0 (4.12 at 52.8, 1.39 at 53.6) | not reached | not reached | 0.137 -> 0.095 | 53.78 s |
(53 s altitudes are read off neighbouring samples, not exact.)
vehicle_status nav_state (identical in all three): 4 loiter (takeoff 17 at ~30.6 s, loiter 39 s) -> 15 (STABILIZED) at sim 52.02 s. land detector: airborne
(landed=0) from the takeoff, no landing state before the abort. Altitude is at 5 m and level until the 52.0 s mode switch, then falls.

## What the scenario commands at 52-55.5 s
Scenario stick_zsine_o6 = settle 3 s, stick, hold 3 s (scenarios.py:162); the runner switches the main mode to stabilized at 52.02 s and streams
MANUAL_CONTROL with constant throttle z=178 (A) / 137 (B, C) (sticks.csv: throttle_applied -0.644 in A), i.e. stick = 2*hover_thr-1 with hover_thr the hover
thrust estimate (stick_profile.py:54/63). The "settle" segment (55.5 s in the G3 events) is timed from the observed mode, 3.5 s after the switch.
So the 52-55.5 s window is not a mode switch + level hold at the hover thrust: PX4's stabilized mode maps that stick value to a collective thrust
only 0.65 (A) / 0.69 (B, C) of the hover thrust (0.115 vs 0.178, 0.095 vs 0.137), a ~30 % thrust deficit, so the vehicle falls ~3.5 m/s^2 and hits
the 0.3 m watchdog about 1.7 s after the switch, before the settle segment.

## Conclusion
Mass x1.3 alone is not the cause: nominal-mass INDI and nominal-mass PID reproduce the same descent at the same time (mode switch 52.02 s, abort
53.7-53.8 s), with the same thrust step ratio. This is a set-up fault of the stabilized stick scenario (stick-to-thrust mapping at the hand-over does not
equal hover thrust), so the seed8/14 aborts say nothing about robustness; any stabilized-mode G3 draw will abort the same way, mass or not.
UNVERIFIED: the exact PX4 mapping that turns stick (z/1000 = hover thrust) into 0.65-0.69 x hover thrust (MPC_THR_CURVE / MPC_THR_HOVER / MANTHR
scaling in the PX4 stabilized path was not read or tested); why earlier S81 stabilized flights did or did not survive was not checked; altctl/posctl/acro
modes were not flown here (those draws in G3 may not be affected; the seed3 run_007 control, mode not checked, also lost height before 58.5 s).
Fix direction (not done): derive the stick value from the inverse thrust curve, or hold the thrust with the position controller until the settle begins.

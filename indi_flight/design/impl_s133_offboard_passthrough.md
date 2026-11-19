# S133 T8 / T7 / T9: pass-through and offboard-without-position probes (MC_INDI_POS_EN=1, 1 seed each)

## T8 ACRO (flown, PASS)
Command: `indi_project/docker/run.sh -n s133acro -t 800 -- python3 indi_flight/bench/run_scenario.py --scenario stick_zsine_o6 --stick-mode acro --controller indi --model quad5in --seed 1 --speed 4 --sim v2 --params indi_flight/results/s133_passthrough/params.params --out indi_flight/results/s133_passthrough/acro` (params = S131 file: MC_INDI_EN 1, MC_INDI_POS_EN 1, MC_RATE_CTL_TYPE 1). The runner supports ACRO (STICK_MAIN_MODE acro=5); the zsine profile is a thrust-only stick (thrust about hover), roll/pitch/yaw sticks neutral.
Checker: `bench/passthrough_check.py flight.ulg` (new).
Method for publisher attribution: ulog has no publisher id. Used (1) vehicle_control_mode flags (position/velocity/altitude all 0 in 71 of 171 samples, nav_state 10 = ACRO), (2) every vehicle_attitude_setpoint / indi_pos_status sample mapped to the preceding vehicle_control_mode sample. LIMIT: this proves no attitude setpoint is logged while the flags are off, not who would have published; only one instance (multi_id 0) exists for each topic, so a second publisher cannot be separated. vehicle_thrust_setpoint is published by the rate controller (mc_indi_rate_control) in every mode, so it cannot attribute IPC; IPC thrust goes through vehicle_attitude_setpoint.thrust_body, covered by (2).
Results:
- vehicle_attitude_setpoint samples while pos/vel/alt all off: 0 of 4186; indi_pos_status samples while all off: 0 of 2674 (the module goes idle in ACRO).
- Flight: no loss of control, tilt max 0.5 deg (mean 0.1) over the ACRO window (the stick had roll/pitch neutral), altitude 0..10.5 m (zsine), horizontal drift max 1.3 m. Note the nav_state 10 window runs 52.0..101.2 s (the runner's final land also happens in ACRO with the stick script).

## T7 offboard velocity-only (flown, PASS)
Added: `Sim.send_vel` (bench/run_scenario.py:490, type mask 0b100111000111: velocity + yaw used, position/acc/yaw-rate ignored), scenario mode "velocity" (run_scenario.py:~1172, segment value = vx m/s, vy = vz = 0), scenario `offb_vel_step` (bench/scenarios.py:204: settle 3 s, vstep 5 s at 2 m/s, vhold 4 s at 0). The prestream before the offboard switch is still the runner's position setpoint (needed to enter offboard); the scenario window is velocity-only. Checker `bench/offb_vel_check.py run_dir`.
Command: same as T8 with `--scenario offb_vel_step` (no --stick-mode), `--out .../vel`.
- vehicle_control_mode in the window: velocity, altitude, climb-rate flags 1 in all 137 samples, manual 0 (position flag toggled 0/1 during the flight, in the velocity-only part IPC ran in velocity control). Nothing is published as attitude setpoint with all three off (0 of 5745).
- vx step vs vehicle_local_position_groundtruth: RMS error over the 5 s 0.62 m/s (dominated by the rise: 90 % of 2 m/s after 1.93 s); last 3 s RMS 0.092 m/s, mean 1.92 m/s. Hold at 0: vx back to 0.07 m/s, 8.3 m travelled in the step, 10.0 m at the end of the hold (braking 1.7 m).
- z hold: reference 5.03 m, max |dz| 0.040 m, RMS 0.018 m; vy RMS 0.013 m/s.
- Acceleration-only setpoints: NOT possible with the runner's offboard path (send_pva always sends position too; no accel-only sender). Skipped, not tested.
- Take-off from the ground on an offboard setpoint alone (want_takeoff, McIndiPosControl.cpp ~706-733): NOT tested; the runner arms and takes off with `commander takeoff` (nav_state 17) then switches to offboard, there is no arm-in-offboard-from-ground path.

## T9 thrust step at take-off -> flight and hover-thrust valid edges (checker `bench/t9_step_check.py`)
Largest consecutive-sample step of vehicle_thrust_setpoint z within +-0.1 s of the edge, as a fraction of the late hover thrust (0.137):
| log | takeoff_state 4->5 (rampup->flight) | hover_thrust_estimate first valid | flight->land edge |
| vel | 0.0014 = 1.03 % PASS | 0.0008 = 0.61 % PASS | 5->3: 0.049 (36 %), land phase, not in scope |
| acro | 0.0084 = 6.12 % FAIL (<2 % required) | 0.0010 = 0.70 % PASS | same |
The acro step is one jump 0.1453 -> 0.1537 between 34.03 and 34.04 s (edge at 34.02 s, first indi_pos_status sample 34.28 s), same tick pattern as the vel run which stays smooth (0.1461 -> 0.1469 -> 0.1483). The two flights have the same take-off sequence (nav takeoff, identical edge times 30.02/31.02/34.02), only the later phase differs, so the difference is run-to-run (one seed each) or related to acro being armed with different manual state at take-off; the cause is UNVERIFIED. Who published that thrust (IPC bypass or the navigator takeoff path) cannot be read from the log, only that it is one 20 ms-tick step of 0.0084, ~6 % of hover. Needs a repeat before calling it a regression of 7770538b55.

## Summary table
| mode | flown | pass/fail | key metric |
| ACRO (stick_zsine_o6) | y | PASS | 0 of 4186 att_sp and 0 of 2674 indi_pos_status samples with pos/vel/alt flags all off; tilt max 0.5 deg |
| Offboard velocity-only (offb_vel_step) | y | PASS | vx RMS 0.092 m/s last 3 s (0.62 over 5 s incl. 1.9 s rise), z max dev 0.040 m |
| Offboard accel-only | n | not testable (no sender) | - |
| Offboard take-off from ground | n | not tested | - |
| T9 takeoff->flight thrust step | y (2 logs) | vel PASS 1.03 %, acro FAIL 6.12 % | see above |

Results: indi_flight/results/s133_passthrough/{acro,vel} (README.md there). New files: bench/passthrough_check.py, bench/offb_vel_check.py, bench/t9_step_check.py. Scenario row: bench/scenarios.py:204; runner edits: bench/run_scenario.py:490 and ~1172.
UNVERIFIED: publisher attribution (limits above); cause of the 6 % acro step; 1 seed each; no unit test for send_vel/velocity mode; "ACRO" window also contains the final land.

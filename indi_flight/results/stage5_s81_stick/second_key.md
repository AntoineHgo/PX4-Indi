# Second key: stick-path stub vs brief_rc_stub_s80.md

Scope: code at a1f2b3b124 (bench) and 53b38dd54e (results). Read-only: no docker, build or flight run; no test executed.
Line numbers refer to `git show a1f2b3b124:<path>`.

## Brief items

- OK  1a `--stick-mode {altctl,posctl,stabilized,acro}`: run_scenario.py:640-643 (choices from STICK_MAIN_MODE, :91).
- OK  1b `COM_RC_IN_MODE` = 1 "MAVLink only": run_scenario.py:92. Brief asked for the value names from this branch's metadata; src/modules/commander/commander_params.yaml:62-71 gives 1 = "MAVLink only (disables RC checks)". Correct.
- OK  1c Stream `manual_control_send` on a fixed sim-time grid at 50 Hz: run_scenario.py:166 (sp_period 0.02), :449 (grid `max(next_sp + period, t)`), :478-481 (send_stick). Measured 50.0 Hz only for indi_posctl (see README line below).
- OK  1d Mode switch by MAV_CMD_DO_SET_MODE with PX4 custom main mode, after take-off: run_scenario.py:818 `cmd(176, 1, main_mode, 0)`; takeoff is the pre-existing command at :767-781, which precedes the switch. Main modes 2/3/5/7 match px4_custom_mode.h.
- MISSING 1e "anchor the schedule on the observed nav_state of that mode (generalise --sched-anchor beyond nav_state 14)": not implemented. --sched-anchor is still only used with --sched (run_scenario.py:827-828, guarded by `a.sched`), and --stick-mode with --sched is refused (:667). Stick segments are timed on sim time from the segment start, not anchored on nav_state. Neither the commit nor the README claims this item.
- OK  2a `mode="stick"` scenario, z profile from ZSINE_O6, hold segment: scenarios.py:161-163 (settle 3 s, stick over ZSINE_O6 duration, hold 3 s). ZSINE_O6 is defined at scenarios.py:29.
- OK  2b Throttle stick = vertical-velocity demand in altctl/posctl, expo inverted: stick_profile.py:52 `inv_expo(vz_up / vz_max)`, VZ_MAX_UP 3.0 (:11) matches MPC_Z_VEL_MAX_UP/_DN set at run_scenario.py:92-93. The 0.6 expo is confirmed as hard-coded in src/lib/sticks/Sticks.hpp:70 (`getThrottleZeroCenteredExpo(float expo = .6f)`). Not verified: the body of `expoDeadzone` (Sticks.cpp), so the forward formula `(1-e)v + e v^3` in stick_profile.py:27-29 is taken from the docstring, not read from source.
- OK  2c Sticks logged with sim time to `sticks.csv` (applied values): run_scenario.py:478-481 (append of t_sim_us and applied z), :483-488 (write_sticks, header t_sim_us,x,y,z,r,throttle_applied,vz_up_demand_mps), :961 (written at the end of the run). The log also contains the neutral pre-stream and settle samples, which stick_check.py filters by window.
- OK  2d Axes and ranges: x pitch, y roll, z throttle in [0,1000] with 500 centre, r yaw; clipping in stick_to_raw (stick_profile.py:17-19). Call order `manual_control_send(sysid, x, y, z, r, 0)` (run_scenario.py:481) matches the MAVLink field order. Sign: vz_up = -vel_z (NED), so stick up = climb (stick_profile.py:50). Not verified: PX4 decode in mavlink_receiver.cpp (not read).
- OK  2e Stabilized/acro thrust mapping: stick = 2 thr - 1 + 0.15 vz/3 (stick_profile.py:54). The code marks it "unverified shape, only a flight stub", so this is consistent with the brief's "not flown" status. Not verified against PX4 thrust decode.
- OK  3a Pre-test code path exists and writes metrics.json, run.json, README.md, stick_check.json under results/stage5_s81_stick/ (53b38dd54e). NOTES.md is present.
- DEVIATION 3b Pre-test pass criteria (manual_control_setpoint >= 40 Hz, nav_state as requested, vehicle follows demand): stick_check.json in 53b38dd54e: pid_altctl 33.4 Hz, follows_demand false; pid_posctl 33.3 Hz, false; indi_altctl 33.3 Hz, false; indi_posctl 50.0 Hz, true. Three of four required runs fail the >= 40 Hz criterion and the follows_demand test (stick_check.py:41 requires rate >= 40). nav_state matches the requested mode in all four. The three 33 Hz runs were flown before the grid change, per the README, so they do not test the committed pacing. The brief's acceptance was not met for altctl at all.
- OK  4 Self-test on synthetic input with known answers: indi_flight/bench/tests/test_stick_profile.py:15-44 (known samples at t = 0, pi/2w, 3pi/2w; inverse-expo round trip; clip and mode checks; ZSINE_O6 peak = pi/2). Not executed (read-only). Weak assertion: line 21 `s["z"] == (500 if want_up == 0 else s["z"])` is always true for non-zero demand.

## Constraints

- OK  Firmware not changed: a1f2b3b124 and 53b38dd54e touch only indi_flight/bench and indi_flight/results.
- OK (by reading) Offboard behaviour unchanged: `sp_grid` defaults False (:167), so the `t + period` branch is kept (:449); params merge is empty without --stick-mode (:741); land uses `sp=None` unless stick. Byte-identity of sched.txt NOT checked (brief asked for it). Unverified.
- Unverified: wall-clock timeout on the stick segment loop (only the pre-stream, offboard_engage and land calls were read).

## README claims vs code and results

- DEVIATION "Status: stub works in ALTCTL and POSCTL on both stacks": altctl runs are 33.3 Hz and follows_demand false for pid_altctl and indi_altctl; pid_posctl is also false. Only indi_posctl meets the brief's criterion.
- DEVIATION "PID and INDI give the same gain and lag to 0.005": posctl gains are 0.858 (PID) and 0.850 (INDI), a 0.008 gap, and lags are 120 ms vs 100 ms. The INDI posctl run was re-flown at a different pacing, so the comparison is not like-for-like.
- OK "gain 0.30 came from expo 0.6, inverting gives 0.86": consistent with the code (stick_profile.py:52) and with the JSON gains (0.859, 0.858, 0.863, 0.850).
- OK "acro and stabilized wired as main modes 5 and 7, not flown": run_scenario.py:91 matches; no flight data for these.
- OK "sends on a fixed sim-time grid, offboard unchanged": matches :449.

VERDICT: DISAGREE

Reason: the code is largely to the brief, but the brief's pre-test acceptance (item 3) is not met for three of four runs, the README's "works in ALTCTL and POSCTL on both stacks" claim is not supported by its own table, and the nav_state anchor generalisation (1e) is missing.

Not verified by this review: no test or run executed, PX4 mavlink_receiver and Sticks.cpp decode not read, offboard byte-identity not checked, stick segment wall timeout not read.

# G5.10 sustained saturation, S147 pre-test (seed 1, one flight + one re-fly, NOT a gate run)

Command (docker, wall timeout 700 s), params g5_events_s145/params.params (MC_INDI_POS_EN 1):
`indi_project/docker/run.sh -n g510s1b -t 700 -- python3 indi_flight/bench/run_scenario.py --controller indi --model quad5in --seed 1 --speed 4 --sim v2 --gps-dly 110 --gnss-delay 110 --params indi_flight/results/g5_events_s145/params.params --scenario sat_sustained --out indi_flight/results/g5_g510_s147/s1`
Check: `python3 indi_flight/bench/g510_check.py indi_flight/results/g5_g510_s147/s1 --json .../g510.json` (self-test bench/tests/test_g510_check.py).

Scenario `sat_sustained` (scenarios.py): hover 5 m (runner fixed TAKEOFF_ALT, not 3 m), "sat" 5 s all motors thrust_scale 0.274 + 3 m x step,
"rec" 10 s scale back to 1 (SIM_GZ_EC_MAX 1413 -> 2700, verified in sends.csv), setpoint kept; "agg" 8 s + "aghold" 12 s full scale.
Built only because missing (F-9): (a) `seg_pos` per-segment position offset in position mode (no existing position-step scenario with a fault),
(b) motor_fault entry field `reset` (fault scales multiply and thrust_scale must be <= 1, so no way to end a fault).

Results (s1_try1_agg20 = 20 m/4 m up agg step, s1 = 37 m/15 m up agg step; same numbers in both):
- SAT part saturated: 96 % of time at the 0.274 limit (proves saturation). Fault ends at "rec" as intended.
- altitude loss 2.15 m (limit 2.0) FAIL; max tilt 48.9 deg (34 deg in SAT, 49 deg right after thrust returns at REC) (limit 20) FAIL;
  no LOC PASS; back within 0.3 m after SAT end 4.3 s PASS (overshoot x 0.48 m).
- AGG part did NOT saturate: motor command max 0.49 (20 m step) and 0.486 (37 m / 15 m step); peak vx 10.2 then 11.9 m/s, vz up only 3 m/s, position loop limits the demand.
  back_s_agg not scored. Checker verdict INVALID (no saturation in AGG).
Unverified / open: the full-scale saturating manoeuvre does not exist yet (needs a different driver, e.g. offboard acceleration/attitude
override or aggressive trajectory; position step is rate-limited by the position loop). Windup is only proxied by recovery time + x overshoot.
LOC definition in checker is mine (tilt >= 60 deg, disarm, nav_state != offboard, z < 0.3 m, run not ok). Sat limit uses actuator_motors
command >= 0.98 x limit. Only seed 1. Gate numbers (alt loss, tilt) fail in the SAT part: a real controller finding, not a scenario fault.

## PID reference (S147 orchestrator, O-13), same scenario and seed, `--controller pid_default`, out pid_s1
alt loss 3.22 m, tilt 44.7 deg, back 5.9 s, SAT part saturated 97 %, AGG not saturated. INDI s1: 2.15 m, 48.9 deg, 4.3 s.
Reading: the 20 deg tilt limit cannot be met by any controller following the gate's own 3 m position step (stock
MPC_TILTMAX_AIR 45 deg is what the position step commands) -> test defect, owner Q9 (first test of the gate). Alt loss
2.15 m > 2.0 m is a real INDI result on this seed (PID 3.22 m). INDI 48.9 deg > 45 deg: A-48. AGG part needs a
driver that can saturate at full scale (position modes are rate- and tilt-limited by design) -> Q9.

## Seeds 2/3 (S147 orchestrator, 2 parallel streams, probe)
s2: alt 2.21 m, tilt 65.0, back 4.42 s; s3: alt 2.21 m, tilt 65.1, back 4.61 s; checker LOC (tilt >= 60) on both.
Max tilt per phase (truth): SAT 34.1/40.3/39.6 (PID 30.3); REC edge, +0.3 s after thrust returns, 48.9/65.0/65.1
(PID 33.4); AGG 45.3-45.4 (PID 44.7). The failure is the saturation-exit transient of INDI, not the gate's tilt
text (Q9 (a) stays for the SAT part). A-48 = gate test failure, cause search next session.

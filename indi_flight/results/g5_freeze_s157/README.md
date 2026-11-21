# S157 stage-6 freeze re-fly of G5 (D-FREEZE-6), typical noise profile

Firmware 23acbdef67 (frozen) + gz_bridge vibration hook 0f56d56bf1/56ebc4e009 (SITL rebuilt S156, checked newer than source).
Plant: quad5in, matched GNSS `--gps-dly 110 --gnss-delay 110`, G4 typical profile `--vib-acc 10 --vib-gyr 0
--imu-noise-scale 4.0` (D-NOISE-PROF; run.json `vib`, `imu_noise_scale` confirm it was applied). Serial, one stream.
Fly one: `bash indi_flight/results/g5_freeze_s157/fly.sh <scenario> <seed> [runner args]`; batch (resumable):
`bash indi_flight/results/g5_freeze_s157/batch.sh` (aborts if a run's params_applied MC_INDI_ID_OK != 1).

## Set-up fault found by the pre-test (fixed, no threshold change)
`bench/params/quad5in_indi_defaults.params` sets `MC_INDI_ID_OK 0`; the runner overlay is `setdefault("MC_INDI_ID_OK", "1")`
(run_scenario.py:1007), so a file that sets 0 wins and the flight runs at 0.5 x K (pre-identification). D-FREEZE-6 assumed
the overlay applied. Fix: `params.params` here = the defaults file with `MC_INDI_ID_OK 1` (only diff). The pre-test flight
is kept as `auto_tour_s1_idok0` (extra data at the firmware-default gain state, not a freeze-set result).

## Pre-test: auto_tour seed 1 at ID_OK 0 (checker bench/auto_smoke_check.py, keyed S135)
ramp max step 7.5 % hover, edge step 4.0 % (<= 10 %), dip 0.000 m (<= 0.3), take-off overshoot -0.10 m / bounce 0.20 m,
touchdown vz 0.721 m/s (<= 0.8), tilt 0.31 deg, re-lift 0.050 m, land vz 0.699, contact->disarm 2.69 s, RTL height
err 0.033 m: all PASS. indi_rate_status and indi_pos_status present (stack valid). Flies, logs, checker runs.

## Freeze set results
Seed 1, checked S157 (checkers g51_check.py / g52_check.py, keyed S136/S138; host python3):
| row | run | verdict | numbers (limit) |
|---|---|---|---|
| G5.1 acro | stick_steps_s1_acro | PASS | RMS roll 1.58 / pitch 1.69 / yaw 3.23 deg/s (<= 10) |
| G5.1 stab | stick_steps_s1_stab | PASS | tilt 0.13/0.15/0.04 deg (<= 3), yaw rate 0.13 deg/s (<= 10) |
| G5.2 altctl | stick_pos_steps_s1_altctl | PASS | z os 0.023 m (<= 0.3), settle 0.35 s (<= 4) |
| G5.2 posctl | stick_pos_steps_s1_posctl | **FAIL** | z settle 4.15 s (> 4.0), os 0.054; x os 0.092 m, settle 3.20 s PASS |
G5.2 posctl z FAIL: gate test failure, cause search <= 1 session (S158). Leads: 2 % band = 0.04 m is near the
typical-profile truth-z noise (S138 sim-default posctl z settle already 1.2-3.0 s); the same z step settles 0.35 s in
altctl. First check: truth z std over the centred window vs 0.04 m, and the last band exit time vs the x-step edge.
Cause search DONE S157: not noise (truth z std 0.018 m over the last 2 s). The controller holds the estimate within
0.02 m of the setpoint (6.895 m) from release + 0.5 s; EKF2 est - truth = -0.078 m at release, -0.047 at +4.0 s,
-0.003 at +5.5 s. The truth settle is the estimator height error decaying; altctl's same step wanders 0.02 m (PASS).
Row stays FAIL as written; owner Q10 (keep / band / estimate-based), PID reference flight of this seed next.
(batch in progress: G5.1 stick_steps acro/stab, G5.2 stick_pos_steps altctl/posctl, G5.3 mission + G5.4 auto_tour,
auto_land10; seeds 1-3. Remaining rows G5.5-G5.11 and the firmware-default cells are next.)

G5.2 seeds 2-3 (S157): altctl PASS (settle 0.35/0.35 s), posctl PASS (z settle 0.36/0.35 s, x os 0.099/0.103 m, settle
3.34/3.32 s). Row G5.2 = 5/6 runs PASS, 1 FAIL (posctl s1, EKF height transient, Q10). Batch 1 complete: 18/18 logs.

### Batch 1 verdicts, all seeds (S158, checks.sh, host python3)
| row | runs | verdict | numbers (limit) |
|---|---|---|---|
| G5.1 acro | stick_steps_s{1,2,3}_acro | PASS 3/3 | rate RMS roll 1.50-1.97, pitch 1.53-1.69, yaw 3.23-3.33 deg/s (<= 10) |
| G5.1 stab | stick_steps_s{1,2,3}_stab | PASS 3/3 | tilt err <= 0.15 deg (<= 3), yaw rate <= 0.13 deg/s |
| G5.2 altctl | stick_pos_steps_s{1,2,3}_altctl | PASS 3/3 | z settle 0.35 s (<= 4) |
| G5.2 posctl | stick_pos_steps_s{1,2,3}_posctl | 2/3 PASS, s1 FAIL | s1 z settle 4.15 s = EKF height transient (Q10); s2/s3 0.36/0.35 s |
| G5.3 mission | auto_tour_s{1,2,3} (g53_mission_check.py) | PASS 3/3 | wp min dist <= 0.95 m, vmax 5.03-5.04 m/s (<= 5.5) |
| G5.4 take-off/land | auto_tour_s*, auto_land10_s* (auto_smoke_check.py) | PASS 6/6 | ramp step 7.5 % hover, edge step 4.1-4.6 % (<= 10 %); land vz 0.70 m/s |
Batch 2 (G5.5/5.7/5.10/events/fwdef) running; o1_lemniscate_s1 FAIL rms_h 0.61 m (as pre-freeze, base A cause RC143).

### Batch 2 seed 1 verdicts (S158, checks.sh SEEDS=1)
| row | run | verdict | numbers (limit) |
|---|---|---|---|
| G5.5 offb_vel_step | offb_vel_step_s1 | PASS | vx RMS last 3 s 0.037 m/s (<= 0.2), end 0.007 (<= 0.1) |
| G5.5 o1/o2/o3/o4/o7 | o*_s1 | **FAIL** | horiz RMS 0.61/0.79/0.62/0.58/0.59 m (<= 0.5); vert 0.03-0.09 PASS |
| G5.5 o5/o6 | o5/o6_s1 | PASS | horiz 0.04, vert 0.036/0.029 m |
| G5.7 | mode_switch10_s1 | PASS | 10 edges, no LOC |
| G5.10 | sat_sustained_s1 | INVALID (no saturation in AGG part) | alt_loss PASS, tilt FAIL (Q9 a), back_sat PASS, back_agg FAIL (Q9 b/c) |
| G5.6/8/9/11 | g5_events_s1 | 1 FAIL line | G5.9a kill 3.75 ms after switch (stock commander latency, Q8 add. 2) |
| fwdef cell G5.1 acro | stick_steps_s1_fwdef_acro (ID_OK 0, W_MAX 0, ACT_TC 0.05) | **FAIL** | rate RMS roll 15.1 / pitch 15.3 / yaw 16.9 deg/s (<= 10); tilt max 43 deg, no LOC |
G5.5: as pre-freeze (RC143 cause: lag in the stock PositionControl a_c of base A); owner Q11.
fwdef FAIL is a gate test failure: cause search S158. Rate-error spectrum (whole flight) shows no distinct oscillation
(peak 2.9-3.1 Hz, the stick content, same as the ID_OK 1 cell; whole-flight RMS 12/11/8 vs 8/7/6 deg/s), so the
lead is slow tracking from the 0.5x K gate (D-DEFAULTS-FW) inside the 0.1 s-skip window. Probe queued
(probes_s158.sh): same cell at ID_OK 1, then PID o1 s1 at the freeze plant for Q11.

### Batch 2 seeds 2-3 and S158 probes (checks.sh SEEDS="2 3"; 54/54 flights rc=0, ID_OK as intended)
| row | s2 | s3 | 3-seed verdict |
|---|---|---|---|
| G5.5 offb_vel_step | PASS 0.030 | PASS 0.026 | PASS 3/3 |
| G5.5 o1/o2/o3/o4/o7 horiz RMS (<= 0.5 m) | 0.60/0.81/0.62/0.57/0.60 | 0.62/0.81/0.62/0.57/0.62 | FAIL 3/3 each (vert PASS) -> Q11 |
| G5.5 o5/o6 | PASS | PASS | PASS 3/3 |
| G5.7 mode_switch10 | PASS | PASS | PASS 3/3 |
| G5.10 sat_sustained | INVALID (AGG not saturating), tilt FAIL | same | Q9 (a)/(c) |
| G5.6/8/9/11 events | 7 PASS, 0 FAIL | 7 PASS, 0 FAIL | s1 G5.9a 3.75 ms FAIL (stock commander latency, Q8 add. 2); s2/s3 PASS |
| fwdef cell acro (ID_OK 0) | 15.1/15.1/17.3 deg/s | 14.8/15.1/16.8 | above the 10 deg/s limit 3/3, no LOC 3/3 |
Firmware-default cell, cause search CLOSED: probe `stick_steps_s1_fwdef_idok1_acro` (same file, only ID_OK 1; W_MAX 0
and ACT_TC 0.05 kept, params_applied checked) PASSES 4.57/4.49/5.42 deg/s. The excess is the 0.5 x K pre-ident gate
(D-DEFAULTS-FW) alone, as GATES G5.1 already records (S136: 13.6/13.0 deg/s at ID_OK 0, t90 = 2.3/(0.5 K)). G5.1 is
defined at identified gains (GATES G5.1), so this is not a G5.1 FAIL; it is reported: the pre-identification
default is safe (no LOC, tilt <= 43.6 deg, 3 seeds) but tracks at half bandwidth, by design.
Q10 PID reference (`stick_pos_steps_s1_posctl_pid`, stock PID, same plant/noise/seed): G5.2 PASS, z settle 3.39 s,
os 0.004 m; x settle 1.92 s. PID meets the row on this seed (margin 0.6 s), so the INDI s1 FAIL is not shown to be
stack-independent; it stays FAIL (1/6 runs).
Q11 PID reference (`o1_lemniscate_s1_pid`, INVALID only for missing indi_pos_status, expected for PID): horiz RMS
0.785 m, vert 0.088 m: PID also misses 0.5 m on o1 (INDI 0.60-0.62 m).

## G5 verdict table at the freeze (S160; checkers keyed S159: key2_g51_g52.md, key2_g54_g58_g59.md, key2_g55_g57.md)
Owner questions scored at option A (D-FREEZE-6). One line per GATES 5b row; "runs" = 3 seeds unless stated.
| row | verdict | evidence / cause |
|---|---|---|
| G5.1 acro, stab | PASS 6/6 | rate RMS <= 1.97/1.69/3.33 deg/s; tilt err <= 0.15 deg. fwdef cell (ID_OK 0) above 10 deg/s 3/3 = 0.5x K gate by design, no LOC (reported, not a G5.1 run) |
| G5.2 altctl, posctl | FAIL 5/6 | posctl s1 z settle 4.15 s > 4.0 = EKF2 height error decay; PID same seed PASS 3.39 s (Q10) |
| G5.3 mission | PASS 3/3 | wp dist <= 0.95 m, vmax <= 5.04 m/s |
| G5.3 hold | PASS 3/3 (key2 pending) | hold RMS 0.044/0.056/0.080 m (<= 0.3), nav 4 over window; hold3.sh S160 (g53_hold_check.txt) |
| G5.4 take-off, land, RTL | PASS 6/6 | edge step 4.0-4.6 % hover (<= 10), land vz 0.70 m/s |
| G5.5 offb_vel_step, o5, o6 | PASS 3/3 each | vx RMS <= 0.037 m/s; horiz 0.04 m |
| G5.5 o1-o4, o7 | FAIL 3/3 each | horiz RMS 0.57-0.81 m > 0.5; base A stock a_c lag (RC143); PID o1 0.785 m also FAIL (Q11) |
| G5.6 false maybe_landed | NOT TESTED | not injectable firmware-free (Q8 b); needs a SITL test hook after the freeze |
| G5.7 mode switches | PASS 3/3 | 10 edges, limits met, no LOC |
| G5.8 RC/link/offboard loss, hover | PASS 3/3 | failsafe entry <= 1 s after the firmware timeout flag (Q8 add. 1/3 option A); 3 m/s rows not flown (Q8 add. 3) |
| G5.9 kill, re-arm, take-off | FAIL 8/9 lines | s1 G5.9a 3.75 ms after switch, outputs 0 in the kill-flag sample (stock commander latency, Q8 add. 2); s2/s3 PASS |
| G5.10 sustained saturation | INVALID | AGG part does not saturate; tilt 45.3 deg = MPC_TILTMAX_AIR vs 20 deg text (Q9 a/c); alt loss and recovery PASS |
| G5.11 estimator reset xy, yaw | PENDING | exact test written S160 (GATES 5b), checker g511_check.py in progress; z part not injectable (Q8 b) |
| F-8 rows (accel-only offboard, take-off on offboard setpoint) | NOT TESTED | owner decision F-8 |
G5 overall: OPEN. Blocking rows: G5.2 (1/6), G5.5 o1-o4/o7, G5.9a s1, G5.10, plus the pending/not-tested rows; all FAIL rows have an
owner question with the cause on the log.

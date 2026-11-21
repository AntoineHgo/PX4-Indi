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

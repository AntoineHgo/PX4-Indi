F1 conclusion: L2 not removed (overturn met: 3/3 flagged), item 3 altitude-offset FAIL 3/3.

# G4 fix probe F1 (S179): MC_INDI_POS_LPF 5 (was 10), params only, cruise_typ s1-s3
Command (fly.sh, 3 seeds in parallel, containers s179f1a/b/c; same as chatter_probe_s178 P1 except params/seed/out):
`run_scenario.py --controller indi --model quad5in --seed S --speed 4 --sim v2 --gps-dly 110 --gnss-delay 110 --scenario traj_lemniscate --vib-acc 10 --vib-gyr 0 --imu-noise-scale 4.0 --params f1_params.params --out f1_lpf5_sS`
Params diff vs g5_freeze_s157/params.params: only `MC_INDI_POS_LPF 5.0` (was 10.0). No MPC_VEL_LP. Firmware untouched (frozen build).
Scoring: score.sh in Docker (gate_g4.sh score, rescore_key1, score_key2, chatter_cruise_s176; scorer paths sed-redirected to score/), outputs score_out.txt, score_key2_out.txt; chain_sN.md = chatter_chain_s178.py default windows, chain_sN_shift.md = L2d window moved to land-cmd+2.6..+7.1 s (as the baseline 62-66.5 vs land cmd 59.4).
Health: 3/3 rc 0, nav_state OFFBOARD -> AUTO_LAND (60.6 / 59.9 / 60.8 s) -> disarm ~71 s; lemniscate rms (estimate/truth) 0.206/0.227, 0.210/0.231, 0.210/0.229 m vs baseline typ s1-s3 0.205/0.227, 0.203/0.222, 0.207/0.236 m: no change. R20 0.057, C20 0.0015, R4 0.19 (baseline P1 0.35), clip 0.

## Detector (key 1 fixed +-2 Hz; key 2 agrees on the lemniscate peak)
| seed | lemniscate (36-54 s) | take-off/loiter | AUTO_LAND |
|---|---|---|---|
| 1 | CHATTER 33.3 Hz, 1.5e-3 | 0/56 windows | CHATTER 20.0 Hz, 1.7e-3 (66.5-71.0 s) |
| 2 | CHATTER 33.3 Hz, 1.5e-3 | 0/56 | CHATTER 20.3 Hz, 2.2e-3 (66.5-71.5 s) |
| 3 | CHATTER 33.3 Hz, 1.4e-3 | 0/56 | CHATTER 20.3 Hz, 2.3e-3 (67.5-72.5 s) |
Key 2 peak 33.2 Hz 1.47/1.47/1.44e-3, all 4 motors. Item 2 FAIL (chatter) on all, item 3 FAIL in key1 table (see score_out.txt). L2 not removed: 3/3 flagged.

## L2d (18.7 Hz line RMS, window 62-66.5 s; shifted window gives the same within 15 %)
| signal | baseline typ_s1 | s1 | s2 | s3 |
|---|---|---|---|---|
| motors diffB | 2.0e-4 | 1.3e-4 | 1.5e-4 | 1.6e-4 |
| motors diffC | 1.8e-4 | 1.3e-4 | 1.4e-4 | 1.5e-4 |
| a_c horizontal | 3.5e-2 | 3.5e-2 | 3.5e-2 | 3.3e-2 |
| a_f horizontal | 2.6e-2 | 6.3e-3 | 6.4e-3 | 5.9e-3 |
| gyro | 9.2e-4 | 7.4e-4 | 8.3e-4 | 8.1e-4 |
| torque_sp | 2.6e-4 | 1.9e-4 | 1.9e-4 | 2.1e-4 |
PID ref diffB 8.5e-5. Reading: a_f drops 4x (LPF works as designed) but a_c is unchanged and motors fall only 20-35 % (P1 level, within the P2 seed spread 8.8e-5..2.0e-4): the 18.7 Hz line in a_c is not coming through the thrust/accelerometer filter. L1 33 Hz unchanged (a_c L1 6.2-6.7e-2).

## Side finding: item 3 (steady state, last 10 s before land) FAIL 3/3 (baseline P1/P2 PASS)
altitude_mean offset 0.20 / 0.16 / 0.25 m (limit 0.1), horizontal rms 0.036 / 0.056 / 0.097 m (limit 0.15 OK). Not investigated: probably the 5 Hz filter lag on the thrust/vertical path after the hold, cause unverified (g3_checks_s175.json per run).

# F3 (S179): MPC_VEL_LP 5 added to the freeze params (MC_INDI_POS_LPF 10), cruise_typ s1-s3
MPC_VEL_LP = "Velocity low pass cutoff frequency", unit Hz, 0 disables (default 0; yaml src/modules/mc_pos_control/multicopter_position_control_params.yaml). The INDI module (McIndiPosControl.cpp:506-508) sets one 1st-order-style filter pair for velocity xy and z at this cutoff, so it filters xy AND z velocity, feeding the velocity P and the acceleration estimate (see P1 notes). 5 Hz here, P1 used 8.
Command: fly_f3.sh (as fly.sh, `--params f3_params.params`, out f3_vellp5_sS, containers s179f3a/b/c); scoring score_f3.sh -> score_f3_out.txt, chain_f3_sN.md (default windows). Params diff vs freeze: `MPC_VEL_LP 5` only.
Health: 3/3 rc 0, AUTO_LAND at 61.6/61.1/61.3 s, disarm ~72 s. Lemniscate tracking rms estimate/truth 0.136/0.167, 0.146/0.186, 0.152/0.218 m (baseline typ 0.203-0.207/0.222-0.236): better. R4 0.40-0.44 % (F1 0.19, baseline P1 0.35), C20 0.0016, clip 0.

| seed | lemniscate (key 1) | take-off/loiter | AUTO_LAND (key 1) | key 2 |
|---|---|---|---|---|
| 1 | CHATTER 88.8 Hz, 1.1e-3 (37-55 s) | 0/58 | CHATTER 20.3 Hz, 1.8e-3 (66-72 s) | 34.5 Hz, 1.07e-3 |
| 2 | CHATTER 88.9 Hz, 1.2e-3 (36.5-54 s) | 0/58 | NOT flagged (land-cmd 0/32 windows) | 33.5 Hz, 1.18e-3 |
| 3 | CHATTER 88.5 Hz, 1.1e-3 (36.5-54.5 s) | 0/58 | CHATTER 20.3 Hz, 3.1e-3 (66-73 s) | 32.0 Hz, 1.11e-3 |
The 33 Hz lemniscate line is no longer the maximum; an 88-89 Hz line (the freeze-6 line) replaces it, so the lemniscate is still flagged 3/3. Item 2 FAIL 3/3.

L2d 18.7 Hz line RMS (window 62-66.5 s) [baseline | s1 | s2 | s3]:
| signal | baseline | s1 | s2 | s3 |
|---|---|---|---|---|
| motors diffB | 2.0e-4 | 1.0e-4 | 1.0e-4 | 1.3e-4 |
| motors diffC | 1.8e-4 | 9.2e-5 | 1.0e-4 | 1.3e-4 |
| a_c horizontal | 3.5e-2 | 6.8e-3 | 7.8e-3 | 7.4e-3 |
| a_f horizontal | 2.6e-2 | 2.1e-2 | 2.3e-2 | 2.3e-2 |
| gyro | 9.2e-4 | 6.0e-4 | 6.2e-4 | 7.5e-4 |
Item 3 (steady state): FAIL 3/3 again, altitude mean offset 0.34 / 0.34 / 0.33 m (limit 0.1), horizontal rms 0.039 / 0.075 / 0.027 m (limit 0.15 OK). Cause unverified (z velocity is filtered by the same parameter).
Reading: a_c falls 5x and motors diffB/C reach about PID level (8.5e-5) on 2 of 3 seeds, 1.3e-4 on seed 3; L2 detector still flags 2/3 (1.8e-3, 3.1e-3) and the 88 Hz line returns on the lemniscate.

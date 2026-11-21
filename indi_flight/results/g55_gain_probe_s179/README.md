# S179 gain probe: MC_INDI_XY_P 1.2 (VP 3.6), params only, seed 1, one flight each (probe, not gate evidence)
Params: `params_xyp12.params` = results/g5_freeze_s157/params.params + `MC_INDI_XY_P 1.2` + `MC_INDI_XY_VP 3.6` (freeze-7 default 1.9 / 3.6). Firmware untouched.
Commands (repo root; containers s179gp*):
- G2: `AMP=0.08 TP=20 SCN=hover_xlong bash fly.sh 0 {2,1} 400 1` (fly.sh = freeze-7 fly.sh with the out dir, container prefix and params base changed; margins and holes as the freeze-7 README).
- G5.5: `fly_rest.sh a|b` (runner args of freeze7_s177 queue.sh with --params params_xyp12), then `bench/g55_check.py RUN --json` -> `*.check.txt`.
- G4: `fly_rest.sh c` (traj_lemniscate, gate_g4.sh fly arguments, seed 1), scored in Docker with `score.sh` (gate_g4 score, rescore_key1, score_key2, chatter_cruise_s176) -> `score_out.txt`.

| test | freeze-7 (1.9/3.6) | XY_P 1.2 |
|---|---|---|
| G2 pt0_ax2_r400_s1 GM / PM / DM / f_c | 11.4 dB / 38.4 deg / 0.189 s / 0.564 Hz | 11.8 dB / 50.2 deg / 0.269 s / 0.517 Hz |
| G2 pt0_ax1_r400_s1 GM / PM / DM / f_c | 11.3 dB / 40.0 deg / 0.215 s / 0.518 Hz | 11.8 dB / 49.5 deg / 0.249 s / 0.553 Hz |
| holes ax2 / ax1 (OVERALL) | PASS / FAIL | PASS / FAIL |
| G5.5 o3_lemniscate_gust s3, H / V RMS (limit 0.5 / 0.3) | 0.323 / 0.060 | 0.345 / 0.079 PASS |
| G5.5 o1_lemniscate s1, H / V RMS | 0.303 / 0.039 | 0.347 / 0.033 PASS |
| G4 cruise_typ_s1 detector, key 1 (fixed +-2 Hz) | CHATTER, lemniscate 33.3 Hz 1.5e-3, L2 20 Hz | CHATTER; lemniscate 36-53.5 s peak 88.5 Hz 1.1e-3 (key 1 old bins 9.5e-4); AUTO_LAND 67-72 s 20.0 Hz 2.3e-3 (old 1.1e-3); take-off/loiter 0/57 windows |
| G4 key 2 | 33.2 Hz 1.48e-3 | 33.5 Hz 1.08e-3, motors m2/m3 |
| G4 item 3 | FAIL on baseline? (not re-read) | FAIL: altitude_mean 0.29 m (limit 0.1), horizontal rms 0.021 m (OK) |
Other G4: R20 0.053, C20 0.00155, R4 0.405, clip 0; item 1 PASS, item 2 FAIL (chatter).
Notes: the hole FAIL of ax1 is identical in verdict to freeze-7 (cause not examined here). Key 1 reports 88.5 Hz as the lemniscate-window peak while key 2 reports 33.5 Hz; not reconciled. Item 3 freeze-7 baseline value not looked up.

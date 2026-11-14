# Speed factor 1 vs 4, INDI frozen candidate, seeds 1-3 (session 22)

Closes the open item of `report/09_discussion.md` 9.4 (D-speed was checked on PID only). Same firmware as the
held-out runs plus the post-freeze fixes D-landyaw (1d776dc6dc) and the `MC_INDI_G2_Y` bound (no effect at G2 = 0).
Params: `results/tuning/indi/r4f/c00/params` (checked in every `run.json`). Speed 4 = the committed held-out runs
`seed<N>_x4` (pre-fix firmware); speed 1 = `seed<N>`, flown in session 22 (`run_batch.sh`, log
`speedcheck_indi_s22.log`). Values per seed 1 / 2 / 3.

| scenario | metric | speed 1 | speed 4 | mean s1/s4 |
|---|---|---|---|---|
| step_diag (H6) | rotation-angle RMS (deg) | 5.76 / 6.10 / 6.17 | 5.71 / 5.84 / 5.75 | 1.04 |
| step_diag (H6) | roll-rate RMS (rad/s) | 0.180 / 0.174 / 0.180 | 0.180 / 0.176 / 0.183 | 0.99 |
| step_diag (H6) | motor-rate RMS (/s) | 1.196 / 1.177 / 1.185 | 1.236 / 1.183 / 1.216 | 0.98 |
| mismatch_combined_rate (H5) | roll-rate RMS (rad/s) | 0.576 / 0.562 / 0.561 | 0.555 / 0.571 / 0.561 | 1.01 |
| mismatch_combined_rate (H5) | roll attitude RMS (deg) | 19.0 / 19.9 / 20.1 | 20.2 / 18.6 / 19.8 | 1.00 |
| mismatch_combined_rate (H5) | motor-rate RMS (/s) | 3.64 / 3.58 / 3.56 | 3.60 / 3.70 / 3.64 | 0.98 |

Reading: rate and effort metrics agree within the seed spread (<= 4 % per seed), and the H5 loss (roll-rate RMS
~0.57 vs PID 0.356 at speed 4) is unchanged at speed 1. The H6 rotation-angle RMS is 4 % higher at speed 1 on
average (up to 7 % on seed 3), which is larger than the speed-4 seed spread and half of INDI's 8 % H6 margin
over PID (0.92x). PID was not re-flown at speed 1 on step_diag (its step_roll attitude RMS moved -2.5 % from speed
4 to 1, `speedcheck_pid_default.md`), so the H6 ratio at speed 1 is unknown; H6 was already at the acceptance
threshold. Two confounds: the firmware differs by the post-freeze fixes, and n = 3.

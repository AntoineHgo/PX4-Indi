# T147: same-seed INDI step_roll spread with the G1.6 determinism flags

Scenario step_roll, seed 1, speed 4, indi, quad5in, `--sim v2`, flags `--sched --sched-anchor` (as in `bench/g16_sched_set.sh`).
No `--paused-start` (not used by the G1.6 set). Logging at the runner default (`--log-from-start`).
400 Hz params `results/g2_step_s64_400/indi.params`; 800 Hz params `results/g2_step_s64/indi.params`.
`fly.sh`: `pre` = r400_1 alone (pre-test); `rest` = r400_2..5 and r800_1..5, at most 5 in parallel.
Firmware: `build/px4_sitl_default`, not rebuilt.

Git: `git rev-parse HEAD` = 002376a3bbcc14ce89cd1e1f8aa7f4062dd8942e (branch feat/indi-flight). `git status --short -uno` empty.
HEAD moved from c8bfc4844c (firmware build base) to 002376a3bb (docs commit). `git diff --stat c8bfc4844c 002376a3bb -- src boards platforms` is empty, so the firmware source is unchanged.

done.txt: all 10 runs rc=0 (r400_1 pre-test, then 9 more), then ALLDONE.
Scoring: `bench/g2_step_metrics.py` (run from `indi_flight/`), output `g2_step_primary_400.json` and `g2_step_primary_800.json`. All 10 pass.
Second key (`bench/t127_step_metrics_key.py`) not run.

## Per-flight results

Arm instant: the schedule file (`sched.txt`) has `30000000 arm`, so the arm is at sim 30.000 s. The `t_arm_us` field in run.json is the runner's sim clock at its arm call (run_scenario.py:753). It is not the PX4 arm instant under `--sched`, and it spreads 30.04-30.90 s. Not verified against the ULog.
Step instant: `sched_t0_us` from run.json (sim time of the step, from the schedule).

| run | rise ms | est settle ms | est OS % | truth OS % | step sim s (sched_t0) | t_arm_us (runner clock, see above) |
|---|---|---|---|---|---|---|
| r400_1 | 207.27 | 351.25 | 0.79 | 0.89 | 55.015000 | 30.891 |
| r400_2 | 201.23 | 343.75 | 0.68 | 0.78 | 55.017500 | 30.416 |
| r400_3 | 201.06 | 342.50 | 0.86 | 0.70 | 55.018750 | 30.902 |
| r400_4 | 206.79 | 351.25 | 0.72 | 0.55 | 55.011250 | 30.561 |
| r400_5 | 203.79 | 340.00 | 1.37 | 1.27 | 55.015000 | 30.558 |
| r800_1 | 209.06 | 353.75 | 0.86 | 0.62 | 55.012499 | 30.501 |
| r800_2 | 215.62 | 360.00 | 0.62 | 0.43 | 55.017500 | 30.782 |
| r800_3 | 210.55 | 352.50 | 1.32 | 1.12 | 55.019999 | 30.460 |
| r800_4 | 211.37 | 356.25 | 0.73 | 0.67 | 55.013749 | 30.880 |
| r800_5 | 201.12 | 343.75 | 1.17 | 1.04 | 55.011250 | 30.036 |

Offboard anchor (ULog nav_state 14, `ulog_anchor_s`): 52.0112-52.0200 s in all 10 runs, i.e. 11-20 ms after the scheduled 52.000 s, as in G1.6.

## Spread per rate (min to max, 5 flights each)

| rate | rise ms | est settle ms | est OS % | truth OS % | step sim s |
|---|---|---|---|---|---|
| 400 Hz, flags | 201.06-207.27 (span 6.2) | 340.0-351.25 (span 11.25) | 0.68-1.37 (span 0.69) | 0.55-1.27 | 55.0113-55.0188 (span 7.5 ms) |
| 800 Hz, flags | 201.12-215.62 (span 14.5) | 343.75-360.0 (span 16.25) | 0.62-1.32 (span 0.70) | 0.43-1.12 | 55.0112-55.0200 (span 8.75 ms) |

## Comparison with the runs without flags

| rate | metric | no flags | with flags |
|---|---|---|---|
| 400 Hz (g16_indi_s67, n=5 at speed 4) | rise | 4.0 ms span | 6.2 ms span |
| | settle | 15.0 ms span | 11.25 ms span |
| | OS | 0.70 span | 0.69 span |
| 800 Hz (g2_clean_s68 batch B, n=5) | rise | 199.0-213.5 (span 14.5) | 201.1-215.6 (span 14.5) |
| | settle | 328.8-367.5 (span 38.7) | 343.75-360.0 (span 16.25) |
| | OS | 0.68-1.66 (span 0.98) | 0.62-1.32 (span 0.70) |

Verdict: the runs with flags are not identical. Settle at 800 Hz is much tighter (38.7 to 16.3 ms span). Settle at 400 Hz is a bit tighter (15 to 11.25 ms). OS is a little tighter at 800 Hz and unchanged at 400 Hz. Rise is no tighter at either rate (4.0 to 6.2 ms at 400 Hz; 14.5 to 14.5 ms at 800 Hz). The step instant, which the flags do pin to sim time, spreads only 7.5-8.75 ms, so the remaining rise and settle spread comes from the loop, not from the step's sim-time placement.

## Unverified

- `sim_schedule_applied` (the topic that marks a player row) was not found in px4.log (count 0). It is a uORB topic in the ULog, and the ULog was not parsed (pyulog not installed). The evidence the schedule ran is `"sched": true`, `sched_t0_us`, and the ULog-derived offboard anchor at 52.01-52.02 s.
- The PX4 arm instant under `--sched` was not read from the ULog. The G1.6 set reported arm applied at 30.000000 s and PX4 response 1.25-10 ms. The `t_arm_us` values here do not match that, so the arm instant needs a ULog check before use.
- The G1.6 note reported a pre-arm EKF height bias (A-14) in some runs. The altitude traces here were not checked.

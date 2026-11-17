# T148: discriminator for the same-seed INDI --sched spread (S68)

Question: does the run-to-run spread of same-seed INDI step_roll flights (400 Hz, `--sched --sched-anchor`) come from the INDI rotor-speed (eRPM telemetry) path, or from elsewhere?
Reference spread (g16_sched_indi_s68, INDI v2, n=5, 400 Hz): rise 6.2 ms, est settle 11.25 ms, est OS 0.69 %.

Common flags (as in `results/g16_sched_indi_s68/fly.sh`): `run_scenario.py --scenario step_roll --model quad5in --rate-hz 400 --seed 1 --speed 4 --sched --sched-anchor`, no `--paused-start`, logging at the runner default. Wall timeout 900 s, container `s68d_<label>`, at most 5 in parallel. Firmware `build/px4_sitl_default`, not rebuilt.

Groups:
- G-pid: `--controller pid --sim v2`, params `results/stage3_s61/pid.params` (the most recent quad5in PID step params; `stage3_s61/fly_steps.sh` and `indi_vs_pid/fly.sh` flew them at 800 Hz, this batch uses 400 Hz as asked).
- G-true: `--controller indi --sim v2true` (exact rotor speed in esc_rpm), params `results/g2_step_s64_400/indi.params`.
- G-lost: `--controller indi --sim v2`, params `results/a30_disc_s68/indi_lost.params` (g2 params + `SIM_GZ_ERPM_LOSS 15`).

Script: `results/a30_disc_s68/fly.sh` (`pre` = pid_1, true_1, lost_1; `rest` = the other 12, then ALLDONE). Done log: `results/a30_disc_s68/done.txt`.

Git: `git rev-parse HEAD` at launch = dafd0571fe7115526b45aa8c09281b289872e27f; `git status --short -uno` shows only `M indi_flight/STATE.md`. HEAD then read as 339e94ca3e67f4f419d8c49a1a751dd588d67f03 during the pre-test (a commit landed on the branch during this run; `head.txt` has the value at pre-test launch). Nothing committed by this task.

Pre-test (pid_1, true_1, lost_1 in parallel): all rc 0, `bench/g2_step_metrics.py` ran on each, and `lost_1/step_roll_indi/run.json` has `params_applied.SIM_GZ_ERPM_LOSS = "15"` (the parameter took effect; the runner did not reject it). The runs record `sim` = v2, v2true, v2 and `sched` = true. Pre-test outputs: `pre_pid.json`, `pre_true.json`, `pre_lost.json`.

done.txt: 15 lines, all `rc=0`, then ALLDONE.
Scores: `score_pid.json`, `score_true.json`, `score_lost.json` (`bench/g2_step_metrics.py`, run from `indi_flight/`). All 15 flights pass the metric's own gates.

## Per-flight results

| group | run | rise ms | est settle ms | est OS % | truth OS % | truth settle ms |
|---|---|---|---|---|---|---|
| G-pid | pid_1 | 172.94 | 350.00 | 0.00 | 0.00 | 357.50 |
| G-pid | pid_2 | 179.48 | 372.50 | 0.00 | 0.00 | 372.50 |
| G-pid | pid_3 | 185.25 | 392.50 | 0.00 | 0.00 | 396.25 |
| G-pid | pid_4 | 185.10 | 396.25 | 0.00 | 0.00 | 405.00 |
| G-pid | pid_5 | 182.40 | 382.50 | 0.00 | 0.00 | 375.00 |
| G-true | true_1 | 208.29 | 350.00 | 1.01 | 0.86 | 350.00 |
| G-true | true_2 | 208.05 | 352.50 | 0.93 | 0.75 | 356.25 |
| G-true | true_3 | 199.46 | 336.25 | 1.28 | 1.09 | 336.25 |
| G-true | true_4 | 204.88 | 350.00 | 0.98 | 0.80 | 350.00 |
| G-true | true_5 | 205.48 | 350.00 | 0.99 | 0.82 | 350.00 |
| G-lost | lost_1 | 206.04 | 337.50 | 1.36 | 1.16 | 337.50 |
| G-lost | lost_2 | 205.47 | 333.75 | 1.47 | 1.34 | 333.75 |
| G-lost | lost_3 | 197.80 | 322.50 | 1.91 | 1.80 | 318.75 |
| G-lost | lost_4 | 206.11 | 335.00 | 1.42 | 1.39 | 335.00 |
| G-lost | lost_5 | 199.01 | 326.25 | 1.88 | 1.92 | 318.75 |

## Spread per group (min to max, n=5)

| group | rise ms | est settle ms | est OS % |
|---|---|---|---|
| G-pid (PID, 800 Hz params) | 172.94-185.25 (span 12.3) | 350.0-396.25 (span 46.25) | 0.00 (span 0) |
| G-true (INDI v2true) | 199.46-208.29 (span 8.8) | 336.25-352.5 (span 16.25) | 0.93-1.28 (span 0.35) |
| G-lost (INDI v2, eRPM lost) | 197.80-206.11 (span 8.3) | 322.5-337.5 (span 15.0) | 1.36-1.91 (span 0.55) |
| Reference: INDI v2 --sched (g16_sched_indi_s68, 400 Hz) | 201.06-207.27 (span 6.2) | 340.0-351.25 (span 11.25) | 0.68-1.37 (span 0.69) |

## Verdict

- G-true: not identical. Rise spread 8.8 ms and settle 16.25 ms, both above one 400 Hz period (2.5 ms). Removing the telemetry model did not remove the spread.
- G-lost: not identical. Rise spread 8.3 ms and settle 15.0 ms. Losing telemetry entirely did not remove the spread either, so the spread is not from the eRPM path alone.
- G-pid: not identical, and the widest (rise 12.3 ms, settle 46.25 ms). The spread is present without INDI at all, so the nondeterminism is not INDI-specific.

Reading: none of the three groups is near-identical. The spread is present with INDI on exact rotor speed, with the telemetry model fully removed, and with plain PID. The eRPM telemetry path is therefore not the (sole) source of the same-seed spread; the source lies in the shared sim/PX4 timing path.

## Caveats (not verified)

- G-pid uses `stage3_s61/pid.params`, which was flown at 800 Hz in S61/S62; this batch sets `--rate-hz 400` as asked, so the PID group is not a like-for-like copy of those flights. PID rise and settle are about 173-185 ms and 350-405 ms, unlike the INDI groups.
- The G-pid "est OS" is 0 for all runs (no overshoot), so its OS spread is not informative.
- The `t_arm_us` / PX4 arm instant and the ULog-level sim-time placement were not re-checked for these groups.
- `sched_t0_us` (step sim time) spans 55.0113-55.0200 s across the groups, which is the same placement as in g16.

# S99 G2 rate-loop margin batch (10 cells, HEAD firmware)

Recipe: identical to `results/g2_rate_pretest_s99/fly.sh` (hover_long, indi_m3a, speed 4, quad5in, sim v2, P1.params base).
Changed only: axis (per-axis params file, `MC_INDI_INJ_AX` 1 roll / 2 pitch / 3 yaw; P1 vs P2 differ only in this key), `--rate-hz` (800 or 400), `--seed` (1 or 2).
Check chain per cell: check_rates.py, pretest_gate.py --delay 4 --length 15, m3a_csv.py (axis 0 roll / 1 pitch / 2 yaw), m3a_margins_pretest.py 1 60 10 <rate>.
Runner: `batch.sh` (serial, resumable: skips a cell whose margins.txt exists). Log: `batch.log`.

All 10 cells: fly rc=0, post rc=0, no crash or failsafe, no warnings from margins, 18/18 bins accepted, gate PASS.

| axis | rate Hz | seed | GM dB | PM deg | DM ms | f_c Hz | bins | gate | warnings |
|---|---|---|---|---|---|---|---|---|---|
| roll | 800 | 1 | 15.89 | 68.2 | 46.2 | 4.10 | 18/18 | PASS | none |
| roll | 800 | 2 | 15.81 | 68.7 | 46.3 | 4.12 | 18/18 | PASS | none |
| roll | 400 | 1 | 13.12 | 70.0 | 50.1 | 3.88 | 18/18 | PASS | none |
| roll | 400 | 2 | 13.23 | 70.0 | 50.8 | 3.83 | 18/18 | PASS | none |
| pitch | 800 | 2 | 16.05 | 68.8 | 46.1 | 4.15 | 18/18 | PASS | none |
| pitch | 400 | 1 | 13.32 | 70.1 | 51.0 | 3.82 | 18/18 | PASS | none |
| pitch | 400 | 2 | 13.16 | 70.5 | 50.3 | 3.90 | 18/18 | PASS | none |
| yaw | 800 | 1 | 21.53 | 87.1 | 154.6 | 1.57 | 18/18 | PASS | none |
| yaw | 800 | 2 | 21.27 | 87.0 | 153.4 | 1.57 | 18/18 | PASS | none |
| yaw | 400 | 2 | 16.17 | 86.5 | 161.2 | 1.49 | 18/18 | PASS | none |

Pitch 800 s1 and yaw 400 s1 are not in this batch; they are the pre-test flights P1 and P2 (`results/g2_rate_pretest_s99/README.md`): P1 pitch 800 s1 GM 15.7, PM 69.0, DM 46.2, f_c 4.15; P2 yaw 400 s1 GM 15.5, PM 87.0, DM 163.6, f_c 1.48.

## Worst of 2 seeds per (axis, rate)

| axis | rate Hz | seeds | worst GM dB | worst PM deg | worst DM ms | GM>=6 | PM>=45 | DM>=2T+L |
|---|---|---|---|---|---|---|---|---|
| roll | 800 | 1, 2 | 15.81 | 68.2 | 46.2 | yes | yes | yes |
| roll | 400 | 1, 2 | 13.12 | 70.0 | 50.1 | yes | yes | yes |
| pitch | 800 | 1 (pre-test P1), 2 | 15.7 | 68.8 | 46.1 | yes | yes | yes |
| pitch | 400 | 1, 2 | 13.16 | 70.1 | 50.3 | yes | yes | yes |
| yaw | 800 | 1, 2 | 21.27 | 87.0 | 153.4 | yes | yes | yes |
| yaw | 400 | 1 (pre-test P2), 2 | 15.5 | 86.5 | 161.2 | yes | yes | yes |

## Check criteria

- GM >= 6 dB: met by all cells (worst 13.12 dB).
- PM >= 45 deg: met by all cells (worst 68.2 deg).
- DM >= 2 control periods + telemetry latency: the params set no `SIM_GZ_ERPM_LAT`, so the default of 0 extra frames applies; the eRPM model's one-frame reply is the only added latency. Assumed L = 1 control period. Requirement: 800 Hz gives 2 x 1.25 + 1.25 = 3.75 ms; 400 Hz gives 2 x 2.5 + 2.5 = 7.5 ms. Worst measured DM is 46.1 ms (800 Hz) and 50.1 ms (400 Hz), so met with margin.

## Notes

- Crossover is the first crossing reported by the script. Yaw crossover is about 1.5 Hz, so its large DM reflects the low crossover, not a faster loop.
- Seed hook: `--seed` as in the pre-test recipe (controller/scenario seed). `--sim-seed` was not used.
- The fly.sh `axis_check` step (all three axes) was not in the requested check chain and was not run.
- Two seeds per cell (pitch 800 and yaw 400 include one pre-test flight), so the spread is a rough repeatability estimate only.

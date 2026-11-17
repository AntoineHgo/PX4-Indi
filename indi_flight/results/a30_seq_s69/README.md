# T153 (a30_seq_s69): A-30 closing test, INDI same-seed at 400 Hz flown sequentially

Command: that of `results/g16_sched_indi_s68/fly.sh` (INDI, step_roll, sim v2, 400 Hz, seed 1, speed 4,
`--sched --sched-anchor`, params `results/g2_step_s64_400/indi.params`), HEAD 4de4836bf2 (firmware as 50bb9ef9ff, not
rebuilt), but 5 runs strictly sequential (S68 flew them up to 5 in parallel). All rc 0, 35-36 s each (`done.txt`).
Metric: `bench/g16_spread.py` (`G16_ROOT=results/a30_seq_s69`), `spread.json`, ms extract `spread_ms.txt`.

| quantity, 4 steps | sequential S69 (span) | S68 same flags, parallel (span) |
|---|---|---|
| rise 10-90 | 3.59 / 2.49 / 4.19 / 4.25 ms (values 201-208 ms) | 6.2 ms |
| settle 5 % | 3.75 / 3.75 / 7.5 / 3.75 ms (306-314 ms) | 11.3 ms |
| overshoot | 0.27 / 0.53 / 0.32 / 0.27 pt | 0.7 pt |
| delay 10 % | 1.6-2.2 ms | |

## Verdict

- Most of the INDI same-seed spread came from parallel host load, as for PID (A-32, `results/a32_load_s69`).
- A residual remains when flown sequentially: rise span up to 4.3 ms (1.7 control periods at 400 Hz) against <= 1.5 ms
  for the PID G1.6 command on sim v1. Not attributed (candidates: sim v2, the INDI rotor-speed input path). It is under
  1/30 of the margin to the G2-STEP limits (worst settle 314 ms against 450 ms).
- A-30 is parked with this bound; the S64 seed-1 outlier lies inside the parallel-load spread.

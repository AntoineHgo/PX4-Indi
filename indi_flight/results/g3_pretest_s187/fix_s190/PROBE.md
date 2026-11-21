# S190 fix probe: commit 2d92dbcf59 (force low-passed at native rate), G3 pre-test draws

Build check: build/px4_sitl_default/bin/px4 mtime 21:39:43 > indi_accel_control.cpp mtime 21:39:32 (current, no rebuild).
Flown with the pre-test's own freeze params (results/g5_freeze_s157/params.params, POS_LPF at freeze value), seed 173, n 300, idx 16, 10, 0, 5.
Ulogs: fix_s190/run_0NN/flight.ulg (untracked). One flight each (new sim realisation; windows shift ~0.1 s). Nothing committed, no firmware change.

## Commands
- Fly: `bash indi_flight/results/g3_pretest_s187/fix_s190/fly.sh 16 10 0 5` (same g3_run.py command as fly_all.sh, container g3f190_<i>, serial; stdout stream_<i>.txt, progress.txt).
- Score (key 1): `bash indi_flight/bench/g3_score_docker.sh indi_flight/results/g3_pretest_s187/fix_s190 > fix_s190/SCORE_KEY1.txt` (per run g3_checks.json/.txt).
- a_f line: `python3 indi_flight/bench/af_line.py <flight.ulg> --t0 40 --t1 50` (new; test: `python3 indi_flight/bench/tests/test_af_line.py`, synthetic 0.25 sine on jittered timestamps, passes). Time base is the ulog timestamp clock (the 40-50 s window of S189); on orig run_016 it reproduces S189 exactly (0.256/0.246).

## Key-1 score, orig (S187) vs fix
| run | mode | orig pass (1/2/3) | fix pass (1/2/3) | orig item-2 lines (p / q) | fix item-2 |
|---|---|---|---|---|---|
| 16 | attitude | FAIL (P/F/P) | PASS (P/P/P) | p 7.25 Hz rms 5.84 (16/51 win); q 6.75 Hz rms 5.15 (9/51) | no lines, 0 flagged; max flagged rms p 1.63, q 1.05 dps |
| 10 | attitude | FAIL (P/F/P) | PASS (P/P/P) | p,q 5.5 Hz rms 6.76/6.92 (15/51) | no lines, 0 flagged; max rms 1.11/1.15 |
| 0 | position | FAIL (P/F/P) | PASS (P/P/P) | p 2.5-3.25 Hz rms 15.5 (37/51); q rms 13.5 (40/51) | no lines, 0 flagged; max rms 3.6/4.9 |
| 5 | position | FAIL (P/F/F) | FAIL (P/F/F) | p 4.5 Hz rms 10.5 (37/51); q 4.5 Hz rms 10.5 (42/51) | p not sustained (max rms 4.4); q sustained, line 2.0 Hz, 6/51 windows, max flagged rms 12.1 dps; item 3 still fails |

## a_f amplitude (indi_pos_status a_f[0]/a_f[1], 40-50 s, Hann, peak amplitude, m/s2)
| run | orig 6.84 Hz (S189) | fix, dominant 2-10 Hz line |
|---|---|---|
| 16 | 0.256 / 0.246 | 0.0059 / 0.0046 at 6.74 Hz (0.0064/0.0045 in 60-90 s) |
| 10 | n/a | 0.0059 / 0.0052 at 5.3 Hz |
| 0 | n/a | 0.030 / 0.025 at 2.6 Hz |
| 5 | n/a | 0.017 / 0.013 at 4.5 Hz |
S189 native-rate recompute predicted 0.022; measured in flight 0.005-0.006 (~45x below orig). Orig a_f was not computed for runs 10/0/5 here.

## Unverified / caveats
- n=1 flight per run, not seed-identical replay; pass/fail near threshold not quantified.
- Run 5 q 2.0 Hz line and item-3 failure not diagnosed (item 3 failed on the original too; not caused by this change as far as tested).
- Item 2 flagged windows are 0 on 3 of 4 runs with rms about 4-6x below orig; a_f line at the former frequency remains tiny but nonzero.
- Only key 1 scored (key 2 not run). Runs 17/9/2 (other INDI-only failures) not flown.

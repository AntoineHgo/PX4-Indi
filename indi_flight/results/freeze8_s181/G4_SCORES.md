# G4 scores, freeze-8 (S181), 18 runs, both keys, with Q18 touchdown-skip re-score

Runs: `g4/{hover,cruise}_{quiet,typ,harsh}_s{1,2,3}` (rc 0). Same scripts and thresholds as freeze-7 G4_SCORES.md (key 1 rescore_s175.py,
key 2 rescore_key2_s175.py, chatter_cruise_s176.py, Q18 g4_chatter_skip_key1.py / key2.py), none edited; path substitution by sed into python stdin only.
Verdicts are NOT stated here (gate verdict is a separate step); this file is per-run results.

## Commands (repo root, Docker; names without "s181" so the flight queue does not stop them)
```
D=indi_flight/results/freeze8_s181/g4; S=indi_flight/results/g4_gate_s169
indi_project/docker/run.sh -n g4f8k1 -t 900 -- sh -c "sh indi_flight/bench/gate_g4.sh score $D; sed 's#results/g4_gate_s169#results/freeze8_s181/g4#' $S/rescore_s175.py | python3 -"        # key 1 -> g4/key1_stdout.txt
indi_project/docker/run.sh -n g4f8k2 -t 900 -- sh -c "sed 's#results/g4_gate_s169#results/freeze8_s181/g4#' $S/rescore_key2_s175.py | python3 -"                                       # key 2 -> g4/key2_stdout.txt
indi_project/docker/run.sh -n g4f8c -t 900 -e RAW=$D/chatter_cruise_raw.txt -- python3 $S/chatter_cruise_s176.py $D/cruise_{quiet,typ,harsh}_s{1,2,3}                                  # -> g4/chatter_cruise_raw.txt
# Q18 (outputs in g4/q18/): self-tests, then
indi_project/docker/run.sh -n g4f8k1 -t 900 -- sh -c "python3 indi_flight/bench/tests/test_g4_chatter_skip_key1.py; python3 indi_flight/bench/tests/test_g4_chatter_skip_key2.py"          # both: ok, broken-skip variant fails as required
indi_project/docker/run.sh -n g4f8k2 -t 900 -- bash -c "python3 indi_flight/bench/g4_chatter_skip_key1.py g4/q18/key1_indi_18_gate.md <18 dirs>; ... --extend g4/q18/key1_indi_18_ext.md <18 dirs>; python3 indi_flight/bench/g4_chatter_skip_key2.py <each dir>"   # key2 -> g4/q18/key2_stdout.txt
```
Generated: `g4/g4_table.md`, `g4/rescore_s175_runs.md`, `g4/<run>/g3_checks_s175.json`, `g4/q18/*`.

## Per-flight table
Limits: R20 <= 1.0/1.5/3 %, C20 <= .004/.006/.012, R4 <= 3/4/6 %, clip 0/0/<=0.1 % (quiet/typ/harsh); cruise R20, C20 = hover limit x1.5.
K1/K2 chatter = gate-script chatter column (Q14 A: line RMS +-2 Hz >= 5e-4, ratio > 20, sustained >= 3 windows). K1 item 2 = rate detector plus chatter (key 1).
Q18 columns = same detectors with the touchdown-window skip. Metric limits: 18/18 within limits on R20, C20, R4, clip.

| run | R20 % | C20 | R4 % | clip | K1 chatter | K1 line RMS max (ratio>20) | K1 rate p/q/r | K1 item 2 | K2 chatter | K2 peak Hz (ratio, line RMS) | K2 item 2 rate (max rms dps p/q/r) | Q18 K1 (skip) | Q18 K2 (skip) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| hover_quiet_s1 | 0.003 | 0.00003 | 0.009 | 0.0000 | no | 1.62e-04 | -/-/- | PASS | no | 22.2 (m0) (1466, 1.44e-04) | pass (0.3/0.4/0.0) | no | no |
| hover_quiet_s2 | 0.003 | 0.00003 | 0.009 | 0.0000 | no | 1.54e-04 | -/-/- | PASS | no | 22.2 (m0) (8435, 1.55e-04) | pass (0.3/0.3/0.0) | no | no |
| hover_quiet_s3 | 0.003 | 0.00003 | 0.008 | 0.0000 | no | 1.49e-04 | -/-/- | PASS | no | 22.2 (m0) (3201, 1.45e-04) | pass (0.3/0.3/0.0) | no | no |
| hover_typ_s1 | 0.011 | 0.00017 | 0.032 | 0.0000 | no | 2.59e-04 | -/-/- | PASS | no | 22.2 (m0) (681, 1.61e-04) | pass (0.5/0.5/0.0) | no | no |
| hover_typ_s2 | 0.011 | 0.00017 | 0.031 | 0.0000 | no | 1.84e-04 | -/-/- | PASS | no | 22.2 (m0) (908, 1.52e-04) | pass (0.4/0.5/0.1) | no | no |
| hover_typ_s3 | 0.011 | 0.00017 | 0.031 | 0.0000 | no | 2.49e-04 | -/-/- | PASS | no | 22.2 (m0) (408, 1.54e-04) | pass (0.5/0.5/0.0) | no | no |
| hover_harsh_s1 | 0.024 | 0.00036 | 0.061 | 0.0000 | no | 6.04e-04 | -/-/- | PASS | no | 20.2 (m2) (123, 6.08e-04) | pass (0.3/0.3/0.0) | no | no |
| hover_harsh_s2 | 0.024 | 0.00036 | 0.061 | 0.0000 | no | 5.76e-04 | -/-/- | PASS | no | 20.0 (m0) (255, 5.74e-04) | pass (0.3/0.4/0.0) | no | no |
| hover_harsh_s3 | 0.024 | 0.00036 | 0.062 | 0.0000 | no | 5.03e-04 | -/-/- | PASS | no | 20.0 (m2) (74, 6.60e-04) | pass (0.4/0.4/0.0) | no | no |
| cruise_quiet_s1 | 0.020 | 0.00061 | 0.235 | 0.0000 | no | 4.19e-04 | -/-/- | PASS | no | 22.2 (m0) (4248, 1.64e-04) | pass (2.4/2.5/0.8) | no | no |
| cruise_quiet_s2 | 0.021 | 0.00063 | 0.267 | 0.0000 | no | 4.11e-04 | -/-/- | PASS | no | 22.2 (m0) (3834, 1.23e-04) | pass (2.4/2.3/0.9) | no | no |
| cruise_quiet_s3 | 0.021 | 0.00063 | 0.260 | 0.0000 | no | 4.14e-04 | -/-/- | PASS | no | 22.2 (m0) (1947, 7.86e-05) | pass (2.4/3.1/0.8) | no | no |
| cruise_typ_s1 | 0.022 | 0.00066 | 0.320 | 0.0000 | no | 4.12e-04 | -/-/- | PASS | no | 22.2 (m0) (986, 1.63e-04) | pass (5.1/5.2/1.3) | no | no |
| cruise_typ_s2 | 0.023 | 0.00068 | 0.338 | 0.0000 | no | 4.15e-04 | -/-/- | PASS | no | 22.2 (m0) (445, 1.51e-04) | pass (5.2/5.7/1.4) | no | no |
| cruise_typ_s3 | 0.023 | 0.00067 | 0.327 | 0.0000 | no | 4.19e-04 | -/-/- | PASS | no | 22.2 (m0) (476, 1.47e-04) | pass (5.6/4.9/1.6) | no | no |
| cruise_harsh_s1 | 0.029 | 0.00084 | 0.594 | 0.0000 | no | 5.52e-04 | S/S/- | FAIL | no | 20.0 (m1) (542, 5.58e-04) | FLAG p,q (14.1/13.2/3.5) | no | no |
| cruise_harsh_s2 | 0.030 | 0.00084 | 0.601 | 0.0000 | no | 5.83e-04 | S/S/- | FAIL | CHATTER | 20.0 (m1) (472, 6.04e-04) | FLAG p,q (13.9/13.5/3.7) | no | CHATTER |
| cruise_harsh_s3 | 0.029 | 0.00084 | 0.610 | 0.0000 | no | 6.04e-04 | S/S/- | FAIL | no | 20.0 (m3) (23, 5.84e-04) | FLAG p,q (14.2/12.4/3.5) | no | no |

## Row verdicts against the stated limits
| row | result |
|---|---|
| R20 | 18/18 within limit (max 0.030 % cruise harsh vs limit 4.5 %) |
| C20 | 18/18 within limit (max 8.4e-4, cruise harsh limit 0.018) |
| R4 | 18/18 within limit (max 0.610 %) |
| clip fraction | 18/18 (all 0) |
| command chatter, hover 9 | key 1 9/9 no chatter, key 2 9/9 no chatter; Q18 skip both keys 9/9 no chatter |
| command chatter, cruise 9 | key 1 9/9 no chatter; key 2 8/9, cruise_harsh_s2 CHATTER (motor m2, 20 Hz line, RMS 6.0e-4, ratio 472 at the max window); Q18 skip key 1 9/9 no, key 2 8/9 (same row still CHATTER) |
| item 2 rate detector, hover (harsh Q15 skip) | 9/9 pass both keys (max 0.6 dps) |
| item 2 rate detector, cruise (informational, outside harsh-hover scope) | harsh s1-s3: key 1 sustained p,q (S/S/-); key 2 FLAG p,q (12.4-14.2 dps vs 5 dps). Quiet/typ pass both keys (typ max 5.6 dps, below limit) |

## Chatter lines
Hover: no sustained line in either key; harsh 20.0-20.8 Hz lines at line RMS 5.0-6.6e-4 (just above the 5e-4 floor) in single windows only (13-17 s takeoff/loiter and 94-100 s), not sustained. Quiet/typ at 22 Hz or 20 Hz, RMS <= 2.6e-4.
Cruise (from chatter_cruise_raw.txt, key1 +-2 Hz): NO line at 33 Hz and NO line at 89 Hz in any flagged span (0/9). The sub-threshold 88.5-89.3 Hz line is still the max-line of key 1 gate (h>1.0 span) in quiet/typ: RMS 4.1-4.2e-4 (limit 5e-4), 0 flagged windows.
Flagged spans exist only at 20-21 Hz: AUTO_LAND (65-74 s, land-cmd windows, RMS 1.7-2.6e-3, 3.3-5.2x floor, 9/9 cruise), harsh cruise also 13-17 s takeoff/loiter (s1, 5.5e-4) and 57.5-65 s (s1-s3, 5.1-5.9e-4, hold-to-land transition).
cruise_harsh_s2 key 2 CHATTER: with the span h>0.3 and no skip, a sustained 20.1 Hz flag at 58.5-65 s (5.7e-4) appears (key 1 h>0.3 noskip = 1, key 2 = 1); with the 3 s skip it is 0. Key 1 gate span (h>1.0) and key 1 Q18 are no.

## Q18 skip
No verdict changes vs the unskipped gate columns: in the gate span no analysed window overlaps the skip interval (0 windows skipped on 18 runs for key 1); `--extend` (whole log) skips 6-7 windows and
shows the AUTO_LAND 20 Hz line at 1.4-2.7e-3 in the skipped windows (not counted). In the whole-log extension 6 rows are CHATTER without the skip (hover_quiet_s3, hover_typ_s1, hover_typ_s3, cruise_quiet_s3, cruise_harsh_s1, cruise_harsh_s2) and none after the skip (0/18); these rows are the Q18 case, outside the gate span.
Key 2 skip: 17/18 no chatter, cruise_harsh_s2 CHATTER (the skip does not change it; flagged windows are mid-flight). 3 runs (hover_harsh_s1, cruise_harsh_s1, s2) have a skipped worst line 70 Hz RMS 1.5e-4.

## Key agreement
Gate columns: keys agree on 17/18 rows. Disagreement: cruise_harsh_s2 chatter, key 1 no, key 2 CHATTER (key 2 span starts at ground-truth height > start + 0.3 m, key 1 gate span h > 1.0 m). Rate detector item 2 on cruise harsh: both keys flag p,q on s1-s3 (agree).

## Comparison to freeze-7
| | freeze-7 | freeze-8 |
|---|---|---|
| metrics R20/C20/R4/clip | 18/18 | 18/18 (R20 about 2x lower, C20 2x lower in cruise, R4 harsh hover 0.06 vs 0.10) |
| hover chatter | 8/9 (hover_harsh_s1 20.0 Hz 9.7e-4 take-off/loiter) | 9/9 both keys |
| cruise chatter | 0/9 both keys, 33.0-33.5 Hz line 1.4-1.5e-3 | key 1 9/9 no, key 2 8/9 (cruise_harsh_s2 20 Hz 6.0e-4, only with h>0.3 and no skip) |
| 33 Hz line | 9/9 cruise | gone |
| 89 Hz line | seen in gain probe | cruise_typ s2 4.15e-4, s3 4.19e-4 (limit 5e-4), s1 4.12e-4, quiet 4.1-4.2e-4: 0 flagged (consistent with the pre-test, 3.8-4.2e-4) |
| harsh cruise rate item 2 | sustained p,q in s2,s3 (key 1), flags 11.7-12.9 dps | key 1 sustained p,q in s1-s3; key 2 p,q in s1-s3 at 12.4-14.2 dps (worse) |

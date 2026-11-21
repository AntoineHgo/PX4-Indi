# G4 scores, freeze-9 (S183), 18 INDI runs, both keys, Q19 skip, PID guard

Runs: `g4/{hover,cruise}_{quiet,typ,harsh}_s{1,2,3}` (rc 0; cruise_harsh_s2 flown in the freeze-9 set) and PID references
`g4_pid/{hover,cruise}_harsh_s{1,2}` (rc 0 on try 1 each, `g4_pid/status.txt`). No verdict is stated here.

## Commands (repo root; Docker via indi_project/docker/run.sh)
```
# INDI, from g4/score_all.sh (previous agent, unchanged; stdout files newer than every flight.ulg, include cruise_harsh_s2, reused)
sh indi_flight/bench/gate_g4.sh score $D                       # -> g4/g4_table.md (R20 R4 C20 clip)
sed 's#results/g4_gate_s169#results/freeze9_s183/g4#; s#rescore_s175_runs#rescore_key1_q19_runs#' g4/rescore_key1_q19.py | python3 -   # key 1 Q19 -> g4/key1_q19_stdout.txt
sed 's#results/g4_gate_s169#results/freeze9_s183/g4#' g4/rescore_key2_q19.py | python3 -                                              # key 2 Q19 -> g4/key2_q19_stdout.txt
python3 g4/guard_q19.py g4/{hover,cruise}_{quiet,typ,harsh}_s{1,2,3} > g4/guard_indi.jsonl                                        # guard, INDI
# PID guard (this session, same script, unchanged)
python3 g4/guard_q19.py g4_pid/{hover,cruise}_harsh_s{1,2} > g4_pid/guard_pid.jsonl
```
Per-run json: `g4/<run>/g3_checks_q19.json`. Guard definition (guard_q19.py docstring): for each nav_state change inside the airborne span, all
4 s windows (hop 1 s, 20-100 Hz, line RMS peak +-2 Hz, 4 motors) overlapping [change, change+3 s]; "flagged" = ratio > 20 and line RMS >= 5e-4.

## Limits (GATES.md section 4 table; cruise R20, C20 = hover limit x1.5; R4 and clip not scaled)
R20 <= 1.0/1.5/3 %, C20 <= .004/.006/.012, R4 <= 3/4/6 %, clip 0/0/<=0.1 % (quiet/typ/harsh). Chatter = Q14 A line RMS >= 5e-4, ratio > 20, sustained,
with Q19 skip of windows overlapping 3 s after a nav_state change (both keys). Item 1 = LOC check, item 2 = rate oscillation detector, item 3 = steady state (rms xy <= 0.15 m, mean |dz| <= 0.1 m).

## Per-run table (value (limit) P/F)
Chatter column = key 1 chatter + max line RMS (ratio>20) / key 2 chatter + line RMS. Item 2 column = key 1 / key 2. Item 3 = xy RMS m / mean dz m.
| run | R20 % | C20 | R4 % | clip | item 1 | chatter K1 / K2 | item 2 K1 / K2 | skipped windows p/q/r (K1) | item 3 |
|---|---|---|---|---|---|---|---|---|---|
| hover_quiet_s1 | 0.003 (1) P | 0.00003 (0.004) P | 0.008 (3) P | 0.0000 (0) P | PASS | no 5.05e-05 / no 4.11e-05 | PASS / pass (0.2/0.2/0.0) | 19/19/19 | 0.012 / -0.022 PASS |
| hover_quiet_s2 | 0.003 (1) P | 0.00003 (0.004) P | 0.010 (3) P | 0.0000 (0) P | PASS | no 4.72e-05 / no 4.27e-05 | PASS / pass (0.3/0.3/0.0) | 19/19/19 | 0.025 / -0.028 PASS |
| hover_quiet_s3 | 0.003 (1) P | 0.00003 (0.004) P | 0.009 (3) P | 0.0000 (0) P | PASS | no 4.54e-05 / no 3.90e-05 | PASS / pass (0.3/0.3/0.0) | 19/19/19 | 0.012 / +0.053 PASS |
| hover_typ_s1 | 0.011 (1.5) P | 0.00016 (0.006) P | 0.029 (4) P | 0.0000 (0) P | PASS | no 7.15e-05 / no 5.24e-05 | PASS / pass (0.3/0.3/0.0) | 19/19/19 | 0.019 / +0.039 PASS |
| hover_typ_s2 | 0.011 (1.5) P | 0.00016 (0.006) P | 0.029 (4) P | 0.0000 (0) P | PASS | no 7.21e-05 / no 5.63e-05 | PASS / pass (0.4/0.4/0.0) | 19/19/19 | 0.032 / -0.037 PASS |
| hover_typ_s3 | 0.011 (1.5) P | 0.00016 (0.006) P | 0.029 (4) P | 0.0000 (0) P | PASS | no 2.58e-04 / no 5.33e-05 | PASS / pass (0.4/0.4/0.0) | 19/19/19 | 0.007 / +0.012 PASS |
| hover_harsh_s1 | 0.023 (3) P | 0.00034 (0.012) P | 0.058 (6) P | 0.0000 (0.001) P | PASS | no 1.45e-04 / no 1.32e-04 | PASS / pass (1.0/0.5/0.0) | 19/19/19 | 0.043 / -0.021 PASS |
| hover_harsh_s2 | 0.023 (3) P | 0.00034 (0.012) P | 0.058 (6) P | 0.0000 (0.001) P | PASS | no 1.43e-04 / no 1.36e-04 | PASS / pass (0.3/0.6/0.0) | 19/19/19 | 0.042 / +0.007 PASS |
| hover_harsh_s3 | 0.022 (3) P | 0.00033 (0.012) P | 0.056 (6) P | 0.0000 (0.001) P | PASS | no 1.43e-04 / no 1.33e-04 | PASS / pass (0.3/0.2/0.0) | 19/19/19 | 0.018 / -0.041 PASS |
| cruise_quiet_s1 | 0.020 (1.5) P | 0.00061 (0.006) P | 0.243 (3) P | 0.0000 (0) P | PASS | no 4.10e-04 / no 3.15e-04 | PASS / pass (2.3/2.1/0.8) | 19/19/19 | 0.024 / +0.183 FAIL |
| cruise_quiet_s2 | 0.021 (1.5) P | 0.00062 (0.006) P | 0.252 (3) P | 0.0000 (0) P | PASS | no 4.04e-04 / no 3.46e-04 | PASS / pass (2.3/2.2/0.7) | 19/19/19 | 0.009 / +0.110 FAIL |
| cruise_quiet_s3 | 0.020 (1.5) P | 0.00061 (0.006) P | 0.242 (3) P | 0.0000 (0) P | PASS | no 4.08e-04 / no 3.22e-04 | PASS / pass (2.3/2.3/0.8) | 19/19/19 | 0.038 / +0.100 PASS |
| cruise_typ_s1 | 0.022 (2.25) P | 0.00065 (0.009) P | 0.305 (4) P | 0.0000 (0) P | PASS | no 4.11e-04 / no 4.10e-04 | PASS / pass (4.5/4.0/1.2) | 20/20/20 | 0.039 / +0.098 PASS |
| cruise_typ_s2 | 0.022 (2.25) P | 0.00065 (0.009) P | 0.310 (4) P | 0.0000 (0) P | PASS | no 4.09e-04 / no 3.46e-04 | PASS / pass (4.5/4.3/1.2) | 19/19/19 | 0.035 / +0.147 FAIL |
| cruise_typ_s3 | 0.022 (2.25) P | 0.00065 (0.009) P | 0.285 (4) P | 0.0000 (0) P | PASS | no 4.05e-04 / no 3.95e-04 | PASS / pass (3.4/3.3/1.0) | 19/19/19 | 0.071 / +0.084 PASS |
| cruise_harsh_s1 | 0.028 (4.5) P | 0.00082 (0.018) P | 0.547 (6) P | 0.0000 (0.001) P | PASS | no 4.14e-04 / no 1.34e-04 | info: K1 FAIL (S/S/-) / info: K2 FLAG p,q (11.9/11.3/3.3) | 19/19/19 | 0.079 / +0.214 FAIL |
| cruise_harsh_s2 | 0.028 (4.5) P | 0.00083 (0.018) P | 0.574 (6) P | 0.0000 (0.001) P | PASS | no 4.19e-04 / no 1.34e-04 | info: K1 FAIL (S/S/-) / info: K2 FLAG p,q (12.1/11.7/3.0) | 20/20/20 | 0.019 / +0.168 FAIL |
| cruise_harsh_s3 | 0.027 (4.5) P | 0.00080 (0.018) P | 0.549 (6) P | 0.0000 (0.001) P | PASS | no 4.23e-04 / no 1.35e-04 | info: K1 FAIL (S/S/-) / info: K2 FLAG p,q (12.7/12.0/3.6) | 20/20/20 | 0.056 / +0.224 FAIL |

## PID guard (Q19: row fails if INDI line RMS in a skipped window exceeds PID at the same transition)
Transition ids as in guard_q19.py (nav_state from->to, nth). "flagged" = ratio > 20 and line RMS >= 5e-4; "any" = max line RMS over all overlapping windows
(Hz). Only in-span transitions have windows. Same scenario and seed, INDI vs PID.
| run | transition | t (s) | in span | n win INDI/PID | INDI flagged rms (Hz) | INDI any rms (Hz) | PID flagged rms (Hz) | PID any rms (Hz) | INDI line RMS > PID |
|---|---|---|---|---|---|---|---|---|---|---|
| hover_harsh_s1 | 4->17#1 | 30.2/30.2 | False/False | 0/0 | - | - | - | - | no |
| hover_harsh_s1 | 17->4#1 | 37.2/38.1 | True/True | 28/28 | - | 3.21e-04 (23.0) | - | 3.84e-04 (22.25) | no |
| hover_harsh_s1 | 4->14#1 | 52.0/52.0 | True/True | 28/28 | - | 1.39e-04 (70.0) | - | 1.02e-04 (70.0) | no |
| hover_harsh_s1 | 14->18#1 | 119.2/119.2 | True/True | 28/28 | 5.23e-04 (20.0) | 5.23e-04 (20.0) | - | 3.00e-04 (23.5) | YES |
| hover_harsh_s1 | 18->14#1 | 130.0/130.1 | False/False | 0/0 | - | - | - | - | no |
| hover_harsh_s2 | 4->17#1 | 30.0/30.2 | False/False | 0/0 | - | - | - | - | no |
| hover_harsh_s2 | 17->4#1 | 37.2/38.1 | True/True | 28/28 | 5.29e-04 (20.0) | 5.29e-04 (20.0) | - | 4.37e-04 (22.25) | YES |
| hover_harsh_s2 | 4->14#1 | 52.0/52.0 | True/True | 28/28 | - | 1.37e-04 (70.0) | - | 1.03e-04 (70.0) | no |
| hover_harsh_s2 | 14->18#1 | 120.0/119.2 | True/True | 28/28 | 5.03e-04 (20.5) | 5.03e-04 (20.5) | - | 3.01e-04 (22.5) | YES |
| hover_harsh_s2 | 18->14#1 | 131.0/130.1 | False/False | 0/0 | - | - | - | - | no |
| cruise_harsh_s1 | 4->17#1 | 31.0/30.2 | False/False | 4/0 | - | 2.97e-04 (22.25) | - | - | no |
| cruise_harsh_s1 | 17->4#1 | 37.2/38.1 | True/True | 28/28 | 5.31e-04 (20.0) | 5.31e-04 (20.0) | - | 4.03e-04 (22.25) | YES |
| cruise_harsh_s1 | 4->14#1 | 52.0/52.0 | True/True | 28/28 | - | 1.41e-04 (70.0) | - | 4.85e-04 (20.0) | no |
| cruise_harsh_s1 | 14->18#1 | 83.2/82.4 | True/True | 28/28 | - | 4.18e-04 (20.25) | - | 3.32e-04 (22.5) | no |
| cruise_harsh_s1 | 18->14#1 | 94.0/93.3 | False/False | 0/0 | - | - | - | - | no |
| cruise_harsh_s2 | 4->17#1 | 30.1/30.2 | False/False | 0/0 | - | - | - | - | no |
| cruise_harsh_s2 | 17->4#1 | 37.2/38.1 | True/True | 28/28 | - | 3.08e-04 (23.0) | - | 3.97e-04 (22.25) | no |
| cruise_harsh_s2 | 4->14#1 | 52.0/52.0 | True/True | 28/28 | - | 1.40e-04 (70.0) | - | 1.03e-04 (32.0) | no |
| cruise_harsh_s2 | 14->18#1 | 82.3/82.4 | True/True | 28/28 | 5.03e-04 (20.8) | 5.03e-04 (20.75) | - | 2.73e-04 (23.75) | YES |
| cruise_harsh_s2 | 18->14#1 | 93.3/93.2 | False/False | 0/0 | - | - | - | - | no |

Guard facts: INDI has a flagged line in a skipped window (20.0-20.8 Hz, 5.03e-4 to 5.31e-4, just over the 5e-4 floor) in 5 transitions, one or more in each of the 4
guard runs (hover_harsh_s1 14->18; hover_harsh_s2 17->4 and 14->18; cruise_harsh_s1 17->4; cruise_harsh_s2 14->18). At each of those the PID run has no flagged window and
its max line RMS is lower (3.00e-4, 4.37e-4, 3.01e-4, 4.03e-4, 2.73e-4 respectively; INDI 5.23e-4, 5.29e-4, 5.03e-4, 5.31e-4, 5.03e-4). So under the S183 text
the INDI line RMS exceeds the PID value at the same transition in 5 of 16 in-span transitions (4 of 4 runs have at least one).
Interpretation: GATES S183 says "chatter lines inside skipped windows are still reported ... the row FAILS if the INDI line RMS in a skipped window exceeds the PID
reference". I compared flagged-line RMS (INDI) against PID line RMS in the same transition (PID 0 when unflagged; the any-window values are in the table, and in each of the 5
cases the PID any-value is also below INDI). If instead any INDI line RMS above the PID any-window RMS counted regardless of the 5e-4 floor, further sub-floor transitions would
also exceed PID (for example 4->14 at 52 s: INDI 1.39-1.41e-4 vs PID 1.02-1.03e-4 at hover_harsh_s1/s2, cruise_harsh_s2; cruise_harsh_s1 14->18 4.18e-4 vs 3.32e-4); the
floor-based reading is the one used for the FAIL flags. Not-in-span transitions have 0 windows except cruise_harsh_s1 4->17 (INDI 4 windows in the transition list, out of the airborne span; not scored).

## Counts per G4 item (18 INDI runs)
| item | result |
|---|---|
| R20 | 18/18 within limit |
| C20 | 18/18 within limit |
| R4 | 18/18 within limit |
| clip | 18/18 (all 0) |
| item 1 (LOC) | 18/18 PASS (key 1) |
| command chatter (Q19 skip), key 1 | 18/18 no chatter (max line RMS of flagged windows 4.23e-4, cruise_harsh_s3; floor 5e-4); hover 9/9, cruise 9/9 |
| command chatter (Q19 skip), key 2 | 18/18 no chatter (max line RMS 4.10e-4 cruise_typ_s1); hover 9/9, cruise 9/9 |
| item 2 harsh hover (in scope per S183) | 3/3 PASS both keys (K2 max 1.0/0.5/0.0 dps) |
| item 2 other rows | quiet/typ hover 6/6 and quiet/typ cruise 6/6 PASS both keys; harsh cruise 3/3 flagged both keys (K1 sustained p,q; K2 FLAG p,q 11.9-12.7 / 11.3-12.0 dps): informational per S183, not counted |
| item 3, harsh hover (in scope per section 4 "G3 items 1-3 hold on the harsh profile in hover") | 3/3 PASS (xy RMS 0.018-0.043 m, mean dz -0.041..+0.007 m) |
| item 3, other rows (informational, interpretation below) | hover quiet/typ 6/6 PASS; cruise 3/9 PASS; cruise FAIL 6/9 all on mean dz 0.110-0.224 m vs 0.1 (xy RMS 0.009-0.079, within 0.15): cruise_harsh_s1,s2,s3, cruise_quiet_s1,s2, cruise_typ_s2 |
| PID guard | 4/4 guard runs have at least one skipped window where INDI line RMS (flagged, >= 5e-4) exceeds PID at the same transition (5 of 16 in-span transitions) |

Interpretation: item 3 is stated in GATES line 361-362 as holding "on the harsh profile in hover"; cruise item 3 values are reported only. The earlier sheets (freeze-7, freeze-8)
carry no PID-offset note for item 3, so I did not assert one. The cruise dz offset was not compared to PID in this session (not verified).

## Key disagreements
Chatter: none (18/18 no chatter on both keys). Item 2: none (hover and quiet/typ cruise pass both; harsh cruise flagged on both). Differences in values only (e.g. key 1 line RMS at
max-ratio vs key 2 line RMS differ by <= 1e-4 because of different span definitions); item 3 and guard are single-script.

## Unverified / notes
- Q19 skip and guard code are being reviewed separately; not reviewed here.
- Guard script comparison on PID used the INDI-run script unchanged; PID run.json "hold" event was present (script ran rc 0, 4 lines, empty .err).
- key1 stdout files were not re-run: both newer (17:59, 18:01) than the newest flight.ulg (cruise_harsh_s2, 17:54) and list all 18 runs.

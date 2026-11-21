# G4 scores, FREEZE-10 (S193), 18 INDI re-fly runs, both keys, Q19 skip, Q20 PID guard

Firmware 7fe6206fcc (FREEZE-10). Queue step 3, 00:20-00:39 2026-11-22. Runs `g4/{hover,cruise}_{quiet,typ,harsh}_s{1,2,3}`, rc 0.
Scored from the existing outputs in `g4/` (no re-fly, no re-run of scoring). fz9 = `results/freeze9_s183/G4_SCORES.md`.
Q20 PID references: `g4_pid` is a symlink to `../freeze9_s183/g4_pid` (freeze-9 flights, hover_harsh and cruise_harsh s1, s2).

## Summary
- Effort (R20, C20, R4, clip): 18/18 PASS (fz9 18/18).
- G4 key 1 (effort, item 1, chatter, item 2): 18/18 PASS (fz9 18/18).
- G4 key 2 (same, key 2 chatter and item 2): 18/18 PASS (fz9 18/18).
- Item 3 steady state FAIL: 9/18, all cruise (9/9; fz9 6/9). Not part of the G4 verdict here, as in the freeze-9 verdict (carried limit, S180/S187). Shown per row so the owner can decide.
- Q20 guard: 54 transitions in 18 INDI runs, both keys: 0 checked, 0 FAIL (fz9 0 checked, 0 FAIL).

## Effort, value (limit) P/F; fz9 beside
Cruise R20 and C20 limits = hover x1.5; R4 and clip not scaled (GATES.md section 4 table, as in freeze-9).

| run | R20 % fz10 (lim) | R20 % fz9 | C20 fz10 (lim) | C20 fz9 | R4 % fz10 (lim) | R4 % fz9 | clip fz10 (lim) | clip fz9 | effort fz10 / fz9 |
|---|---|---|---|---|---|---|---|---|---|
| hover_quiet_s1 | 0.003 (1) P | 0.003 (1) P | 0.00003 (0.004) P | 0.00003 (0.004) P | 0.009 (3) P | 0.008 (3) P | 0.0000 (0) P | 0.0000 (0) P | PASS / PASS |
| hover_quiet_s2 | 0.003 (1) P | 0.003 (1) P | 0.00003 (0.004) P | 0.00003 (0.004) P | 0.009 (3) P | 0.010 (3) P | 0.0000 (0) P | 0.0000 (0) P | PASS / PASS |
| hover_quiet_s3 | 0.003 (1) P | 0.003 (1) P | 0.00003 (0.004) P | 0.00003 (0.004) P | 0.008 (3) P | 0.009 (3) P | 0.0000 (0) P | 0.0000 (0) P | PASS / PASS |
| hover_typ_s1 | 0.008 (1.5) P | 0.011 (1.5) P | 0.00014 (0.006) P | 0.00016 (0.006) P | 0.025 (4) P | 0.029 (4) P | 0.0000 (0) P | 0.0000 (0) P | PASS / PASS |
| hover_typ_s2 | 0.008 (1.5) P | 0.011 (1.5) P | 0.00013 (0.006) P | 0.00016 (0.006) P | 0.024 (4) P | 0.029 (4) P | 0.0000 (0) P | 0.0000 (0) P | PASS / PASS |
| hover_typ_s3 | 0.008 (1.5) P | 0.011 (1.5) P | 0.00013 (0.006) P | 0.00016 (0.006) P | 0.024 (4) P | 0.029 (4) P | 0.0000 (0) P | 0.0000 (0) P | PASS / PASS |
| hover_harsh_s1 | 0.016 (3) P | 0.023 (3) P | 0.00025 (0.012) P | 0.00034 (0.012) P | 0.041 (6) P | 0.058 (6) P | 0.0000 (0.001) P | 0.0000 (0.001) P | PASS / PASS |
| hover_harsh_s2 | 0.016 (3) P | 0.023 (3) P | 0.00025 (0.012) P | 0.00034 (0.012) P | 0.041 (6) P | 0.058 (6) P | 0.0000 (0.001) P | 0.0000 (0.001) P | PASS / PASS |
| hover_harsh_s3 | 0.016 (3) P | 0.022 (3) P | 0.00025 (0.012) P | 0.00033 (0.012) P | 0.042 (6) P | 0.056 (6) P | 0.0000 (0.001) P | 0.0000 (0.001) P | PASS / PASS |
| cruise_quiet_s1 | 0.021 (1.5) P | 0.020 (1.5) P | 0.00062 (0.006) P | 0.00061 (0.006) P | 0.248 (3) P | 0.243 (3) P | 0.0000 (0) P | 0.0000 (0) P | PASS / PASS |
| cruise_quiet_s2 | 0.020 (1.5) P | 0.021 (1.5) P | 0.00061 (0.006) P | 0.00062 (0.006) P | 0.245 (3) P | 0.252 (3) P | 0.0000 (0) P | 0.0000 (0) P | PASS / PASS |
| cruise_quiet_s3 | 0.022 (1.5) P | 0.020 (1.5) P | 0.00064 (0.006) P | 0.00061 (0.006) P | 0.279 (3) P | 0.242 (3) P | 0.0000 (0) P | 0.0000 (0) P | PASS / PASS |
| cruise_typ_s1 | 0.022 (2.25) P | 0.022 (2.25) P | 0.00064 (0.009) P | 0.00065 (0.009) P | 0.268 (4) P | 0.305 (4) P | 0.0000 (0) P | 0.0000 (0) P | PASS / PASS |
| cruise_typ_s2 | 0.022 (2.25) P | 0.022 (2.25) P | 0.00064 (0.009) P | 0.00065 (0.009) P | 0.266 (4) P | 0.310 (4) P | 0.0000 (0) P | 0.0000 (0) P | PASS / PASS |
| cruise_typ_s3 | 0.021 (2.25) P | 0.022 (2.25) P | 0.00063 (0.009) P | 0.00065 (0.009) P | 0.254 (4) P | 0.285 (4) P | 0.0000 (0) P | 0.0000 (0) P | PASS / PASS |
| cruise_harsh_s1 | 0.023 (4.5) P | 0.028 (4.5) P | 0.00066 (0.018) P | 0.00082 (0.018) P | 0.271 (6) P | 0.547 (6) P | 0.0000 (0.001) P | 0.0000 (0.001) P | PASS / PASS |
| cruise_harsh_s2 | 0.023 (4.5) P | 0.028 (4.5) P | 0.00065 (0.018) P | 0.00083 (0.018) P | 0.274 (6) P | 0.574 (6) P | 0.0000 (0.001) P | 0.0000 (0.001) P | PASS / PASS |
| cruise_harsh_s3 | 0.024 (4.5) P | 0.027 (4.5) P | 0.00067 (0.018) P | 0.00080 (0.018) P | 0.295 (6) P | 0.549 (6) P | 0.0000 (0.001) P | 0.0000 (0.001) P | PASS / PASS |

## Noise: chatter, item 2, item 1, item 3, per key; fz9 beside
K1 chatter = max line RMS at ratio > 20 (limit 5e-4 flags; "no" = not flagged). K2 chatter = line RMS at peak ratio, same rule. Item 2 detail = max flagged-window rms (deg/s) p/q/r.
Item 3 = xy RMS (limit 0.15 m) / mean dz (limit 0.1 m), fz9 in parentheses.

| run | K1 chatter fz10 (fz9) | K1 item 2 fz10 (fz9) | K2 chatter fz10 (fz9) | K2 item 2 detail fz10 (fz9) | item 1 fz10 (fz9) | item 3 fz10 (fz9) | K1 G4 | K2 G4 |
|---|---|---|---|---|---|---|---|---|
| hover_quiet_s1 | 4.96e-05 (5.05e-05) no | PASS (PASS) | 4.07e-05 (4.11e-05) no | pass 0.3/0.2/0.0 (fz9 pass (0.2/0.2/0.0)) | PASS (PASS) | 0.013 / +0.008 PASS (fz9 0.012 / -0.022 PASS) | PASS | PASS |
| hover_quiet_s2 | 5.26e-05 (4.72e-05) no | PASS (PASS) | 5.01e-05 (4.27e-05) no | pass 0.3/0.3/0.0 (fz9 pass (0.3/0.3/0.0)) | PASS (PASS) | 0.026 / +0.028 PASS (fz9 0.025 / -0.028 PASS) | PASS | PASS |
| hover_quiet_s3 | 4.76e-05 (4.54e-05) no | PASS (PASS) | 3.89e-05 (3.90e-05) no | pass 0.3/0.2/0.0 (fz9 pass (0.3/0.3/0.0)) | PASS (PASS) | 0.017 / +0.016 PASS (fz9 0.012 / +0.053 PASS) | PASS | PASS |
| hover_typ_s1 | 1.90e-04 (7.15e-05) no | PASS (PASS) | 4.92e-05 (5.24e-05) no | pass 0.5/0.5/0.1 (fz9 pass (0.3/0.3/0.0)) | PASS (PASS) | 0.027 / -0.015 PASS (fz9 0.019 / +0.039 PASS) | PASS | PASS |
| hover_typ_s2 | 1.78e-04 (7.21e-05) no | PASS (PASS) | 5.69e-05 (5.63e-05) no | pass 0.4/0.5/0.0 (fz9 pass (0.4/0.4/0.0)) | PASS (PASS) | 0.055 / -0.011 PASS (fz9 0.032 / -0.037 PASS) | PASS | PASS |
| hover_typ_s3 | 1.80e-04 (2.58e-04) no | PASS (PASS) | 5.68e-05 (5.33e-05) no | pass 0.3/0.4/0.0 (fz9 pass (0.4/0.4/0.0)) | PASS (PASS) | 0.023 / -0.037 PASS (fz9 0.007 / +0.012 PASS) | PASS | PASS |
| hover_harsh_s1 | 1.14e-04 (1.45e-04) no | PASS (PASS) | 8.70e-05 (1.32e-04) no | pass 0.3/0.3/0.0 (fz9 pass (1.0/0.5/0.0)) | PASS (PASS) | 0.027 / +0.013 PASS (fz9 0.043 / -0.021 PASS) | PASS | PASS |
| hover_harsh_s2 | 1.13e-04 (1.43e-04) no | PASS (PASS) | 1.01e-04 (1.36e-04) no | pass 0.3/0.3/0.0 (fz9 pass (0.3/0.6/0.0)) | PASS (PASS) | 0.033 / -0.029 PASS (fz9 0.042 / +0.007 PASS) | PASS | PASS |
| hover_harsh_s3 | 1.11e-04 (1.43e-04) no | PASS (PASS) | 9.94e-05 (1.33e-04) no | pass 0.3/0.3/0.0 (fz9 pass (0.3/0.2/0.0)) | PASS (PASS) | 0.047 / +0.004 PASS (fz9 0.018 / -0.041 PASS) | PASS | PASS |
| cruise_quiet_s1 | 4.10e-04 (4.10e-04) no | PASS (PASS) | 3.46e-04 (3.15e-04) no | pass 2.6/2.7/0.9 (fz9 pass (2.3/2.1/0.8)) | PASS (PASS) | 0.030 / +0.192 FAIL (fz9 0.024 / +0.183 FAIL) | PASS | PASS |
| cruise_quiet_s2 | 4.09e-04 (4.04e-04) no | PASS (PASS) | 3.96e-04 (3.46e-04) no | pass 2.2/2.2/0.8 (fz9 pass (2.3/2.2/0.7)) | PASS (PASS) | 0.025 / +0.275 FAIL (fz9 0.009 / +0.110 FAIL) | PASS | PASS |
| cruise_quiet_s3 | 4.06e-04 (4.08e-04) no | PASS (PASS) | 4.00e-05 (3.22e-04) no | pass 2.3/3.4/1.0 (fz9 pass (2.3/2.3/0.8)) | PASS (PASS) | 0.026 / +0.135 FAIL (fz9 0.038 / +0.100 PASS) | PASS | PASS |
| cruise_typ_s1 | 4.08e-04 (4.11e-04) no | PASS (PASS) | 3.24e-04 (4.10e-04) no | pass 2.5/3.1/0.7 (fz9 pass (4.5/4.0/1.2)) | PASS (PASS) | 0.043 / +0.316 FAIL (fz9 0.039 / +0.098 PASS) | PASS | PASS |
| cruise_typ_s2 | 4.11e-04 (4.09e-04) no | PASS (PASS) | 4.01e-04 (3.46e-04) no | pass 2.2/3.6/1.2 (fz9 pass (4.5/4.3/1.2)) | PASS (PASS) | 0.038 / +0.333 FAIL (fz9 0.035 / +0.147 FAIL) | PASS | PASS |
| cruise_typ_s3 | 4.07e-04 (4.05e-04) no | PASS (PASS) | 3.38e-04 (3.95e-04) no | pass 2.1/2.7/0.9 (fz9 pass (3.4/3.3/1.0)) | PASS (PASS) | 0.036 / +0.288 FAIL (fz9 0.071 / +0.084 PASS) | PASS | PASS |
| cruise_harsh_s1 | 4.08e-04 (4.14e-04) no | PASS (info: K1 FAIL (S/S/-)) | 1.01e-04 (1.34e-04) no | pass 2.2/2.3/0.9 (fz9 info: K2 FLAG p,q (11.9/11.3/3.3)) | PASS (PASS) | 0.050 / +0.119 FAIL (fz9 0.079 / +0.214 FAIL) | PASS | PASS |
| cruise_harsh_s2 | 4.12e-04 (4.19e-04) no | PASS (info: K1 FAIL (S/S/-)) | 2.91e-04 (1.34e-04) no | pass 2.4/2.5/1.0 (fz9 info: K2 FLAG p,q (12.1/11.7/3.0)) | PASS (PASS) | 0.095 / +0.291 FAIL (fz9 0.019 / +0.168 FAIL) | PASS | PASS |
| cruise_harsh_s3 | 4.12e-04 (4.23e-04) no | PASS (info: K1 FAIL (S/S/-)) | 8.79e-05 (1.35e-04) no | pass 2.3/2.9/0.8 (fz9 info: K2 FLAG p,q (12.7/12.0/3.6)) | PASS (PASS) | 0.049 / +0.330 FAIL (fz9 0.056 / +0.224 FAIL) | PASS | PASS |

Note: K1 chatter column shows the freeze-10 max line RMS at ratio>20 first, then the flag; K2 column shows the line RMS at peak ratio. Both keys: 18/18 "no" chatter.

## Q20 PID guard (both keys, S187 rule)
Key 1 (`g4/guard_q20_key1_stdout.txt`): 54 transitions, 0 checked, 0 FAIL. Max INDI narrow RMS over skipped windows 3.459e-04 (hover_harsh_s2 14->18), vs floor 5e-4 and bound 1e-3. fz9 max 4.839e-04 (hover_harsh_s2 17->4).
Key 2 (`g4/guard_q20_key2_stdout.txt`, JSON): 54 transitions, 0 checked, 0 FAIL. Max INDI narrow RMS 3.459e-04 (hover_harsh_s2 14->18). PID refs present for 12 transitions.
Guard PID side: transitions with a PID reference are hover_harsh and cruise_harsh s1, s2 only (freeze-9 PID flights); none reached the floor.

Self-tests: key 1 `guard_q20_selftest1.txt` 8/8 PASS, "selftest OK". Key 2 `guard_q20_selftest2.txt` 9/9 PASS.

## Integrity
- stderr: all 7 stderr/err files are 0 bytes (`key1_stderr`, `key2_stderr`, `key1_q19_stderr`, `key2_q19_stderr`, `guard_q20_key1_stderr`, `guard_q20_key2_stderr`, `guard_indi.err`). No traceback or error text in any g4 text output. `score_g4_table.log` is 0 bytes; `g4_table.md` was written directly by `gate_g4.sh score`.
- Expected outputs: all present (g4_table.md, key1/key2 stdout, key1/key2 Q19 stdout, guard_indi.jsonl, chatter_stdout.txt, guard_q20 key1/key2 stdout, both self-test files, score_all.done, g4_score.done). All 18 run dirs have flight.ulg, g3_checks_q19.json, g4_metrics.json.
- Paths: the `log` field of all 18 `g3_checks_q19.json` points to `freeze10_s193`. No `freeze9` string in the g4 scripts or text outputs. The only freeze-9 link is `g4_pid` (symlink to `../freeze9_s183/g4_pid`), which the Q20 guard reads for the PID references of hover_harsh and cruise_harsh s1, s2. This is by design in `g4_score.sh` (PID not re-flown); I did not verify that the PID firmware matches 7fe6206fcc.
- Self-tests: `q18/selftests.txt` prints 4 FAIL lines and a final "OK (skip passes, broken skip fails as required)". The FAIL lines are the deliberate broken-skip controls and are identical to freeze-9 (`freeze9_s183/g4/q18/selftests.txt`). Q20 self-tests: no FAIL.
- Key 1 vs key 2 disagreement: none. Verdicts for effort, item 1, chatter and item 2 match on all 18 rows. The pre-Q19 files (`key1_stdout.txt`, `key2_stdout.txt`) also show no chatter and item 2 PASS everywhere.
- Raw chatter (`chatter_stdout.txt`, no Q19 skip): flagged windows occur in 9/9 cruise runs, all in the land-cmd phase (3-7 windows per run). Sustained chatter is 0 in all variants for all 9 runs.
- Git (`git status --short indi_flight/results`): tracked modifications are `freeze10_s193/g4/rescore_key1_q19.py` (path rewrite freeze9 to freeze10 by the scoring `sed -i`, in scope) and `freeze10_s193/queue_status.tsv` (not from this scoring). No tracked file outside freeze10_s193 is modified. Nothing committed.

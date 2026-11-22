# G3 pre-test re-run S197 (Q24 B, GNSS mismatch +-50 ms)

Purpose: the owner narrowed the sampler GNSS compensation mismatch from +-100 ms to +-50 ms (DECISIONS.md D-OWNER-Q24, GATES.md owner amendments S197). Same firmware (binary sha256 d220e193... in all 14 new runs), seed 173, n 300. Draws whose plant did not change keep their freeze-10 flight and verdicts (`../freeze10_s193/g3_pretest/`). Changed draws were re-flown.

Old range evidence (kept as is): key 1 16/20, key 2 16/20, fails 02, 03, 05, 08 (`../freeze10_s193/g3_pretest/README.md`).

## Verification
`draw_diff.json` (from `draw_diff.py`): the 14 changed draws (01 02 03 04 05 08 09 10 11 12 13 16 17 18) differ only in `gnss.ekf_delay_ms`, `gnss.drawn_ekf_delay_ms`, `factors.gnss.mismatch_offset_ms`, the `--gnss-delay` argument and output path strings. `params_equal` is true for all. Draws 00 06 07 14 15 19 have no diff (mismatch 0).

## Commands (repo root)
- `bash indi_flight/results/g3_pretest_q24_s197/fly_all.sh 1`, then `... 2 3 4 5 8 9 10` (earlier session), then `... 11 12 13 16 17 18` (this session; run 11 had been cut, re-flown in place). All rc 0 (`progress.txt`).
- `bash indi_flight/results/g3_pretest_q24_s197/score_all.sh` (key 1 `bench/g3_score_docker.sh`, key 2 `bench/g3_checks_key2.py`) writes `SCORE_KEY1.txt`, `SCORE_KEY2.txt`, `key2/`.

## Per-draw table
GNSS: true latency / new ekf compensation / mismatch (ms). Unchanged draws: freeze-10 verdicts.

| run | changed | latency / ekf / mismatch | key 1 | key 2 | note / failing check |
|---|---|---|---|---|---|
| 00 | n | 152 / 152 / +0 (old ekf 152, +0) | PASS | PASS | freeze-10 flight;  |
| 01 | y | 86 / 79 / +7 (old ekf 73, +13) | PASS | PASS | new flight;  |
| 02 | y | 226 / 178 / +48 (old ekf 131, +95) | FAIL | FAIL | new flight; i3 horiz RMS 0.318 m (limit 0.30), both keys |
| 03 | y | 168 / 158 / +10 (old ekf 148, +20) | FAIL | FAIL | new flight; i2 q-axis sustained 2.0 Hz, 3 windows, flagged RMS 17.7 dps (key 1); 2.0 Hz at 35 s, max 11.8 dps (key 2) |
| 04 | y | 170 / 219 / -49 (old ekf 268, -98) | PASS | PASS | new flight;  |
| 05 | y | 186 / 144 / +42 (old ekf 102, +84) | PASS | PASS | new flight;  |
| 06 | n | 219 / 219 / +0 (old ekf 219, +0) | PASS | PASS | freeze-10 flight;  |
| 07 | n | 123 / 123 / +0 (old ekf 123, +0) | PASS | PASS | freeze-10 flight;  |
| 08 | y | 107 / 139 / -32 (old ekf 170, -63) | FAIL | FAIL | new flight; i2 q-axis sustained 10.75 Hz, 14 windows, flagged RMS 7.5 dps (key 1); 10.75 Hz at 25 s, max 7.9 dps (key 2) |
| 09 | y | 154 / 135 / +19 (old ekf 116, +38) | PASS | PASS | new flight;  |
| 10 | y | 248 / 218 / +30 (old ekf 189, +59) | PASS | PASS | new flight;  |
| 11 | y | 245 / 256 / -11 (old ekf 268, -23) | PASS | PASS | new flight;  |
| 12 | y | 176 / 193 / -17 (old ekf 210, -34) | PASS | PASS | new flight;  |
| 13 | y | 119 / 166 / -47 (old ekf 213, -94) | PASS | PASS | new flight;  |
| 14 | n | 120 / 120 / +0 (old ekf 120, +0) | PASS | PASS | freeze-10 flight;  |
| 15 | n | 190 / 190 / +0 (old ekf 190, +0) | PASS | PASS | freeze-10 flight;  |
| 16 | y | 203 / 222 / -19 (old ekf 240, -37) | PASS | PASS | new flight;  |
| 17 | y | 201 / 195 / +6 (old ekf 190, +11) | PASS | PASS | new flight;  |
| 18 | y | 209 / 249 / -40 (old ekf 289, -80) | PASS | PASS | new flight;  |
| 19 | n | 207 / 207 / +0 (old ekf 207, +0) | PASS | PASS | freeze-10 flight;  |

## Totals under +-50 ms
- Key 1: 17/20 pass. Key 2: 17/20 pass. Fails 02, 03, 08 on both keys.
- Not counted: 03 (key 1) and 08 failed for the PID reference under the old range (freeze10_s193 README: 03 PID key 1 FAIL / key 2 PASS; 08 PID FAIL on both keys). Both still fail with INDI under the new range (03 key 1 and key 2, 08 both keys), so they are reported as shared with PID only where the PID ref failed. Counting only non-shared failures: key 1 only 02 is INDI-specific; key 2 02 and 03 (PID key 2 passed 03).
- 02: mismatch is now +48 ms (was +95), still item 3 horiz RMS 0.318 m vs 0.30 limit on both keys (was 0.499). PID ref passes 02 (old firmware), so INDI-side. Item 2 now passes.
- 05: mismatch now +42 ms (was +84): PASS both keys, item 3 horiz RMS 0.284 m (limit 0.30), item 2 clean. 02 does not pass, 05 does.
- Key 2 col 5 (G4 chatter, not in the G3 verdict) False for 10, 16, 18.

## Caveats
- Oscillation limits are the detector's sustained-line rule, not a numeric threshold; RMS values are flagged-window values from the check json files.
- Run 11 partial files were overwritten by the re-fly; run_011 disturbance_summary.json / disturbance_trigger.json show as modified in git for that reason.
- Not checked: whether the 02 item 3 miss (0.318 vs 0.30) is within run-to-run noise.

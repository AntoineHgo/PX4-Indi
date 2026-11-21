# FREEZE-10 G3 pre-test (S193): results

## What was flown
- Firmware FREEZE-10 at 7fe6206fcc (revert of aa4fd2654a). run.json `binary_commit` c0b733e677 (docs commit on 7fe6206fcc, as in the S191 probe); binary sha256 d220e193... is identical in all 20 runs.
- Recipe of g3_pretest_s190: `bench/g3_run.py --seed 173 --n 300`, draws 0-19 (`fly_all.sh`). Applied draws and argv match S190 exactly, except S193 adds the `gnss.drawn_ekf_delay_ms` key and output paths.
- Launched by `../queue.sh` step 1, 22:58:28 to 23:34:16, rc 0 (queue_status.tsv). Scored in the same step. This note only reads existing outputs.

## Counts
- Key 1: 16/20 pass (S191: 15/20). Fails 02, 03, 05, 08.
- Key 2: 16/20 pass (S191: 16/20). Fails 02, 03, 05, 08.
- Item 1: 20/20 on both keys. Item 2 fails: key 1 02, 03, 08; key 2 02, 03, 05, 08. Item 3 fails: 02, 05 on both keys.
- Changed vs S190 (key 1): 19 FAIL to pass; 05 item 2 FAIL to pass (item 3 still fails); 02 now also fails item 2 (q 2.0 Hz). Key 2 verdicts unchanged. G4 chatter flag (col 5): 004 gone, 005 new (016, 018 as before).

## Per-run table
Key 2 columns: pass / item1 / item2 / item3 / col5. Mismatch = `gnss.latency_ms` (true delay) minus `gnss.ekf_delay_ms` (compensation), ms. PID = key 1 / key 2 pass, from `g3_pretest_s187/pid_refs/`.

| run | key 1 | key 1 failing item and detector line (axis, Hz, RMS dps) | key 2 | mismatch ms | PID ref |
|---|---|---|---|---|---|
| 00 | pass | | T T T T T | 0 | P/P |
| 01 | pass | | T T T T T | +13 | none |
| 02 | FAIL | i2: q 2.0 Hz, 4 win, 14.5; i3: horiz 0.499 m | F T F F T | +95 | P/P |
| 03 | FAIL | i2: q 2.0 Hz (2 lines, 3 and 4 win), 19.9 | F T F T T | +20 | F/P (q 2.5 Hz, 12.6) |
| 04 | pass | | T T T T T | -98 | none |
| 05 | FAIL | i3: horiz 0.488 m; no i2 line (q 6 flagged win, not sustained) | F T F F F | +84 | P/P |
| 06 | pass | | T T T T T | 0 | none |
| 07 | pass | | T T T T T | 0 | none |
| 08 | FAIL | i2: q 10.75 Hz, 14 win, 9.6 | F T F T T | -63 | F/F (p 11 Hz, r 8 Hz) |
| 09 | pass | | T T T T T | +38 | P/P |
| 10 | pass | | T T T T T | +59 | P/P |
| 11 | pass | | T T T T T | -23 | none |
| 12 | pass | | T T T T T | -34 | none |
| 13 | pass | | T T T T T | -94 | F/F (i3) |
| 14 | pass | | T T T T T | 0 | none |
| 15 | pass | | T T T T T | 0 | none |
| 16 | pass | | T T T T F | -37 | P/P |
| 17 | pass | | T T T T T | +11 | P/P |
| 18 | pass | | T T T T F | -80 | none |
| 19 | pass | | T T T T T | 0 | none |

Key 2 failing lines (time s, Hz, RMS dps): 02 q 2.0 Hz at 29.0, 16.2; 03 q 2.5 Hz at 25.0, 18.7; 05 q 2.0 Hz at 33.0, 13.0; 08 q 10.75 Hz at 25.0, 8.4. Key 1 line offsets are relative to its detector start and key 2 times are flight time; the two time bases were not reconciled.

## Runs 02 and 05
- 02: q 2.0 Hz oscillation (key 1 14.5 dps, key 2 16.2 dps), item 3 horiz 0.499 m (limit 0.30). Mismatch +95 ms, the largest positive draw. Same failure set as S190 (where item 3 was 0.54 m with q 12.2 dps on the S191 trace).
- 05: no key 1 sustained line; key 2 q 2.0 Hz at 33 s, 13.0 dps. Item 3 horiz 0.488 m. Mismatch +84 ms, the second largest. S191 measured 8.5 dps at 1.45 Hz.
- Matches the S191/S192 finding in outcome: both draws fail again with a large uncompensated GNSS delay, and the matched-GNSS probe (`freeze10_cand_s191/README.md` section 4) passed items 1-3 on both keys (0.133 and 0.108 m).
- Not confirmed: the detector band is 2.0-40 Hz (`bench/g3_checks.py` line 58), so a 1.45 Hz line cannot be reported as such. The 2.0 Hz lines sit on the band floor. Whether they are the same 1.45 Hz accel-loop oscillation was not checked here.
- PID refs for 02 and 05 pass on both keys, so the failure is INDI-side on these draws (see caveats on binary).

## Runs 03 and 08
- 03: INDI item 2 fails on both keys (key 1 q 2.0 Hz at 19.9 dps; key 2 q 2.5 Hz at 18.7 dps). Item 3 passes (0.202 m, alt 0.023). Mismatch +20 ms. PID ref: key 1 FAIL (q 2.5 Hz, 3 windows, 12.6 dps), key 2 PASS (max q RMS 1.75 dps). Same key 1 vs key 2 split as the S189 reconcile (key 1 has no nav-change skip).
- 08: INDI item 2 fails on both keys (q 10.75 Hz, 9.6 and 8.4 dps). Item 3 passes (0.080 m). Mismatch -63 ms. PID ref: fails both keys on p 11 Hz and r 8 Hz (key 2 PID p RMS 205 dps; q not sustained). Different axis than INDI, close frequency.

## Column 5 (key 2 `chatter` pass)
- It is `chatter["pass"]` from `bench/g3_checks_key2.py` (printed as the 5th field, line 293). It is the G4 motor-command chatter check (command lines in 20-100 Hz). True means no sustained chatter.
- It does not enter the G3 verdict: `pass = item1 and item2 and item3` (line 198). Runs 16 and 18 pass G3 with col 5 False.
- False in 05, 16, 18. Key 1 `g4_command_chatter_sustained` is True for the same three runs, so the two keys agree.

## Caveats and not found
- The PID refs are not in `g3_pretest_s190/`. They are in `g3_pretest_s187/pid_refs/` (S188 batch, 10 runs: 00, 02, 03, 05, 08, 09, 10, 13, 16, 17). Their binary is commit 7dc87e84c3 (sha c6a11b2ba9), not the S193 binary. The comparison crosses firmware.
- No separate S192 matched-GNSS note found. Used `freeze10_cand_s191/README.md` section 4 and `g3_matched/`.
- Not run: the 1.45 Hz trace (q145_trace.txt) on the S193 logs.
- PID refs not flown for 01, 04, 06, 07, 11, 12, 14, 15, 18, 19: "none".

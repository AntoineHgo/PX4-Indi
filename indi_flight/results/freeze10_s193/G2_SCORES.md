# G2 at FREEZE-10 (S193 cells, firmware 7fe6206fcc), scores

Queue step 4 ran 2026-11-22 00:39-01:14 (queue_status.tsv, all rc 0). Outer cells, spot cells and G2-STEP flights come from `queue.sh` step 4. The primary outer table, the second key, and the G2-STEP scorers were run by hand (host python3, no containers), as freeze-9 did (see Commands). Freeze-9 values are beside each value, in parentheses where the freeze-9 table has freeze-8 too.

Limits (as freeze-8 and freeze-9): PM >= 45 deg; GM >= 6 dB (GM n/a = no -180 crossing in the 0.2-8 Hz band, so no GM limit; plateau GM = key2 phase-plateau gain margin); DM >= 2 control periods + telemetry latency (never binding). Q13 A: bins with |L| > 1 within 10 deg of -180 deg are gain-reduction margins 20log10|L| and must also be >= 6 dB. Key2 agreement: |dPM| <= 3 deg and |dGM| <= 1 dB, same presence/absence of GM, otherwise BLOCKED.

## G2 outer loops (24 cells)

| cell | GM dB (primary) | plateau GM dB (key2) | PM deg (primary) | PM deg (key2) | DM ms (primary) | holes | key2 | verdict | freeze-9 GM / PM / DM (holes, key2 final after S184) |
|---|---|---|---|---|---|---|---|---|---|
| pt0_ax1_r400_s1 | 13.5 | 12.95 | 50.2 | 51.7 | 388 | PASS | agree (dPM +1.5) | PASS | 13.7 / 51.2 / 412 (PASS, agree) |
| pt0_ax1_r400_s2 | 13.6 | 13.04 | 49.7 | 50.0 | 367 | PASS | agree (+0.3) | PASS | 13.4 / 51.6 / 384 (first hole FAIL, re-flown PASS) |
| pt0_ax1_r800_s1 | 14.0 | 13.35 | 52.4 | 52.2 | 399 | PASS | agree (-0.2) | PASS | 14.0 / 49.0 / 354 (PASS, agree) |
| pt0_ax1_r800_s2 | 14.0 | 13.30 | 55.3 | 55.3 | 386 | PASS | agree (-0.1) | PASS | 14.0 / 48.5 / 358 (PASS, agree) |
| pt0_ax2_r400_s1 | 13.5 | 12.88 | 50.5 | 50.1 | 377 | PASS | agree (-0.3) | PASS | 13.5 / 51.6 / 406 (PASS, agree) |
| pt0_ax2_r400_s2 | 13.5 | 12.96 | 49.1 | 49.4 | 367 | PASS | agree (+0.3) | PASS | 13.6 / 55.7 / 388 (PASS, agree) |
| pt0_ax2_r800_s1 | 13.9 | 13.26 | 51.3 | 51.7 | 383 | PASS | agree (+0.4) | PASS | 14.1 / 49.9 / 374 (PASS, agree) |
| pt0_ax2_r800_s2 | 14.0 | 13.23 | 53.0 | 53.2 | 405 | PASS | agree (+0.2) | PASS | 14.0 / 51.0 / 378 (PASS, agree) |
| pt0_ax3_r400_s1 | n/a | 27.99 | 66.3 | 65.7 | 267 | PASS | agree (-0.6) | PASS | n/a / 70.4 / 262 (PASS, agree) |
| pt0_ax3_r400_s2 | n/a | 28.03 | 68.2 | 68.5 | 283 | PASS | agree (+0.3) | PASS | n/a / 68.7 / 271 (PASS, agree) |
| pt0_ax3_r800_s1 | n/a | 28.03 | 67.2 | 67.4 | 263 | PASS | agree (+0.2) | PASS | n/a / 71.7 / 313 (PASS, agree) |
| pt0_ax3_r800_s2 | n/a | 28.03 | 65.4 | 66.1 | 246 | PASS | agree (+0.7) | PASS | n/a / 65.5 / 246 (first hole FAIL, re-flown PASS) |
| pt1_ax1_r400_s1 | 13.8 | 13.27 | 52.5 | 52.6 | 470 | PASS | agree (+0.1) | PASS | 14.1 / 58.9 / 491 (PASS, agree) |
| pt1_ax1_r400_s2 | 14.0 | 13.44 | 57.5 | 57.4 | 464 | PASS | agree (-0.1) | PASS | 13.9 / 57.6 / 512 (first hole FAIL, re-flown PASS) |
| pt1_ax1_r800_s1 | 14.4 | n/a | 71.3 | 67.8 | 591 | PASS | BLOCKED (dPM -3.48) | PASS on margins only (not clean) | 14.5 / 53.2 / 452 (PASS, agree) |
| pt1_ax1_r800_s2 | 14.3 | n/a | 55.7 | 55.9 | 490 | PASS | agree (+0.2) | PASS | 14.5 / 55.3 / 475 (PASS, agree) |
| pt1_ax2_r400_s1 | 13.9 | 13.20 | 54.1 | 54.2 | 476 | PASS | agree (+0.1) | PASS | 13.8 / 54.2 / 483 (PASS, agree) |
| pt1_ax2_r400_s2 | 13.8 | n/a | 59.6 | 58.9 | 542 | **FAIL** | agree (-0.7) | PASS on margins only (not clean) | 13.9 / 60.5 / 534 (PASS, agree) |
| pt1_ax2_r800_s1 | 14.6 | n/a | 56.9 | 56.2 | 483 | PASS | agree (-0.6) | PASS | 14.4 / 56.6 / 465 (PASS, agree) |
| pt1_ax2_r800_s2 | 14.3 | n/a | 52.9 | 54.9 | 461 | PASS | agree (+2.0) | PASS | 14.5 / 62.5 / 558 (PASS, agree) |
| pt1_ax3_r400_s1 | n/a | n/a | 64.5 | 63.3 | 288 | PASS | agree (-1.2) | PASS | n/a / 63.9 / 273 (key2 BLOCKED, S184) |
| pt1_ax3_r400_s2 | n/a (key2 GM 16.3) | n/a | 58.7 | 58.2 | 243 | PASS | BLOCKED (GM present in key2 only) | PASS on margins only (not clean) | n/a / 64.5 / 272 (key2 BLOCKED, S184) |
| pt1_ax3_r800_s1 | n/a | n/a | 59.3 | 58.9 | 229 | PASS | agree (-0.4) | PASS | n/a / 63.1 / 256 (holes FAIL and key2 BLOCKED, S184 FAIL) |
| pt1_ax3_r800_s2 | 22.4 (key2 17.8) | n/a | 66.2 | 64.7 | 287 | PASS | BLOCKED (dGM -4.6) | PASS on margins only (not clean) | n/a / 65.4 / 263 (PASS, agree) |

Hole-report FAIL, the one cell: pt1_ax2_r400_s2. Its only FAIL row is vehicle_local_position_setpoint (controller class), max gap 22.50 ms and excess 11.25 ms (limit 10 ms), missing 0 %. Other classes are within limits.

Totals (24 outer cells):
- Margins: PM >= 45 24/24 (min 49.1 deg, pt0_ax2_r400_s2); GM >= 6 or n/a 24/24; DM 24/24 (min 229 ms, pt1_ax3_r800_s1; not binding).
- Clean (holes PASS and key2 agree): 20/24. Per group: ax1 7/8 (BLOCKED: pt1_ax1_r800_s1), ax2 7/8 (hole FAIL: pt1_ax2_r400_s2), ax3 6/8 (BLOCKED: pt1_ax3_r400_s2, pt1_ax3_r800_s2). Margins only (not clean): 4 cells, disjoint.
- Holes PASS 23/24 (FAIL: pt1_ax2_r400_s2). Key2 agree 21/24 (BLOCKED: pt1_ax1_r800_s1, pt1_ax3_r400_s2, pt1_ax3_r800_s2).
- Worst xy PM 49.1 deg (pt0_ax2_r400_s2; freeze-9 min 48.5). Worst xy GM 13.5 dB (pt0_ax1_r400_s1; freeze-9 min 13.4). Lowest plateau GM 12.88 dB (pt0_ax2_r400_s1). Worst ax3 PM 58.7 deg (pt1_ax3_r400_s2, primary; freeze-9 min 59.9). Worst DM 229 ms (pt1_ax3_r800_s1; freeze-9 min 231 ms).
- Freeze-9 final after S184: clean 21/24 (holes FAIL pt1_ax3_r800_s1; key2 BLOCKED pt1_ax3_r400_s1, pt1_ax3_r400_s2, pt1_ax3_r800_s1).

## G2 spot-check cells

Scored as freeze-9: rate cell from the queue's `m3a_margins_pretest.py` output (read, not re-run); attitude cell from `ratesp_csv.py --margins` json and `attitude_break_check.py`. No second key on the spot cells (as freeze-9).

| cell | GM dB | PM deg | DM ms | limit | holes (OVERALL) | verdict | freeze-9 GM / PM / DM (holes) |
|---|---|---|---|---|---|---|---|
| roll800_fwdef_s2 (rate) | 15.7 | 46.9 | 75.5 | GM>=6, PM>=45, DM>=2 periods | PASS | PASS (PM +1.9 deg) | 15.9 / 47.1 / 76.1 (FAIL, single row vehicle_local_position_setpoint count-disagree) |
| ax2_r400_s1 (pitch att) | 13.7 at 4.29 Hz; see note | 48.0 | 93.5 | GM>=6, PM>=45, DM>=2 periods | PASS | PASS (check RESULT PASS; see note on GM) | 13.2 / 47.4 / 91.5 (PASS) |

Note on ax2_r400_s1 GM: the scorer's `gm_db` field is the minimum over phase crossings and reads -17.31 dB. Two -180 crossings exist: 4.29 Hz with GM +13.7 dB (|L| < 1, the plateau-type margin), and a new low-frequency crossing at 0.237 Hz with |L| = +7.3 (20log10|L| = +17.3 dB). Freeze-9 had only the 4.29 Hz crossing. Under Q13 A the 0.237 Hz bin is a gain-reduction margin of 17.3 dB, which is >= 6 dB, so the cell passes with GM 13.7 dB. Read literally as the scorer's signed minimum, it is -17.3 dB and FAILS. The owner should confirm this reading before the cell counts. Its `_margins.err` is 0 bytes.

Total: 2/2 meet the margin limits on the Q13 A reading. Read literally (signed minimum over crossings), ax2_r400_s1 shows -17.3 dB and would FAIL, so the owner must rule on it. Rate cell hole check PASS (freeze-9 FAIL), so it is clean; att cell hole check PASS.

## G2-STEP (inner-loop attitude step), 3 seeds x roll/pitch/yaw

Pass per seed: roll/pitch overshoot <= 5 %, 2 % settle <= 450 ms; yaw overshoot <= 5 %, settle <= 1350 ms. Truth columns are reported, not a pass condition.

| seed | axis | est rise (ms) | freeze-9 rise | OS est / truth (%) | settle est (ms) | freeze-9 settle | truth settle (ms, not a pass condition) | verdict | key2 (rise / OS / settle) |
|---|---|---|---|---|---|---|---|---|---|
| 1 | roll | 189.40 | 189.1 | 0.41 / 0.45 | 345.00 | 345.0 | 341.25 | PASS | 191.2 / 0.41 / 345.0 |
| 1 | pitch | 190.61 | 189.3 | 0.65 / 0.55 | 333.75 | 333.8 | 1980.00 | PASS | 191.2 / 0.65 / 333.8 |
| 1 | yaw | 628.29 | 621.4 | 0.03 / 0.00 | 1170.00 | 1150.0 | 1766.25 | PASS | 626.2 / 0.03 / 1170.0 |
| 2 | roll | 190.60 | 188.6 | 0.44 / 0.36 | 333.75 | 331.3 | 330.00 | PASS | 191.2 / 0.44 / 333.8 |
| 2 | pitch | 187.45 | 189.7 | 0.52 / 0.31 | 347.50 | 330.0 | 2713.75 | PASS | 187.5 / 0.52 / 347.5 |
| 2 | yaw | 626.83 | 622.4 | 0.17 / 0.00 | 1176.25 | 1177.5 | 3692.50 | PASS | 626.2 / 0.17 / 1176.2 |
| 3 | roll | 187.42 | 188.1 | 0.65 / 0.10 | 341.25 | 345.0 | 2898.75 | PASS | 187.5 / 0.65 / 341.2 |
| 3 | pitch | 187.29 | 190.5 | 0.40 / 0.38 | 342.50 | 333.8 | 342.50 | PASS | 187.5 / 0.40 / 342.5 |
| 3 | yaw | 627.01 | 620.9 | 0.03 / 0.00 | 1196.25 | 1180.0 | NaN | PASS | 626.2 / 0.03 / 1196.2 |

Count: 9/9 PASS (script pass True on all). Key2 agrees on every overshoot and settle; rise within 2.1 ms. Worst roll/pitch settle 347.5 ms (pitch s2, limit 450); worst roll/pitch overshoot 0.65 % (roll s3, pitch s1; limit 5). Worst yaw settle 1196.25 ms (s3, 89 % of 1350; freeze-9 max 1180.0). Yaw overshoot <= 0.17 %.

## Integrity

- Hole-report FAIL (needs a re-fly by hand, not re-flown here): g2o pt1_ax2_r400_s2 (controller class, excess 11.25 ms > 10 ms).
- Non-empty `*_margins.err` with errors: none. All 24 outer `_margins.err` files are 0 bytes; the spot `ax2_r400_s1_margins.err` is 0 bytes.
- Missing outputs: none. 24/24 outer cells have flight.ulg, `_margins.json`, `_pinj.csv`, `_holes.txt`, `_margins.err`; spot rate `margins.txt`, `holes.txt`; spot att `_margins.json`, `_check.txt`, `_holes.txt`; 9/9 G2-STEP flights and key2 files. The queue's log has no non-zero rc.
- Blocked key2 cells (margins PASS, not clean): pt1_ax1_r800_s1, pt1_ax3_r400_s2, pt1_ax3_r800_s2 (not re-flown; owner decision).

## Commands run

Host python3 from repo root, `S` = scratchpad (no containers):
- `sed 's#g2_outer_freeze_s163#freeze10_s193/g2o#' indi_flight/bench/g2_freeze_table_s163.py > $S/tab10.py; python3 $S/tab10.py > indi_flight/results/freeze10_s193/g2o/table_out.txt` (rc 0; the rate section it prints refers to an old folder and is not scored)
- `sed -e 's#g2_outer_freeze_s163#freeze10_s193/g2o#' -e "s#^HERE = .*#HERE = '$PWD/indi_flight/bench'#" indi_flight/bench/g2_key2_outer_s164.py > $S/key2_10.py; python3 $S/key2_10.py > indi_flight/results/freeze10_s193/g2o/key2_run_stdout.txt` (rc 0, self-test PASS; wrote g2o/key2.md)
- G2-STEP, cwd freeze10_s193: `python3 indi_flight/bench/g2_step_metrics.py steps/g2_step_primary.json steps/seed{1,2,3}/step_{roll,pitch,yaw}_indi > steps/step_out.txt` (rc 0)
- G2-STEP second key, cwd freeze10_s193: `python3 indi_flight/bench/t127_step_metrics_key.py steps/seed<N>/step_<axis>_indi steps/key2_seed<N>_<axis>.md` (rc 0 x9)
- Spot cells and outer margins/holes: read from queue output, not re-run.

# Re-score S194 (current g2o after the pt1_ax2_r400_s2 re-fly)

Hole re-fly: g2o `pt1_ax2_r400_s2` had the one hole FAIL (controller class, vehicle_local_position_setpoint, max gap 22.50 ms, excess 11.25 ms). Its files were moved (mv, not rm) to `g2o/orig_s194/`. Then `bash indi_flight/results/freeze10_s193/queue.sh 4` ran once. Every other step-4 done-file was present, so only this cell flew (queue_status.tsv `g2o_pt1_ax2_r400_s2` 01:19:14 to 01:20:29, rc 0; queue.log STEP4 01:19:14, QUEUE_END 01:20:29). Docker via `indi_project/docker/run.sh` with `-t 1200` for the flight and `-t 240` for the margins and hole report. Queue stdout is in `g2o/refly_s194_stdout.txt`.

Commands (repo root, host python3, no containers for scoring; `S` = scratchpad, outputs not kept there):
- `sed 's#g2_outer_freeze_s163#freeze10_s193/g2o#' indi_flight/bench/g2_freeze_table_s163.py > $S/tab10_s194.py; python3 $S/tab10_s194.py > $S/table_out_s194.txt` (rc 0). Output went to scratch, so `g2o/table_out.txt` is unchanged. Diff against the S193 table: only the pt1_ax2_r400_s2 row changes.
- `sed -e 's#g2_outer_freeze_s163#freeze10_s193/g2o#' -e "s#^HERE = .*#HERE = '$PWD/indi_flight/bench'#" indi_flight/bench/g2_key2_outer_s164.py > $S/key2_10_s194.py; python3 $S/key2_10_s194.py > $S/key2_run_stdout_s194.txt` (rc 0, self-test PASS, rewrote `g2o/key2.md`). Diff against the S193 key2.md: only the pt1_ax2_r400_s2 rows change.

Hole cell, before and after (primary margins from `*_margins.json`, holes from `*_holes.txt`):

| run | GM dB | PM deg | DM s | key2 PM / dPM deg | key2 GM dB | sim missing % (holes, max ms) | controller missing % (holes, max ms) | hole OVERALL |
|---|---|---|---|---|---|---|---|---|
| S193 original (`g2o/orig_s194/`) | 13.83 | 59.59 | 0.542 | 58.94 / -0.65 | 13.97 | 0.0126 (10, 5.00) | 0.0000 (0, 22.50 FAIL, excess 11.25 > 10) | FAIL |
| S194 re-fly (`g2o/`) | 13.90 | 56.86 | 0.485 | 57.76 / +0.89 | 14.02 | 0.0050 (4, 5.00) | 0.0000 (0, 0.00) | PASS |

The original's failing row had 0 missing samples, so the failure was a single long gap (22.50 ms against a 10 ms excess limit), not a missing-sample fraction. The re-fly is clean on all classes. Both runs pass the margin limits by a wide margin (PM 56.9 deg vs 45; GM 13.9 dB vs 6; DM 0.485 s, not binding), and key2 agrees on both (|dPM| <= 3 deg, |dGM| <= 1 dB).

Blocked key-2 cells (margins from both keys, all values from the S194 scorer run, DM in ms in the table):

| cell | key1 PM deg | key1 GM dB | key1 DM ms | key2 PM deg | key2 GM dB | key2 DM ms | dPM / dGM | key1 limits (PM>=45, GM>=6 or n/a) | key2 limits | both keys pass? | reason blocked |
|---|---|---|---|---|---|---|---|---|---|---|---|
| pt1_ax1_r800_s1 | 71.28 | 14.40 | 590.5 | 67.81 | 14.51 | 562.9 | -3.48 / +0.11 | PASS | PASS | yes | dPM beyond 3 deg |
| pt1_ax3_r400_s2 | 58.70 | n/a (no -180 crossing) | 243.0 | 58.15 | 16.28 | 255.5 | -0.55 / GM in key2 only | PASS (no GM limit) | PASS | yes | GM present in key2 only |
| pt1_ax3_r800_s2 | 66.17 | 22.37 | 287.1 | 64.72 | 17.80 | 284.9 | -1.45 / -4.57 | PASS | PASS | yes | dGM beyond 1 dB |

All three cells pass both keys' margin limits (PM >= 45 deg, GM >= 6 dB where a GM exists, DM not binding at >= 0.24 s). They stay BLOCKED on key agreement only, which is an owner decision (not re-flown).

Totals after S194 (24 outer cells):
- Holes PASS 24/24 (was 23/24; no hole FAIL left). Key2 agree 21/24, BLOCKED pt1_ax1_r800_s1, pt1_ax3_r400_s2, pt1_ax3_r800_s2 (unchanged).
- Clean (holes PASS and key2 agree): 21/24 (was 20/24). Per group: ax1 7/8, ax2 8/8, ax3 6/8. Margins only (not clean): 3 cells, the three BLOCKED ones.
- Margins: PM >= 45 24/24, GM >= 6 or n/a 24/24, DM 24/24. Min xy PM still 49.1 deg (pt0_ax2_r400_s2); min DM still 229 ms (pt1_ax3_r800_s1). The pt1_ax2_r400_s2 row in the S193 table above, and the Integrity bullet naming it as a hole FAIL, are superseded by this section; the S193 text is left as written.

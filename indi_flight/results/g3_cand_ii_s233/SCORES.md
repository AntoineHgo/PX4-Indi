# G3 candidate (ii) (per-motor map correction, MC_INDI_MAP_TC 0.2, MAP_LIM 0.5, ACT_BLD 1.0) pass-line scores, S233

Scored 2026-11-26 by `score.sh` (same as cand (i): g3_score.sh key 1, g3_checks_key2.py key 2, host python /tmp/g3venv, no scorer edits). Raw: raw_key1_<draw>.txt/.json, raw_key2_<draw>.txt, key2_<draw>/. Pass line: DECISIONS.md D-RATE-BLD-2 "S226 ACTIVE". Binary: /tmp/px4_cand_ii/build/px4_sitl_default/bin/px4 (commit 43547406d3e), sha256 d5ca23f5f4ff69f741d353d779eeb508670ed249c048e60e7c1d21ce10ff8d1c; params cand_ii.params (== g5_freeze_s157), draws and seeds as in g3_cand_i_s231/README.md; one flight each, --speed 1. Baselines as in g3_cand_i_s231/SCORES.md (joint and 264 FREEZE-10: LOC; 262, 283: s230 indi_d262 / indi_d283).

## joint -- baseline LOC
| item | key 1 | key 2 | baseline |
|---|---|---|---|
| 1 | FAIL: LOC, flight aborted by watchdog (tilt > 60 deg for 0.5 s, 113 deg at sim t=60.13); scorer INVALID | same (INVALID) | LOC |
| 2, 3 | not scorable (aborted) = fail | same | n/a |
Cand (i) passed this draw (tilt 43.95 deg). Cand (ii) is a regression here.

## 264 -- baseline LOC
| item | key 1 | key 2 | baseline |
|---|---|---|---|
| 1 | FAIL: LOC, watchdog abort (tilt > 60 deg, 108 deg at sim t=60.26); scorer INVALID | same (INVALID) | LOC |
| 2, 3 | not scorable = fail | same | n/a |
Cand (i) did not LOC (tilt 54.29, exc 5.347 m).

## 262 -- baseline s230 indi_d262 (no ACT_TC draw)
| item | key 1 | key 2 | baseline (K1 / K2) |
|---|---|---|---|
| 1 | PASS: tilt 47.69, drop 0.003, exc 1.683 m | PASS: same, drop 0.040 | PASS 45.98 deg, exc 1.826 |
| 2 | PASS: p/q/r no sustained line (rms at max ratio 2.09/2.05/0.54 dps) | PASS: none sustained, max rms 2.15/2.62/1.07 dps | PASS (q 1.93 / 5.31) |
| 3 | PASS: rms 0.082 m, alt 0.043 m | PASS: same | PASS 0.040 / -0.070 |
| 4 (rep.) | horiz 0.952 (>0.5), vert 0.115 | same | 0.988 / 0.067 |
| 5 (rep.) | fault@44.74: max pos err 1.215 m, FAIL; gust 0.195 m pass | fault: 1.215 m, att 10.72 deg; gust pass | fault 1.305 m |
FLIGHT CELL PASS (items 1-3, both keys).

## 283 -- baseline s230 indi_d283 (same draw)
| item | key 1 | key 2 | baseline (K1 / K2) |
|---|---|---|---|
| 1 | PASS: tilt 43.65, drop 0.060, exc 0.751 m | PASS: same, drop 0.089 | PASS 43.56, exc 0.770 |
| 2 | FAIL: q sustained (rms at max ratio 5.88 dps, 14 flagged windows; p 3.12, r 2.50 not) | FAIL: q sustained at 48.0 s, max rms p/q/r 3.08/7.30/2.84 dps | FAIL, q sustained: K1 5.95; K2 2.86/7.77/2.91 |
| 3 | PASS: rms 0.045 m, alt -0.078 m | PASS: same | PASS 0.030 / 0.032 |
| 4 (rep.) | horiz 0.461, vert 0.056: pass | same | 0.485 / 0.095 |
| 5 (rep.) | gust 0.072 m: pass | gust 0.075 m, att 1.66 deg | gust 0.074 m |
Item 2 "not worse" than baseline on the q metric: K1 5.88 <= 5.95, K2 7.30 <= 7.77. K2 p 3.08 vs 2.86 is slightly higher, as in cand (i) (the "not worse" metric is not defined further in the pass line). Treated as not worse on q = baseline-failing cell, reported as G3 risk.

## Verdict (D-RATE-BLD-2 S226 ACTIVE): MISSED
Failing items: joint item 1 (LOC, flight aborted) and 264 item 1 (LOC, flight aborted), both keys; items 2-3 of those two are unscorable. 262 passes, 283 not worse than baseline. Any missed cell = candidate fails. Next per the solver brief: candidate (iii).

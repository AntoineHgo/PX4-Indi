# G3 candidate (i) (MC_INDI_ACT_BLD 0.10) pass-line scores, S231

Scored 2026-11-26 by `score.sh` (host python /tmp/g3venv, no scorer edits). Raw: raw_key1_<draw>.txt/.json, raw_key2_<draw>.txt, key2_<draw>/run_NNN.json. Pass line: DECISIONS.md D-RATE-BLD-2 "S226 ACTIVE": item 1 pass; item 2 pass (S225 fault-window rule, applied by key 2; key 1 skipped-window list carries the same rule); item 3 pass on the S214 window; both keys. For 262/283 a cell the FREEZE-10 baseline already fails is judged "not worse" (same key metric <= baseline). Items 4-5 reported only. Item 6 n/a (not rate mode) on all draws. Limits as coded in the keys (item 1: tilt>60 deg for >0.2 s, drop>2 m, NaN, ground contact, horizontal excursion > 5.0 m; item 3 rms limit 0.15 m (joint, no wind) or 0.3 m (wind), |alt| <= 0.2 m).

Baselines: joint and 264 FREEZE-10 (tb 1.0) = LOC, no key scores (falsifier_s222 README: joint tilt 86.7 deg; g3_refly_actc_s212 run_024 aborted by flight watchdog, tilt>60 deg, SCORES.tsv INVALID; different scenario, older, not event hover). No blend264_s223 folder exists. 262 and 283 baselines: g3_pretest_s230 indi_d262 (NOTE: flown without the ACT_TC draw, so not the same plant as the pass-line 262) and indi_d283 (same draw).

## joint (restore264 joint plant, fault only, no wind) -- baseline: LOC (tilt 86.7 deg)

| item | key 1 | key 2 | baseline |
|---|---|---|---|
| 1 | PASS: tilt max 43.95 deg, drop 0.047 m, exc 1.231 m | PASS: tilt 43.95, drop 0.042, exc 1.231 | LOC |
| 2 | PASS: p/q/r no sustained line (rms at max ratio 2.29/2.16/2.27 dps), position none | PASS: none sustained, max rms p/q/r 3.04/4.47/2.35 dps | n/a |
| 3 | PASS: rms 0.0646 m (<=0.15), alt -0.040 m | PASS: same | n/a |
| 4 (rep.) | horiz 0.484 (<=0.5), vert 0.062 m: pass | same | n/a |
| 5 (rep.) | fault@44.81: max pos err 1.837 m, recovery 0.0005 s, re-excursion; FAIL | fault@58.687: max pos 1.837 m, max att 18.83 deg; FAIL | n/a |
| 6 | n/a | n/a | |

FLIGHT CELLS PASS (items 1-3, both keys). Item 5 fails both keys (reported only). G4 chatter sustained True (not G3).

## 264 (C212 run_024, wind + sag, fault + gust) -- baseline: LOC

| item | key 1 | key 2 | baseline |
|---|---|---|---|
| 1 | FAIL: tilt max 54.29 deg (no >60 deg), drop 0.021 m, exc 5.347 m (> 5.0) | FAIL: tilt 54.29, drop 0.110, exc 5.347 | LOC |
| 2 | FAIL: p/q/r all sustained (rms at max ratio 33.5/21.9/24.1 dps; 10/11/4 flagged windows) | FAIL: p/q/r sustained, max rms 36.25/26.51/25.91 dps | n/a |
| 3 | PASS: rms 0.0475 m, alt 0.057 m | PASS: same | n/a |
| 4 (rep.) | horiz 2.840 (>0.5), vert 0.271 | same | n/a |
| 5 (rep.) | fault: max pos err 1.772 m, FAIL; gust: 0.085 m, pass | fault: pos 1.772 m, att 20.73 deg; gust: pos 0.085 m, att 4.43 deg | n/a |

FLIGHT CELLS MISS: item 1 excursion 5.347 m vs 5.0 m (both keys); item 2 p, q, r sustained (both keys, no limit exceeded numerically, any sustained line fails).

## 262 (C212 run_022, wind + sag, fault + gust) -- baseline s230 indi_d262 (no ACT_TC draw)

| item | key 1 | key 2 | baseline (K1 / K2) |
|---|---|---|---|
| 1 | PASS: tilt 46.55, drop 0.057, exc 2.098 m | PASS: same, drop 0.041 | PASS 45.98 deg, exc 1.826 |
| 2 | FAIL: q sustained (rms at max ratio 7.06 dps, 8 flagged windows; p 2.19, r 3.45 not) | FAIL: q sustained from 51 s, max rms q 14.88 dps (p 5.95, r 3.93) | PASS (K1 q 1.93 dps, 1 window; K2 max rms q 5.31) |
| 3 | PASS: rms 0.040 m, alt -0.023 m | PASS: same | PASS 0.040 / -0.070 |
| 4 (rep.) | horiz 1.119, vert 0.062 | same | 0.988 / 0.067 |
| 5 (rep.) | fault: pos 1.263 m FAIL; gust: 0.172 m pass | fault: pos 1.263 m, att 10.89 deg; gust: pos 0.172 m, att 9.40 deg | fault 1.305 m, 11.96 deg; gust 0.279 m, 8.78 deg |

FLIGHT CELLS MISS: item 2 q sustained, both keys; baseline item 2 passes on both keys, so no "not worse" relief (q max rms 14.88 vs 5.31 dps on K2, 7.06 vs 1.93 on K1).

## 283 (plain draw, wind only, gust + tel loss/frozen) -- baseline s230 indi_d283 (same draw)

| item | key 1 | key 2 | baseline (K1 / K2) |
|---|---|---|---|
| 1 | PASS: tilt 43.53, drop 0.000, exc 0.793 m | PASS: same, drop 0.028 | PASS 43.56, exc 0.770 |
| 2 | FAIL: q sustained (rms at max ratio 6.54 dps, 14 windows; max flagged 7.66; p 2.05, r 3.02 not) | FAIL: q sustained, max rms p/q/r 3.20/7.54/3.04 dps | FAIL, q sustained: K1 5.95 (max flagged 7.29); K2 2.86/7.77/2.91 |
| 3 | PASS: rms 0.0283 m, alt -0.006 m | PASS: same | PASS 0.030 / 0.032 |
| 4 (rep.) | horiz 0.469, vert 0.059: pass | same | 0.485 / 0.095 |
| 5 (rep.) | gust: pos 0.098 m, pass | gust: pos 0.098 m, att 1.63 deg; tel_loss 0.107 m, 1.63 deg (not gated); tel_frozen 0.107 m, 1.63 deg (not gated) | gust 0.074 m, 1.72 deg |

Item 2 "not worse" than baseline: key 1 WORSE (q rms at max ratio 6.54 vs 5.95; max flagged 7.66 vs 7.29; flagged windows equal at 14); key 2 q max rms 7.54 <= 7.77 (not worse on q) but p 3.20 vs 2.86 and r 3.04 vs 2.91 slightly higher. The metric for "not worse" is not defined further in the pass line; read per key on the q axis that fails, key 1 MISS, key 2 met. Keys disagree on this cell (single-flight noise is not characterised).

FLIGHT CELLS MISS (key 1): item 2 q, 6.54 vs baseline 5.95 dps (key 2: 7.54 vs 7.77, not worse). Keys disagree.

## Max tilt on joint and 264 (LOC check)
- joint: 43.95 deg (both keys), no LOC (no >60 deg).
- 264: 54.29 deg (both keys), no LOC by the >60 deg rule, but item 1 fails on excursion 5.347 m > 5.0 m. Both baselines were LOC.

## Summary
| draw | verdict | keys agree |
|---|---|---|
| joint | FLIGHT CELLS PASS | yes |
| 264 | MISS (item 1 excursion, item 2 p/q/r) | yes |
| 262 | MISS (item 2 q) | yes |
| 283 | MISS on key 1 (item 2 q 6.54 vs 5.95), key 2 not worse | no |

Candidate (i) fails the pass line (any missed cell = candidate fails). Item 5 (Q34 open) is reported above per event with raw max position and tilt error, no verdict given here. Unverified: item 2 skip windows were taken as printed by the keys; the 262 baseline lacks the ACT_TC draw; baselines for joint/264 are older-scenario LOC flights, not event hover.

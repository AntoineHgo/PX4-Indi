# G3 candidate (iii) pass-line scores, S236

Scored 2026-11-26 by `score.sh` (g3_score.sh key 1, g3_checks_key2.py key 2, host python /tmp/g3venv, no scorer edits). Raw: raw_key1_<draw>.txt/.json, raw_key2_<draw>.txt, key2_<draw>/. Pass line: DECISIONS.md D-RATE-BLD-2 "S226 ACTIVE". Binary /tmp/px4_cand_iii (params cand_iii.params). Sanity: all four flights ran the full scenario (chain.out exit=0, run.json outcome ok, validity valid, ~2.7 min each; cand (ii) joint and 264 had aborted by watchdog). One flight per draw. Baselines and cand (ii) values as in g3_cand_ii_s233/SCORES.md. Item 5 is blocked by Q34 (raw values only, no reading).

## Cells (K1 / K2 = key 1 / key 2)
| draw | item | cand (iii) K1 | cand (iii) K2 | agree | pass | cand (ii) K1 / K2 | baseline |
|---|---|---|---|---|---|---|---|
| joint | 1 LOC | tilt 44.66, drop 0.042, exc 1.386 m | same tilt, drop 0.081, exc 1.386 | yes | PASS | LOC abort (113 deg) / same | LOC |
| joint | 2 | no sustained p/q/r (rms 2.07/1.37/6.31 dps) | none (max rms 6.32/4.80/5.72) | yes | PASS | unscorable | n/a |
| joint | 3 | rms 0.028 m, alt 0.061 | same | yes | PASS | unscorable | n/a |
| joint | 4 (rep.) | 0.475 / 0.129 | same | yes | n/a | n/a | n/a |
| joint | 5 raw | fault@44.82 pos 2.012 m: blocked by Q34 | pos 2.012 m, att 30.9 deg: blocked by Q34 | | not scored | n/a | n/a |
| 264 | 1 LOC | FAIL: tilt 66.89 (>60 deg for 0.165 s), drop 0.033, exc 6.069 m; no watchdog abort | FAIL: same tilt, drop 0.519, exc 6.069 | yes | FAIL | LOC abort (108 deg) / same | LOC |
| 264 | 2 | FAIL: p/q/r sustained (rms 58.4/16.1/43.0 dps) | FAIL: sustained (61.4/34.0/44.2) | yes | FAIL | unscorable | n/a |
| 264 | 3 | rms 0.053 m, alt 0.061 | same | yes | PASS | unscorable | n/a |
| 264 | 4 (rep.) | 2.938 / 0.441 | same | yes | n/a | n/a | n/a |
| 264 | 5 raw | fault@44.79 pos 2.148 m; gust 0.122 m: blocked by Q34 | fault 2.148 m, att 28.5 deg; gust 0.132 m: blocked by Q34 | | not scored | n/a | n/a |
| 262 | 1 LOC | PASS: tilt 47.21, drop 0.057, exc 2.032 m | PASS: drop 0.072 | yes | PASS | PASS 47.69 / exc 1.683 | PASS 45.98 / 1.826 |
| 262 | 2 | FAIL: q sustained (rms 7.55 dps; p 2.28, r 3.47 not) | FAIL: q sustained (9.89; p 5.12, r 4.21 not) | yes | FAIL (baseline PASS, so not-worse rule gives no cover) | PASS (q 2.09 / 2.62) | PASS (q 1.93 / 5.31) |
| 262 | 3 | rms 0.032 m, alt 0.003 | same | yes | PASS | PASS 0.082 / 0.043 | PASS 0.040 / -0.070 |
| 262 | 4 (rep.) | 1.108 / 0.141 | same | yes | n/a | 0.952 / 0.115 | 0.988 / 0.067 |
| 262 | 5 raw | fault@44.77 pos 1.329 m; gust 0.147 m: blocked by Q34 | fault 1.329 m, att 14.5 deg; gust 0.147 m, att 11.7 deg: blocked by Q34 | | not scored | fault 1.215 m | fault 1.305 m |
| 283 | 1 LOC | PASS: tilt 43.24, drop 0.0, exc 0.743 m | PASS: drop 0.054 | yes | PASS | PASS 43.65 / 0.751 | PASS 43.56 / 0.770 |
| 283 | 2 | FAIL: q sustained (rms 5.82; p 2.22, r 2.66 not) | FAIL: q sustained (7.14; p 3.03, r 2.75 not) | yes | FAIL on its own; baseline also fails: q K1 5.82 <= 5.95, K2 7.14 <= 7.77 so NOT WORSE, G3 risk | FAIL q 5.88 / 7.30 (not worse) | FAIL q 5.95 / 7.77 |
| 283 | 3 | rms 0.025 m, alt -0.017 | same | yes | PASS | PASS 0.045 / -0.078 | PASS 0.030 / 0.032 |
| 283 | 4 (rep.) | 0.473 / 0.080 | same | yes | n/a | 0.461 / 0.056 | 0.485 / 0.095 |
| 283 | 5 raw | gust 0.062 m: blocked by Q34 | gust 0.081 m; tel_loss/frozen 0.089 m: blocked by Q34 | | not scored | gust 0.072 m | 0.074 m |

Other (not on the pass line): key 2 command chatter (G4) sustained at ~88 Hz on joint, 264, 262; passes on 283. Not scored here.

## Verdict (D-RATE-BLD-2 S226 ACTIVE): (iii) MISSES the pass line
LOC cells: joint no LOC (cand (ii) LOC fixed); 262 no LOC; 283 no LOC; 264 FAILS item 1 (tilt 66.9 deg, 0.165 s above 60, exc 6.07 m; flight not aborted) and item 2 (sustained p/q/r oscillation), both keys. 262 item 2 (q sustained) is a new failure vs a passing baseline, both keys. 283 item 2 not worse than baseline (reported G3 risk). Items failing per key (identical on both): 264 items 1, 2; 262 item 2; 283 item 2 (not worse, covered). Keys agree on every pass/fail. Any missed cell = candidate fails. Per the pass line: none of (i)-(iii) passes -> route B (GATES "Owner amendment S225"). Item 5 not scored (Q34 open).

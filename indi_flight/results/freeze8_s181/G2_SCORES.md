# G2 outer loops at freeze-8 (S181 cells), scores

Commands (repo root; keyed scripts run on copies in the scratchpad, only the results path g2_outer_freeze_s163 replaced by freeze8_s181/g2o; key2 copy also has HERE hard-set to the repo bench dir):
`sed 's#g2_outer_freeze_s163#freeze8_s181/g2o#' indi_flight/bench/g2_freeze_table_s163.py > $S/tab8.py; python3 $S/tab8.py` (primary table, outer part)
`sed -e 's#g2_outer_freeze_s163#freeze8_s181/g2o#' -e "s#^HERE = .*#HERE = '$PWD/indi_flight/bench'#" indi_flight/bench/g2_key2_outer_s164.py > $S/key2_8.py; python3 $S/key2_8.py` (second key, wrote freeze8_s181/g2o/key2.md)
Hole check: `grep OVERALL g2o/*_holes.txt`. Limits as freeze-7: PM >= 45 deg, GM >= 6 dB (GM n/a = no -180 crossing in 0.2-8 Hz band; plateau GM = key2 phase-plateau gain margin, n/a = none), DM >= 2 control periods + latency (never binding, all DM 240-352 ms).
Key2 agreement tolerance (as freeze-7, from g2_key2_outer_s164.py): |dPM| <= 3 deg and |dGM| <= 1 dB, plus same presence/absence of a GM; otherwise BLOCKED. Bins column = key2 kept/excited bins (coherence >= 0.8), not the primary's own count.
Note: the table script prints margins PASS = FAIL for ax3 cells because gm is NaN there; verdicts below treat GM n/a as no limit (as freeze-7).

| cell | GM dB | plateau GM dB (key2) | PM deg | DM | limit | verdict | notes |
|---|---|---|---|---|---|---|---|
| pt0_ax1_r400_s1 | 10.9 | 11.0 | 54.6 | 271 ms | PM>=45, GM>=6 | PASS | holes PASS; kept/exc bins (key2) 16/17; key2 agree |
| pt0_ax1_r400_s2 | 10.8 | 10.9 | 52.8 | 263 ms | PM>=45, GM>=6 | PASS | holes PASS; kept/exc bins (key2) 17/17; key2 agree |
| pt0_ax1_r800_s1 | 11.2 | 11.2 | 53.9 | 292 ms | PM>=45, GM>=6 | PASS | holes PASS; kept/exc bins (key2) 17/17; key2 agree |
| pt0_ax1_r800_s2 | 11.3 | 11.3 | 54.1 | 286 ms | PM>=45, GM>=6 | PASS | holes PASS; kept/exc bins (key2) 17/17; key2 agree |
| pt0_ax2_r400_s1 | 10.8 | 10.9 | 51.4 | 268 ms | PM>=45, GM>=6 | PASS | holes PASS; kept/exc bins (key2) 17/17; key2 agree |
| pt0_ax2_r400_s2 | 10.9 | 10.9 | 55.3 | 286 ms | PM>=45, GM>=6 | PASS | holes PASS; kept/exc bins (key2) 17/17; key2 agree |
| pt0_ax2_r800_s1 | 11.0 | 11.1 | 49.9 | 266 ms | PM>=45, GM>=6 | PASS | holes PASS; kept/exc bins (key2) 17/17; key2 agree |
| pt0_ax2_r800_s2 | 11.2 | 11.2 | 50.0 | 271 ms | PM>=45, GM>=6 | PASS | holes PASS; kept/exc bins (key2) 17/17; key2 agree |
| pt0_ax3_r400_s1 | n/a | 28.2 | 67.5 | 276 ms | PM>=45, GM>=6 | PASS | holes PASS; kept/exc bins (key2) 15/16; key2 agree |
| pt0_ax3_r400_s2 | n/a | 28.1 | 63.1 | 240 ms | PM>=45, GM>=6 | PASS on margins only (not clean) | holes PASS; kept/exc bins (key2) 16/16; key2 BLOCKED |
| pt0_ax3_r800_s1 | n/a | n/a | 66.9 | 290 ms | PM>=45, GM>=6 | PASS | holes PASS; kept/exc bins (key2) 15/16; key2 agree |
| pt0_ax3_r800_s2 | n/a | 28.1 | 64.4 | 241 ms | PM>=45, GM>=6 | PASS | holes PASS; kept/exc bins (key2) 15/16; key2 agree |
| pt1_ax1_r400_s1 | 11.2 | 11.2 | 60.8 | 333 ms | PM>=45, GM>=6 | PASS | holes PASS; kept/exc bins (key2) 16/17; key2 agree |
| pt1_ax1_r400_s2 | 11.4 | 11.3 | 59.4 | 320 ms | PM>=45, GM>=6 | PASS | holes PASS; kept/exc bins (key2) 17/17; key2 agree |
| pt1_ax1_r800_s1 | 11.7 | 11.6 | 63.7 | 352 ms | PM>=45, GM>=6 | PASS | holes PASS; kept/exc bins (key2) 16/17; key2 agree |
| pt1_ax1_r800_s2 | 11.7 | 11.6 | 57.1 | 309 ms | PM>=45, GM>=6 | PASS | holes PASS; kept/exc bins (key2) 17/17; key2 agree |
| pt1_ax2_r400_s1 | 11.1 | 11.0 | 54.3 | 327 ms | PM>=45, GM>=6 | PASS | holes PASS; kept/exc bins (key2) 14/17; key2 agree |
| pt1_ax2_r400_s2 | 11.1 | 11.0 | 56.5 | 316 ms | PM>=45, GM>=6 | PASS | holes PASS; kept/exc bins (key2) 15/17; key2 agree |
| pt1_ax2_r800_s1 | 11.7 | 11.5 | 57.4 | 314 ms | PM>=45, GM>=6 | PASS | holes PASS; kept/exc bins (key2) 16/17; key2 agree |
| pt1_ax2_r800_s2 | 11.6 | 11.4 | 56.4 | 317 ms | PM>=45, GM>=6 | PASS | holes PASS; kept/exc bins (key2) 15/17; key2 agree |
| pt1_ax3_r400_s1 | n/a | n/a | 60.2 | 256 ms | PM>=45, GM>=6 | PASS on margins only (not clean) | holes PASS; kept/exc bins (key2) 5/16; key2 BLOCKED |
| pt1_ax3_r400_s2 | n/a | 14.0 | 61.2 | 259 ms | PM>=45, GM>=6 | PASS | holes PASS; kept/exc bins (key2) 14/16; key2 agree |
| pt1_ax3_r800_s1 | n/a | n/a | 66.6 | 272 ms | PM>=45, GM>=6 | PASS | holes PASS; kept/exc bins (key2) 14/16; key2 agree |
| pt1_ax3_r800_s2 | n/a | n/a | 62.0 | 249 ms | PM>=45, GM>=6 | PASS | holes PASS; kept/exc bins (key2) 5/16; key2 agree |

**Total: 24/24 meet the margin limits (22/24 also have holes PASS and key2 not BLOCKED); 0/24 FAIL.**
Key2 BLOCKED (2, both ax3 cells, PM disagreement just over 3 deg): pt0_ax3_r400_s2 (dPM +3.47), pt1_ax3_r400_s1 (dPM +3.59, kept bins 5/16 in key2). Those two show "PASS on margins only (not clean)". All xy cells agree (|dPM| <= 0.95 deg, |dGM| <= 0.02 dB).
Hole check: 24/24 OVERALL PASS, no FAIL (freeze-7 had 11/24 hole FAIL). Plateau GM at ax3 (key2): 28.1-28.3 (pt0), 14.0 (pt1_ax3_r400_s2), otherwise n/a.
Worst (min over cells): xy PM 49.9 deg (pt0_ax2_r800_s1), xy GM 10.8 dB (pt0_ax1_r400_s2 / ax2), yaw-axis (ax3) PM 60.2 deg (pt1_ax3_r400_s1) no GM crossing, DM min 240 ms (pt0_ax3_r400_s2) vs limit ~5-10 ms + latency.
Pass counts: PM>=45 24/24; GM>=6 24/24 (16 xy cells GM 10.8-11.7, 8 ax3 n/a); DM 24/24.
Freeze-7 comparison: xy PM was 38.4-47.4 deg (13/16 cells FAIL PM), GM 11.3-12.9; freeze-8 xy PM 49.9-63.7 deg (0/16 FAIL), GM 10.8-11.7 (about 0.5-1 dB lower), f_c 0.46-0.56 Hz. ax3 PM 63-68 (pt0)/60-67 (pt1) vs freeze-7 61-71. pt1_ax3_r800_s1 now has valid margins (freeze-7 had none).
Model prediction at freeze-7 (g2_outer_model_s177.md) was PM 46 / GM 7.9 for the old XY gains; not re-derived for 1.2/3.6.

# G2 spot-check at freeze-8 (S181 cells), scores

Commands (queue-produced, read not re-run; same commands as freeze-7 spot SCORES.md): rate `m3a_margins_pretest.py D/roll800_fwdef_s2/s1.csv 1 60 10 800 > margins.txt` (gate.md PASS); att `attitude_break_check.py ... --Tp 10 --fmin 0.2 --fmax 20` (RESULT PASS) then `ratesp_csv.py ... --margins > ax2_r400_s1_margins.json`; holes: OVERALL line of holes files (g2s/holes.txt is absent, roll holes are in roll800_fwdef_s2/holes.txt).
ax2_r400_s1_margins.err is empty (0 bytes): no warnings or errors.

| cell | GM dB (freeze-7) | PM deg (freeze-7) | DM ms (freeze-7) | limit | verdict | hole check |
|---|---|---|---|---|---|---|
| roll800_fwdef_s2 | 15.9 (16.1) | 41.3 (47.8) | 70.6 (80.6) | GM>=6, PM>=45, DM>=2 periods | FAIL: PM 41.3 < 45 (-6.5 deg vs freeze-7) | OVERALL PASS |
| ax2_r400_s1 (pitch att) | 13.6 (19.1) | 42.2 (43.0) | 82.1 (88.7) | GM>=6, PM>=45, DM>=2 periods | FAIL: PM 42.2 < 45 (-0.8 deg vs freeze-7); GM -5.5 dB vs freeze-7 | OVERALL PASS |

**Total: 0/2 PASS (both fail PM). Second key (rate and att) not run, primary only, as freeze-7.**

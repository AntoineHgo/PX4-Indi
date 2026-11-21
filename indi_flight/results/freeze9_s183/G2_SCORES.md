# G2 at freeze-9 (S183 cells, MC_INDI_XY_VP 2.4), scores

## G2 outer loops

Commands (repo root; keyed scripts run unchanged on scratchpad copies, only the results path g2_outer_freeze_s163 replaced by freeze9_s183/g2o; key2 copy also has HERE hard-set to the repo bench dir), identical to freeze-8:
`sed 's#g2_outer_freeze_s163#freeze9_s183/g2o#' indi_flight/bench/g2_freeze_table_s163.py > $S/tab9.py; python3 $S/tab9.py` (primary table, outer part)
`sed -e 's#g2_outer_freeze_s163#freeze9_s183/g2o#' -e "s#^HERE = .*#HERE = '$PWD/indi_flight/bench'#" indi_flight/bench/g2_key2_outer_s164.py > $S/key2_9.py; python3 $S/key2_9.py` (second key, wrote freeze9_s183/g2o/key2.md, self-test PASS)
Hole check: `grep OVERALL g2o/*_holes.txt`. Limits as freeze-8: PM >= 45 deg, GM >= 6 dB (GM n/a = no -180 crossing in 0.2-8 Hz band; plateau GM = key2 phase-plateau gain margin, n/a = none), DM >= 2 control periods + latency (never binding). Key2 agreement tolerance as freeze-8: |dPM| <= 3 deg and |dGM| <= 1 dB, same presence/absence of GM, otherwise BLOCKED.
Host python3 worked, no containers started. Values in each cell: freeze-9 (freeze-8). The table script also prints the margins PASS = FAIL for ax3 cells (gm NaN); verdicts treat GM n/a as no limit, as freeze-8. The rate-cell table it prints refers to an old folder and is not part of this score.

| cell | GM dB | plateau GM dB (key2) | PM deg | DM | limit | verdict | notes |
|---|---|---|---|---|---|---|---|
| pt0_ax1_r400_s1 | 13.7 (10.9) | 13.07 (11.0) | 51.2 (54.6) | 412 ms (271) | PM>=45, GM>=6 | PASS | holes PASS; kept/exc bins (key2) 16/17; key2 agree |
| pt0_ax1_r400_s2 | 13.4 (10.8) | 12.95 (10.9) | 51.6 (52.8) | 384 ms (263) | PM>=45, GM>=6 | PASS on margins only (not clean) | holes FAIL; kept/exc bins (key2) 17/17; key2 agree |
| pt0_ax1_r800_s1 | 14.0 (11.2) | 13.27 (11.2) | 49.0 (53.9) | 354 ms (292) | PM>=45, GM>=6 | PASS | holes PASS; kept/exc bins (key2) 17/17; key2 agree |
| pt0_ax1_r800_s2 | 14.0 (11.3) | 13.29 (11.3) | 48.5 (54.1) | 358 ms (286) | PM>=45, GM>=6 | PASS | holes PASS; kept/exc bins (key2) 16/17; key2 agree |
| pt0_ax2_r400_s1 | 13.5 (10.8) | 12.93 (10.9) | 51.6 (51.4) | 406 ms (268) | PM>=45, GM>=6 | PASS | holes PASS; kept/exc bins (key2) 17/17; key2 agree |
| pt0_ax2_r400_s2 | 13.6 (10.9) | 13.01 (10.9) | 55.7 (55.3) | 388 ms (286) | PM>=45, GM>=6 | PASS | holes PASS; kept/exc bins (key2) 17/17; key2 agree |
| pt0_ax2_r800_s1 | 14.1 (11.0) | 13.33 (11.1) | 49.9 (49.9) | 374 ms (266) | PM>=45, GM>=6 | PASS | holes PASS; kept/exc bins (key2) 17/17; key2 agree |
| pt0_ax2_r800_s2 | 14.0 (11.2) | 13.28 (11.2) | 51.0 (50.0) | 378 ms (271) | PM>=45, GM>=6 | PASS | holes PASS; kept/exc bins (key2) 17/17; key2 agree |
| pt0_ax3_r400_s1 | n/a (n/a) | n/a (28.2) | 70.4 (67.5) | 262 ms (276) | PM>=45, GM>=6 | PASS | holes PASS; kept/exc bins (key2) 15/16; key2 agree |
| pt0_ax3_r400_s2 | n/a (n/a) | n/a (28.1) | 68.7 (63.1) | 271 ms (240) | PM>=45, GM>=6 | PASS | holes PASS; kept/exc bins (key2) 14/16; key2 agree |
| pt0_ax3_r800_s1 | n/a (n/a) | n/a (n/a) | 71.7 (66.9) | 313 ms (290) | PM>=45, GM>=6 | PASS | holes PASS; kept/exc bins (key2) 14/16; key2 agree |
| pt0_ax3_r800_s2 | n/a (n/a) | n/a (28.1) | 65.5 (64.4) | 246 ms (241) | PM>=45, GM>=6 | PASS on margins only (not clean) | holes FAIL; kept/exc bins (key2) 14/16; key2 agree |
| pt1_ax1_r400_s1 | 14.1 (11.2) | 13.45 (11.2) | 58.9 (60.8) | 491 ms (333) | PM>=45, GM>=6 | PASS | holes PASS; kept/exc bins (key2) 16/17; key2 agree |
| pt1_ax1_r400_s2 | 13.9 (11.4) | 13.35 (11.3) | 57.6 (59.4) | 512 ms (320) | PM>=45, GM>=6 | PASS on margins only (not clean) | holes FAIL; kept/exc bins (key2) 16/17; key2 agree |
| pt1_ax1_r800_s1 | 14.5 (11.7) | n/a (11.6) | 53.2 (63.7) | 452 ms (352) | PM>=45, GM>=6 | PASS | holes PASS; kept/exc bins (key2) 17/17; key2 agree |
| pt1_ax1_r800_s2 | 14.5 (11.7) | n/a (11.6) | 55.3 (57.1) | 475 ms (309) | PM>=45, GM>=6 | PASS | holes PASS; kept/exc bins (key2) 17/17; key2 agree |
| pt1_ax2_r400_s1 | 13.8 (11.1) | 13.19 (11.0) | 54.2 (54.3) | 483 ms (327) | PM>=45, GM>=6 | PASS | holes PASS; kept/exc bins (key2) 15/17; key2 agree |
| pt1_ax2_r400_s2 | 13.9 (11.1) | 13.19 (11.0) | 60.5 (56.5) | 534 ms (316) | PM>=45, GM>=6 | PASS | holes PASS; kept/exc bins (key2) 15/17; key2 agree |
| pt1_ax2_r800_s1 | 14.4 (11.7) | n/a (11.5) | 56.6 (57.4) | 465 ms (314) | PM>=45, GM>=6 | PASS | holes PASS; kept/exc bins (key2) 16/17; key2 agree |
| pt1_ax2_r800_s2 | 14.5 (11.6) | n/a (11.4) | 62.5 (56.4) | 558 ms (317) | PM>=45, GM>=6 | PASS | holes PASS; kept/exc bins (key2) 16/17; key2 agree |
| pt1_ax3_r400_s1 | n/a (n/a) | n/a (n/a) | 63.9 (60.2) | 273 ms (256) | PM>=45, GM>=6 | PASS on margins only (not clean) | holes PASS; kept/exc bins (key2) 14/16; key2 BLOCKED |
| pt1_ax3_r400_s2 | n/a (n/a) | n/a (14.0) | 64.5 (61.2) | 272 ms (259) | PM>=45, GM>=6 | PASS on margins only (not clean) | holes PASS; kept/exc bins (key2) 14/16; key2 BLOCKED |
| pt1_ax3_r800_s1 | n/a (n/a) | n/a (n/a) | 63.1 (66.6) | 256 ms (272) | PM>=45, GM>=6 | PASS on margins only (not clean) | holes FAIL; kept/exc bins (key2) 13/16; key2 agree |
| pt1_ax3_r800_s2 | n/a (n/a) | n/a (n/a) | 65.4 (62.0) | 263 ms (249) | PM>=45, GM>=6 | PASS | holes PASS; kept/exc bins (key2) 7/16; key2 agree |

**Total: 24/24 meet the margin limits (18/24 also have holes PASS and key2 not BLOCKED); 0/24 FAIL margins.** Freeze-8 was 24/24 margins, 22/24 clean.
Per-group pass counts (margins): PM>=45 24/24; GM>=6 24/24 (16 xy cells GM 13.4-14.6, 8 ax3 n/a); DM 24/24. By group: ax1 8/8, ax2 8/8, ax3 8/8 (all freeze-8: same). Holes PASS 20/24 (freeze-8 24/24); key2 agree 22/24 (freeze-8 22/24).
Hole FAIL (4): pt0_ax1_r400_s2, pt1_ax1_r400_s2, pt0_ax3_r800_s2, pt1_ax3_r800_s1. In each the only FAIL row is vehicle_local_position_setpoint (controller class) "count-disagree: count-based missing -1..-3"; controller-class hole numbers are within limits (missing 0-0.024 % vs 0.10 %, excess 0-8.75 ms vs 10) in all four, but the OVERALL line is FAIL and is reported as such.
Key2 BLOCKED (2, both pt1_ax3, PM disagreement just over 3 deg): pt1_ax3_r400_s1 (dPM -3.34, key2 lower), pt1_ax3_r400_s2 (dPM -3.27). Freeze-8 also had 2 BLOCKED ax3 cells (different ones: pt0_ax3_r400_s2, pt1_ax3_r400_s1). All xy cells agree (|dPM| <= 2.14 deg, |dGM| <= 0.14 dB). Margins-only PASS (not clean) = margins pass with a hole FAIL and/or key2 BLOCKED; the 6 non-clean cells are the 4 hole-FAIL plus the 2 BLOCKED cells (disjoint).
Worst (min over cells): xy PM 48.5 deg (pt0_ax1_r800_s2; freeze-8 min 49.9), xy GM 13.4 dB (pt0_ax1_r400_s2; freeze-8 min 10.8), yaw-axis (ax3) PM 63.1 deg (pt1_ax3_r800_s1; freeze-8 min 60.2) no GM crossing, DM min 246 ms (pt0_ax3_r800_s2; freeze-8 min 240 ms).
Freeze-8 comparison: xy GM rose about 2.5-3 dB (10.8-11.7 to 13.4-14.6), xy PM 48.5-62.5 deg vs 49.9-63.7, f_c 0.31-0.40 Hz vs 0.46-0.56 Hz (lower crossover from XY_VP 2.4). ax3 PM 63-72 vs 60-67.

# G2-STEP at freeze-9

pending (9 flights still flying).

# G2 spot-check at freeze-9 (S183 cells), scores

Commands (queue-produced, read not re-run; same as freeze-8): rate `m3a_margins_pretest.py D/roll800_fwdef_s2/s1.csv 1 60 10 800 > margins.txt` (gate.md PASS); att `attitude_break_check.py ... --Tp 10 --fmin 0.2 --fmax 20` (RESULT PASS) then `ratesp_csv.py ... --margins > ax2_r400_s1_margins.json`; holes: OVERALL line of roll800_fwdef_s2/holes.txt and g2s/ax2_r400_s1_holes.txt. ax2_r400_s1_margins.err is 0 bytes. Values: freeze-9 (freeze-8).

| cell | GM dB | PM deg | DM ms | limit | verdict | hole check |
|---|---|---|---|---|---|---|
| roll800_fwdef_s2 (rate) | 15.9 (15.9) | 47.1 (41.3) | 76.1 (70.6) | GM>=6, PM>=45, DM>=2 periods | PASS (PM +5.8 deg vs freeze-8) | OVERALL FAIL (freeze-8 PASS): single row vehicle_local_position_setpoint count-disagree (count-based missing -1); controller class missing 0.0207 % (limit 0.10), max 17.5 ms, excess 6.25 ms (limit 10) |
| ax2_r400_s1 (pitch att) | 13.2 (13.6) | 47.4 (42.2) | 91.5 (82.1) | GM>=6, PM>=45, DM>=2 periods | PASS (PM +5.2 deg vs freeze-8) | OVERALL PASS |

**Total: 2/2 meet the margin limits (freeze-8 0/2). Rate cell has a hole-check OVERALL FAIL, so it is "PASS on margins only (not clean)"; att cell is clean.** Second key not run (primary only, as freeze-8). Rate PM 47.1 is only 2.1 deg above the limit; att 47.4 is 2.4 deg above.

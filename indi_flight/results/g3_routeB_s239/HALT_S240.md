# S240 route B: why runs 002, 003, pretest draw 37 score FAIL (read-only)

## Task 1: runs 002 and 37 (empty failing-item column)
- Aggregation defect (b). Overall verdict = scorer `pass`; the failing list checks only items 1-3:
  bench/g3_chain.sh:572-576 (`items = (item1_loc, item2_oscillation, item3_steady_state)`, `lab` uses j.get("pass")).
  Key-2 `pass` = items 1-6 (bench/g3_checks_key2.py:386-396, "campaign pass = items 1-6"). Items 4-6 never reach
  key*_failing, SCORES.tsv (g3_chain.sh:596,616-617) or the halt filter (g3_chain.sh:677, only item1/item2).
- Run 002: items 1,2,3 pass both keys. FAIL = item 4 tracking: horizontal RMS 0.834 m > 0.5 m (g3_checks.json item4_tracking,
  key2/run_002.json item4_tracking, same value). Item 5 passes, item 6 n/a. Item 4 is a real gate item (GATES.md:316, 749;
  Q33 keeps item 4 limits, :882). So (a) real failure of a gate item, hidden by the column. Not item 5.
- Draw 37: items 1-4 pass (item 4 horiz 0.469 m). FAIL = item 5 recovery only: fault@t0 event, max error after return 0.472 m
  > 0.3 m, re_excursion true, att err 14.5 deg; gust event passes (0.109 m). Both keys agree (pretest37/run_037/g3_checks.json
  item5_recovery; pretest37/key2/run_037.json). Item 5 is the undecided item, so this is (c): the empty column is defect (b),
  and whether the item-5 FAIL counts depends on the owner question. Scoring follows GATES.md:878-880 (Q33 reference) as written.
- g4 chatter column (col 5) is True everywhere: not a cause. No parse error: JSONs load, `pass` is a boolean false.

## Task 2: run 003 item 2 (both keys FAIL)
- Axis q (pitch rate) only; p, r not sustained; position limit cycle not sustained (p2p 0.18/0.24/0.03 m).
- Key 1: lines [2.00 Hz, window idx 50, 3 windows] and [2.25 Hz, idx 54, 3 windows]; 10 of 108 windows flagged; line RMS at
  max ratio 10.0 dps, max flagged 13.6 dps (limits: RMS > 5 dps, peak ratio > 20, >= 3 consecutive windows, f within 10 %;
  g3_checks.py:74, 161).
- Key 2: sustained, at [50.0, 2.0 Hz] (meaning of "at" unverified), max_rms_dps 12.3. Keys agree: q at about 2 Hz.
- Time: airborne 19.7-130.9 s (key 1 clock); idx 50 maps to about 70 s, inside the lemniscate main segment (67.8-85.6 s),
  about 50 s after takeoff (index-to-time mapping inferred, unverified). Skipped windows (28/108) do not cover it.
- Run 003 also fails item 4 (horiz RMS 0.553 m > 0.5), unlisted.
- Draw 003: tau x2.79 down / x2.43 up (slow motors), mass 0.745, inertia 0.99/1.02/0.84, G1 k p 1.16 r 0.90 y 1.34,
  weak_motor off, saturation off, loop delay 1/1 ms, EKF delay 158 ms, tel_frozen motor 3 1 s, wind 2.2 m/s steady,
  gust peak 3.8 m/s, no sag, vibration 1.17x.

## Task 3: other draws
- 002: tau up 0.56 / down 1.31, mass 1.11, inertia 1.19/1.02/1.04, G1 k p 0.99 r 0.70 y 1.13, weak off, sat off, delay 1/1 ms,
  EKF 178 ms, tel_loss motor 3 2 s, sag 0.94, wind 4.7 / 8.4 m/s peak, vibration 3.2x.
- 37: tau up 0.61 / down 0.64, mass 0.92, inertia 1.29/0.93/1.08, G1 k p 1.05 r 0.92 y 0.80, WEAK MOTOR 3 at 0.743, sat off,
  delay 0/0 ms, EKF 246 ms, tel_loss motor 2 2 s, sag 0.953, wind 1.5 / 3.6 m/s peak, vibration 2.2x.

## Conclusion
SCORES.tsv and chain_score.json report only items 1-3; item 4 (002, 003) and item 5 (37) fail the verdict silently. The halt
filter (g3_chain.sh:677) fired correctly only for 003 (real q oscillation). Not checked: plant cause of the 0.83 m tracking RMS.

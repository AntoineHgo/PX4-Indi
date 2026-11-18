# T184 second key: hole_report duplicate-stamp pairing and count tolerance (c5b5a897e9)

Verdict: AGREE WITH MINOR

Probes: indi_flight/bench/tests/t184_probe.py and t184_probe2.py (scratch, numpy only, run with python3 -B).
Self-test: `python3 -B indi_flight/bench/tests/test_hole_report.py` exit 0, "ALL PASS" (8 S87 cases included).

1. Genuine drop, no duplicate nearby: reported by both methods (probe A: missing 1, count-based 1, PASS).
   Counter-example that does go unreported by both: a drop with an unrelated duplicate stamp 4 samples away
   (probe B): gap-based 0 (dup absorbs the gap), count-based 0 (the dup adds one sample, the drop removes one).
   The cross-check cannot see this because the two errors cancel in both counts. Spec permits the cancel,
   but the count check is not an independent detector for drop+dup pairs. A dup 9 samples away does not absorb (probe C).
   Probe G (drop plus a publish-jitter pair 10 samples later) gives the right total (1) but attributes it to the
   jitter gap's location when the drop steals the pair's duplicate (greedy, earliest-first).

2. Far duplicate (>8 samples) cannot absorb a gap (probe C). One duplicate absorbs at most one missing period
   (shared `used` set), so one dup cannot absorb two gaps (probe D: two drops, one dup between, missing 1, count 1).
   Note the drop-plus-dup masking in item 1 is the only way a real loss is hidden; it needs a dup inside the 8-sample window.

3. Tolerance = 1 + int(0.001 x all duplicate stamps, post-skip). For 120 s at 800 Hz with 3000 duplicates the tolerance is 4.
   Probe J (3000 paired jitter pairs plus k unpaired far dups): k=4 passes (disagreement 4), k=5 fails.
   Largest passing disagreement = 4 (about 4 / 96000 samples). Tolerance counts ALL dups, paired ones included, so it grows
   with publish jitter rather than with the unpaired inconsistency it is meant to bound.
   Wrong-rate topic: half the log stamped at 1251 us vs median 1250 gives disagreement 38 (FAIL, probe K);
   half at 1250.3 us gives 12 (FAIL, probe K2). A rate error of about 0.02 % or more is caught at this tolerance.
   A rate error that is consistent with the topic's own median is invisible to both methods (pre-existing).

4. Test run: exit 0, ALL PASS, all 8 S87 cases and the S86 cases pass.

5. Max-gap check: unchanged for the controller/sim targets. Gaps with dt > 2 x median + 1 are always listed, and the
   keep/drop rule for dt <= 2 x median + 1 is the same as before. The 10 ms limit is still applied to listed gaps.
   Minor pre-existing gap (not introduced by this diff): a k=2 gap absorbed by a duplicate is dropped from the list
   whatever its dt, so on a slow controller-class topic it escapes the 10 ms limit. Probe2: 50 Hz
   vehicle_local_position_setpoint with a 40 ms gap plus one dup gives PASS, max_hole_ms 0.0.
   At 800 Hz (2 x 1.25 ms + 1 us) this cannot occur. Recommend exempting dt > LIM_HOLE_MS from absorption.

Minor items: (a) the 10 ms escape above (pre-existing, spec-relevant for slow topics); (b) the cross-check is blind to
drop+dup pairs (spec-sanctioned, document it); (c) tolerance counts paired duplicates as well as unpaired ones.

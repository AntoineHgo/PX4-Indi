# T182 / S87: count cross-check false FAIL in hole_report.py

## Cause
- The comparison is already `abs(cm - gm) > 1`. The "disagreement of 1" (gyro, torque) and "3" (actuator_motors) in the report
  tables were not the compared quantities. The table `miss` column excludes gaps attributed to a sim hole. The sim topic
  sensor_gyro is not cross-checked at all, so it cannot FAIL on this.
- The only real failing comparison on pt1_ax3_r800_s1 was actuator_motors: gap-based 36 vs count-based 34, a difference of 2.
- Mechanism: stamps sit on a 1250 us grid and are exact, so rounding and 1 us jitter are not the cause. Controller topics show
  publish jitter as a dup stamp (dt = 0) paired with a 2-period gap. Across the whole log gm - cm = number of dup stamps that
  were not absorbed by a gap. Two flaws made dups go unpaired:
  1. A dup only cancelled a gap of at most 2 periods. A 3-period gap (dt 3750) with one dup was counted as 2 missing, but
     the sample count says 1.
  2. Pairing was greedy by distance. A dup near two gaps could be taken by the wrong one and leave a neighbour unpaired.
- actuator_motors is not on a different period. It is the same 1250 us period, but it has the most dups (3056 vs 1371 for
  angular_velocity), so it accumulates the most pairing noise.

## Fix (bench/hole_report.py)
- `find_gaps` returns `(t, dt, missing)`. Each dup within DUP_WINDOW (8 samples) of a gap absorbs one missing period.
  The match is earliest-unused-dup-in-window, which is optimal for equal windows.
- A gap longer than 2 periods stays listed even if its count is absorbed, so the 10 ms max-hole check is not weakened.
- Tolerance: `tol = 1 + int(DUP_NOISE * n_dup_stamps)`, with DUP_NOISE = 0.001 (the controller missing limit). The 1 covers
  the rounding of span/median. gm - cm is the number of dups no gap can absorb, which is physically a duplicate stamp and
  not a lost sample. A healthy 800 Hz flight has about 0.07 % of its dups unpaired (2 of 2853 on pt0_ax3_r800_s1).
  0.1 % of the dups allows that and still rejects excess.
- Few dups gives tol = 1, which is the spec. A lone hole always stays visible in gm. Hiding one needs a coincident dup, so
  the count-based number then reads low and the gap-based number stays high. The 5-lost-plus-5-far-dups S86 case still FAILs.
- `count_tol` is added to each controller row in the report.

## Tests (bench/tests/test_hole_report.py, run with `python3 -B`, numpy only)
All pass (`ALL PASS`). New cases:
- healthy 800 Hz with +-1 us jitter plus dup+2-period pairs: PASS
- 3-period gap with 1 dup: both methods read 1
- single dropped sample: reported as missing 1 / count-based 1
- disagreement of 1 is tolerated
- disagreement of 2 with few dups: FAIL
- ~1200 jitter pairs: tolerance scales to 2
- 2 unpaired dups among ~1200: PASS
- 6 unpaired dups among ~1200: FAIL

Break checks (each fix broken once, the matching test FAILed, then restored):
- `DUP_NOISE = 0`: "many publish-jitter dups" and "2 unpaired dups" FAIL
- `while miss > 0 and k <= 2` (old 2-period-only cancel): "3-period gap + 1 dup" FAILs
- tolerance + 5: "disagreement of 2", "6 unpaired" and the S86 case FAIL

Warning: `python3 -I` ignores PYTHONDONTWRITEBYTECODE. An edit that keeps the file size and lands in the same second reuses a
stale `__pycache__/hole_report.*.pyc`. This gave a false failure during break checks. Use `python3 -B`.

## Re-run on s86 cells (Docker, one at a time)
| cell | before | after | remaining reason if FAIL |
|---|---|---|---|
| pt0_ax1_r400_s1 | FAIL | FAIL | real holes (sim 15 ms, ctrl 12.5 ms, outer 21 ms); count-disagree on 3 topics (400 Hz, sub-period 1250 us stamp jitter, cm 29 vs gm 9, not investigated further) |
| pt0_ax3_r400_s2 | PASS | PASS | |
| pt0_ax3_r800_s1 | FAIL | PASS | |
| pt0_ax3_r800_s2 | FAIL | FAIL | outer topic hole 18.75 ms (> 10); no count-disagree |
| pt1_ax1_r400_s1 | FAIL | FAIL | real holes (sim 12.5 ms, ctrl 12.5 ms, outer 18.75 ms); outer topic count-disagree (89 Hz, irregular period, cm -7) |
| pt1_ax3_r400_s1 | PASS | PASS | |
| pt1_ax3_r400_s2 | PASS | PASS | |
| pt1_ax3_r800_s1 | FAIL | PASS | |
| pt1_ax3_r800_s2 | FAIL | FAIL | real holes (sim 12.5 ms, ctrl 13.75 ms, outer 18.75 ms) |
(The "before" column for the cells not named in the task is from the old reporter; I did not re-read it, apart from the two named cells.)

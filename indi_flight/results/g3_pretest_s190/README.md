# G3 pre-test re-fly S190 (20 draws, Q22 box) with the D-AF-ALIAS fixes

Same draws/command as S188 (`../g3_pretest_s187/`), re-flown after 2d92dbcf59 (force low-pass at its own rate) and 4afa7a97b6 (re-seed force filter after a gap).
Scored with the two existing keyed scorers (key 1 `g3_checks.py` via `g3_score_docker.sh`, key 2 `g3_checks_key2.py`), commands in `score.sh`
(= scoring block of `fly_all.sh`; batch was flown with SKIP_SCORE=1). Outputs: SCORE_KEY1.txt, SCORE_KEY2.txt, run_*/g3_checks.json, key2/*.json.

## Firmware
All 20 runs: `provenance.binary_sha256` b12ca5dcc8... = sha256 of build/px4_sitl_default/bin/px4 (mtime 21:51:14 on 2026-11-21).
`git.commit` (repo HEAD at launch) is 4afa7a97b6 (run 0), 91719345b2 (1-6), e94cbf0db6 (7-19): all contain both fixes in source.
FLAG: `provenance.binary_commit` reads 887f3a76c0 in every run, which is the commit BEFORE 4afa7a97b6. The binary was built 21 s before 4afa7a97b6 was
committed, so it was most likely built from the working tree holding fix 2 (binary_commit = HEAD at build time). UNVERIFIED: no check that fix 2 is in the binary.

## Results (key 2 columns: pass / item1 / item2 / item3; key 1 shows item 2 as "p/q lines")
Item 1 passes 20/20 on both keys. Item 2 is the p/q/r/position oscillation; item 3 is steady state. Chatter (G4, not a G3 gate) in key 1/2: 004, 016, 018.

| run | key 1 | key 2 | item 2 line (key 1 / key 2) | S188 (both keys) |
|---|---|---|---|---|
| 00 | pass | pass | none | FAIL i2 p/q 2.5-3.3 Hz (key 2 7.0 s, 2.5 Hz) |
| 02 | FAIL i3 (horiz RMS 0.54 m) | FAIL i2+i3 | key 1: q not sustained (5 flagged windows); key 2: q 2.0 Hz at t=29 s | FAIL i2 q 2.0 Hz + i3 |
| 03 | FAIL i2 | FAIL i2 | q 2.0 Hz (key 1 3 windows t=26-47; key 2 at t=27) | FAIL i2 q 2.0 Hz |
| 05 | FAIL i2+i3 (0.50 m) | FAIL i2+i3 | q 2.0 Hz (t=32; key 2 t=29) | FAIL i2 p/q 4.5 Hz + i3 |
| 08 | FAIL i2 | FAIL i2 | q 10.75 Hz (t=24/25) | FAIL i2 q 10.8 Hz |
| 19 | FAIL i2 | pass | key 1: q 2.0 Hz, 3 windows at t=47; key 2: none | pass |
| 09,10,13,16,17 | pass | pass | none | FAIL i2 (09 p 2.75 Hz, 10 p/q 5.3, 13 p 2.75, 16 p 7 Hz, 17 p/q 3 Hz) |
| 01,04,06,07,11,12,14,15,18 | pass | pass | none | pass |

Run 17 is a new draw (old draw replaced in S187), not strictly comparable run-for-run to S173; S188 17 already used the new draw.

## Counts
- Key 1: 15 pass / 5 FAIL (02, 03, 05, 08, 19). Key 2: 16 pass / 4 FAIL (02, 03, 05, 08). S188: 10/20 on both keys.
- Item 2 failures remaining: key 1 4/20 (03, 05, 08, 19), key 2 4/20 (02, 03, 05, 08); S188 10/20.
- Item 3 failures: 02, 05 (same as S188), both horiz RMS ~0.5 m vs 0.3 limit.
- S188 INDI-only failures were 00/02/05/09/10/16/17. Fixed: 00, 09, 10, 16, 17. Still failing: 02, 05. (03/08/13 failed with PID in S188 too: 13 now passes, 03 and 08 still fail.)
- Still failing and shared with PID in S188: 03 (2 Hz q), 08 (10.75 Hz q). INDI-only still failing: 02, 05 (and 19 on key 1 only, new vs S188).
- The 2.5-7.3 Hz p/q lines are gone; remaining lines are 2.0 Hz q (02, 03, 05, 19) and 10.75 Hz q (08).

## Key agreement
Verdicts differ for 19 only (key 1 FAIL, key 2 pass). Item-2 attribution also differs for 02 (key 1 no item 2 failure, key 2 q 2 Hz).
GATES.md line 555: "G4 item 2 (Q15 A): the sustained-oscillation detector skips windows that overlap the 3 s after a nav_state change". It is listed under G4 item 2;
this README did not verify that it applies to G3 item 2 (S189 reconcile note says key 1 lacks the skip and 03 passes PID under key 2).
Key 1 reports skipped_windows = 0 for run 19, key 2 skips 21 windows incl. t >= 48.96 s. Whether the key-1 flag at t=47 s is a nav-change window is UNVERIFIED
(window phases differ between keys; the key-2 skip starts after t=47.96). So the 19 and 02 disagreements are not shown to be the known nav-change difference.

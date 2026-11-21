# G4 command chatter, freeze-7, Q18 A land-window skip: KEY 2 re-score (S180)

Script: `indi_flight/bench/g4_chatter_skip_key2.py` (key-2 chatter path of `g3_checks_key2.py`, same Q14 A rule: 4 s windows, 20-100 Hz,
peak > 20 x median AND line RMS +-2 Hz >= 5e-4, >= 3 consecutive windows within +-10 % in frequency; plus the skip of every 4 s window
overlapping [ground_contact - 1 s, landed + 1 s]). ground_contact = last rise of vehicle_land_detected.ground_contact, landed = the next
rise of .landed, both read from each run's flight.ulg. No landing -> nothing skipped. Detector input = actuator_motors over the same
airborne span as key 2 (ground-truth height > start + 0.3 m). KEY1.md, key-1 script and touchdown_s179.md were not read.

Commands (repo root):
```
indi_project/docker/run.sh -n k2st -t 300 -- python3 indi_flight/bench/tests/test_g4_chatter_skip_key2.py
indi_project/docker/run.sh -n k2rs -t 900 -- sh -c "for p in hover cruise; do for q in quiet typ harsh; do for s in 1 2 3; do python3 indi_flight/bench/g4_chatter_skip_key2.py indi_flight/results/freeze7_s177/g4/${p}_${q}_s$s; done; done; done"
```

## Self-test (12 checks, known answers; synthetic 70 Hz line on motor 1, skip interval [39,43] s)
land_window logic (last gc rise, next landed rise; no landing -> None); line only inside the land window -> not flagged; line
at 5-25 s -> flagged; same line with no landing -> flagged; line ending at 39.0 s (windows end <= skip start) -> flagged;
line from 43.0 s (window start == skip end, touching, not overlapping) -> flagged; line from 42.5 s -> flagged; skipped worst line
reported at ~70 Hz; skipped window count 7 (starts 36..42). All PASS.
Break check (`--self-test --break` disables the skip): 4 checks FAIL (inside-window line flagged, window [39,43) flagged, skipped
worst not reported, skipped count 0), rc=1. The test file asserts that the broken variant fails (`OK` printed).

## Per-run result
| run | chatter after skip | ground_contact / landed (s) | worst non-skipped line: Hz | ratio | line RMS | window start s | skipped windows' worst line: Hz, RMS |
|---|---|---|---|---|---|---|---|
| hover_quiet_s1 | no | 127.0 / 127.7 | 39.0 (m3) | 5820 | 1.36e-04 | 122 | none (no analysed window overlaps; airborne span ends 126.2 s) |
| hover_quiet_s2 | no | 128.0 / 128.7 | 22.2 (m2) | 6591 | 1.45e-04 | 38 | none (no analysed window overlaps; airborne span ends 127.2 s) |
| hover_quiet_s3 | no | 127.1 / 127.8 | 39.0 (m1) | 5757 | 1.38e-04 | 121 | none (no analysed window overlaps; airborne span ends 126.3 s) |
| hover_typ_s1 | no | 127.9 / 128.6 | 39.0 (m1) | 600 | 1.43e-04 | 121 | none (no analysed window overlaps; airborne span ends 127.1 s) |
| hover_typ_s2 | no | 127.1 / 127.7 | 39.0 (m0) | 573 | 1.41e-04 | 121 | none (no analysed window overlaps; airborne span ends 126.3 s) |
| hover_typ_s3 | no | 127.3 / 127.9 | 70.0 (m3) | 590 | 1.09e-04 | 112 | none (no analysed window overlaps; airborne span ends 126.5 s) |
| hover_harsh_s1 | CHATTER (sustained, motors m0,m1,m2,m3) | 127.6 / 128.3 | 20.0 (m0) | 1353 | 9.74e-04 | 38 | 70.0 Hz, 2.88e-04 |
| hover_harsh_s2 | no | 127.3 / 128.0 | 20.0 (m2) | 706 | 9.44e-04 | 37 | none (no analysed window overlaps; airborne span ends 126.5 s) |
| hover_harsh_s3 | no | 127.5 / 128.2 | 20.0 (m3) | 904 | 9.12e-04 | 37 | none (no analysed window overlaps; airborne span ends 126.7 s) |
| cruise_quiet_s1 | CHATTER (sustained, motors m0,m1,m2,m3) | 90.5 / 91.2 | 33.2 (m1) | 12146 | 1.50e-03 | 61 | none (no analysed window overlaps; airborne span ends 89.7 s) |
| cruise_quiet_s2 | CHATTER (sustained, motors m0,m1,m2,m3) | 90.4 / 91.1 | 33.5 (m1) | 543 | 1.44e-03 | 61 | none (no analysed window overlaps; airborne span ends 89.6 s) |
| cruise_quiet_s3 | CHATTER (sustained, motors m0,m1,m2,m3) | 90.4 / 91.1 | 33.2 (m1) | 2677 | 1.48e-03 | 61 | none (no analysed window overlaps; airborne span ends 89.6 s) |
| cruise_typ_s1 | CHATTER (sustained, motors m0,m1,m2,m3) | 90.9 / 91.6 | 33.2 (m3) | 3892 | 1.48e-03 | 65 | none (no analysed window overlaps; airborne span ends 90.2 s) |
| cruise_typ_s2 | CHATTER (sustained, motors m0,m1,m2,m3) | 90.4 / 91.1 | 33.5 (m1) | 2404 | 1.52e-03 | 61 | none (no analysed window overlaps; airborne span ends 89.6 s) |
| cruise_typ_s3 | CHATTER (sustained, motors m0,m1,m2,m3) | 90.3 / 91.0 | 33.0 (m1) | 439 | 1.48e-03 | 68 | none (no analysed window overlaps; airborne span ends 89.5 s) |
| cruise_harsh_s1 | CHATTER (sustained, motors m0,m1,m2,m3) | 90.7 / 91.4 | 33.2 (m1) | 997 | 1.46e-03 | 68 | 70.0 Hz, 2.92e-04 |
| cruise_harsh_s2 | CHATTER (sustained, motors m0,m1,m2,m3) | 90.6 / 91.2 | 33.2 (m1) | 725 | 1.45e-03 | 61 | none (no analysed window overlaps; airborne span ends 89.8 s) |
| cruise_harsh_s3 | CHATTER (sustained, motors m0,m1,m2,m3) | 90.8 / 91.5 | 33.2 (m1) | 795 | 1.45e-03 | 68 | 70.0 Hz, 2.95e-04 |

## Reading
- Verdicts identical to the pre-skip key-2 chatter column of G4_SCORES.md: hover 8/9 no chatter, hover_harsh_s1 CHATTER; cruise 9/9 CHATTER.
- The skip changes nothing: every flagged line is mid-flight (hover_harsh_s1 20 Hz at window 38 s, the rest of the 20 Hz harsh hover
  lines are not sustained; cruise 33 Hz at 61-68 s), far from the landing at ~91 s (cruise) / ~127 s (hover).
- Land windows: ground_contact and landed are 0.6-0.8 s apart in all 18 runs. The airborne span ends ~1 s before ground_contact,
  so only 3 runs (hover_harsh_s1, cruise_harsh_s1, cruise_harsh_s3) have an analysed window overlapping the skip interval; their
  skipped worst line is 70 Hz at RMS ~2.9e-04 (< 5e-4, would not have flagged anyway). The other 15 runs have no touchdown
  window inside the analysed span at all (nothing to skip).
- Caveat: the 20 Hz / 33 Hz lines are at the key-2 band edges / unchanged from before; this re-score does not explain them.

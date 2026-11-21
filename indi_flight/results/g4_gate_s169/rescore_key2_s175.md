# G4 re-score, key2, Q14 A + Q15 A (2026-11-21)

Key2 = `bench/g3_checks_key2.py` (key1 not read). Driver: `results/g4_gate_s169/rescore_key2_s175.py`. Per-run JSON rewritten at `<run>/g3_checks_key2.json`.

## Rule implementation
- Q14 A: window flagged when peak/median(20-100 Hz) > 20 AND line RMS >= 5e-4 (one DShot step; actuator_motors 0-1). Line RMS = sqrt(PSD integrated over +-2 Hz around the peak; was +-2 bins before). Chatter verdict keeps the existing "sustained" rule: >=3 consecutive 4 s windows (1 s step), peak within +-10 %. Table peak/ratio/RMS = the flagged window with the largest line RMS over the motors (or the max-ratio window if none flagged).
- Q15 A: item-2 rate detector (p,q,r, 2-40 Hz, rms > 5 dps, ratio > 20, sustained) skips every 4 s window overlapping [t_change, t_change+3 s] of any vehicle_status.nav_state change (a skipped window also breaks a streak). Applied to all 18 runs. Airborne span as before (height > ground + 0.3 m).
- Also: `pos_limit_cycle` returns "not evaluated" when the hold is < 10 s (cruise holds are 3 s; it crashed before). Position limit cycle is not part of the Q15 detector and is not scored here.

## Per-run table
Item 2 detail = max rms in windows with ratio > 20, deg/s (p/q/r). Skipped = window start range, then number of skipped windows for p/q/r (same for all axes). nav changes = count of nav_state changes in the whole log.

| run | chatter peak Hz | ratio | line RMS (0-1) | chatter | item 2 | item 2 detail (max flagged-window rms dps p/q/r) | nav changes (n) | skipped windows (start s, p/q/r) |
|---|---|---|---|---|---|---|---|---|
| hover_quiet_s1 | 22.2 (m3) | 37 | 1.18e-03 | CHATTER m2,m3 | pass | 0.2/0.8/0.0 | 5 | 34..122 s (21/21/21) |
| hover_quiet_s2 | 20.8 (m1) | 23 | 1.14e-03 | CHATTER m0,m1 | pass | 0.2/0.2/0.0 | 5 | 34..123 s (21/21/21) |
| hover_quiet_s3 | 39.0 (m0) | 7483 | 1.41e-04 | no | pass | 0.2/0.2/0.0 | 5 | 34..122 s (21/21/21) |
| hover_typ_s1 | 22.2 (m3) | 299 | 2.73e-03 | CHATTER m2,m3 | pass | 0.6/0.9/0.0 | 5 | 34..122 s (21/21/21) |
| hover_typ_s2 | 22.2 (m1) | 431 | 1.71e-03 | CHATTER m0,m1,m2,m3 | pass | 1.2/0.9/0.0 | 5 | 34..122 s (21/21/21) |
| hover_typ_s3 | 22.2 (m2) | 1393 | 1.90e-03 | CHATTER m0,m2,m3 | pass | 0.6/0.9/0.0 | 5 | 34..123 s (21/21/21) |
| hover_harsh_s1 | 22.5 (m1) | 320 | 2.14e-03 | no | pass | 1.8/1.5/0.0 | 5 | 34..122 s (21/21/21) |
| hover_harsh_s2 | 22.2 (m0) | 343 | 4.38e-03 | CHATTER m0,m1,m2,m3 | pass | 0.2/0.3/0.0 | 5 | 34..122 s (21/21/21) |
| hover_harsh_s3 | 22.5 (m3) | 411 | 2.29e-03 | CHATTER m3 | pass | 0.2/0.2/0.0 | 5 | 34..123 s (21/21/21) |
| cruise_quiet_s1 | 22.2 (m3) | 63 | 1.25e-03 | CHATTER m0,m1,m2,m3 | pass | 1.9/1.9/0.8 | 5 | 34..85 s (21/21/21) |
| cruise_quiet_s2 | 88.8 (m2) | 1402 | 6.76e-04 | CHATTER m1,m2,m3 | pass | 2.2/2.3/0.8 | 5 | 34..86 s (21/21/21) |
| cruise_quiet_s3 | 22.2 (m1) | 41 | 8.64e-04 | CHATTER m0,m1,m3 | pass | 2.1/2.0/0.8 | 5 | 34..85 s (21/21/21) |
| cruise_typ_s1 | 22.2 (m2) | 543 | 2.09e-03 | CHATTER m0,m1,m2,m3 | pass | 2.2/2.9/1.1 | 5 | 34..85 s (21/21/21) |
| cruise_typ_s2 | 22.2 (m3) | 630 | 3.21e-03 | CHATTER m0,m1,m2,m3 | pass | 2.1/2.0/0.8 | 5 | 34..85 s (21/21/21) |
| cruise_typ_s3 | 20.5 (m2) | 33 | 2.23e-03 | CHATTER m0,m1,m2,m3 | pass | 2.0/1.9/0.8 | 5 | 34..85 s (21/21/21) |
| cruise_harsh_s1 | 22.0 (m2) | 276 | 4.25e-03 | CHATTER m0,m1,m2,m3 | pass | 5.0/4.9/1.4 | 5 | 34..85 s (21/21/21) |
| cruise_harsh_s2 | 22.5 (m3) | 258 | 2.28e-03 | CHATTER m0,m1,m2,m3 | pass | 4.7/5.0/1.3 | 5 | 34..85 s (21/21/21) |
| cruise_harsh_s3 | 22.5 (m2) | 136 | 2.86e-03 | CHATTER m0,m1,m2,m3 | pass | 4.9/4.9/1.2 | 5 | 34..85 s (21/21/21) |

## Summary
- Chatter flagged (sustained): 16 of 18 runs at least one motor (all except hover_quiet_s3, hover_harsh_s1). hover_quiet_s3 peak RMS 1.4e-4 (below the step). hover_harsh_s1 has flagged windows (ratio 320, RMS 2.1e-3) but never 3 consecutive within 10 %.
- Item 2: 0 of 18 flagged (all pass); max flagged-window rms 5.0 deg/s (cruise_harsh).
- The dominant line is ~22 Hz with RMS 1e-3 to 4e-3 (2-9 DShot steps), not the 70 Hz of the earlier harsh result. Q14 A removes only the quiet-hover-s3 case, so the rule does not rescue most runs; the 22 Hz line is real in command amplitude over the airborne span (takeoff + hold + landing, not only the hold).

## Unverified / caveats
- Chatter span is the airborne span (takeoff and landing included), not the hold only; a 22 Hz line may come from transitions. Not split here.
- Cruise item 2 values 4.7-5.0 dps sit at the 5 dps floor edge for p/q (not flagged because not sustained).
- Skipped-window count (21 of ~85-90 per axis) is large because there are 5 nav_state changes per log, several in takeoff/landing; the three hover-hold windows are probably not skipped but this was not itemised.
- Key1 not compared (by instruction).

## Test / break-check log
Tests: `bench/tests/test_g3_checks_key2_q14_q15.py` (4 tests). Break checks run once each by monkeypatching constants:
- normal: 4/4 pass.
- DSHOT_STEP=0 -> test_substep_line_not_chatter FAILS (others pass).
- NAV_SKIP_S=0 -> test_burst_after_nav_change_skipped FAILS (others pass).
- Existing `python3 bench/g3_checks_key2.py --self-test`: still all PASS.

## Commands
```
python3 indi_flight/bench/tests/test_g3_checks_key2_q14_q15.py   # needs pytest; tests were run via a direct-call harness (pytest absent on host)
indi_project/docker/run.sh -n g4k2 -t 900 -- python3 -I indi_flight/results/g4_gate_s169/rescore_key2_s175.py > indi_flight/results/g4_gate_s169/_tbl.txt
```

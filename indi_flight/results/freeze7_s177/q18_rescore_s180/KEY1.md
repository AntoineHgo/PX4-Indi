# Q18 A re-score, key 1 (S180): command chatter with the touchdown skip

Script `indi_flight/bench/g4_chatter_skip_key1.py` (key-1 detector `g3_checks.line_detector` unmodified: 20-100 Hz, 4 s Hann windows, hop 1 s,
peak > 20 x median, line RMS peak +-2 Hz >= 5e-4, sustained = >= 3 consecutive windows, any of the 4 motors). New: a window overlapping
[ground_contact - 1 s, landed + 1 s] is skipped (counts as unflagged). ground_contact = last 0->1 edge of vehicle_land_detected.ground_contact
(= rise of the final descent), landed = next 0->1 edge of .landed. Every one of the 23 logs has exactly one such rise (no flight without landing;
a flight with none would skip nothing). Self-test `indi_flight/bench/tests/test_g4_chatter_skip_key1.py`: ok; with `G4_SKIP_DISABLE=1` it fails
(edge assert, and the land-window-only 20 Hz line then flags: verified on a copy without the edge asserts). Docker, repo root:
```
indi_project/docker/run.sh -n k1t -t 600 -- python3 indi_flight/bench/tests/test_g4_chatter_skip_key1.py
indi_project/docker/run.sh -n k1s -t 900 -- sh -c "python3 indi_flight/bench/g4_chatter_skip_key1.py [--extend] indi_flight/results/freeze7_s177/q18_rescore_s180/key1_indi_18_<gate|ext>.md <18 run dirs freeze7_s177/g4/*>"
(same for the 5 PID dirs -> key1_pid_<gate|ext>.md);  helpers: landtimes_probe.py (edge times), lines_probe.py (sustained line start times)
```

## Main finding: the skip changes no verdict as the gate scores it
The gate's key-1 detector span is the airborne span h > 1.0 m (`g3_checks.evaluate`, ta..te). It ends 1.5-2 s BEFORE ground_contact
(e.g. hover_harsh_s1 te 102.72, ground_contact 104.53, skip start 103.53), so no 4 s window of that span overlaps the land window
(skipped windows 0 on all 18 + 5 runs). The touchdown windows seen in S176/S179 (66-72 s) exist only when the detector runs over the whole log
(chatter_cruise_s176.py: tm[0]..tm[-1]). I therefore give two tables: GATE span (verdict as scored) and EXTENDED span (te = last actuator_motors
sample; the skip is active there, 6-7 windows skipped per run). Verdict columns: after skip / without skip.

### hover_harsh_s1 20.0 Hz flag: NOT in the land window (refuted)
Sustained line (3 windows, all 4 motors) 20.0 Hz, first window start 12.5 s, i.e. windows 12.5-16.5, 13.5-17.5, 14.5-18.5 (flagged span 11.5-18.5,
RMS up to 9.7e-4): the take-off/LOITER phase (OFFBOARD at about 29 s), ~85 s before ground_contact 104.53 / landed 105.22 (skip interval 103.53-106.22).
The same 20-23 Hz take-off line (windows 11.5-17.5) appears in hover_harsh_s2/s3 and cruise_harsh_s1-3 but only in s1 does it reach 3 consecutive
windows at one frequency. Flags at 94.5-99.5 s (AUTO_LAND descent, 20-22.8 Hz, 8.7e-4) are before the skip interval, only 1-2 windows, not sustained.
So Q18 A does not clear hover_harsh_s1: hover 1/9 remains FAIL with the skip.

## Per-run table, GATE span (verdict as scored; chatter after skip / no skip identical)
| run | airborne | gc / landed | skip interval | chatter after skip | chatter no skip | worst non-skipped line (Hz, ratio, RMS, window) |
| --- | --- | --- | --- | --- | --- | --- |
| hover_quiet_s1 | 11.7-102.3 | 104.05 / 104.74 | 103.05-105.74 (0/87 win) | no | no | 39.0 Hz, x350, 2.29e-04, win 94.7-98.7 (m3) |
| hover_quiet_s2 | 11.5-103.1 | 104.85 / 105.52 | 103.85-106.52 (0/88 win) | no | no | 39.0 Hz, x295, 2.21e-04, win 95.5-99.5 (m2) |
| hover_quiet_s3 | 11.6-102.3 | 104.07 / 104.74 | 103.07-105.74 (0/87 win) | no | no | 39.0 Hz, x302, 2.26e-04, win 94.6-98.6 (m1) |
| hover_typ_s1 | 11.6-103.0 | 104.83 / 105.51 | 103.83-106.51 (0/88 win) | no | no | 22.5 Hz, x369, 2.69e-04, win 11.6-15.6 (m3) |
| hover_typ_s2 | 11.4-102.1 | 103.83 / 104.52 | 102.83-105.52 (0/87 win) | no | no | 22.5 Hz, x262, 2.76e-04, win 11.4-15.4 (m0) |
| hover_typ_s3 | 12.4-103.2 | 104.96 / 105.64 | 103.96-106.64 (0/87 win) | no | no | 22.5 Hz, x207, 2.59e-04, win 12.4-16.4 (m3) |
| hover_harsh_s1 | 11.5-102.7 | 104.53 / 105.22 | 103.53-106.22 (0/88 win) | CHATTER | CHATTER | 20.0 Hz, x1715, 9.65e-04, win 14.5-18.5 (m0) |
| hover_harsh_s2 | 11.5-102.4 | 104.23 / 104.91 | 103.23-105.91 (0/87 win) | no | no | 20.0 Hz, x612, 9.17e-04, win 13.5-17.5 (m2) |
| hover_harsh_s3 | 11.5-102.6 | 104.38 / 105.06 | 103.38-106.06 (0/88 win) | no | no | 20.0 Hz, x1021, 8.98e-04, win 13.5-17.5 (m3) |
| cruise_quiet_s1 | 11.7-65.7 | 67.56 / 68.24 | 66.56-69.24 (0/51 win) | CHATTER | CHATTER | 33.3 Hz, x7563, 1.47e-03, win 37.7-41.7 (m1) |
| cruise_quiet_s2 | 11.7-65.6 | 67.43 / 68.12 | 66.43-69.12 (0/50 win) | CHATTER | CHATTER | 33.3 Hz, x1976, 1.41e-03, win 41.7-45.7 (m3) |
| cruise_quiet_s3 | 11.9-65.9 | 67.73 / 68.41 | 66.73-69.41 (0/50 win) | CHATTER | CHATTER | 33.3 Hz, x3730, 1.46e-03, win 37.9-41.9 (m1) |
| cruise_typ_s1 | 11.9-66.4 | 68.14 / 68.81 | 67.14-69.81 (0/51 win) | CHATTER | CHATTER | 33.3 Hz, x2366, 1.47e-03, win 38.9-42.9 (m1) |
| cruise_typ_s2 | 11.4-65.4 | 67.17 / 67.84 | 66.17-68.84 (0/50 win) | CHATTER | CHATTER | 33.3 Hz, x2860, 1.51e-03, win 37.4-41.4 (m1) |
| cruise_typ_s3 | 11.9-65.7 | 67.54 / 68.23 | 66.54-69.23 (0/50 win) | CHATTER | CHATTER | 33.0 Hz, x470, 1.45e-03, win 44.9-48.9 (m1) |
| cruise_harsh_s1 | 11.4-65.6 | 67.44 / 68.12 | 66.44-69.12 (0/51 win) | CHATTER | CHATTER | 33.3 Hz, x1018, 1.41e-03, win 44.4-48.4 (m1) |
| cruise_harsh_s2 | 11.6-65.7 | 67.53 / 68.20 | 66.53-69.20 (0/51 win) | CHATTER | CHATTER | 33.5 Hz, x758, 1.47e-03, win 37.6-41.6 (m1) |
| cruise_harsh_s3 | 11.6-66.0 | 67.76 / 68.45 | 66.76-69.45 (0/51 win) | CHATTER | CHATTER | 33.3 Hz, x965, 1.42e-03, win 44.6-48.6 (m1) |
(18 runs; hover 8/9 no chatter, hover_harsh_s1 CHATTER; cruise 9/9 CHATTER; the cruise line is 33.0-33.5 Hz through the lemniscate (35-53 s), flagged
spans 34.4-52.9 s, 6.4e-4 to 1.5e-3, ratio up to x7563; the "worst non-skipped line" column gives the line with the largest RMS among ratio > 20 windows
even when it is below 5e-4 or not sustained. Land-window values are not computed here: nothing is skipped.)
Flagged non-skipped windows per run (spans of flagged windows, any motor): hover_harsh_s1 11.5-18.5 + 94.5-99.5; hover_harsh_s2 11.5-17.5 + 94.5-99.5;
hover_harsh_s3 11.5-17.5 + 94.5-99.5; cruise_*: 34.4-52.9 (33 Hz) + (harsh) 11.4-18.4 take-off and 57.4-62.4 hold-end/early land-cmd spans; full list in key1_indi_18_ext.md.

## Per-run table, EXTENDED span (detector runs to the last motor sample; skip active)
Columns: run | detector span | ground_contact / landed | skip interval (skipped / total windows) | chatter after skip | chatter without skip | worst non-skipped line | flagged non-skipped spans | worst SKIPPED land-window line (Hz, ratio, line RMS, window).
| run | airborne | gc / landed | skip interval | chatter after skip | chatter no skip | worst non-skipped line (Hz, ratio, RMS, window) | flagged non-skipped windows | skipped land-window worst line (Hz, ratio, RMS, window) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hover_quiet_s1 | 11.7-109.2 | 104.05 / 104.74 | 103.05-105.74 (6/94 win) | no | CHATTER | 39.0 Hz, x350, 2.29e-04, win 94.7-98.7 (m3) | 0 | 20.0 Hz, x31, 2.92e-03, win 101.7-105.7 (m1) |
| hover_quiet_s2 | 11.5-109.9 | 104.85 / 105.52 | 103.85-106.52 (6/95 win) | no | no | 39.0 Hz, x295, 2.21e-04, win 95.5-99.5 (m2) | 0 | 20.5 Hz, x36, 1.90e-03, win 103.5-107.5 (m1) |
| hover_quiet_s3 | 11.6-109.2 | 104.07 / 104.74 | 103.07-105.74 (6/94 win) | no | CHATTER | 39.0 Hz, x302, 2.26e-04, win 94.6-98.6 (m1) | 0 | 21.0 Hz, x27, 2.44e-03, win 101.6-105.6 (m1) |
| hover_typ_s1 | 11.6-109.9 | 104.83 / 105.51 | 103.83-106.51 (6/95 win) | no | no | 22.5 Hz, x369, 2.69e-04, win 11.6-15.6 (m3) | 0 | 20.0 Hz, x33, 1.69e-03, win 103.6-107.6 (m3) |
| hover_typ_s2 | 11.4-109.0 | 103.83 / 104.52 | 102.83-105.52 (6/94 win) | no | no | 22.5 Hz, x262, 2.76e-04, win 11.4-15.4 (m0) | 0 | 22.0 Hz, x24, 1.33e-03, win 102.4-106.4 (m2) |
| hover_typ_s3 | 12.4-110.1 | 104.96 / 105.64 | 103.96-106.64 (6/94 win) | no | no | 22.5 Hz, x207, 2.59e-04, win 12.4-16.4 (m3) | 0 | 20.3 Hz, x26, 1.21e-03, win 104.4-108.4 (m1) |
| hover_harsh_s1 | 11.5-110.3 | 104.53 / 105.22 | 103.53-106.22 (6/95 win) | CHATTER | CHATTER | 20.0 Hz, x1715, 9.65e-04, win 14.5-18.5 (m0) | 11.5-18.5 (20.0-22.8 Hz, 9.7e-04); 94.5-99.5 (20.0-22.8 Hz, 8.7e-04) | 23.5 Hz, x21, 1.96e-03, win 102.5-106.5 (m2) |
| hover_harsh_s2 | 11.5-109.0 | 104.23 / 104.91 | 103.23-105.91 (6/94 win) | no | CHATTER | 20.0 Hz, x612, 9.17e-04, win 13.5-17.5 (m2) | 11.5-17.5 (20.0-23.0 Hz, 9.2e-04); 94.5-99.5 (21.5-89.5 Hz, 6.5e-04) | 21.3 Hz, x46, 1.98e-03, win 102.5-106.5 (m0) |
| hover_harsh_s3 | 11.5-110.1 | 104.38 / 105.06 | 103.38-106.06 (7/95 win) | no | no | 20.0 Hz, x1021, 8.98e-04, win 13.5-17.5 (m3) | 11.5-17.5 (20.0-23.0 Hz, 9.0e-04); 94.5-99.5 (20.3-22.3 Hz, 7.6e-04) | 20.0 Hz, x20, 2.51e-03, win 102.5-106.5 (m1) |
| cruise_quiet_s1 | 11.7-72.4 | 67.56 / 68.24 | 66.56-69.24 (6/57 win) | CHATTER | CHATTER | 33.3 Hz, x7563, 1.47e-03, win 37.7-41.7 (m1) | 35.7-52.7 (22.0-89.3 Hz, 1.5e-03) | 20.3 Hz, x28, 2.11e-03, win 65.7-69.7 (m3) |
| cruise_quiet_s2 | 11.7-72.4 | 67.43 / 68.12 | 66.43-69.12 (6/57 win) | CHATTER | CHATTER | 33.3 Hz, x1976, 1.41e-03, win 41.7-45.7 (m3) | 35.7-51.7 (22.0-89.3 Hz, 1.4e-03) | 20.3 Hz, x25, 2.67e-03, win 65.7-69.7 (m0) |
| cruise_quiet_s3 | 11.9-72.6 | 67.73 / 68.41 | 66.73-69.41 (6/57 win) | CHATTER | CHATTER | 33.3 Hz, x3730, 1.46e-03, win 37.9-41.9 (m1) | 35.9-52.9 (33.0-89.3 Hz, 1.5e-03) | 20.3 Hz, x34, 1.99e-03, win 65.9-69.9 (m1) |
| cruise_typ_s1 | 11.9-73.1 | 68.14 / 68.81 | 67.14-69.81 (6/58 win) | CHATTER | CHATTER | 33.3 Hz, x2366, 1.47e-03, win 38.9-42.9 (m1) | 35.9-52.9 (33.0-89.3 Hz, 1.5e-03) | 20.3 Hz, x21, 2.11e-03, win 65.9-69.9 (m3) |
| cruise_typ_s2 | 11.4-72.0 | 67.17 / 67.84 | 66.17-68.84 (6/57 win) | CHATTER | CHATTER | 33.3 Hz, x2860, 1.51e-03, win 37.4-41.4 (m1) | 34.4-52.4 (22.3-89.3 Hz, 1.5e-03) | 20.3 Hz, x24, 2.22e-03, win 65.4-69.4 (m0) |
| cruise_typ_s3 | 11.9-72.5 | 67.54 / 68.23 | 66.54-69.23 (6/57 win) | CHATTER | CHATTER | 33.0 Hz, x470, 1.45e-03, win 44.9-48.9 (m1) | 34.9-52.9 (22.0-89.3 Hz, 1.4e-03) | 20.0 Hz, x25, 1.34e-03, win 66.9-70.9 (m1) |
| cruise_harsh_s1 | 11.4-73.0 | 67.44 / 68.12 | 66.44-69.12 (6/58 win) | CHATTER | CHATTER | 33.3 Hz, x1018, 1.41e-03, win 44.4-48.4 (m1) | 11.4-18.4 (20.0-23.0 Hz, 9.8e-04); 34.4-52.4 (22.3-89.3 Hz, 1.4e-03); 57.4-62.4 (21.3-88.3 Hz, 6.2e-04) | 20.3 Hz, x43, 2.43e-03, win 65.4-69.4 (m2) |
| cruise_harsh_s2 | 11.6-73.1 | 67.53 / 68.20 | 66.53-69.20 (7/58 win) | CHATTER | CHATTER | 33.5 Hz, x758, 1.47e-03, win 37.6-41.6 (m1) | 11.6-17.6 (20.0-23.0 Hz, 9.1e-04); 35.6-52.6 (22.0-89.3 Hz, 1.5e-03); 57.6-62.6 (22.0-89.5 Hz, 5.9e-04) | 20.0 Hz, x36, 4.71e-03, win 65.6-69.6 (m1) |
| cruise_harsh_s3 | 11.6-73.3 | 67.76 / 68.45 | 66.76-69.45 (6/58 win) | CHATTER | CHATTER | 33.3 Hz, x965, 1.42e-03, win 44.6-48.6 (m1) | 11.6-17.6 (20.0-23.0 Hz, 8.7e-04); 35.6-52.6 (22.3-89.0 Hz, 1.4e-03); 57.6-63.6 (20.5-89.5 Hz, 7.0e-04) | 23.3 Hz, x21, 2.16e-03, win 65.6-69.6 (m3) |
Without the skip, three hover runs (hover_quiet_s1, hover_quiet_s3, hover_harsh_s2) would be sustained-flagged by the touchdown windows when the span is extended;
with the skip they are clear. In the gate span they were never flagged. Skipped land-window lines: 20-23.5 Hz, RMS 1.2e-3 to 2.9e-3 (hover), 1.3e-3 to 4.7e-3 (cruise).

## PID land-window values (same script; 5 PID runs: g4_gate_s169/pid_hover_typ_s1, pid_cruise_typ_s1, a54_s169/pid_hover_harsh_s1, a56_pid_s173/pid_hover_harsh_s2/s3)
GATE span: all 5 no chatter, skipped windows 0, worst line 4.98e-4 (pid_hover_harsh_s1, x20, 21.0 Hz, below 5e-4 and not > 20x), others <= 4.5e-4. EXTENDED span:
| run | airborne | gc / landed | skip interval | chatter after skip | chatter no skip | worst non-skipped line (Hz, ratio, RMS, window) | flagged non-skipped windows | skipped land-window worst line (Hz, ratio, RMS, window) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pid_hover_typ_s1 | 13.6-110.6 | 105.50 / 106.19 | 104.50-107.19 (7/94 win) | no | no | 22.3 Hz, x746, 2.32e-04, win 13.6-17.6 (m3) | 0 | 20.0 Hz, x25, 1.13e-03, win 103.6-107.6 (m3) |
| pid_cruise_typ_s1 | 13.6-73.4 | 68.44 / 69.14 | 67.44-70.14 (6/56 win) | no | no | 89.3 Hz, x993, 4.19e-04, win 43.6-47.6 (m2) | 0 | 26.0 Hz, x33, 1.17e-03, win 66.6-70.6 (m3) |
| pid_hover_harsh_s1 | 15.5-112.3 | 107.39 / 108.09 | 106.39-109.09 (6/93 win) | no | no | 21.0 Hz, x20, 4.98e-04, win 22.5-26.5 (m0) | 0 | 21.5 Hz, x34, 1.46e-03, win 105.5-109.5 (m1) |
| pid_hover_harsh_s2 | 13.4-110.3 | 105.42 / 106.12 | 104.42-107.12 (6/93 win) | no | no | 22.3 Hz, x2045, 4.52e-04, win 13.4-17.4 (m3) | 0 | 20.0 Hz, x25, 1.17e-03, win 103.4-107.4 (m3) |
| pid_hover_harsh_s3 | 13.4-111.0 | 106.11 / 106.81 | 105.11-107.81 (6/94 win) | no | no | 22.3 Hz, x1258, 3.68e-04, win 13.4-17.4 (m2) | 0 | 21.5 Hz, x27, 1.07e-03, win 104.4-108.4 (m3) |
PID land window: 20.0-26.0 Hz, ratio x25-x34, line RMS 1.07e-3 to 1.46e-3 (INDI 1.2e-3 to 4.7e-3; INDI hover typ about 1.2-1.7e-3 comparable to PID 1.1-1.5e-3, INDI cruise/harsh 2-5e-3). PID verdict no chatter (as gate and extended, with and without skip).
Caveat: 5 PID runs only (typ hover/cruise seed 1, harsh hover 1-3, stock params, no PID cruise_quiet/harsh), different take-off timing than INDI.

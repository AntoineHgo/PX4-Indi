# G3 item 2 / item 3 breakdown, key1 (S186)

Source: `results/g3_excursion_s186/key1/run_*.json` (and `run_017_pid.json`), produced by `bench/g3_checks.py`.
Chatter RMS = `max_rms_ratio_flagged` per motor (rate RMS in deg/s for p/q/r). Item 3 limits: horizontal RMS 0.15 m calm / 0.30 m wind, altitude |mean| 0.10 m calm / 0.20 m sag, roll/pitch mean 1.0 deg (attitude mode only).

| run | mode / wind / sag | item2 sustained | item2 detail | item3 | item3 fail (value vs limit) |
|---|---|---|---|---|---|
| 000 | pos / wind / sag | chatter | M0-M3 78.0, 78.0, 77.5, 77.5 Hz; RMS 1.04-1.05e-3 | PASS | none |
| 001 | pos / wind | chatter | M0-M3 77.5-78.0 Hz (two lines on M0-M3); RMS 0.93-1.10e-3 | PASS | none |
| 002 | pos / wind / sag | chatter | M0-M3 77.5-78.0 Hz plus 88.75-89.0 Hz lines; RMS 0.95-1.04e-3 | FAIL | horiz 0.692 > 0.30 |
| 003 | pos / wind | p, q, r | p 3.25 Hz (19 fw, RMS 51.8); q 2.0 Hz (52 fw, RMS 286); r 2.0 Hz (21 fw, RMS 131) deg/s | FAIL | horiz 0.450 > 0.30; alt -0.273 (abs > 0.10) |
| 004 | att / no wind / no sag | none | p, q, r, chatter all ok | PASS | none |
| 005 | pos / wind / sag | chatter | M0-M3 77.5-89.0 Hz; RMS 0.99-1.11e-3 | FAIL | horiz 0.603 > 0.30 |
| 006 | pos / wind / sag | chatter | M0-M3 77.5-78.0 Hz; RMS 1.24-1.27e-3 | PASS | none |
| 007 | pos / wind | p, q, r | p 4.0 Hz (11 fw, RMS 37.1); q 2.0 Hz (32 fw, RMS 239); r 2.0 Hz (16 fw, RMS 75.6) deg/s | FAIL | alt -0.102 (abs > 0.10) |
| 008 | pos / wind / sag | q, chatter | q 10.75 Hz (14 fw, RMS 8.6 deg/s); M0-M3 77.5 Hz, RMS 1.39-1.48e-3 | PASS | none |
| 009 | pos / wind / sag | chatter | M0-M3 77.5 Hz; RMS 0.86-0.93e-3 | FAIL | horiz 0.344 > 0.30 |
| 010 | att / no wind / no sag | chatter | M0-M3 50.25 Hz (11 fw); RMS 0.716-0.719e-3 | PASS | none |
| 011 | pos / wind / sag | none | all ok | PASS | none |
| 012 | pos / wind | none | all ok | PASS | none |
| 013 | pos / wind / sag | p, q, r, chatter | p 2.0 Hz (51 fw, RMS 203); q 2.25 Hz (18 fw, RMS 10.9); r 2.25/2.0 Hz (15 fw, RMS 22.4) deg/s; M0-M3 77.5-78.0 Hz, RMS 0.67-0.72e-3 | PASS | none |
| 014 | pos / wind / sag | chatter | M0-M3 77.5-78.0 Hz; RMS 0.83-0.86e-3 | PASS | none |
| 015 | pos / wind / sag | chatter | M0-M3 77.5-78.0 Hz; RMS 1.03-1.06e-3 | PASS | none |
| 016 | att / no wind / no sag | none | all ok | PASS | none |
| 017 | pos / wind | p, q, r, chatter | p 3.25/2.0 Hz (23 fw, RMS 363); q 2.0/5.0 Hz (60 fw, RMS 698); r 2.0 Hz (22 fw, RMS 139) deg/s; M1 90.25/22.5 Hz (RMS 0.0176), M2 21.0 Hz (RMS 0.0264), M3 90.25/22.5 Hz (RMS 0.0355) | FAIL | horiz 0.481 > 0.30; alt -0.218 (abs > 0.10) |
| 017_pid | pos / wind | p, q | p 2.75/3.25/3.0 Hz (31 fw, RMS 18); q 2.5/2.75 Hz (32 fw, RMS 28.8) deg/s | PASS | none |
| 018 | pos / wind / sag | chatter | M0-M3 77.5-78.0 Hz; RMS 1.96-2.10e-3 | PASS | none |
| 019 | pos / wind | chatter | M0-M3 77.5-78.0 Hz; RMS 0.83-0.84e-3 | PASS | none |

Notes: fw = flagged windows (all, including unsustained). Item 1 (LOC) fails only in run_017 (`item1_loc.pass` false); it is outside this table. Per-motor values are listed as ranges where they differ.

Provenance: the JSONs were produced by the current checker. All 21 files have `max_rms_ratio_flagged` (Q14 field), chatter lines are 3-tuples, chatter flagged RMS is at least 6.7e-4 (consistent with the 5e-4 gate), `.json` and `.txt` are byte-identical, and `bench/g3_checks.py` (mtime 18:37:13) predates all outputs (18:37:58 to 18:38:48). The ±2 Hz integration width cannot be checked from the JSON alone; the working tree currently matches HEAD (debe458b1d).

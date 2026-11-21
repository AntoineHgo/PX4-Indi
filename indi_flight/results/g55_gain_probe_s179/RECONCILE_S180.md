# S180 reconcile: G4 chatter L1 (88.5 vs 33.5 Hz) and item 3 z offset (probe read, not gate evidence)
Scripts (Docker, repo root, existing key code imported unmodified): `reconcile_s180.py` (task 1), `item3_s180.py` (task 2). Run dir `score/cruise_typ_s1` (GP, XY_P 1.2). Item 3 JSONs in `pid_ref_s180/`. No flight was needed (PID run existed).

## Task 1: 88.5 Hz vs 33.5 Hz
Same window 36-53.5 s, same signal (actuator_motors control[0..3], 4 motors, per motor), same PSD (4 s Hann, detrend constant, 20-100 Hz band, 0.25 Hz bin, peak/median ratio > 20, line RMS over peak +-2 Hz >= 5e-4). Per window, key 1 (g3_checks.line_detector, 800 Hz uniform grid) and key 2 (psd_windows, 800 Hz np.interp grid) agree to <1 % on peak Hz, ratio (ratio differs 0.2-1.5 %, grid/FFT normalisation) and identical line RMS to 3 digits. Neither bin width, detrending, nor motor choice differs.
The difference is only in what each REPORTS:
- The peak frequency in this window is not stable. The strongest bin hops between about 22 Hz, 33.5 Hz and 88.5-89.25 Hz from one 4 s window to the next (e.g. m0: 33.0, 33.75, 88.75, 88.75, 22.25, 33.5, 88.5, 89.25, 33.5, 33.5, 88.75, 22.25 Hz for t0 = 37..48).
- Key 1 (chatter_cruise_s176 track + chatter_s175.runs_of; hop 0.5 s, strongest-RMS motor per window, a flagged run spanning 36.0-53.5 s) reports the MEDIAN of the per-window peak frequencies over the whole run = 88.5 Hz, and the MAX line RMS over the run = 1.08e-3 (+-2 Hz; +-2 bins 9.5e-4 old).
- Key 2 (chatter(): per motor, whole flight, hop 1 s) reports the peak Hz of the single window with the largest line RMS among flagged windows (per motor; the table shows the motor with max RMS) = m1, window t0 = 46 s, 33.50 Hz, ratio 189, RMS 1.080e-3.
- So the max RMS is the same window in both (m1, t0 46, 33.5 Hz, 1.08e-3; key 1 prints 1.1e-3). 88.5 Hz is a median over hopping lines, 33.5 Hz is the peak of the one largest window. Both numbers are correct descriptions of different statistics. Median definition also differs from the in-window ratio median (band median of the PSD, 20-100 Hz, same in both).
- Whole-flight key 2 reports per motor (f, ratio, RMS): m0 20.0 Hz 25 2.09e-3 (AUTO_LAND, outside the lemniscate), m1 33.5 189 1.08e-3, m2 21.0 Hz 20.06 2.32e-3 (AUTO_LAND), m3 33.5 112 9.7e-4. The overall peak is the AUTO_LAND line (20-21 Hz, 2.3e-3), not 33.5.

Lines flagged as chatter by BOTH keys (sustained = >= 3 consecutive flagged windows, freq within 10 %), window 36-53.5, hop 1 s, identical in both:
- m2, 89.25 Hz: start t0 = 47 (windows 47, 48, 49), RMS 5.62e-4 / 6.71e-4 / 5.46e-4, ratios (key1/key2) 114.0/112.4, 112.6/112.2, 226.1/225.7.
- m3, 33.5 Hz: start t0 = 45 (windows 45, 46, 47), RMS 7.58e-4 / 9.11e-4 / 6.05e-4, ratios 161.3/159.8, 227.8/227.3, 69.6/68.0.
- m0 and m1: flagged in 11 and 12 of 14 windows but the peak frequency hops by more than 10 %, so no line is sustained (neither key).
- Outside the window, both flag AUTO_LAND 67-72 s (about 20 Hz, 2.3e-3) per the score_out (key 1 whole-run detector and key 2).
- Caveat: m2 and m3 are flagged on 5e-4-level RMS, only 1-2x the floor; key1 old +-2 bins RMS (4.0-7.3e-4) would drop several of these windows (key 1 old = 0 sustained in score_out).

## Task 2: item 3 (z offset)
GATES.md section 4 (line 305): item 3 (steady state: horizontal RMS, altitude |mean| <= 0.10 calm / 0.20 sag, roll/pitch in attitude mode) applies to every run (campaign proposes 70 % position mode, 20 % attitude, 10 % rate; rate runs use item 6 in place). In the G4 (g3_checks) rescore it is evaluated on all 18 runs, position mode, window = last 10 s of the `hold` event (hover) or of the `traj` event (cruise).
Values (altitude mean m / horizontal RMS m), same keyed script (g3_checks.py --skip-nav-change, window from run.json):
| run | freeze-7 INDI | GP INDI (XY_P 1.2) | PID reference |
|---|---|---|---|
| cruise_typ_s1 | 0.129 / 0.036 FAIL (window 66.1-76.1) | 0.290 / 0.021 FAIL (65.3-75.3) | 0.295 / 0.050 FAIL (65.4-75.4) |
Freeze-7 all runs (alt / horiz): hover 9 runs alt -0.038..0.096, horiz 0.007-0.070, all PASS; cruise (9 runs): alt 0.093 (typ_s2 PASS), 0.101, 0.127, 0.129, 0.163, 0.191, 0.195, 0.198, 0.198, 8 of 9 FAIL, horiz 0.013-0.058.
Cause visible in the data (not INDI): in every cruise run the cruise window (about 65-76 s log time) is AFTER the AUTO_LAND command (nav_state 18 at 60.3-60.5 s) and lands at about 70-71 s: truth height 4.9 m at 60 s, about 2.0 m at 65 s, 0 at 70 s; window mean height 0.14 to 0.34 m. The `traj` event times are on the runner clock, which is about 20 s ahead of log time (chatter_cruise_s176 computes this offset), and rescore_s175.py uses them as log times. The trajectory is actually 36.0-53.5 s in log time. So item 3 for cruise is scored on the landing descent, and the altitude mean is a function of land timing (GP and PID have nearly identical timing: 0.290 and 0.295).
PID reference: existing run `results/g4_gate_s169/pid_cruise_typ_s1` (seed 1, same scenario) scored; no new flight. PID shows the same offset (0.295 m vs INDI GP 0.290 m), so this is a PX4 / test-window fact, not INDI. Item 3 for the hover rows (window inside the hold) is clean for INDI.
Unverified: whether the PID run's flags equal the INDI cruise scenario flags exactly (profile typ, same 4.0 noise); the 20 s clock offset I took from the script comment and the nav_state times (not re-derived); the freeze-7 g3_checks_s175.json values were read as stored, and the freeze-7 cruise_typ_s1 re-score above gave 0.129 as stored.

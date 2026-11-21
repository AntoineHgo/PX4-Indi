# FREEZE-10 candidate probe (S191): firmware 7fe6206fcc (revert of aa4fd2654a, body-rate feed-forward in every mode, plus D-AF-ALIAS fixes)

Probe list: DECISIONS.md D-OWNER-Q23. Raw evidence committed in 093e578731. One flight per row (s1), serial, scripts fly_a.sh / fly_b.sh / score_g3.sh.

## Build and unit tests
- Build: build.log ends `[15/15] Linking px4` (22:38), after the revert commit (22:37). run.json provenance: binary_commit c0b733e677 (docs commit directly on 7fe6206fcc), dirty False, header_newer_than_binary False. So the source is the candidate; the hash string in the binary is c0b733e677, not 7fe6206fcc.
- Unit tests: unit_test_all.log, 0 FAILED; suites PASSED 60, 15, 4, 4, 6, 6, 6, 6 tests (incl. IndiRateFeedforwardGate 6/6). unit_test.log is only the binary list.

## 1. G5.7 mode_switch10 s1-s3 (key1 checker + key2 checker)
- s1 PASS: max attitude jump 3.53 deg, max thrust step 8.03 % hover, LOC none (limits 5 deg, 20 %). Key1 verdict PASS.
- s2 PASS: jump 3.42 deg, thrust step 1.96 %, LOC none. Key1 PASS.
- s3 PASS: jump 3.61 deg, thrust step 4.55 %, LOC none. Key1 PASS.
- Validity (leaveP speed >= 1.5 at the 4 posctl exits): min 1.97 / 1.97 / 1.96, VALID. Freeze-9: FAIL 3/3, jump 5.8-10.7 deg at hold edges. Now worst 3.61 deg: PASS 3/3.

## 2. G5.4 / G5.3 (auto_land10_typ_s1, auto_tour_typ_s1, auto_tour_harsh_s1)
All three .check.txt: every G5.4 line PASS. G5.3 mission g53 check: PASS on tour_typ and tour_harsh (4/4 waypoints within limit, vmax 5.11 / 5.12 m/s vs 5.5).
- land10_typ: overshoot -0.050 m, bounce 0.200, ramp 7.5 % / edge 4.7 % hover, dip 0.000, td vz 0.694, tilt 0.32 deg, re-lift 0.048, land mean vz 0.705, contact->disarm 2.69 s. Key2 (key2_g54*.txt) agrees (td vz 0.694, edge 4.69 %, mean vz 0.701).
- tour_typ: overshoot -0.082, bounce 0.200, ramp 7.5 / edge 4.6 %, td vz 0.710, tilt 0.23, re-lift 0.049, mean vz 0.701, disarm 2.69 s, RTL err 0.026 m.
- tour_harsh: overshoot -0.102, bounce 0.200, ramp 7.5 / edge 4.6 %, td vz 0.685, tilt 0.50, re-lift 0.050, mean vz 0.705, disarm 2.68 s, RTL err 0.080 m.
- Freeze-9 (G5_SCORES.md, key1, s1-s3 ranges): overshoot -0.010..-0.086, bounce 0.200, ramp/edge 7.5-7.6 / 4.1-4.7 %, td vz 0.685-0.727, tilt 0.21-0.54, re-lift 0.049-0.050, mean vz 0.691-0.707, RTL err 0.010-0.055 m. 10 % rule: outside the freeze-9 range by more than 10 %: tour_harsh RTL err 0.080 m (worst freeze-9 0.055, limit 1 m) and tour_harsh overshoot -0.102 m (worst -0.086, limit 0.5 m); both far inside limits. All others within range. Freeze-9 has no harsh tour row (compared with typ ranges); one flight vs three, not statistical.
- Tracking RMS (xy mission 0.157 typ / 0.154 harsh m) not in freeze-9 G5_SCORES.md: not compared.
- omega_ff peaks (omega_ff_peaks_out.txt, dps, norm; r always 0): takeoff 6.8 (land10) / 5.5 (tour_typ) / 19.5 (tour_harsh); loiter 0.27 / 0.19 / 1.32; mission 34.9 (typ) / 35.2 (harsh); rtl 32.2 / 24.9; land 0.43. Non-zero in every mode, including take-off, loiter, mission.

## 3. G4 cruise_typ_s1 (g4/)
- Rows scored (g4_table.md, GATES typ cruise limits R20 2.25 %, C20 0.009, R4 4 %, clip 0): R20 0.022 % PASS, C20 0.00064 PASS, R4 0.258 % PASS, clip 0.0000 PASS. Freeze-9 cruise_typ s1-s3: R20 0.022, C20 0.00065, R4 0.285 (s3): same.
- Chatter, item 2 (rate oscillation), item 3 (steady state), PID guard: NOT SCORED. key1/key2 Q19 stdout hold only the header; the stderr show the rescore scripts failed (missing g3_checks_q19.json; key2 script looped over runs that were not flown). The rescore scripts live under freeze9_s183/g4 and were not re-run here.
- omega_ff in offboard (omega_ff_peaks_g4_out.txt): non-zero, peak |w| 106.9 dps (q 105.0, p 28.6, r 0), p99 74 dps over 52.0-94.9 s: YES. Freeze-9 G4_SCORES.md has no omega_ff figure.

## 4. G3 draws 02 and 05, matched GNSS compensation (g3_matched/)
| draw | key1 item 1 / 2 / 3 | key2 item 1 / 2 / 3 | key1 / key2 verdict |
|---|---|---|---|
| 02 | pass / pass (no line; p 1 flagged window, q 0) / pass (horiz RMS 0.133 m, alt -0.035) | pass / pass (max rms p/q/r 2.7/3.7/1.2 dps, none sustained) / pass (0.133 m) | pass / pass |
| 05 | pass / pass (no flagged window) / pass (horiz RMS 0.108 m, alt -0.047) | pass / pass (max rms 2.8/2.6/0.9 dps) / pass (0.108 m) | pass / pass |
- S190 unmatched (g3_pretest_s190 README.md): 02 key1 FAIL i3 (0.54 m), key2 FAIL i2 + i3; 05 FAIL i2 + i3 (0.50 m) on both keys, item 2 line detector reading 2.0 Hz.
- q line at 1.45 Hz, 50-58 s (q145_trace.txt, g3_line_trace_s191.py, LS fit): 02 1.83 dps, 05 0.71 dps, against S191 unmatched 12.2 / 8.5 dps (x0.15, x0.08). The scan's strongest line is now 1.0 Hz (2.6 / 1.1 dps), not 1.45 Hz. Pitch setpoint at 1.45 Hz 0.08 / 0.12 deg (unmatched 1.48 / 1.05).
- Item 1: tilt max 43.4 / 43.0 deg, excursion 0.72 / 0.67 m, no ground contact (as unmatched, passes).

## Overall
- Do all D-OWNER-Q23 probe checks pass? NO for completeness: every scored check passes (G5.7 3/3, G5.4 3/3, G5.3 2/2, G4 R/C/clip, G3 02/05 both keys), but the G4 chatter / item 2 / item 3 / PID guard rows of cruise_typ_s1 are not scored (scorer failure, see 3), so the G4 verdict is incomplete. No check failed.
- G3 02/05: matched GNSS compensation REMOVES the failure (1.45 Hz accel-loop oscillation 12.2/8.5 -> 1.8/0.7 dps, item 3 0.54/0.50 -> 0.13/0.11 m, items 1-3 pass on both keys). Two draws only; the other S190 failing draws (03, 08, 19) were not re-flown matched.

## G4 rows (S192 re-score)
cruise_typ_s1 only, existing freeze-9 scripts, unchanged (key1 `freeze9_s183/g4/rescore_key1_q19.py` via sed on the path; key2 `rescore_key2_q19.py` via sed restricting its loops to cruise/typ/s1; `guard_q19.py`; `bench/g4_guard_q20_key{1,2}.py`; `g4_gate_s169/chatter_cruise_s176.py` with RAW=g4/chatter_cruise_raw.txt, tracked file stays clean). Outputs in g4/: key1_q19_stdout.txt, key2_q19_stdout.txt, guard_indi.jsonl, guard_q20_key{1,2}_stdout.txt, chatter_stdout.txt. Scipy was missing on the host (scripts need it, normally run in docker); it was installed outside the repo (scratchpad, v1.18.1) and used via PYTHONPATH, no docker. Limits per freeze9_s183/G4_SCORES.md.

| row | limit | this probe | freeze-9 cruise_typ_s1 | verdict |
|---|---|---|---|---|
| chatter key 1 (line RMS >= 5e-4 and ratio > 20, sustained, Q19 skip) | no sustained chatter | no; max line RMS (ratio>20) 4.11e-04 | no; 4.11e-04 | PASS |
| chatter key 2 | no sustained chatter | no; line RMS 3.97e-04 (peak 89.2 Hz m0, ratio 1031) | no; 4.10e-04 | PASS |
| item 1 (LOC) | pass | PASS | PASS | PASS |
| item 2 key 1 (rate oscillation, p/q/r sustained) | none sustained | PASS (-/-/-, 19/19/19 skipped windows) | PASS (-/-/-, 20/20/20) | PASS |
| item 2 key 2 | none sustained | pass (max rms 2.2/2.3/0.8 dps; freeze-9 4.5/4.0/1.2 key1/key2 max for p/q/r) | pass (4.5/4.0/1.2) | PASS |
| item 3 steady state | xy RMS <= 0.15 m, mean abs dz <= 0.1 m | xy RMS 0.021 m PASS; mean dz 0.168 m (key1 value, abs) FAIL | xy 0.039 m; dz +0.098 m PASS | FAIL |
| Q20 PID guard key 1 / key 2 | INDI line RMS not above PID at same transition (only where flagged and PID ref exists) | 0 checked (no INDI flagged window; max narrow RMS 1.61e-04 at 17->4#1; no PID typ ref) | 0 checked (same, no PID typ ref) | not applicable (no checked transition, 0 FAIL) |
| Q19 guard (guard_q19.py) | flagged = ratio > 20 and RMS >= 5e-4 | no flagged transition (max any 1.87e-04 at 17->4#1) | n/a, freeze-9 typ not compared (no PID typ ref) | no flag |

Note: item 3 altitude FAIL (0.168 m vs 0.1 m) is the only failing G4 row; freeze-9 failed the same row on cruise_typ_s2 (0.147 m) and on every harsh cruise run (0.17-0.22 m), so this probe's value is in the freeze-9 spread but above its s1.

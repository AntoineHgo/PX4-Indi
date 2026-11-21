# G4 chatter, cruise (traj_lemniscate), S176: localisation and PID reference

Commands (repo root):
- `RAW=indi_flight/results/g4_gate_s169/chatter_cruise_s176_raw.txt indi_project/docker/run.sh -n chatc -t 900 -- python3 indi_flight/results/g4_gate_s169/chatter_cruise_s176.py indi_flight/results/g4_gate_s169/cruise_*_s? indi_flight/results/g4_gate_s169/pid_cruise_typ_s1`
  (new wrapper, imports `chatter_s175.py` and `bench/g3_checks*.py` unmodified; same Q14 flag, 4 s Hann, hop 0.5 s, 20-100 Hz, ratio>20, line RMS >= 5e-4, any motor; key1 line RMS at +-2 Hz, old +-2 bins also in raw).
- PID flight: `indi_project/docker/run.sh -n chatpc -t 900 -- python3 indi_flight/bench/run_scenario.py --controller pid --model quad5in --seed 1 --speed 4 --sim v2 --gps-dly 110 --gnss-delay 110 --scenario traj_lemniscate --vib-acc 10 --vib-gyr 0 --imu-noise-scale 4.0 --out indi_flight/results/g4_gate_s169/pid_cruise_typ_s1` (rc 0, flight.ulg present, stock params; INDI used the freeze params).
- Times are log time. run.json event times are on the runner clock, log = runner - 22..23.4 s (matched at OFFBOARD entry, +-0.3 s). Phases (all INDI runs): TAKEOFF ~7-8 to 14-15, LOITER to ~29, OFFBOARD hold to traj start ~35, trajectory 35-52.3 (3 s ramp, 2 laps of a 4x2 m lemniscate), 3 s hold to ~55, AUTO_LAND ~59.4 (quiet_s2 60.6) to touchdown ~70-71.
- Flagged-window phase counts use window centre, fixed +-2 Hz flag. The trajectory is never at constant velocity (mean |dv/dt| 1.7-1.9 m/s2), so "steady cruise" cannot be separated from turns; the line is flagged in 24-26 of 28 trajectory windows, i.e. continuously, and 0 of 12 in the OFFBOARD hover hold before it and 0 of 6 in the hold after.

| run | traj windows flagged (89 Hz line, max RMS) | take-off/loiter windows (20-25 Hz, max RMS) | AUTO_LAND windows (peak Hz, max RMS) | max RMS / 5e-4 | key1 fixed / old / key2 sustained (noskip) |
|---|---|---|---|---|---|
| indi quiet_s1 | 25/29 (89.3, 6.9e-4) | 7/55 (22.3, 1.3e-3) | 4/30 (20.3, 1.9e-3) | 3.7 | 1/1/1 |
| indi quiet_s2 | 25/28 (89.3, 6.8e-4) | 0/56 | 3/31 (20.3, 2.4e-3) | 4.7 | 1/1/1 |
| indi quiet_s3 | 24/28 (89.3, 6.9e-4) | 5/55 (24.5, 8.9e-4) | 6/30 (20.0, 2.0e-3) | 4.1 | 1/1/1 |
| indi typ_s1 | 24/28 (89.3, 6.9e-4) | 7/55 (24.5, 8.5e-4) | 12/30 (22.3, 2.1e-3) | 4.1 | 1/1/1 |
| indi typ_s2 | 25/29 (89.3, 6.9e-4) | 5/54 (22.5, 7.3e-4) | 12/30 (22.3, 3.2e-3) | 6.3 | 1/1/1 |
| indi typ_s3 | 25/29 (89.3, 7.0e-4) | 14/54 (20.5, 2.3e-3) | 13/30 (20.0, 2.1e-3) | 4.5 | 1/1/1 |
| indi harsh_s1 | 25/28 (88.8, 7.4e-4) | 14/55 (23.0, 1.3e-3) | 19/30 (22.0, 4.3e-3) | 8.6 | 1/1/1 |
| indi harsh_s2 | 26/29 (88.9, 6.9e-4) | 17/54 (20.0, 1.6e-3) | 20/32 (22.3, 2.8e-3) | 5.6 | 1/1/1 |
| indi harsh_s3 | 25/28 (88.9, 6.9e-4) | 14/55 (24.5, 1.3e-3) | 20/32 (22.3, 3.0e-3) | 6.0 | 1/1/1 |
| PID typ_s1 | 0/28 | 0/57 | 4/30 (26.0, 1.2e-3), span 65.5-71.0 = touchdown only | 2.4 | 0/0/0 (all span/skip combos) |

All 9 INDI runs: key1 fixed, key1 old and key2 all 1 with no skip (9/9); with the 3 s nav skip only the old-width key1 flips to 0 in some skip cases (typ_s1, harsh_s2, harsh_s3); key1 fixed and key2 stay 1 in every run and span/skip combination. PID flight not repeated for harsh (typ shows no chatter, step 4 condition not met).

## Conclusion
- The cruise flag is INDI-specific: PID typ_s1 (same scenario, seed, noise) has 0 sustained chatter and no line in the trajectory (0/28 windows) or in take-off/loiter; only a 4-window ~26 Hz touchdown transient (1.2e-3) in the last 5 s, same as the PID hover references.
- Three INDI lines. (a) During the lemniscate (35-52.5 s, continuous, all 9 runs, quiet to harsh alike): ~89 Hz, max line RMS 6.8e-4 to 7.4e-4 = 1.4-1.5x the floor; borderline in amplitude, flagged 24-26 of ~28 windows, absent in the preceding/following hover. (b) During AUTO_LAND: 20-22 Hz, 1.9e-3 to 4.3e-3 = 4-8.6x the floor (same line as hover s175; larger in harsh), starts about 2 s after AUTO_LAND entry window. (c) Weak 20-25 Hz in take-off/loiter in 8 of 9 runs, 7.3e-4 to 2.3e-3 (1.5-4.6x); not in PID.
- Largest exceedance overall is the landing line (up to 8.6x floor), not cruise itself. The cruise (89 Hz) line alone is 1.4-1.5x the threshold, would pass if the floor were ~1e-3 but the landing and take-off lines would still flag.
- Unverified: cause of the 89 Hz line (no probe, e.g. rotor-rate related or position/rate loop); constant-velocity vs turns not separable (lemniscate); PID is a single seed; log-clock offset +-0.3 s.

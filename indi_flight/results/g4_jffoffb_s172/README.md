# G4 harsh hover re-fly, D-JFF-OFFB (rate FF only in offboard), S172

Fix under test: `_indi.setFeedforward(_vehicle_control_mode.flag_control_offboard_enabled)` in McIndiPosControl.cpp (uncommitted).
Not committed. Writes only under this directory.

## Commands (repo root, Docker only)
- Build: `indi_project/docker/run.sh -n s172offbbuild -t 3000 -- make px4_sitl_default` -> build.log, BUILD_RC 0;
  `McIndiPosControl.cpp.o` recompiled (1 hit).
- Format: `run.sh -n s172offbfmt -- sh Tools/astyle/check_code_style.sh src/modules/mc_indi_pos_control/McIndiPosControl.cpp`
  -> astyle.log, rc 0.
- Flights: `sh indi_flight/bench/gate_g4.sh fly indi_flight/results/g4_jffoffb_s172 harsh hover <1|2|3>`, serial; status.txt 3 x rc 0.
- Analysis: `run.sh -n s172offbana -- bash indi_flight/results/g4_jffoffb_s172/analyse.sh` -> analyse.log, g4_table.md,
  per-run g3_checks.json (window = G4 window, ulog base; exit 1 = FAIL verdict, not an error), omega_offb.py (pyulog).

## Per run (all harsh hover, rc 0)
| run | R20 % | R4 % | C20 | i1 | i2 (no chatter) | i3 | omega_ff offb / land peak (deg/s) | descent q std (deg/s) |
|---|---|---|---|---|---|---|---|---|
| harsh_s1 | 0.034 | 0.085 | 0.00053 | PASS | PASS | PASS | 0 / 0 | 1.9 |
| harsh_s2 | 0.034 | 0.085 | 0.00053 | PASS | PASS | PASS | 0 / 0 | 13.9 |
| harsh_s3 | 0.034 | 0.084 | 0.00053 | PASS | FAIL: p (roll) 2.0 Hz, 3 windows | PASS | 0 / 0 | 0.4 |

Chatter (A-54 70 Hz line) flagged in all 3, as before. Item-2 flag position harsh_s3: window index 82, airborne start 11.49 s,
so about 93.5-98.5 s, straddling AUTO_LAND entry (96.1 s). Offboard entry at 28.8-29.0 s, land entry 95.9-96.1 s, touchdown 104.8-105.1 s.

## Comparison with results/g4_jff_s172 (D-JFF-SOURCE, harsh rows, same computation)
| | D-JFF-SOURCE (prev) | D-JFF-OFFB (this) |
|---|---|---|
| omega_ff land peak (deg/s) | 24.0-27.6 (3 runs) | 0 (3 runs) |
| descent q std (deg/s) | 10.9-12.4 | 0.4, 1.9, 13.9 |
| item 2 (no chatter) | 1/3 fail (q 2.5 Hz) | 1/3 fail (p 2.0 Hz) |

## Verdicts (G4 rows R20/R4/C20/clip: PASS 3/3)
- omega_ff target (< 3 deg/s over [AUTO_LAND entry, touchdown]): PASS 3/3 (exactly 0). FF is off in AUTO_LAND as intended.
- Sanity (offboard FF nonzero?): NOT SHOWN. omega_ff is 0 in the offboard hold too (0 nonzero samples). Expected for a constant
  hover setpoint, since FF is a difference of the acceleration setpoint, so this check is uninformative with hover runs.
  A moving offboard trajectory is needed to show FF is on in offboard. Unverified.
- Descent pitch-rate std is not consistent (0.4, 1.9, 13.9). With FF zero, harsh_s2 still has large pitch noise, so the
  descent oscillation is not caused by omega_ff alone. Not investigated.
- Item 2 harsh_s3 still flags a 2 Hz line near AUTO_LAND entry (roll axis), not cleared.

# G4 hover re-fly with D-JFF-SOURCE (S172)

Fix under test: uncommitted diff in src/modules/mc_indi_pos_control/ (jerk feed-forward always differenced from a_ff;
trajectory_setpoint.jerk not used). Result: the omega_ff target (< 3 deg/s) is NOT met. Not committed, no firmware edits.

## Commands (repo root, Docker only)
- Build: `indi_project/docker/run.sh -n s172build -t 3000 -- make px4_sitl_default` -> build.log, BUILD_RC 0
  (run_scenario.py flies build/px4_sitl_default by default; McIndiPosControl.cpp recompiled).
- Format (check only): `run.sh -n s172fmt -- sh Tools/astyle/check_code_style.sh <file>` for the .cpp and .hpp: rc 0 both.
  `git diff --check` on the module: no output.
- Flights: `sh indi_flight/bench/gate_g4.sh fly indi_flight/results/g4_jff_s172 <pr> hover <sd>`, 9 serial, driver batch_driver.out,
  BATCH_DONE marker. status.txt: 9 x `rc 0`. Stray px4-indi containers before the batch: none.
- Score: `run.sh -n g4score -t 900 -- sh indi_flight/bench/gate_g4.sh score indi_flight/results/g4_jff_s172` -> g4_table.md.
- g3: `run.sh -n g3s172b -- bash indi_flight/results/g4_jff_s172/g3_batch.sh` (window = G4 window, hold+5 s..end, ulog base,
  as the s169 g3_checks.json files). Output hover_*/g3_checks.json; exit 1 = verdict FAIL, not an error.
- omega_ff: `run.sh -n omega172 -- bash indi_flight/results/g4_jff_s172/omega_batch.sh` (omega_ff.py, pyulog). AUTO_LAND =
  vehicle_status nav_state 18 entry; touchdown = first vehicle_land_detected landed==1 after entry; q = vehicle_angular_velocity xyz[1].

## Runs (new = D-JFF-SOURCE build, all hover, rc 0)
R20/R4/C20/C4/clip from g4_table.md (all PASS, margin large). i1 = item 1 LOC, i2nc = item 2 on p,q,r,position (no chatter),
i2 = item 2 as the script defines it (includes command_chatter, the known A-54 70 Hz line, flagged in all 9 runs),
i3 = item 3. omega_ff peak = max(|roll|,|pitch|) over [AUTO_LAND entry, touchdown].

| run | R20 % | R4 % | C20 | i1 | i2nc | i2 | i3 | omega_ff roll / pitch peak (deg/s) | peak t - entry (s) | descent q std (deg/s) |
|---|---|---|---|---|---|---|---|---|---|---|
| harsh_s1 | 0.034 | 0.085 | 0.00053 | P | P | F (chatter) | P | 24.0 / 26.5 | 1.5 | 12.4 |
| harsh_s2 | 0.034 | 0.085 | 0.00053 | P | P | F (chatter) | P | 24.5 / 26.5 | 1.3 | 10.9 |
| harsh_s3 | 0.034 | 0.086 | 0.00053 | P | F (q 2.5 Hz) | F | P | 24.5 / 27.6 | 1.4 | 12.1 |
| typ_s1 | 0.014 | 0.038 | 0.00022 | P | P | F (chatter) | P | 27.7 / 18.4 | 0.3 | 1.6 |
| typ_s2 | 0.014 | 0.038 | 0.00022 | P | P | F (chatter) | P | 27.6 / 21.0 | 0.3 | 1.8 |
| typ_s3 | 0.014 | 0.038 | 0.00022 | P | P | F (chatter) | P | 25.2 / 25.9 | 0.3 | 3.0 |
| quiet_s1 | 0.003 | 0.010 | 0.00003 | P | P | F (chatter) | P | 5.9 / 14.0 | 0.9 | 1.4 |
| quiet_s2 | 0.003 | 0.009 | 0.00003 | P | P | F (chatter) | P | 6.2 / 10.3 | 0.05 | 0.6 |
| quiet_s3 | 0.003 | 0.010 | 0.00003 | P | P | F (chatter) | P | 6.7 / 2.5 | 0.06 | 0.4 |

Item-2 flag positions (window index = seconds from the first airborne sample, airborne start from g3_checks.json):
- harsh_s3 new: q 2.5 Hz in 3 windows, index 83 (airborne start 11.41 s), i.e. about 94.4-99 s, straddling AUTO_LAND entry (96.0 s).
- chatter (command_chatter, 20-100 Hz) flagged in all 9 new runs: the known A-54 clause, not a new finding.

## Old vs new, harsh_s2 (same omega_ff computation; old = results/g4_gate_s169/hover_harsh_s2)
| run | omega_ff roll / pitch peak | peak t - entry | descent q std | item 2 q (current g3, like-for-like) |
|---|---|---|---|---|
| old S169 harsh_s2 | 27.4 / 26.1 | 1.1 s | 7.3 | 2.0 Hz, 3 windows, index 82 (~93.6 s): FAIL |
| new S172 harsh_s2 | 24.5 / 26.5 | 1.3 s | 10.9 | none on p,q,r,pos: PASS |
Old harsh_s1/s3 under current g3 (like-for-like): item 2 no-chatter PASS. Old omega_ff was not computed for s1/s3.

## Verdicts (G4 metric rows R20/R4/C20/clip: PASS 9/9)
- omega_ff target (< 3 deg/s peak): FAIL 9/9. Peaks 5.9-27.7 deg/s (quiet 6-7 roll, typ/harsh 24-28). Peaks sit at or within
  1.5 s of the AUTO_LAND entry, so the spike is still there after the fix.
- Item 2 without chatter: harsh 1/3 flagged (harsh_s3, 2.5 Hz at entry; old harsh_s2 2.0 Hz). Not cleared.
- Descent q noise: harsh q std 10.9-12.4 deg/s on new runs vs 7.3 old harsh_s2: not reduced in the harsh runs checked.

## Unverified / flagged
- The fix may not be the cause removed: the spike is still present at entry. Cause (e.g. the acceleration difference stepping at
  AUTO_LAND entry) NOT verified by this run; not investigated further (out of scope).
- AUTO_LAND entry here is 96.0 s (vehicle_status nav_state 18, ulog base), consistent with the s169 g3 t_land 96.0. The a56 README
  quotes 119.06 s entry / 127.2 s touchdown for the same old run: unexplained, not reconciled.
- bench/a55_key1_all.sh and the run.json event times: run.json is on a ~23 s different base from the ulog. Passing run.json times
  straight to g3_checks.py (as that script does) picks the wrong window (ground-state). This batch uses the G4 (ulog) window instead.
  Item 3 of the S170 A-55 check may have used the wrong window; not re-checked here.

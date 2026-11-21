# G5.10 SAT part feasibility (S187, owner Q21), seed 1, INDI and PID, freeze-9 config, no firmware edit, no commit

Why: owner Q21 (GATES.md "Owner amendments S187"): one flight per stack at thrust scale 0.30 (T/W 2.19) with a 3 m climb plus the 3 m x step;
valid only if all 4 motors >= 0.99 for >= 1 s in BOTH stacks, else the SAT part is dropped (option C).

Scenario diff: new `sat_q21` in bench/scenarios.py (`sat_sustained` untouched, other users). Segments settle 3 s, hov 4 s (SIM_GZ_THR_SC 0.30 via
motor_fault, one step during the settled hover), sat 6 s (setpoint +3 m x, +3 m up = NED z -3), rec 10 s (scale reset to 1). Event "sat" kept.
Scorer bench/g510_score_motors.py: recovery reference is now hold + the scenario's final "rec" seg_pos offset (`_target`), because the step is
not undone and the old reference (original hold) could never be reached within 0.3 m. Thresholds unchanged.

Command: `indi_flight/results/g510_q21_s187/fly.sh <indi|pid> 1` (copy of the s184 fly.sh, outputs here; timeout 1000, docker run.sh -t 900).

| stack | run | all-4 >= 0.99 in sat window | max motor in window | alt loss | tilt max | recovery | hover estimate in window | validity |
|---|---|---|---|---|---|---|---|---|
| INDI | completed | 0.0 s (any-motor 0.0 s) | 0.869 | 0.06 m | 28.2 deg | not reached (None) | 0.29 .. 0.337 (0.137 before hov; 0.337 looks like the estimator clamp) | INVALID (no saturation) |
| PID | WatchdogTrip at sim 60.75 (3.18 m below hold, 2.4 s after the scale step), no "sat" event | n/a | n/a | n/a | n/a | n/a | not read | INVALID (aborted before the step) |

Verdict: not valid in either stack, so per Q21 the SAT part is dropped (G5.10 = stabilized full-scale part, Q17 A). No further flights, no seeds 2-3.
INDI at scale 0.30 climbs 3 m with motors peaking at 0.87 (no saturation); PID cannot hold altitude after the single 0.30 step (hover estimate lags).
Not verified: PID with a gentler scale change (would be a different set-up than Q21); the 0.337 clamp value was not checked in source.

Raw files: flight.ulg (114 MB / 54 MB), sends.csv, gz.log, *.log are matched by indi_flight/.gitignore (*.ulg, results/**/sends.csv, results/**/*.log).
